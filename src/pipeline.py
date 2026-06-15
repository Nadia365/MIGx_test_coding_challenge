"""
Main ETL pipeline: Extract -> Transform -> Load.

This file ties the steps together in order.
"""

from src.config import DB_PATH, MAX_STUDIES
from src.db.connection import get_connection, init_database
from src.ingest.xml_ingest import extract_from_folder, extract_from_path
from src.load.loader import load_records
from src.transform.clean import clean_record
from src.transform.validate import validate_records, write_quarantine


def run_etl(source_path=None, fixtures_folder=None, max_studies=None, db_path=None):
    """
    Run the full pipeline.

    fixtures_folder -> use test XML files (for tests / Docker demo)
    otherwise       -> read from the Kaggle zip
    """
    limit = max_studies if max_studies is not None else MAX_STUDIES
    target_db = db_path or DB_PATH

    # --- Step 1: Extract ---
    print("STEP 1/3 EXTRACT — reading XML files")
    if fixtures_folder:
        print(f"  source: {fixtures_folder}")
        raw_records, parse_errors = extract_from_folder(fixtures_folder)
    else:
        print(f"  source: zip (max {limit} studies)")
        raw_records, parse_errors = extract_from_path(source_path, max_studies=limit)

    print(f"  extracted {len(raw_records)} records, {len(parse_errors)} parse errors")

    # --- Step 2: Transform ---
    print("STEP 2/3 TRANSFORM — clean and validate")
    cleaned = []
    for record in raw_records:
        cleaned.append(clean_record(record))

    valid, invalid = validate_records(cleaned)
    all_rejected = invalid + parse_errors
    quarantine_path = write_quarantine(all_rejected)

    print(f"  valid: {len(valid)}, rejected: {len(all_rejected)}")

    # --- Step 3: Load ---
    print("STEP 3/3 LOAD — writing to SQLite")
    init_database(db_path=target_db)
    conn = get_connection(target_db)
    try:
        counts = load_records(conn, valid)
    finally:
        conn.close()

    for table, count in counts.items():
        print(f"  {table}: {count} rows")

    return {
        "extracted": len(raw_records),
        "parse_errors": len(parse_errors),
        "valid": len(valid),
        "rejected": len(all_rejected),
        "validation_rejected": len(invalid),
        "quarantine_file": str(quarantine_path) if quarantine_path else None,
        "loaded": counts,
    }
