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

def test_factor_breakdown_explainability():
    score_res = calculate_composite_alert_score(
        growth_rate=466.7,
        significance_score=4.40,
        claim_count=35,
        cross_code_count=5,
        coherence_score=0.720
    )
    fb = score_res["factor_breakdown"]
    assert "growth_velocity" in fb
    assert "statistical_significance" in fb
    assert "cluster_volume" in fb
    assert "cross_code_dispersion" in fb
    assert "semantic_coherence" in fb

    assert fb["growth_velocity"]["points_earned"] == 30.0
    assert fb["statistical_significance"]["points_earned"] == 25.0
    assert fb["cluster_volume"]["points_earned"] == 15.0
    assert fb["cross_code_dispersion"]["points_earned"] == 15.0
    assert fb["semantic_coherence"]["points_earned"] == 10.8

    # Sum of factors equals 95.8
    total_pts = sum(f["points_earned"] for f in fb.values())
    assert round(total_pts, 1) == 95.8
    assert score_res["alert_score"] == 95.8
    assert score_res["alert_level"] == "CRITICAL"
