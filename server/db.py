import sqlite3
from pathlib import Path

DB_PATH = Path("data/server/vault.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vaults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    server_share TEXT NOT NULL,
    encrypted_vault BLOB NOT NULL,
    vault_nonce BLOB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_db()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def close_db(conn: sqlite3.Connection) -> None:
    conn.close()