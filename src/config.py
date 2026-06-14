"""
Project paths and settings.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ZIP_PATH = REPO_ROOT / "sample_data" / "archive.zip.download" / "archive.zip"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"

DATA_DIR = REPO_ROOT / "data" / "processed"
DB_PATH = DATA_DIR / "trials.db"
SCHEMA_PATH = REPO_ROOT / "src" / "db" / "schema.sql"

MAX_STUDIES = int(os.environ.get("MAX_STUDIES", "500"))
