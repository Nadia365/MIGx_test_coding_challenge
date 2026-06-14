"""
Parse one ClinicalTrials.gov XML file into a study record + child rows.
"""

import xml.etree.ElementTree as ET


def _text(parent, tag: str) -> str:
    """Get trimmed text from a child tag, or empty string."""
    if parent is None:
        return ""
    child = parent.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def parse_study_xml(xml_bytes: bytes, source_file: str = "") -> dict:
    """
    Parse XML bytes into the pipeline record shape:
      { study: {...}, conditions: [...], interventions: [...], locations: [...] }
    """
    root = ET.fromstring(xml_bytes)

    id_info = root.find("id_info")
    nct_id = _text(id_info, "nct_id") if id_info is not None else ""

    study = {
        "nct_id": nct_id,
        "title": _text(root, "brief_title"),
        "study_type": _text(root, "study_type"),
        "phase": _text(root, "phase"),
        "status": _text(root, "overall_status"),
        "start_date": _text(root, "start_date"),
        "completion_date": _text(root, "completion_date"),
        "enrollment": _text(root, "enrollment"),
        "source_file": source_file,
    }

    conditions = []
    for cond in root.findall("condition"):
        if cond.text and cond.text.strip():
            conditions.append({"condition_name": cond.text.strip()})

    interventions = []
    for inter in root.findall("intervention"):
        name = _text(inter, "intervention_name")
        if name:
            interventions.append(
                {
                    "intervention_name": name,
                    "intervention_type": _text(inter, "intervention_type") or None,
                }
            )

    locations = []
    for loc in root.findall("location"):
        addr = loc.find("facility/address")
        if addr is not None:
            locations.append(
                {
                    "country": _text(addr, "country") or None,
                    "city": _text(addr, "city") or None,
                    "state": _text(addr, "state") or None,
                }
            )

    return {
        "study": study,
        "conditions": conditions,
        "interventions": interventions,
        "locations": locations,
    }
