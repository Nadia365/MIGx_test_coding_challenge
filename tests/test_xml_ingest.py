from src.config import FIXTURES_DIR
from src.ingest.xml_ingest import extract_from_folder


def test_extract_from_folder_returns_two_good_records():
    records, parse_errors = extract_from_folder(FIXTURES_DIR)

    assert len(records) == 2
    assert len(parse_errors) == 0
    nct_ids = {r["study"]["nct_id"] for r in records}
    assert nct_ids == {"NCT00000102", "NCT00000125"}


def test_malformed_xml_collected_as_parse_error(validation_fixtures_dir):
    records, parse_errors = extract_from_folder(validation_fixtures_dir)

    assert len(records) == 3  # missing_title, invalid_nct, date_order
    assert len(parse_errors) == 1
    assert parse_errors[0]["study"]["source_file"] == "bad_malformed.xml"
    assert "xml_parse_error" in parse_errors[0]["rejection_reason"]
