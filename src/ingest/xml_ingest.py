"""
Read clinical trial XML files from a zip archive or a folder of fixtures.
"""

import zipfile
from pathlib import Path

from src.config import ZIP_PATH
from src.ingest.xml_parser import parse_study_xml


def extract_from_folder(folder: Path) -> list[dict]:
    """Parse all .xml files in a directory (used for tests)."""
    records = []
    for path in sorted(folder.glob("*.xml")):
        data = path.read_bytes()
        records.append(parse_study_xml(data, source_file=path.name))
    return records


def extract_from_path(source_path: Path | None = None, max_studies: int = 500) -> list[dict]:
    """Read up to max_studies XML files from the Kaggle zip."""
    zip_path = source_path or ZIP_PATH
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    records = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        xml_names = [n for n in zf.namelist() if n.endswith(".xml")]
        for name in xml_names[:max_studies]:
            data = zf.read(name)
            # Use the filename part for source_file (e.g. NCT00000102.xml)
            source_file = Path(name).name
            records.append(parse_study_xml(data, source_file=source_file))

    return records
