"""Foydalanuvchining oxirgi dizaynini server qayta yoqilganda ham saqlaydi."""
import json
import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parent / "data")))
DATABASE = DATA_DIR / "logo_bot.sqlite3"


def db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DATABASE, timeout=10)
    return con


def init_db():
    with db() as con:
        con.execute("CREATE TABLE IF NOT EXISTS last_logo (user_id INTEGER PRIMARY KEY, spec TEXT NOT NULL)")


def get_spec(user_id: int):
    with db() as con:
        row = con.execute("SELECT spec FROM last_logo WHERE user_id=?", (user_id,)).fetchone()
    return json.loads(row[0]) if row else None


def save_spec(user_id: int, spec: dict):
    clean = {k: v for k, v in spec.items() if not k.startswith("_")}
    with db() as con:
        con.execute("INSERT INTO last_logo (user_id, spec) VALUES (?, ?) "
                    "ON CONFLICT(user_id) DO UPDATE SET spec=excluded.spec", (user_id, json.dumps(clean, ensure_ascii=False)))


def reset_spec(user_id: int):
    with db() as con:
        con.execute("DELETE FROM last_logo WHERE user_id=?", (user_id,))
