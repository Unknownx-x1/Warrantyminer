import pytest
from apps.api.services.scoring import calculate_composite_alert_score

def test_critical_alert_score():
    score_res = calculate_composite_alert_score(
        growth_rate=280.0,
        significance_score=3.5,
        claim_count=22,
        cross_code_count=5,
        coherence_score=0.88
    )
    assert score_res["alert_level"] in ["CRITICAL", "HIGH"]
    assert score_res["alert_score"] >= 75.0
    assert score_res["factors"]["cross_code_score"] == 100.0

def test_normal_alert_score():
    score_res = calculate_composite_alert_score(
        growth_rate=5.0,
        significance_score=0.2,
        claim_count=4,
        cross_code_count=1,
        coherence_score=0.60
    )
    assert score_res["alert_level"] == "NORMAL"
    assert score_res["alert_score"] < 40.0
