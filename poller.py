"""
ClassMind - step 4: the poller.

Checks all your active Classroom courses for new slide material,
extracts text, generates notes/highlights/quiz via Groq, and pushes the
result to Telegram. Run alongside bot.py — this script owns ingestion,
bot.py owns the interactive side (currently just /start).

Run:
    python poller.py

Requires token.json to already exist (run main.py -> /auth/login once
first) and chat_id.txt to exist (send /start to the bot once first).
"""

import json
import time
import traceback

import auth
import classroom_client
import config
import drive_extract
import generate
import telegram_push


def load_seen() -> set[str]:
    if not config.SEEN_MATERIALS_FILE.exists():
        return set()
    return set(json.loads(config.SEEN_MATERIALS_FILE.read_text()))


def save_seen(seen: set[str]) -> None:
    config.SEEN_MATERIALS_FILE.write_text(json.dumps(sorted(seen)))


def format_summary_message(course_name: str, post_title: str, materials: dict) -> str:
    highlights = "\n".join(f"- {h}" for h in materials.get("highlights", []))
    quiz_lines = []
    for i, qa in enumerate(materials.get("quiz", []), start=1):
        quiz_lines.append(f"{i}. {qa['question']}\n   Answer: {qa['answer']}")
    quiz = "\n\n".join(quiz_lines)

    return (
        f"New lecture processed: {post_title}\n"
        f"Course: {course_name}\n\n"
        f"Highlights:\n{highlights}\n\n"
        f"Quiz:\n{quiz}\n\n"
        f"Full notes in the next message."
    )


def process_item(creds, course_name: str, item: dict, seen: set[str]) -> None:
    key = f"{item['post_id']}:{item['drive_file_id']}"

    print(f"[{course_name}] new material: {item['drive_file_title']}")

    try:
        _, text = drive_extract.extract_text(creds, item["drive_file_id"])
    except ValueError as e:
        print(f"  skipped (unsupported type): {e}")
        seen.add(key)  # don't retry unsupported files every poll
        save_seen(seen)
        return
    except Exception:
        print("  extraction failed:")
        traceback.print_exc()
        return  # retry next poll

    if not text.strip():
        print("  skipped (no extractable text)")
        seen.add(key)
        save_seen(seen)
        return

    try:
        materials = generate.generate_lecture_materials(text)
    except Exception:
        print("  generation failed:")
        traceback.print_exc()
        return  # retry next poll

    try:
        summary = format_summary_message(course_name, item["post_title"], materials)
        telegram_push.push(summary)
        telegram_push.push(f"Full notes — {item['post_title']}:\n\n{materials['notes']}")
    except Exception:
        print("  push failed:")
        traceback.print_exc()
        return  # retry next poll; regenerating is wasteful but safe

    seen.add(key)
    save_seen(seen)
    print("  done.")


def run_once(seen: set[str]) -> set[str]:
    creds = auth.load_credentials()
    if creds is None:
        print("Not authenticated. Run main.py and visit /auth/login first.")
        return seen

    classroom = classroom_client.get_classroom_service(creds)
    courses = classroom_client.list_courses(classroom)

    for course in courses:
        course_id = course["id"]
        course_name = course["name"]

        try:
            items = classroom_client.list_new_course_materials(classroom, course_id)
        except Exception:
            print(f"[{course_name}] failed to list materials:")
            traceback.print_exc()
            continue

        for item in items:
            key = f"{item['post_id']}:{item['drive_file_id']}"
            if key in seen:
                continue
            process_item(creds, course_name, item, seen)

    return seen


def main() -> None:
    print(
        f"ClassMind poller starting. Checking every "
        f"{config.POLL_INTERVAL_SECONDS}s. Ctrl+C to stop."
    )
    seen = load_seen()
    while True:
        try:
            seen = run_once(seen)
        except Exception:
            print("Poll cycle failed:")
            traceback.print_exc()
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
