"""
ClassMind - Google OAuth helpers.

Single-user, local tool: credentials are pickled-as-JSON to token.json
after the first login, then silently refreshed on every subsequent run.
No session/user table needed at this scale.
"""

import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from config import CLIENT_SECRETS_FILE, REDIRECT_URI, SCOPES, TOKEN_FILE

# Holds in-flight Flow objects keyed by `state` between /auth/login and
# /auth/callback. Fine for a single local user; would need a real store
# (redis, db) if this ever became multi-user.
_pending_flows: dict[str, Flow] = {}


def build_flow() -> Flow:
    return Flow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )


def start_login() -> str:
    """Creates an auth URL and stashes the Flow so callback can finish it."""
    flow = build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",       # needed to get a refresh_token
        include_granted_scopes="true",
        prompt="consent",            # forces refresh_token on repeat logins too
    )
    _pending_flows[state] = flow
    return auth_url


def finish_login(state: str, authorization_response: str) -> Credentials:
    flow = _pending_flows.pop(state, None)
    if flow is None:
        # Fallback: rebuild the flow. Works because state is still valid
        # server-side with Google; we just lose the exact Flow instance.
        flow = build_flow()

    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    save_credentials(creds)
    return creds


def save_credentials(creds: Credentials) -> None:
    TOKEN_FILE.write_text(creds.to_json())


def load_credentials() -> Credentials | None:
    if not TOKEN_FILE.exists():
        return None

    data = json.loads(TOKEN_FILE.read_text())
    creds = Credentials.from_authorized_user_info(data, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)

    return creds
