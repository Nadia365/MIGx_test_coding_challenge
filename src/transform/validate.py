"""
Check data quality and write bad rows to a quarantine CSV file.
"""

import csv
import re

from src.config import QUARANTINE_DIR

# Valid NCT IDs look like NCT00000102 (NCT + 8 digits)
NCT_PATTERN = re.compile(r"^NCT\d{8}$")
QUARANTINE_FILE = QUARANTINE_DIR / "rejected_studies.csv"


def filter_child_rows(record):
    """Remove empty condition/intervention/location rows."""
    conditions = []
    for c in record.get("conditions", []):
        name = (c.get("condition_name") or "").strip()
        if name:
            conditions.append(c)

    interventions = []
    for i in record.get("interventions", []):
        name = (i.get("intervention_name") or "").strip()
        if name:
            interventions.append(i)

    locations = []
    for loc in record.get("locations", []):
        has_data = loc.get("country") or loc.get("city") or loc.get("state")
        if has_data:
            locations.append(loc)

    return {
        "study": record["study"],
        "conditions": conditions,
        "interventions": interventions,
        "locations": locations,
    }


def validate_record(record):
    """
    Check one study record.
    Returns (True, '') if OK, or (False, reason) if bad.
    """
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


def validate_records(records):
    """
    Split records into valid and invalid lists.
    If the same nct_id appears twice, keep the last one.
    """
    valid_by_id = {}
    invalid = []

    for record in records:
        record = filter_child_rows(record)
        ok, reason = validate_record(record)
        nct_id = record["study"].get("nct_id", "")

        if not ok:
            record["rejection_reason"] = reason
            invalid.append(record)
        else:
            valid_by_id[nct_id] = record

    return list(valid_by_id.values()), invalid


def make_parse_error(source_file, message="xml_parse_error"):
    """Build a quarantine row when XML parsing fails."""
    return {
        "study": {"nct_id": "", "title": "", "source_file": source_file},
        "rejection_reason": message,
    }


def write_quarantine(invalid_records):
    """Save rejected rows to CSV. Returns file path, or None if nothing to save."""
    if not invalid_records:
        return None

    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    with QUARANTINE_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["nct_id", "title", "source_file", "rejection_reason"],
        )
        writer.writeheader()

        for rec in invalid_records:
            study = rec.get("study", {})
            writer.writerow({
                "nct_id": study.get("nct_id", ""),
                "title": study.get("title", ""),
                "source_file": study.get("source_file", ""),
                "rejection_reason": rec.get("rejection_reason", ""),
            })

    return QUARANTINE_FILE
