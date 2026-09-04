import pytest
from datetime import date
from apps.api.services.ingestion import parse_date_safely, normalize_claim_record

def test_parse_date_safely():
    assert parse_date_safely("2026-05-17") == date(2026, 5, 17)
    assert parse_date_safely("2026/01/14") == date(2026, 1, 14)
    assert parse_date_safely("14-01-2026") == date(2026, 1, 14)
    assert parse_date_safely(None) is None

def test_normalize_claim_record_valid():
    raw = {
        "claim_id": " C-10021 ",
        "date": "2026-05-17",
        "product_model": "Model X",
        "plant": "Plant A",
        "failure_code": " OTHER ",
        "narrative": " Customer reports clunking noise from front left when driving over rough roads. "
    }
    normalized = normalize_claim_record(raw)
    assert normalized is not None
    assert normalized["external_claim_id"] == "C-10021"
    assert normalized["claim_date"] == date(2026, 5, 17)
    assert normalized["failure_code"] == "OTHER"
    assert normalized["narrative"] == "Customer reports clunking noise from front left when driving over rough roads."

def test_normalize_claim_record_missing_id():
    raw = {
        "claim_id": "",
        "date": "2026-05-17",
        "narrative": "Some text"
    }
    assert normalize_claim_record(raw) is None

def test_normalize_claim_record_missing_narrative():
    raw = {
        "claim_id": "C-10021",
        "date": "2026-05-17",
        "narrative": ""
    }
    assert normalize_claim_record(raw) is None
