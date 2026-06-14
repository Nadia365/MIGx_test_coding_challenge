"""
Create (or reset) the SQLite database using schema.sql.

Usage (from project root):
    python -m src.init_db
"""

from src.config import DB_PATH
from src.db.connection import init_database, list_tables


def main():
    print(f"Initializing database at: {DB_PATH}")
    init_database()
    tables = list_tables()
    print("Tables created:")
    for name in tables:
        print(f"  - {name}")
    print("Done.")


if __name__ == "__main__":
    main()
