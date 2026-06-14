"""
Validate cleaned records and write rejected rows to a quarantine CSV.
"""

import csv
import re
from pathlib import Path

from src.config import QUARANTINE_DIR

NCT_PATTERN = re.compile(r"^NCT\d{8}$")
QUARANTINE_FILE = QUARANTINE_DIR / "rejected_studies.csv"


def validate_record(record: dict) -> tuple[bool, str]:
    """Check one record. Returns (is_valid, rejection_reason)."""
    study = record.get("study", {})
    nct_id = (study.get("nct_id") or "").strip()
    title = (study.get("title") or "").strip()

    if not nct_id:
        return False, "missing nct_id"
    if not NCT_PATTERN.match(nct_id):
        return False, "invalid nct_id format"
    if not title:
        return False, "missing title"

    return True, ""


def validate_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Split records into valid and invalid lists.
    Duplicate nct_id: keep the last occurrence (simulates reload).
    """
    valid_by_id: dict[str, dict] = {}
    invalid: list[dict] = []

    for record in records:
        ok, reason = validate_record(record)
        nct_id = record["study"].get("nct_id", "")

        if not ok:
            invalid.append({**record, "rejection_reason": reason})
            continue

        valid_by_id[nct_id] = record

    return list(valid_by_id.values()), invalid


def write_quarantine(invalid_records: list[dict]) -> Path | None:
    """Write rejected studies to CSV. Returns path or None if nothing rejected."""
    if not invalid_records:
        return None

    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for rec in invalid_records:
        study = rec.get("study", {})
        rows.append(
            {
                "nct_id": study.get("nct_id", ""),
                "title": study.get("title", ""),
                "source_file": study.get("source_file", ""),
                "rejection_reason": rec.get("rejection_reason", ""),
            }
        )

    fieldnames = ["nct_id", "title", "source_file", "rejection_reason"]
    with QUARANTINE_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return QUARANTINE_FILE
