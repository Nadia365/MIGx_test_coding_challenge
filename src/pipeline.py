"""
ETL pipeline: Extract XML -> Transform -> Load into SQLite.
"""

import logging
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

    # Extract
    if fixtures_folder:
        logger.info("Extracting from fixtures: %s", fixtures_folder)
        raw_records = extract_from_folder(fixtures_folder)
    else:
        logger.info("Extracting from zip (max=%s)", limit)
        raw_records = extract_from_path(source_path, max_studies=limit)

    # Transform
    cleaned = [clean_record(r) for r in raw_records]
    valid, invalid = validate_records(cleaned)
    quarantine_path = write_quarantine(invalid)

    # Load
    target_db = db_path or DB_PATH
    init_database(db_path=target_db)
    conn = get_connection(target_db)
    try:
        counts = load_records(conn, valid)
    finally:
        conn.close()

    return {
        "extracted": len(raw_records),
        "valid": len(valid),
        "rejected": len(invalid),
        "quarantine_file": str(quarantine_path) if quarantine_path else None,
        "loaded": counts,
    }
