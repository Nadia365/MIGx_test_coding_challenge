"""
Command-line entry point for the ETL pipeline.

Examples:
    python -m src.run_pipeline --fixtures
    python -m src.run_pipeline --max-studies 500 --report
"""

import argparse

from src.config import FIXTURES_DIR, MAX_STUDIES
from src.db.connection import get_connection
from src.pipeline import run_etl
from src.analytics.report import print_report


def print_summary(result):
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
    print("\nLoaded rows:")
    for table, count in result["loaded"].items():
        print(f"  {table}: {count}")


def print_db_counts():
    conn = get_connection()
    try:
        print("\nDatabase row counts:")
        tables = ("studies", "study_conditions", "study_interventions", "study_locations")
        for table in tables:
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]}")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Run clinical trial ETL pipeline")
    parser.add_argument("--max-studies", type=int, default=MAX_STUDIES)
    parser.add_argument("--fixtures", action="store_true", help="Use tests/fixtures")
    parser.add_argument("--report", action="store_true", help="Print analytics after load")
    args = parser.parse_args()

    if args.fixtures:
        result = run_etl(fixtures_folder=FIXTURES_DIR)
    else:
        result = run_etl(max_studies=args.max_studies)

    print_summary(result)
    print_db_counts()

    if args.report:
        print_report()


if __name__ == "__main__":
    main()
