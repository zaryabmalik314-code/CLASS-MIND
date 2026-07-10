"""
One-time script: mark every currently-pending Classroom material as
"seen" WITHOUT generating notes for it. Run this once to clear the old
backlog, so the poller only reacts to new posts going forward.

Usage (locally or via Railway Console, same folder as poller.py):
    python mark_backlog_seen.py
"""
import auth
import classroom_client
from poller import load_seen, save_seen

def main():
    creds = auth.load_credentials()
    if not creds:
        print("Not authenticated. Run main.py and visit /auth/login first.")
        return

    seen = load_seen()
    classroom = classroom_client.get_classroom_service(creds)
    courses = classroom_client.list_courses(classroom)

    marked = 0
    for course in courses:
        course_id = course["id"]
        course_name = course["name"]
        try:
            items = classroom_client.list_new_course_materials(classroom, course_id)
        except Exception as e:
            print(f"[{course_name}] failed to list materials: {e}")
            continue
        for item in items:
            key = f"{item['post_id']}:{item['drive_file_id']}"
            if key in seen:
                continue
            seen.add(key)
            marked += 1
            print(f"[{course_name}] marked as seen (skipped): {item['drive_file_title']}")

    save_seen(seen)
    print(f"\nDone. Marked {marked} old items as seen. Poller will now only react to new posts.")

if __name__ == "__main__":
    main()
