"""
Parse one ClinicalTrials.gov XML file into a Python dictionary.
"""

import xml.etree.ElementTree as ET


def get_xml_text(parent, tag):
    """Read text from a child XML tag. Returns '' if missing."""
    if parent is None:
        return ""
    child = parent.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def parse_study_xml(xml_bytes, source_file=""):
    """
    Turn one XML file into our pipeline record shape:

        study       -> one dict with nct_id, title, dates, etc.
        conditions  -> list of disease names
        interventions -> list of drugs/treatments
        locations   -> list of cities/countries
    """
    root = ET.fromstring(xml_bytes)

    # Main study fields
    id_info = root.find("id_info")
    if id_info is not None:
        nct_id = get_xml_text(id_info, "nct_id")
    else:
        nct_id = ""

    study = {
        "nct_id": nct_id,
        "title": get_xml_text(root, "brief_title"),
        "study_type": get_xml_text(root, "study_type"),
        "phase": get_xml_text(root, "phase"),
        "status": get_xml_text(root, "overall_status"),
        "start_date": get_xml_text(root, "start_date"),
        "completion_date": get_xml_text(root, "completion_date"),
        "enrollment": get_xml_text(root, "enrollment"),
        "source_file": source_file,
    }

    # One row per <condition> tag
    conditions = []
    for cond in root.findall("condition"):
        if cond.text and cond.text.strip():
            conditions.append({"condition_name": cond.text.strip()})

    # One row per <intervention> tag
    interventions = []
    for inter in root.findall("intervention"):
        name = get_xml_text(inter, "intervention_name")
        if name:
            interventions.append({
                "intervention_name": name,
                "intervention_type": get_xml_text(inter, "intervention_type") or None,
            })

    # One row per <location> tag
    locations = []
    for loc in root.findall("location"):
        addr = loc.find("facility/address")
        if addr is not None:
            locations.append({
                "country": get_xml_text(addr, "country") or None,
                "city": get_xml_text(addr, "city") or None,
                "state": get_xml_text(addr, "state") or None,
            })

    return {
        "study": study,
        "conditions": conditions,
        "interventions": interventions,
        "locations": locations,
    }
