"""Database table definitions and seed data.

Each submodule owns one table's schema (DDL) and its deterministic seed data.
``create_all`` / ``seed_all`` fan out across every table so ``app.db`` stays a
generic connection/initialisation layer with no table-specific knowledge.
"""

import sqlite3

from app.tables import products, users

# Order matters if tables ever reference each other; keep dependencies first.
_TABLES = (products, users)


def create_all(conn: sqlite3.Connection) -> None:
    """Create every table's schema."""
    for table in _TABLES:
        conn.execute(table.SCHEMA)


def seed_all(conn: sqlite3.Connection) -> None:
    """Seed every table with its deterministic sample data."""
    for table in _TABLES:
        table.seed(conn)
    conn.commit()
