"""
ClassMind - shared config.

Scopes are chosen a bit ahead of the current step so we don't have to
re-run the OAuth consent flow every time we add a feature later
(materials ingestion, Drive/Slides pulls, etc). Readonly everywhere —
we never write back to Classroom or Drive.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Allows OAuth redirect over http://localhost during local dev.
# Never set this in anything that isn't localhost.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# Google sometimes auto-grants extra scopes alongside what we requested
# (e.g. classroom.student-submissions.me.readonly tags along with
# classroom.coursework.me.readonly). oauthlib treats ANY scope mismatch
# as fatal by default, including the app receiving MORE than it asked
# for. This relaxes that check so token exchange doesn't crash.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

BASE_DIR = Path(__file__).parent

load_dotenv(BASE_DIR / ".env")  # reads local secrets from .env; no-ops if missing (e.g. on Railway)

# On Railway, DATA_DIR points at a mounted Volume so token.json/chat_id.txt/
# seen_materials.json survive redeploys. Locally it just defaults to this
# folder, same as before.
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR)))
DATA_DIR.mkdir(parents=True, exist_ok=True)

CLIENT_SECRETS_FILE = DATA_DIR / "client_secret.json"
TOKEN_FILE = DATA_DIR / "token.json"


def _bootstrap_file_from_env(path: Path, env_var: str) -> None:
    """
    If the file doesn't exist yet but its content was passed as an env var,
    write it out. Lets Railway start with credentials generated locally
    (via your one-time browser OAuth login) instead of needing its own
    interactive login — paste the *contents* of client_secret.json and
    token.json into Railway's env var values, not this chat.
    """
    if path.exists():
        return
    value = os.getenv(env_var)
    if value:
        path.write_text(value)


_bootstrap_file_from_env(CLIENT_SECRETS_FILE, "GOOGLE_CLIENT_SECRET_JSON")
_bootstrap_file_from_env(TOKEN_FILE, "GOOGLE_TOKEN_JSON")

REDIRECT_URI = "http://localhost:8000/auth/callback"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID_FILE = DATA_DIR / "chat_id.txt"

# --- Groq (generation) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Poller ---
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))  # 5 min default
SEEN_MATERIALS_FILE = DATA_DIR / "seen_materials.json"
