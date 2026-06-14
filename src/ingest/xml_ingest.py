"""
Read clinical trial XML files from a zip archive or a folder of fixtures.
"""

import logging
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from src.config import ZIP_PATH
from src.ingest.xml_parser import parse_study_xml
from src.transform.validate import make_parse_error

logger = logging.getLogger(__name__)


def _parse_file(data: bytes, source_file: str) -> tuple[dict | None, dict | None]:
    """Parse one XML file. Returns (record, parse_error) — only one is set."""
    try:
        return parse_study_xml(data, source_file=source_file), None
    except ET.ParseError as exc:
        logger.warning("XML parse error in %s: %s", source_file, exc)
        return None, make_parse_error(source_file, f"xml_parse_error: {exc}")


def extract_from_folder(folder: Path) -> tuple[list[dict], list[dict]]:
    """Parse all .xml files in a directory. Returns (records, parse_errors)."""
    records = []
    parse_errors = []

    for path in sorted(folder.glob("*.xml")):
        record, error = _parse_file(path.read_bytes(), source_file=path.name)
        if record:
            records.append(record)
        if error:
            parse_errors.append(error)

    return records, parse_errors


def extract_from_path(
    source_path: Path | None = None, max_studies: int = 500
) -> tuple[list[dict], list[dict]]:
    """Read up to max_studies XML files from the Kaggle zip."""
    zip_path = source_path or ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    records = []
    parse_errors = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        xml_names = [n for n in zf.namelist() if n.endswith(".xml")]
        for name in xml_names[:max_studies]:
            source_file = Path(name).name
            record, error = _parse_file(zf.read(name), source_file=source_file)
            if record:
                records.append(record)
            if error:
                parse_errors.append(error)

    return records, parse_errors
