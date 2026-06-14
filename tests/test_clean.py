from src.transform.clean import clean_date, clean_phase, clean_record


def test_clean_phase_empty_becomes_unknown():
    assert clean_phase("") == "Unknown"
    assert clean_phase("Phase 2") == "Phase 2"


def test_clean_date_month_year():
    assert clean_date("February 1994") == "1994-02-01"
    assert clean_date("") is None
    assert clean_date("not-a-real-date") is None


def test_clean_date_unparseable_returns_none():
    assert clean_date("TBD sometime soon") is None


def test_clean_record_parses_enrollment():
    record = {
        "study": {
            "nct_id": "NCT00000125",
            "title": "Test",
            "phase": "",
            "start_date": "February 1994",
            "completion_date": "",
            "enrollment": "1636",
        },
        "conditions": [],
        "interventions": [],
        "locations": [],
    }
    cleaned = clean_record(record)
    assert cleaned["study"]["phase"] == "Unknown"
    assert cleaned["study"]["enrollment"] == 1636
