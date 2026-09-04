import pytest
from datetime import date
from apps.api.models.claim import Claim
from apps.api.services.trends import compute_cluster_trend_statistics

def test_trend_growth_and_zscore():
    # Build 7 months of claims with accelerating growth
    claims = []
    # Month 1: 1 claim
    claims.append(Claim(claim_date=date(2026, 1, 15), narrative="test"))
    # Month 2: 1 claim
    claims.append(Claim(claim_date=date(2026, 2, 15), narrative="test"))
    # Month 3: 2 claims
    claims.append(Claim(claim_date=date(2026, 3, 10), narrative="test"))
    claims.append(Claim(claim_date=date(2026, 3, 20), narrative="test"))
    # Month 4: 2 claims
    claims.append(Claim(claim_date=date(2026, 4, 10), narrative="test"))
    claims.append(Claim(claim_date=date(2026, 4, 20), narrative="test"))
    # Month 5: 4 claims
    for _ in range(4):
        claims.append(Claim(claim_date=date(2026, 5, 15), narrative="test"))
    # Month 6: 6 claims
    for _ in range(6):
        claims.append(Claim(claim_date=date(2026, 6, 15), narrative="test"))
    # Month 7: 12 claims (surge)
    for _ in range(12):
        claims.append(Claim(claim_date=date(2026, 7, 15), narrative="test"))

    stats = compute_cluster_trend_statistics(claims)
    assert stats["current_volume"] == 12.0
    assert stats["baseline_volume"] > 0
    assert stats["growth_rate"] > 100.0
    assert stats["significance_score"] > 2.0
    assert len(stats["time_series"]) >= 6
