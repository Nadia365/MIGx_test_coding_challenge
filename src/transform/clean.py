"""
Clean and normalize parsed study records before validation and load.
"""

import re
from datetime import datetime

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def clean_phase(phase: str | None) -> str:
    """Empty phase becomes 'Unknown' so analytics can group it."""
    if not phase or not str(phase).strip():
        return "Unknown"
    return str(phase).strip()


def clean_date(raw: str | None) -> str | None:
    """
    Normalize messy XML date strings to ISO YYYY-MM-DD.
    Returns None when the value is missing or unparseable.
    """
    if not raw or not str(raw).strip():
        return None

    text = str(raw).strip()

    # Already ISO-like: 1994-02-01 or 1994-02
    if re.match(r"^\d{4}-\d{2}(-\d{2})?$", text):
        parts = text.split("-")
        year, month = parts[0], parts[1]
        day = parts[2] if len(parts) > 2 else "01"
        return f"{year}-{month}-{day}"

    # "February 1994" or "December 1990"
    match = re.match(r"^([A-Za-z]+)\s+(\d{4})$", text)
    if match:
        month_name, year = match.groups()
        month_num = MONTHS.get(month_name.lower())
        if month_num:
            return f"{year}-{month_num:02d}-01"

    # "November 3, 1999"
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%Y"):
        try:
            dt = datetime.strptime(text, fmt)
            if fmt == "%Y":
                return f"{dt.year}-01-01"
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def _clean_enrollment(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def clean_record(record: dict) -> dict:
    """Return a copy of the record with cleaned study fields."""
    study = dict(record["study"])
    study["phase"] = clean_phase(study.get("phase"))
    study["start_date"] = clean_date(study.get("start_date"))
    study["completion_date"] = clean_date(study.get("completion_date"))
    study["enrollment"] = _clean_enrollment(study.get("enrollment"))

    return {
        "study": study,
        "conditions": list(record.get("conditions", [])),
        "interventions": list(record.get("interventions", [])),
        "locations": list(record.get("locations", [])),
    }
