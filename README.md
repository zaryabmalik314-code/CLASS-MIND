# ClassMind — Step 2: Classroom OAuth proof of concept

## Setup
1. Drop your real `client_secret.json` (downloaded from Google Cloud Console)
   into this folder, next to `main.py`.
2. `pip install -r requirements.txt`
3. `uvicorn main:app --reload`

## Test the flow
1. Open http://localhost:8000/auth/login in your browser.
2. Log in with your Google account (must be added as a test user in the
   OAuth consent screen, since the app is in Testing mode).
3. Approve the requested scopes. You'll be redirected back and see a
   `{"status": "connected", ...}` JSON response. This also writes
   `token.json` to disk — that's your saved (and auto-refreshing)
   credential for all future runs.
4. Open http://localhost:8000/courses — you should see your enrolled
   Classroom courses as JSON.

## Notes
- `token.json` and `client_secret.json` are secrets — add both to
  `.gitignore` before you push this anywhere.
- Scopes requested now include coursework/materials and Drive readonly,
  even though step 2 only *uses* the courses scope. This is so you won't
  need to re-consent when you build the ingestion step — just re-run
  /auth/login once if Google ever complains about missing scopes.
- If Google throws a redirect_uri_mismatch error, double check the
  redirect URI in Cloud Console matches http://localhost:8000/auth/callback
  exactly (no trailing slash).
