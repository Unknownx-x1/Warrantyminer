import os
import sys
import json
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from apps.api.db.session import SessionLocal
from apps.api.models import Cluster, ClusterClaim, Claim, FailureSignature
from apps.api.services.trends import compute_cluster_trend_statistics
from apps.api.services.scoring import calculate_composite_alert_score

def debug_trend_analysis():
    db = SessionLocal()
    print("=" * 70)
    print("           WarrantyPatternMiner -- Trend Analysis Debugger")
    print("=" * 70)

    # 1. Fetch highest alert score cluster
    top_cluster = db.query(Cluster).order_by(Cluster.alert_score.desc()).first()
    if not top_cluster:
        print("[ERROR] No clusters found in database. Please run pipeline first.")
        db.close()
        return

    print(f"\nTarget Cluster ID:    {top_cluster.id}")
    print(f"Cluster Label:        {top_cluster.label}")
    print(f"Total Member Claims:  {top_cluster.claim_count}")
    print(f"Alert Score / Level:  {top_cluster.alert_score} ({top_cluster.alert_level})")

    # 2. Extract and inspect all member claims
    claims = [cm.claim for cm in top_cluster.claim_memberships]
    claims_sorted = sorted(claims, key=lambda c: (c.claim_date or c.created_at))

    print("\n--- Member Claims Breakdown ---")
    print(f"{'Claim ID':<12} {'Date':<12} {'Month':<10} {'Code':<18} {'Plant':<22}")
    print("-" * 75)

    month_buckets = defaultdict(list)
    for c in claims_sorted:
        d_str = c.claim_date.strftime("%Y-%m-%d") if c.claim_date else "N/A"
        m_str = c.claim_date.strftime("%Y-%m") if c.claim_date else "N/A"
        month_buckets[m_str].append(c)
        print(f"{c.external_claim_id:<12} {d_str:<12} {m_str:<10} {c.failure_code or 'OTHER':<18} {c.plant or 'Unknown':<22}")

    # 3. Monthly Timeline Aggregation
    print("\n--- Chronological Monthly Timeline ---")
    sorted_months = sorted(month_buckets.keys())
    counts_by_month = [len(month_buckets[m]) for m in sorted_months]

    for m in sorted_months:
        print(f"  {m} | {len(month_buckets[m]):>2} claims")

    # 4. Statistical Baseline and Emergence Computation
    hist_counts = counts_by_month[:-1] if len(counts_by_month) > 1 else counts_by_month
    recent_volume = counts_by_month[-1] if counts_by_month else 0

    base_mean = float(np.mean(hist_counts)) if hist_counts else 0.0
    base_std = float(np.std(hist_counts, ddof=1)) if len(hist_counts) > 1 else (float(np.std(hist_counts)) if hist_counts else 1.0)

    # Growth calculation
    if base_mean > 0:
        growth = ((recent_volume - base_mean) / base_mean) * 100.0
    else:
        growth = recent_volume * 100.0

    # Z-score calculation
    epsilon = 0.5
    z_score = (recent_volume - base_mean) / (base_std + epsilon) if (base_std + epsilon) > 0 else 0.0

    # CUSUM Calculation
    k = base_mean * 0.5
    s_pos = 0.0
    cusum_series = []
    for cnt in counts_by_month:
        s_pos = max(0.0, s_pos + (cnt - base_mean - k))
        cusum_series.append(s_pos)

    print("\n--- Statistical Metrics Calculation ---")
    print(f"Baseline Window:       {sorted_months[:-1] if len(sorted_months) > 1 else sorted_months}")
    print(f"Baseline Values:       {hist_counts}")
    print(f"Baseline Mean (mu):    {base_mean:.2f} claims/month")
    print(f"Baseline Std (sigma):  {base_std:.2f}")
    print(f"Recent Period:         {sorted_months[-1] if sorted_months else 'N/A'}")
    print(f"Recent Volume:         {recent_volume} claims")
    print(f"Growth Rate (Delta%):  +{growth:.1f}%")
    print(f"Statistical Z-Score:   {z_score:.2f}")
    print(f"CUSUM (Max Accum):     {max(cusum_series):.2f}")

    # 5. Composite Alert Score Decomposition
    coherence = top_cluster.coherence_score
    cross_codes = top_cluster.cross_code_count
    claim_count = top_cluster.claim_count

    score_result = calculate_composite_alert_score(
        growth_rate=growth,
        significance_score=z_score,
        claim_count=claim_count,
        cross_code_count=cross_codes,
        coherence_score=coherence
    )

    factors = score_result["factors"]
    print("\n--- Alert Score 5-Factor Decomposition ---")
    print(f"1. Growth Factor (30%):        Norm = {factors['growth_score']:>5.1f} / 100  | Weighted = {0.30 * factors['growth_score']:>5.2f}")
    print(f"2. Significance Factor (25%):  Norm = {factors['significance_score']:>5.1f} / 100  | Weighted = {0.25 * factors['significance_score']:>5.2f}")
    print(f"3. Cluster Size Factor (15%):  Norm = {factors['size_score']:>5.1f} / 100  | Weighted = {0.15 * factors['size_score']:>5.2f}")
    print(f"4. Cross-Code Factor (15%):    Norm = {factors['cross_code_score']:>5.1f} / 100  | Weighted = {0.15 * factors['cross_code_score']:>5.2f}")
    print(f"5. Coherence Factor (15%):     Norm = {factors['coherence_score']:>5.1f} / 100  | Weighted = {0.15 * factors['coherence_score']:>5.2f}")
    print("-" * 75)
    print(f"Final Computed Alert Score:    {score_result['alert_score']} / 100 ({score_result['alert_level']})")

    db.close()
    print("=" * 70)

if __name__ == "__main__":
    debug_trend_analysis()
