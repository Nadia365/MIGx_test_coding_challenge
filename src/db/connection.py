"""
SQLite database helpers.

Creates the database file and applies schema.sql.
"""

import sqlite3
from pathlib import Path

from src.config import DB_PATH, DATA_DIR, SCHEMA_PATH


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a connection to the trials database."""
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database(db_path: Path | str | None = None, schema_path: Path | str | None = None) -> Path:
    """
    Create tables and indexes from schema.sql.
    Safe to run multiple times (uses IF NOT EXISTS).
    """
    db = Path(db_path) if db_path else DB_PATH
    schema = Path(schema_path) if schema_path else SCHEMA_PATH

    if not schema.exists():
        raise FileNotFoundError(f"Schema file not found: {schema}")

    sql = schema.read_text(encoding="utf-8")
    conn = get_connection(db)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()

    return db


def list_tables(db_path: Path | str | None = None) -> list[str]:
    """Return table names in the database (useful for tests)."""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
