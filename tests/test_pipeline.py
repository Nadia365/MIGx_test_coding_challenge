import os
import tempfile

from src.config import FIXTURES_DIR
from src.db.connection import get_connection
from src.pipeline import run_etl


def test_etl_loads_fixtures_into_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        result = run_etl(fixtures_folder=FIXTURES_DIR, db_path=db_path)

        assert result["valid"] >= 2
        assert result["loaded"]["studies"] >= 2

        conn = get_connection(db_path)
        cur = conn.execute("SELECT COUNT(*) FROM studies")
        count = cur.fetchone()[0]
        conn.close()
        assert count >= 2
