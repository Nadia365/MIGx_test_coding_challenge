"""
Read XML trial files from the zip archive or from a folder (tests/fixtures).
"""

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from src.config import ZIP_PATH
from src.ingest.xml_parser import parse_study_xml
from src.transform.validate import make_parse_error


def extract_from_folder(folder):
    """
    Read every .xml file in a folder.
    Returns: (good_records, parse_errors)
    """
    records = []
    parse_errors = []

    for path in sorted(folder.glob("*.xml")):
        try:
            data = path.read_bytes()
            record = parse_study_xml(data, source_file=path.name)
            records.append(record)
        except ET.ParseError:
            # Broken XML goes to quarantine, not crash the whole pipeline
            parse_errors.append(make_parse_error(path.name, "xml_parse_error"))

    return records, parse_errors


def extract_from_path(source_path=None, max_studies=500):
    """
    Read up to max_studies XML files from the Kaggle zip.
    Returns: (good_records, parse_errors)
    """
    zip_path = source_path or ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    records = []
    parse_errors = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        xml_names = [n for n in zf.namelist() if n.endswith(".xml")]

        for name in xml_names[:max_studies]:
            source_file = Path(name).name
            try:
                data = zf.read(name)
                record = parse_study_xml(data, source_file=source_file)
                records.append(record)
            except ET.ParseError:
                parse_errors.append(make_parse_error(source_file, "xml_parse_error"))

    return records, parse_errors
