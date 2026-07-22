"""SQLite connection management and database initialisation.

Table schemas and seed data live in the :mod:`app.tables` package; this module
only owns the connection lifecycle and orchestrates create/seed on startup.
"""

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app import tables
from app.config import settings

_connection: sqlite3.Connection | None = None

# The connection is shared across the threadpool that serves requests
# (``check_same_thread=False``). A single sqlite3 connection is *not* safe for
# simultaneous use by multiple threads, so all access is serialised through this
# lock. It is held only for the duration of a logical DB operation, never across
# the slow event-bus publish, so concurrent writers still overlap on that cost.
_lock = threading.Lock()


def _get_connection() -> sqlite3.Connection:
    """Return the shared SQLite connection, creating it on first use."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(settings.database_path, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
    return _connection


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield the shared connection while holding the serialising lock.

    All access to the single shared connection must go through here so that
    concurrent requests never use it simultaneously. The lock is released as
    soon as the block exits, before any slow event-bus publish.
    """
    conn = _get_connection()
    with _lock:
        yield conn


def init_db() -> None:
    """Create every table's schema and seed deterministic sample data.

    ``reset_db_file`` has already removed any previous database file, so this
    starts from a clean schema without needing an explicit DROP.
    """
    conn = _get_connection()
    tables.create_all(conn)
    tables.seed_all(conn)


def reset_db_file() -> None:
    """Close any open connection and remove the database file for a clean start."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
    path = Path(settings.database_path)
    if path.exists():
        path.unlink()
