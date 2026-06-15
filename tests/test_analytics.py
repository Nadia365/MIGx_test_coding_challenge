import os
import tempfile

from src.analytics.report import load_queries, run_report
from src.config import FIXTURES_DIR, QUERIES_PATH
from src.pipeline import run_etl


def test_load_queries_returns_five_queries():
    queries = load_queries(QUERIES_PATH)
    names = [name for name, _ in queries]
    assert len(queries) == 5
    assert "trials_by_type_and_phase" in names
    assert "top_conditions" in names
    assert "intervention_completion_rates" in names
    assert "geographic_distribution" in names
    assert "timeline_by_phase" in names


def test_analytics_queries_run_on_fixture_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        run_etl(fixtures_folder=FIXTURES_DIR, db_path=db_path)

        results = run_report(db_path=db_path)

        assert len(results) == 5
        for item in results:
            assert item["columns"]
            # fixture data is small but each query should execute without error
            assert isinstance(item["rows"], list)


def test_top_conditions_returns_fixture_conditions():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        run_etl(fixtures_folder=FIXTURES_DIR, db_path=db_path)

        results = run_report(db_path=db_path)
        top = next(r for r in results if r["name"] == "top_conditions")
        condition_names = {row[0] for row in top["rows"]}

        assert "Ocular Hypertension" in condition_names
        assert "Congenital Adrenal Hyperplasia" in condition_names
