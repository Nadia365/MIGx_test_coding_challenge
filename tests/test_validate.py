import csv

from src.transform.validate import (
    filter_child_rows,
    validate_record,
    validate_records,
    write_quarantine,
)


def test_reject_missing_title():
    record = {"study": {"nct_id": "NCT00000001", "title": ""}, "conditions": []}
    ok, reason = validate_record(record)
    assert ok is False
    assert "title" in reason


def test_reject_missing_nct_id():
    record = {"study": {"nct_id": "", "title": "Some Study"}, "conditions": []}
    ok, reason = validate_record(record)
    assert ok is False
    assert "nct_id" in reason


def test_reject_invalid_nct_id():
    record = {"study": {"nct_id": "BAD123", "title": "Some Study"}, "conditions": []}
    ok, reason = validate_record(record)
    assert ok is False
    assert "invalid nct_id" in reason


def test_reject_start_date_after_completion():
    record = {
        "study": {
            "nct_id": "NCT00000001",
            "title": "Bad Dates",
            "start_date": "2020-01-01",
            "completion_date": "2010-01-01",
        },
        "conditions": [],
    }
    ok, reason = validate_record(record)
    assert ok is False
    assert "start_date after completion_date" in reason


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
    assert len(invalid) == 0


def test_filter_empty_child_rows():
    record = {
        "study": {"nct_id": "NCT00000001", "title": "Test"},
        "conditions": [{"condition_name": ""}, {"condition_name": "Diabetes"}],
        "interventions": [{"intervention_name": ""}],
        "locations": [{"country": None, "city": None, "state": None}],
    }
    filtered = filter_child_rows(record)
    assert len(filtered["conditions"]) == 1
    assert filtered["conditions"][0]["condition_name"] == "Diabetes"
    assert len(filtered["interventions"]) == 0
    assert len(filtered["locations"]) == 0


def test_write_quarantine_creates_csv(quarantine_tmp):
    invalid = [
        {
            "study": {
                "nct_id": "BAD",
                "title": "",
                "source_file": "bad.xml",
            },
            "rejection_reason": "missing title",
        }
    ]
    path = write_quarantine(invalid)

    assert path is not None
    assert path.exists()

    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["source_file"] == "bad.xml"
    assert rows[0]["rejection_reason"] == "missing title"


def test_write_quarantine_returns_none_when_empty(quarantine_tmp):
    assert write_quarantine([]) is None
