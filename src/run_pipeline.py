"""
Run the clinical trial ETL pipeline.

Usage (from project root):
    python -m src.run_pipeline
    python -m src.run_pipeline --max-studies 500
    python -m src.run_pipeline --fixtures
"""

import argparse
import logging

from src.config import FIXTURES_DIR, MAX_STUDIES
from src.db.connection import get_connection
from src.pipeline import run_etl

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def print_summary(result: dict) -> None:
    print("\n" + "=" * 50)
    print("PIPELINE SUMMARY")
    print("=" * 50)
    print(f"Extracted:  {result['extracted']}")
    print(f"Valid:      {result['valid']}")
    print(f"Rejected:   {result['rejected']}")
    if result.get("parse_errors"):
        print(f"Parse errs: {result['parse_errors']}")
    if result.get("quarantine_file"):
        print(f"Quarantine: {result['quarantine_file']}")
    if result.get("elapsed_seconds") is not None:
        print(f"Elapsed:    {result['elapsed_seconds']}s")
    print("\nLoaded rows:")
    for table, count in result["loaded"].items():
        print(f"  {table}: {count}")


def print_db_counts() -> None:
    conn = get_connection()
    try:
        print("\nDatabase row counts:")
        for table in ("studies", "study_conditions", "study_interventions", "study_locations"):
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]}")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Run clinical trial ETL pipeline")
    parser.add_argument(
        "--max-studies",
        type=int,
        default=MAX_STUDIES,
        help=f"Max XML files from zip (default: {MAX_STUDIES})",
    )
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Load tests/fixtures only (2 sample studies)",
    )
    args = parser.parse_args()

    if args.fixtures:
        result = run_etl(fixtures_folder=FIXTURES_DIR)
    else:
        result = run_etl(max_studies=args.max_studies)

    print_summary(result)
    print_db_counts()


if __name__ == "__main__":
    main()
