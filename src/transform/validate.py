"""
Validate cleaned records and write rejected rows to a quarantine CSV.
"""

import csv
import re
from pathlib import Path

from src.config import QUARANTINE_DIR

NCT_PATTERN = re.compile(r"^NCT\d{8}$")
QUARANTINE_FILE = QUARANTINE_DIR / "rejected_studies.csv"


def filter_child_rows(record: dict) -> dict:
    """
    Drop empty child rows (conditions/interventions/locations with no useful data).
    """
    conditions = [
        c for c in record.get("conditions", [])
        if (c.get("condition_name") or "").strip()
    ]
    interventions = [
        i for i in record.get("interventions", [])
        if (i.get("intervention_name") or "").strip()
    ]
    locations = [
        loc for loc in record.get("locations", [])
        if any(loc.get(k) for k in ("country", "city", "state"))
    ]
    return {
        **record,
        "conditions": conditions,
        "interventions": interventions,
        "locations": locations,
    }


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

    start = study.get("start_date")
    completion = study.get("completion_date")
    if start and completion and start > completion:
        return False, "start_date after completion_date"

    return True, ""


def validate_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Split records into valid and invalid lists.
    Duplicate nct_id: keep the last occurrence (simulates reload).
    """
    valid_by_id: dict[str, dict] = {}
    invalid: list[dict] = []

    for record in records:
        sanitized = filter_child_rows(record)
        ok, reason = validate_record(sanitized)
        nct_id = sanitized["study"].get("nct_id", "")

        if not ok:
            invalid.append({**sanitized, "rejection_reason": reason})
            continue

        valid_by_id[nct_id] = sanitized

    return list(valid_by_id.values()), invalid


def make_parse_error(source_file: str, message: str = "xml_parse_error") -> dict:
    """Build a quarantine row for a file that failed XML parsing."""
    return {
        "study": {"nct_id": "", "title": "", "source_file": source_file},
        "rejection_reason": message,
    }


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
