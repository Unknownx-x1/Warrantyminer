import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import date
from apps.api.models.claim import Claim

logger = logging.getLogger(__name__)

def compute_cluster_trend_statistics(claims: List[Claim]) -> Dict[str, Any]:
    """
    Computes chronological time-series aggregation, historical baseline, growth rate,
    Z-score statistical significance, and CUSUM emergence tracking.
    """
    if not claims:
        return {
            "time_series": [],
            "baseline_volume": 0.0,
            "current_volume": 0.0,
            "growth_rate": 0.0,
            "significance_score": 0.0,
            "cusum_score": 0.0
        }

    # Extract dates and convert to Monthly periods (YYYY-MM)
    date_strs = [c.claim_date.strftime("%Y-%m") for c in claims if c.claim_date]
    if not date_strs:
        return {
            "time_series": [],
            "baseline_volume": 0.0,
            "current_volume": 0.0,
            "growth_rate": 0.0,
            "significance_score": 0.0,
            "cusum_score": 0.0
        }

    # Determine date range
    all_dates = sorted([c.claim_date for c in claims if c.claim_date])
    min_date = all_dates[0]
    max_date = all_dates[-1]

    # Create monthly range from min_date to max_date
    period_index = pd.date_range(start=min_date.replace(day=1), end=max_date.replace(day=1), freq="MS")
    period_keys = [d.strftime("%Y-%m") for d in period_index]

    if not period_keys:
        period_keys = sorted(list(set(date_strs)))

    counts_by_period = {p: 0 for p in period_keys}
    for d in date_strs:
        if d in counts_by_period:
            counts_by_period[d] += 1

    series_data = []
    counts_list = []
    
    for p in period_keys:
        cnt = counts_by_period[p]
        counts_list.append(cnt)
        series_data.append({
            "period": p,
            "claim_count": cnt,
            "baseline": 0.0,
            "z_score": 0.0
        })

    n_periods = len(counts_list)
    if n_periods == 1:
        current_vol = float(counts_list[0])
        baseline_vol = current_vol
        growth_rate = 0.0
        z_score = 0.0
        cusum = 0.0
        series_data[0]["baseline"] = round(baseline_vol, 1)
        series_data[0]["z_score"] = 0.0
    elif n_periods == 2:
        baseline_vol = float(counts_list[0])
        current_vol = float(counts_list[1])
        growth_rate = round(((current_vol - baseline_vol) / max(baseline_vol, 1.0)) * 100.0, 1)
        z_score = 2.0 if current_vol > baseline_vol else 0.0
        cusum = max(0.0, current_vol - baseline_vol)
        series_data[0]["baseline"] = round(baseline_vol, 1)
        series_data[1]["baseline"] = round(baseline_vol, 1)
        series_data[1]["z_score"] = z_score
    else:
        # Recent period is the latest chronological period
        current_vol = float(counts_list[-1])
        
        # Historical baseline: average of previous periods prior to latest period
        hist_counts = counts_list[:-1]
        baseline_vol = float(np.mean(hist_counts))
        baseline_std = float(np.std(hist_counts, ddof=1)) if len(hist_counts) > 1 else 1.0

        # Growth Rate vs Historical Baseline
        if baseline_vol > 0:
            growth_rate = round(((current_vol - baseline_vol) / baseline_vol) * 100.0, 1)
        else:
            growth_rate = round(current_vol * 100.0, 1)

        # Statistical Z-Score (with epsilon=0.5 to protect against low baseline variance)
        epsilon = 0.5
        z_score = round((current_vol - baseline_vol) / (baseline_std + epsilon), 2)

        # CUSUM Calculation with slack parameter k = 0.5 * baseline_mean
        k = baseline_vol * 0.5
        cusum_val = 0.0
        for idx, cnt in enumerate(counts_list):
            if idx < len(hist_counts):
                # Progressive rolling baseline for earlier periods
                roll_base = float(np.mean(counts_list[:max(1, idx + 1)]))
                series_data[idx]["baseline"] = round(roll_base, 1)
                curr_std = float(np.std(counts_list[:max(1, idx + 1)], ddof=1)) if idx > 0 else 1.0
                period_z = (cnt - roll_base) / (curr_std + epsilon)
                series_data[idx]["z_score"] = round(max(0.0, period_z), 2)
            else:
                series_data[idx]["baseline"] = round(baseline_vol, 1)
                series_data[idx]["z_score"] = z_score

            cusum_val = max(0.0, cusum_val + (cnt - baseline_vol - k))

        cusum = round(cusum_val, 2)

    return {
        "time_series": series_data,
        "baseline_volume": round(baseline_vol, 1),
        "current_volume": round(current_vol, 1),
        "growth_rate": max(0.0, growth_rate),
        "significance_score": max(0.0, z_score),
        "cusum_score": cusum
    }
