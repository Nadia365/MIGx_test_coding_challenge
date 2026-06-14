from src.transform.validate import validate_record, validate_records


def test_reject_missing_title():
    record = {"study": {"nct_id": "NCT00000001", "title": ""}, "conditions": []}
    ok, reason = validate_record(record)
    assert ok is False
    assert "title" in reason


def test_duplicate_nct_id_keeps_last():
    records = [
        {
            "study": {"nct_id": "NCT00000001", "title": "First"},
            "conditions": [],
            "interventions": [],
            "locations": [],
        },
        {
            "study": {"nct_id": "NCT00000001", "title": "Second"},
            "conditions": [],
            "interventions": [],
            "locations": [],
        },
    ]
    valid, invalid = validate_records(records)
    assert len(valid) == 1
    assert valid[0]["study"]["title"] == "Second"
