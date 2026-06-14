"""Shared pytest fixtures for validation tests."""

from pathlib import Path

import pytest

FIXTURES_VALIDATION_DIR = Path(__file__).resolve().parent / "fixtures_validation"


@pytest.fixture
def quarantine_tmp(tmp_path, monkeypatch):
    """Use a temp directory for quarantine CSV output in tests."""
    quarantine_file = tmp_path / "rejected_studies.csv"
    monkeypatch.setattr("src.transform.validate.QUARANTINE_DIR", tmp_path)
    monkeypatch.setattr("src.transform.validate.QUARANTINE_FILE", quarantine_file)
    return tmp_path


@pytest.fixture
def validation_fixtures_dir():
    return FIXTURES_VALIDATION_DIR
