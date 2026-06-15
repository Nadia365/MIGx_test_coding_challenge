"""
Paths used across the project.
Change these here instead of hard-coding paths in every file.
"""

import os
from pathlib import Path

# Project root folder (one level up from src/)
REPO_ROOT = Path(__file__).resolve().parents[1]

# Where the Kaggle zip lives (not in git — download separately)
ZIP_PATH = REPO_ROOT / "sample_data" / "archive.zip.download" / "archive.zip"

# Small XML files used for tests and Docker demo
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"

# SQLite database file
DATA_DIR = REPO_ROOT / "data" / "processed"
DB_PATH = DATA_DIR / "trials.db"
SCHEMA_PATH = REPO_ROOT / "src" / "db" / "schema.sql"

# Bad rows go here as a CSV
QUARANTINE_DIR = REPO_ROOT / "data" / "quarantine"

# Analytics SQL file
QUERIES_PATH = REPO_ROOT / "src" / "analytics" / "queries.sql"

# How many XML files to read from the zip (use env var to override)
MAX_STUDIES = int(os.environ.get("MAX_STUDIES", "500"))
