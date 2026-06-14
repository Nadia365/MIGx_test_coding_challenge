from src.config import FIXTURES_DIR
from src.ingest.xml_parser import parse_study_xml


def test_parse_fixture_has_nct_id_and_title():
    xml_path = FIXTURES_DIR / "NCT00000102.xml"
    record = parse_study_xml(xml_path.read_bytes(), source_file="NCT00000102.xml")

    assert record["study"]["nct_id"] == "NCT00000102"
    assert "Congenital Adrenal Hyperplasia" in record["study"]["title"]
    assert len(record["conditions"]) >= 1
    assert len(record["interventions"]) >= 1
    assert len(record["locations"]) >= 1
