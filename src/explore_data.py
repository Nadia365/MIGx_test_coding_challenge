"""
Step 1: Data exploration script for the All Clinical Trials dataset.

Reads a sample of XML files from the zip in sample_data/ and prints
basic stats about fields, missing values, and data quality issues.

Usage:
    python src/explore_data.py
    python src/explore_data.py --sample-size 300
"""

import argparse
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def get_text(element, tag: str) -> str:
    """Safely get text from a child XML tag."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def parse_one_study(xml_bytes: bytes) -> dict:
    """
    Parse one clinical study XML file into a simple dictionary.
    We keep this flat for exploration — normalization comes later.
    """
    root = ET.fromstring(xml_bytes)

    # nct_id lives under id_info in ClinicalTrials.gov XML
    id_info = root.find("id_info")
    nct_id = get_text(id_info, "nct_id") if id_info is not None else ""

    conditions = [c.text.strip() for c in root.findall("condition") if c.text]
    interventions = []
    for inter in root.findall("intervention"):
        interventions.append(
            {
                "name": get_text(inter, "intervention_name"),
                "type": get_text(inter, "intervention_type"),
            }
        )

    countries = []
    cities = []
    for loc in root.findall("location"):
        addr = loc.find("facility/address")
        if addr is not None:
            country = get_text(addr, "country")
            city = get_text(addr, "city")
            if country:
                countries.append(country)
            if city:
                cities.append(city)

    return {
        "nct_id": nct_id,
        "title": get_text(root, "brief_title"),
        "study_type": get_text(root, "study_type"),
        "phase": get_text(root, "phase"),
        "status": get_text(root, "overall_status"),
        "start_date": get_text(root, "start_date"),
        "completion_date": get_text(root, "completion_date"),
        "enrollment": get_text(root, "enrollment"),
        "num_conditions": len(conditions),
        "num_interventions": len(interventions),
        "num_locations": len(countries),
        "conditions": conditions,
        "countries": countries,
    }


def explore_zip(zip_path: Path, sample_size: int) -> dict:
    """
    Open the zip and parse up to sample_size XML files.
    Returns summary statistics for reporting.
    """
    records = []
    parse_errors = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        xml_names = [n for n in zf.namelist() if n.endswith(".xml")]
        total_in_zip = len(xml_names)
        to_read = xml_names[:sample_size]

        for name in to_read:
            try:
                data = zf.read(name)
                record = parse_one_study(data)
                record["source_file"] = name
                records.append(record)
            except ET.ParseError:
                parse_errors += 1

    # --- compute simple stats ---
    missing_title = sum(1 for r in records if not r["title"])
    missing_phase = sum(1 for r in records if not r["phase"])
    missing_start = sum(1 for r in records if not r["start_date"])
    missing_completion = sum(1 for r in records if not r["completion_date"])
    multi_condition = sum(1 for r in records if r["num_conditions"] > 1)
    multi_intervention = sum(1 for r in records if r["num_interventions"] > 1)
    multi_location = sum(1 for r in records if r["num_locations"] > 1)

    phase_counts = Counter(r["phase"] or "(missing)" for r in records)
    status_counts = Counter(r["status"] or "(missing)" for r in records)
    study_type_counts = Counter(r["study_type"] or "(missing)" for r in records)

    # Collect example date strings to show format variety
    date_examples = set()
    for r in records:
        if r["start_date"]:
            date_examples.add(r["start_date"])
        if r["completion_date"]:
            date_examples.add(r["completion_date"])
        if len(date_examples) >= 8:
            break

    return {
        "zip_path": str(zip_path),
        "total_files_in_zip": total_in_zip,
        "sample_parsed": len(records),
        "parse_errors": parse_errors,
        "missing_title": missing_title,
        "missing_phase": missing_phase,
        "missing_start_date": missing_start,
        "missing_completion_date": missing_completion,
        "multi_condition_studies": multi_condition,
        "multi_intervention_studies": multi_intervention,
        "multi_location_studies": multi_location,
        "phase_counts": dict(phase_counts.most_common(10)),
        "status_counts": dict(status_counts.most_common(10)),
        "study_type_counts": dict(study_type_counts.most_common()),
        "date_format_examples": sorted(date_examples)[:8],
        "sample_records": records[:3],  # first 3 for display
    }


def print_report(summary: dict) -> None:
    """Print a readable exploration report to the console."""
    print("=" * 60)
    print("CLINICAL TRIALS DATA EXPLORATION REPORT")
    print("=" * 60)
    print(f"Zip file:              {summary['zip_path']}")
    print(f"Total XML files:       {summary['total_files_in_zip']:,}")
    print(f"Sample parsed:         {summary['sample_parsed']:,}")
    print(f"Parse errors:          {summary['parse_errors']}")
    print()
    print("--- Missing values (in sample) ---")
    print(f"  Missing title:           {summary['missing_title']}")
    print(f"  Missing phase:           {summary['missing_phase']}")
    print(f"  Missing start_date:      {summary['missing_start_date']}")
    print(f"  Missing completion_date: {summary['missing_completion_date']}")
    print()
    print("--- Multi-value fields (need normalization) ---")
    print(f"  Studies with 2+ conditions:    {summary['multi_condition_studies']}")
    print(f"  Studies with 2+ interventions: {summary['multi_intervention_studies']}")
    print(f"  Studies with 2+ locations:     {summary['multi_location_studies']}")
    print()
    print("--- Study types ---")
    for k, v in summary["study_type_counts"].items():
        print(f"  {k}: {v}")
    print()
    print("--- Top phases ---")
    for k, v in summary["phase_counts"].items():
        print(f"  {k}: {v}")
    print()
    print("--- Top statuses ---")
    for k, v in summary["status_counts"].items():
        print(f"  {k}: {v}")
    print()
    print("--- Date format examples (inconsistent formats expected) ---")
    for d in summary["date_format_examples"]:
        print(f"  {d}")
    print()
    print("--- Sample record (first study) ---")
    if summary["sample_records"]:
        r = summary["sample_records"][0]
        print(f"  NCT ID:    {r['nct_id']}")
        print(f"  Title:     {r['title'][:70]}...")
        print(f"  Type:      {r['study_type']}")
        print(f"  Phase:     {r['phase']}")
        print(f"  Status:    {r['status']}")
        print(f"  Start:     {r['start_date']}")
        print(f"  Complete:  {r['completion_date']}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Explore clinical trials XML data")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=200,
        help="Number of XML files to parse (default: 200)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    zip_path = repo_root / "sample_data" / "archive.zip.download" / "archive.zip"

    if not zip_path.exists():
        print(f"ERROR: Dataset not found at {zip_path}")
        print("Please place the Kaggle download in sample_data/archive.zip.download/")
        return

    summary = explore_zip(zip_path, args.sample_size)
    print_report(summary)


if __name__ == "__main__":
    main()
