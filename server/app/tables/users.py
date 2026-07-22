"""Users table: schema (DDL) and seed credentials.

Passwords are hashed at import time so the stored rows only ever hold bcrypt
hashes, never plaintext.
"""

import sqlite3

from passlib.context import CryptContext

from app.schemas import UserRole

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

SCHEMA = """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    )
"""

# Demo users. Passwords are hashed once, at import time.
_SEED_USERS = [
    ("demo", _pwd.hash("password123"), UserRole.USER),
    ("admin", _pwd.hash("admin123"), UserRole.ADMIN),
]


def seed(conn: sqlite3.Connection) -> None:
    """Insert the demo users."""
    conn.executemany(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        [
            (username, password_hash, role.value)
            for username, password_hash, role in _SEED_USERS
        ],
    )
