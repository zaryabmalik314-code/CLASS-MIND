# Deploying ClassMind to Railway

This gets `bot.py` and `poller.py` running on Railway instead of your PC,
so Telegram's block in Pakistan stops being your problem — Railway's
servers aren't affected by it.

Google login is NOT redone on Railway. You already have a working
`token.json` from logging in locally — we just carry that over as an
environment variable. No Cloud Console changes needed.

## 1. Push this folder to GitHub

If it's not already a repo:
```powershell
cd "C:\Users\DELL\OneDrive\Documents\PROJECTS\CLASS MIND"
git init
git add .
git commit -m "ClassMind: OAuth + Telegram bot + ingestion pipeline"
```
Then create a repo on GitHub (via the website or `gh repo create`) and push.
`.gitignore` already excludes `client_secret.json`, `token.json`, `.env`,
`chat_id.txt`, `seen_materials.json` — none of your secrets get committed.

## 2. Create the Railway project

1. railway.app → New Project → Deploy from GitHub repo → pick this repo.
2. Railway will try to auto-deploy immediately — that's fine, we'll fix
   the start command next.

## 3. Add a Volume

In the Railway project → your service → Settings → Volumes → New Volume.
Mount it at: `/data`

This is where `token.json`, `chat_id.txt`, and `seen_materials.json` will
live — without this, Railway wipes those files on every redeploy.

## 4. Set environment variables

In Settings → Variables, add:

| Variable | Value |
|---|---|
| `DATA_DIR` | `/data` |
| `TELEGRAM_BOT_TOKEN` | (your bot token) |
| `GROQ_API_KEY` | (your Groq key) |
| `POLL_INTERVAL_SECONDS` | `300` (or whatever you want) |
| `GOOGLE_CLIENT_SECRET_JSON` | paste the full contents of your local `client_secret.json` |
| `GOOGLE_TOKEN_JSON` | paste the full contents of your local `token.json` |

To get those file contents on your PC:
```powershell
Get-Content client_secret.json -Raw
Get-Content token.json -Raw
```
Copy the output, paste as the env var value in Railway's dashboard.
(Paste into Railway, not into this chat.)

## 5. Two services, one repo

You need `bot.py` and `poller.py` running as two separate long-lived
processes. In Railway:

- Your first service: Settings → Deploy → Custom Start Command → `python bot.py`
- Add a second service in the same project (same repo, same env vars,
  same Volume mounted at `/data`) → Custom Start Command → `python poller.py`

Both services need the same environment variables and the same Volume
attached — that's how they share `chat_id.txt` (written by `bot.py`,
read by `poller.py` via `telegram_push.py`) and `token.json`.

## 6. Deploy and check logs

Once both services deploy, check each one's Logs tab:
- `bot.py` service should show: `ClassMind bot polling...`
- `poller.py` service should show: `ClassMind poller starting...` followed
  by it working through your courses

If `poller.py` errors on missing scopes again, it means the `token.json`
you copied into `GOOGLE_TOKEN_JSON` is stale — regenerate it locally
first (redo `/auth/login` once on your PC) before copying it over.

## 7. Ongoing updates

Any time you push new code to GitHub, Railway auto-redeploys both
services. The Volume persists across redeploys, so `token.json` etc.
won't be lost.
