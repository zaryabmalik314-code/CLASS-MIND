"""
ClassMind - Step 2 proof of concept.

Run:
    uvicorn main:app --reload

Flow:
    1. GET /            -> sanity check
    2. GET /auth/login   -> redirects to Google consent screen
    3. GET /auth/callback -> Google redirects here, we exchange code for
       tokens and save them to token.json
    4. GET /courses      -> uses saved token to call Classroom API and
       list your enrolled courses
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import auth

app = FastAPI(title="ClassMind")


@app.get("/")
def root():
    return {"status": "ok", "next": "GET /auth/login to connect Google Classroom"}


@app.get("/auth/login")
def login():
    auth_url = auth.start_login()
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
def callback(request: Request):
    full_url = str(request.url)
    state = request.query_params.get("state")

    if not state:
        raise HTTPException(400, "Missing state param from Google redirect")

    creds = auth.finish_login(state=state, authorization_response=full_url)
    return {
        "status": "connected",
        "message": "Token saved to token.json. You can close this tab and hit /courses.",
        "scopes_granted": creds.scopes,
    }


@app.get("/courses")
def list_courses():
    creds = auth.load_credentials()
    if creds is None:
        raise HTTPException(401, "Not authenticated yet. Visit /auth/login first.")

    service = build("classroom", "v1", credentials=creds)

    try:
        courses = []
        page_token = None
        while True:
            resp = (
                service.courses()
                .list(pageToken=page_token, courseStates=["ACTIVE"])
                .execute()
            )
            courses.extend(resp.get("courses", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    except HttpError as e:
        raise HTTPException(502, f"Classroom API error: {e}")

    return {
        "count": len(courses),
        "courses": [
            {"id": c["id"], "name": c["name"], "section": c.get("section")}
            for c in courses
        ],
    }
