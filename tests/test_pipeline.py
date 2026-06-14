import os
import tempfile
from pathlib import Path

from src.config import FIXTURES_DIR
from src.db.connection import get_connection
from src.pipeline import run_etl

FIXTURES_VALIDATION_DIR = Path(__file__).resolve().parent / "fixtures_validation"


def test_etl_loads_fixtures_into_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        result = run_etl(fixtures_folder=FIXTURES_DIR, db_path=db_path)

        assert result["valid"] >= 2
        assert result["parse_errors"] == 0
        assert result["loaded"]["studies"] >= 2

        conn = get_connection(db_path)
        cur = conn.execute("SELECT COUNT(*) FROM studies")
        count = cur.fetchone()[0]
        conn.close()
        assert count >= 2


def test_etl_quarantines_bad_validation_fixtures(quarantine_tmp):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        result = run_etl(fixtures_folder=FIXTURES_VALIDATION_DIR, db_path=db_path)

        assert result["extracted"] == 3
        assert result["parse_errors"] == 1
        assert result["validation_rejected"] == 3
        assert result["rejected"] == 4
        assert result["valid"] == 0
        assert result["quarantine_file"] is not None

        conn = get_connection(db_path)
        count = conn.execute("SELECT COUNT(*) FROM studies").fetchone()[0]
        conn.close()
        assert count == 0
