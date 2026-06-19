import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/acg_rights.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                creator_alias TEXT NOT NULL,
                work_type TEXT NOT NULL,
                platform_url TEXT,
                tags TEXT,
                declaration TEXT,
                file_path TEXT,
                file_name TEXT,
                sha256 TEXT,
                phash_hex TEXT,
                simhash_hex TEXT,
                text_sample TEXT,
                features_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def insert_work(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = dict(data)
    data["created_at"] = now
    data["features_json"] = json.dumps(data.get("features", {}), ensure_ascii=False)

    columns = [
        "title", "creator_alias", "work_type", "platform_url", "tags", "declaration",
        "file_path", "file_name", "sha256", "phash_hex", "simhash_hex", "text_sample",
        "features_json", "created_at"
    ]
    values = [data.get(c) for c in columns]

    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO works ({','.join(columns)}) VALUES ({','.join(['?'] * len(columns))})",
            values
        )
        conn.commit()
        return cur.lastrowid


def list_works(limit=200):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM works ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_work(work_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM works WHERE id = ?", (work_id,)).fetchone()
    return dict(row) if row else None
