"""
ClassMind - Telegram bot skeleton (step 3).

This is the interactive side of the bot: it polls Telegram for incoming
messages/commands. Run it as its own long-lived process, separate from
the FastAPI app (main.py) and separate from any future ingestion script.

Run:
    python bot.py

First step: send /start to your bot in Telegram. That saves your chat_id
to chat_id.txt, which is what telegram_push.py uses later to push
notes/quizzes to you without you needing to message first.
"""

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    config.CHAT_ID_FILE.write_text(str(chat_id))
    await update.message.reply_text(
        "ClassMind connected.\n\n"
        "I'll push structured notes, highlights, and a quiz here whenever "
        "a new lecture slide deck shows up in your tracked Classroom courses.\n\n"
        "Chat-based Q&A over your lecture content isn't wired up yet — "
        "that's a later step (RAG chat)."
    )


async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder until the RAG chat endpoint (step 6) is wired in.
    await update.message.reply_text(
        "Got your message, but I can't answer questions yet — "
        "that comes online once the RAG chat step is built."
    )


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN not set. Create a .env file next to bot.py "
            "with a line: TELEGRAM_BOT_TOKEN=your_token_here"
        )

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    print("ClassMind bot polling. Send /start to your bot in Telegram. Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
