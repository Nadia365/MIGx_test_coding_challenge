"""
Clean messy raw values before validation and load.
"""

import re
from datetime import datetime

# Map month names to numbers for dates like "February 1994"
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def clean_phase(phase):
    """Empty phase -> 'Unknown' so we can group it in analytics."""
    if not phase or not str(phase).strip():
        return "Unknown"
    return str(phase).strip()


def clean_date(raw):
    """
    Turn text dates into ISO format YYYY-MM-DD.
    Returns None if missing or we can't parse it.
    """
    if not raw or not str(raw).strip():
        return None

    text = str(raw).strip()

    # Already looks like 1994-02-01 or 1994-02
    if re.match(r"^\d{4}-\d{2}(-\d{2})?$", text):
        parts = text.split("-")
        year = parts[0]
        month = parts[1]
        day = parts[2] if len(parts) > 2 else "01"
        return f"{year}-{month}-{day}"

    # "February 1994" -> 1994-02-01
    match = re.match(r"^([A-Za-z]+)\s+(\d{4})$", text)
    if match:
        month_name = match.group(1).lower()
        year = match.group(2)
        month_num = MONTHS.get(month_name)
        if month_num:
            return f"{year}-{month_num:02d}-01"

    # "November 3, 1999" and a few other formats
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%Y"):
        try:
            dt = datetime.strptime(text, fmt)
            if fmt == "%Y":
                return f"{dt.year}-01-01"
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def clean_enrollment(value):
    """Turn enrollment string into an integer, or None if bad."""
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def clean_record(record):
    """Clean the study fields in one record. Child lists stay as-is."""
    study = dict(record["study"])
    study["phase"] = clean_phase(study.get("phase"))
    study["start_date"] = clean_date(study.get("start_date"))
    study["completion_date"] = clean_date(study.get("completion_date"))
    study["enrollment"] = clean_enrollment(study.get("enrollment"))

    return {
        "study": study,
        "conditions": list(record.get("conditions", [])),
        "interventions": list(record.get("interventions", [])),
        "locations": list(record.get("locations", [])),
    }
