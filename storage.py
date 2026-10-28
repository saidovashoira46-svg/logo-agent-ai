"""Persistent PostgreSQL on Render; local SQLite on Windows for development."""
import json
import os
import sqlite3
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
DATABASE = DATA_DIR / "logo_bot.sqlite3"


def _pg_conn():
    import psycopg
    return psycopg.connect(DATABASE_URL, connect_timeout=10)


def _sqlite_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE, timeout=10)


def _ensure_persistent():
    if os.getenv("RENDER") and not DATABASE_URL:
        raise RuntimeError("DATABASE_URL yo'q: Render lokal SQLite ma'lumotlarini saqlamaydi.")


def init_db():
    _ensure_persistent()
    if DATABASE_URL:
        with _pg_conn() as con:
            con.execute("CREATE TABLE IF NOT EXISTS last_logo (user_id BIGINT PRIMARY KEY, spec TEXT NOT NULL)")
    else:
        with _sqlite_conn() as con:
            con.execute("CREATE TABLE IF NOT EXISTS last_logo (user_id INTEGER PRIMARY KEY, spec TEXT NOT NULL)")


def get_spec(user_id: int):
    _ensure_persistent()
    if DATABASE_URL:
        with _pg_conn() as con:
            row = con.execute("SELECT spec FROM last_logo WHERE user_id=%s", (user_id,)).fetchone()
    else:
        with _sqlite_conn() as con:
            row = con.execute("SELECT spec FROM last_logo WHERE user_id=?", (user_id,)).fetchone()
    return json.loads(row[0]) if row else None


def save_spec(user_id: int, spec: dict):
    _ensure_persistent()
    clean = {k: v for k, v in spec.items() if not k.startswith("_")}
    body = json.dumps(clean, ensure_ascii=False)
    if DATABASE_URL:
        with _pg_conn() as con:
            con.execute("INSERT INTO last_logo (user_id,spec) VALUES (%s,%s) "
                        "ON CONFLICT(user_id) DO UPDATE SET spec=EXCLUDED.spec", (user_id, body))
    else:
        with _sqlite_conn() as con:
            con.execute("INSERT INTO last_logo (user_id,spec) VALUES (?,?) "
                        "ON CONFLICT(user_id) DO UPDATE SET spec=excluded.spec", (user_id, body))


def reset_spec(user_id: int):
    _ensure_persistent()
    if DATABASE_URL:
        with _pg_conn() as con:
            con.execute("DELETE FROM last_logo WHERE user_id=%s", (user_id,))
    else:
        with _sqlite_conn() as con:
            con.execute("DELETE FROM last_logo WHERE user_id=?", (user_id,))
