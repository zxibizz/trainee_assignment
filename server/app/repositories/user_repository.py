"""Data-access layer for users (SQLite)."""

from app.db import get_connection
from app.schemas import User, UserRole


class UserRepository:
    """All SQL for the ``users`` table lives here."""

    def get_password_hash(self, username: str) -> str | None:
        """Return the stored password hash for ``username``, or ``None``."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
        return row["password_hash"] if row is not None else None

    def get_user(self, username: str) -> User | None:
        """Return the ``User`` for ``username``, or ``None`` if unknown."""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT username, role FROM users WHERE username = ?", (username,)
            ).fetchone()
        if row is None:
            return None
        return User(username=row["username"], role=UserRole(row["role"]))
