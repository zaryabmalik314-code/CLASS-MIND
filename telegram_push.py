"""
ClassMind - push helper (step 3, other half).

Decoupled from bot.py on purpose: the ingestion/generation pipeline
(steps 4-6) will import `push()` to send notes/highlights/quizzes to you
whenever new lecture content is processed. It does a plain HTTP call to
the Bot API, so it doesn't need bot.py's polling loop running at all —
the pipeline and the interactive bot can run as separate processes,
or you can trigger a push from a one-off script/cron job.

Requires: you've sent /start to the bot at least once (so chat_id.txt
exists).

Run directly to send yourself a test message:
    python telegram_push.py
"""

import requests

import config

TELEGRAM_MAX_LEN = 4096
_SAFE_CHUNK = TELEGRAM_MAX_LEN - 100  # headroom for encoding overhead


def _chunks(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i : i + size]


def push(text: str, parse_mode: str | None = None) -> None:
    """
    Sends `text` to your saved chat_id, splitting into multiple messages
    if it exceeds Telegram's ~4096 char limit (lecture notes routinely will).

    parse_mode defaults to None (plain text) rather than Markdown, since
    LLM-generated content can contain *, _, [, ] etc. that break Telegram's
    Markdown parser and cause the whole send to fail. Only pass parse_mode
    explicitly for messages you've hand-written and control the formatting of.
    """
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN not set. Create a .env file next to this "
            "script with a line: TELEGRAM_BOT_TOKEN=your_token_here"
        )
    if config.TELEGRAM_CHAT_ID:
        chat_id = config.TELEGRAM_CHAT_ID
    elif config.CHAT_ID_FILE.exists():
        chat_id = config.CHAT_ID_FILE.read_text().strip()
    else:
        raise RuntimeError(
            "No chat_id available. Either set TELEGRAM_CHAT_ID as an env "
            "var, or run bot.py and send /start to your bot in Telegram "
            "first (writes chat_id.txt)."
        )

    for chunk in _chunks(text, _SAFE_CHUNK):
        data = {"chat_id": chat_id, "text": chunk}
        if parse_mode:
            data["parse_mode"] = parse_mode
        resp = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data,
            timeout=10,
        )
        resp.raise_for_status()


if __name__ == "__main__":
    push("ClassMind push test — if you see this, the backend can message you directly.")
    print("Push sent. Check Telegram.")
