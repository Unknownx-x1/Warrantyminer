import pytest
from apps.api.services.mismatch import evaluate_code_mismatch

def test_mismatch_electrical_nff_suspension():
    res = evaluate_code_mismatch(
        assigned_code="ELECTRICAL-NFF",
        component="front-left suspension",
        symptom="clunking / knocking noise",
        narrative="Customer hears metallic tapping from front left suspension, no DTCs found."
    )
    assert res["is_mismatch"] == 1
    assert res["mismatch_severity"] == "HIGH"
    assert "contradicts" in res["reason"] or "inconsistent" in res["reason"]

def test_mismatch_generic_other_with_specific_defect():
    res = evaluate_code_mismatch(
        assigned_code="OTHER",
        component="front-left suspension",
        symptom="clunking / knocking noise",
        narrative="Front end knocks over speed bumps."
    )
    assert res["is_mismatch"] == 1
    assert res["mismatch_severity"] == "HIGH"
    assert "generic" in res["reason"].lower()

def test_match_agreement_suspension():
    res = evaluate_code_mismatch(
        assigned_code="SUSPENSION",
        component="front-left suspension",
        symptom="clunking / knocking noise",
        narrative="Front suspension clunking on rough roads."
    )
    assert res["is_mismatch"] == 0
    assert res["mismatch_severity"] == "NORMAL"
