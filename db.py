import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "classmind.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # lets readers work while writer commits
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            lecture_title TEXT NOT NULL,
            date_processed TEXT NOT NULL,
            notes TEXT NOT NULL,
            highlights TEXT NOT NULL,
            quiz TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_lecture(course_name: str, lecture_title: str, notes: str, highlights: list, quiz: list):
    conn = get_conn()
    conn.execute(
        """INSERT INTO lectures (course_name, lecture_title, date_processed, notes, highlights, quiz)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            course_name,
            lecture_title,
            datetime.now(timezone.utc).isoformat(),
            notes,
            json.dumps(highlights),
            json.dumps(quiz),
        ),
    )
    conn.commit()
    conn.close()
