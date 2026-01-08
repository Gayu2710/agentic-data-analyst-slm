import sqlite3
from pathlib import Path

# olist.db will live in the db/ folder at project root
DB_PATH = Path(__file__).resolve().parent.parent / "db" / "olist.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows as dict-like objects
    return conn
