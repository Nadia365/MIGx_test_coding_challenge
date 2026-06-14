"""
ETL pipeline: Extract XML -> Transform -> Load into SQLite.

Orchestrator: runs Extract, Transform (clean + validate), and Load in order.
"""

import logging
import time
from pathlib import Path

from src.config import DB_PATH, MAX_STUDIES
from src.db.connection import get_connection, init_database
from src.ingest.xml_ingest import extract_from_folder, extract_from_path
from src.load.loader import load_records
from src.transform.clean import clean_record
from src.transform.validate import validate_records, write_quarantine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_etl(
    source_path: Path | None = None,
    fixtures_folder: Path | None = None,
    max_studies: int | None = None,
    db_path: Path | None = None,
) -> dict:
    """
    Run extract, transform, and load.

    Use fixtures_folder for tests; otherwise reads from the zip file.
    """
    limit = max_studies if max_studies is not None else MAX_STUDIES
    t0 = time.perf_counter()

    # --- Extract ---
    logger.info("STEP 1/3 EXTRACT — reading XML files")
    if fixtures_folder:
        logger.info("  source: fixtures folder %s", fixtures_folder)
        raw_records, parse_errors = extract_from_folder(fixtures_folder)
    else:
        logger.info("  source: zip archive (max=%s studies)", limit)
        raw_records, parse_errors = extract_from_path(source_path, max_studies=limit)

    logger.info("  extracted %s records (%s parse errors)", len(raw_records), len(parse_errors))

    # --- Transform: clean + validate ---
    logger.info("STEP 2/3 TRANSFORM — clean and validate")
    cleaned = [clean_record(r) for r in raw_records]
    logger.info("  cleaned %s records", len(cleaned))

    valid, invalid = validate_records(cleaned)
    all_rejected = invalid + parse_errors
    quarantine_path = write_quarantine(all_rejected)

    logger.info(
        "  valid: %s | rejected: %s (validation: %s, parse errors: %s)",
        len(valid),
        len(all_rejected),
        len(invalid),
        len(parse_errors),
    )
    if quarantine_path:
        logger.info("  quarantine file: %s", quarantine_path)

    # --- Load ---
    logger.info("STEP 3/3 LOAD — writing to SQLite")
    target_db = db_path or DB_PATH
    init_database(db_path=target_db)
    conn = get_connection(target_db)
    try:
        counts = load_records(conn, valid)
    finally:
        conn.close()

    for table, count in counts.items():
        logger.info("  %s: %s rows inserted/updated", table, count)

    elapsed = time.perf_counter() - t0
    logger.info("Pipeline finished in %.1f seconds", elapsed)

    return {
        "extracted": len(raw_records),
        "parse_errors": len(parse_errors),
        "valid": len(valid),
        "rejected": len(all_rejected),
        "validation_rejected": len(invalid),
        "quarantine_file": str(quarantine_path) if quarantine_path else None,
        "loaded": counts,
        "elapsed_seconds": round(elapsed, 1),
    }
