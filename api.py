import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import get_conn, init_db

app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend's real origin before going live
    allow_methods=["GET"],
    allow_headers=["*"],
)


def row_to_lecture(row):
    return {
        "id": row["id"],
        "course": row["course_name"],
        "lecture_title": row["lecture_title"],
        "date": row["date_processed"],
        "notes": row["notes"],
        "highlights": json.loads(row["highlights"]),
        "quiz": json.loads(row["quiz"]),
    }


@app.get("/api/lectures")
def list_lectures():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM lectures ORDER BY date_processed DESC").fetchall()
    conn.close()
    return [row_to_lecture(r) for r in rows]


@app.get("/api/lectures/{lecture_id}")
def get_lecture(lecture_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM lectures WHERE id = ?", (lecture_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return row_to_lecture(row)


@app.get("/api/courses")
def list_courses():
    conn = get_conn()
    rows = conn.execute(
        "SELECT course_name, COUNT(*) as count FROM lectures GROUP BY course_name ORDER BY course_name"
    ).fetchall()
    conn.close()
    return [{"course": r["course_name"], "lecture_count": r["count"]} for r in rows]
