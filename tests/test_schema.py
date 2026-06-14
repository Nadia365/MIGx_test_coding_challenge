import os
import tempfile

from src.db.connection import init_database, list_tables, get_connection


def test_init_database_creates_all_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        init_database(db_path=db_path)

        tables = set(list_tables(db_path=db_path))
        expected = {
            "studies",
            "study_conditions",
            "study_interventions",
            "study_locations",
        }
        assert expected.issubset(tables)


def test_studies_table_accepts_insert():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        init_database(db_path=db_path)

        conn = get_connection(db_path)
        conn.execute(
            "INSERT INTO studies (nct_id, title) VALUES (?, ?)",
            ("NCT00000001", "Test Study"),
        )
        conn.commit()
        cur = conn.execute("SELECT COUNT(*) FROM studies")
        assert cur.fetchone()[0] == 1
        conn.close()
