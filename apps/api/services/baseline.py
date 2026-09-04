import logging
from datetime import date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from apps.api.models.claim import Claim
from apps.api.models.cluster import Cluster

logger = logging.getLogger(__name__)

def calculate_dynamic_lead_time(
    cluster_claims: List[Claim],
    traditional_code_buckets: Dict[str, List[Claim]],
    single_code_threshold: int = 10
) -> Tuple[Optional[str], Optional[str], Optional[int], str]:
    """
    Evaluates detection timestamps for both surveillance paradigms:
    1. Semantic Detection Date (T_semantic): Date when the consolidated cluster emerged (e.g. at the 8th claim).
    2. Traditional Detection Date (T_traditional): Date when ANY individual structured failure code reached single_code_threshold (10 claims).

    Returns:
    (semantic_date_str, traditional_date_str, lead_time_days, lead_time_status)
    - If traditional monitoring NEVER reached threshold within the observation window:
      traditional_date_str = None, lead_time_days = None, lead_time_status = "NO_ALERT_WITHIN_OBSERVATION_WINDOW"
    - If traditional monitoring reached threshold:
      lead_time_days = (T_traditional - T_semantic).days
    """
    if not cluster_claims:
        return None, None, None, "NO_DATA"

    sorted_claims = sorted([c for c in cluster_claims if c.claim_date], key=lambda c: c.claim_date)
    if not sorted_claims:
        return None, None, None, "NO_DATA"

    # Semantic Detection Date: Date when the consolidated cluster emerged (e.g. claim #8)
    emergence_index = min(len(sorted_claims) - 1, max(3, len(sorted_claims) // 4))
    semantic_detection_date = sorted_claims[emergence_index].claim_date
    semantic_date_str = semantic_detection_date.strftime("%Y-%m-%d")

    # Traditional Detection Date: Date when ANY individual single failure code reached single_code_threshold (10 claims)
    traditional_trigger_dates = []
    for code, claims in traditional_code_buckets.items():
        if len(claims) >= single_code_threshold:
            code_sorted = sorted([c for c in claims if c.claim_date], key=lambda c: c.claim_date)
            if len(code_sorted) >= single_code_threshold:
                traditional_trigger_dates.append(code_sorted[single_code_threshold - 1].claim_date)

    if traditional_trigger_dates:
        earliest_traditional_date = min(traditional_trigger_dates)
        traditional_date_str = earliest_traditional_date.strftime("%Y-%m-%d")
        lead_time_days = (earliest_traditional_date - semantic_detection_date).days
        if lead_time_days > 0:
            lead_time_status = "FINITE_LEAD_TIME_ADVANTAGE"
        else:
            lead_time_status = "TRADITIONAL_DETECTED_FIRST_OR_SAME_DAY"
    else:
        # Traditional monitoring NEVER crossed threshold within the observation window
        traditional_date_str = None
        lead_time_days = None
        lead_time_status = "NO_ALERT_WITHIN_OBSERVATION_WINDOW"

    return semantic_date_str, traditional_date_str, lead_time_days, lead_time_status

def compute_traditional_baseline_comparison(db: Session, target_cluster_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes side-by-side comparison: Traditional Structured-Code view vs WarrantyPatternMiner Semantic Cluster view.
    Everything is dynamically computed from actual database records.
    """
    cluster_query = db.query(Cluster).filter(Cluster.cluster_index != -1)
    if target_cluster_id:
        target_cluster = cluster_query.filter(Cluster.id == target_cluster_id).first()
    else:
        target_cluster = cluster_query.order_by(Cluster.alert_score.desc()).first()

    if not target_cluster:
        return {
            "has_data": False,
            "message": "No clusters available for comparison."
        }

    # Fetch actual member claims in this cluster
    cluster_claims = [cm.claim for cm in target_cluster.claim_memberships]
    cluster_claim_count = len(cluster_claims)

    # Traditional system groups claims strictly by failure_code
    code_bucket_claims = defaultdict(list)
    for c in cluster_claims:
        code_bucket_claims[c.failure_code or "UNASSIGNED"].append(c)

    # Compute traditional code breakdown
    single_code_alert_threshold = 10
    traditional_breakdown = []
    any_traditional_alert = False

    for code, claims_list in sorted(code_bucket_claims.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(claims_list)
        alert_triggered = count >= single_code_alert_threshold
        if alert_triggered:
            any_traditional_alert = True
        status_text = "SURGE DETECTED" if alert_triggered else "NORMAL (Below threshold of 10)"
        traditional_breakdown.append({
            "code": code,
            "claim_count": count,
            "status": status_text,
            "alert": alert_triggered,
            "threshold_reached": alert_triggered
        })

    # Calculate actual dynamic lead time and detection dates
    semantic_date, traditional_date, lead_time_days, lead_time_status = calculate_dynamic_lead_time(
        cluster_claims=cluster_claims,
        traditional_code_buckets=code_bucket_claims,
        single_code_threshold=single_code_alert_threshold
    )

    if traditional_date is None:
        trad_status = "NO_ALERT_WITHIN_OBSERVATION_WINDOW"
        trad_explanation = f"Claims are fragmented across {len(code_bucket_claims)} distinct structured failure codes. No single failure code breached the alert threshold ({single_code_alert_threshold} claims) during the observation window."
    else:
        trad_status = "ALERT_TRIGGERED"
        trad_explanation = f"Traditional single-code monitoring eventually breached the {single_code_alert_threshold}-claim threshold on {traditional_date}."

    return {
        "has_data": True,
        "cluster_id": target_cluster.id,
        "cluster_label": target_cluster.label,
        "alert_level": target_cluster.alert_level,
        "alert_score": target_cluster.alert_score,
        "growth_rate": target_cluster.growth_rate,
        "total_cluster_claims": cluster_claim_count,
        "cross_code_count": len(code_bucket_claims),
        "semantic_detection_date": semantic_date,
        "traditional_detection_date": traditional_date,
        "lead_time_days": lead_time_days,
        "lead_time_status": lead_time_status,
        "traditional_monitoring": {
            "title": "Traditional Code-Level Monitoring",
            "status": trad_status,
            "detection_date": traditional_date,
            "explanation": trad_explanation,
            "code_buckets": traditional_breakdown
        },
        "semantic_monitoring": {
            "title": "WarrantyPatternMiner Semantic Intelligence",
            "status": f"ALERT: {target_cluster.alert_level}",
            "detection_date": semantic_date,
            "explanation": f"Semantic analysis unified {cluster_claim_count} claims across {len(code_bucket_claims)} codes into one high-coherence cluster showing +{target_cluster.growth_rate:.0f}% growth.",
            "growth_percentage": target_cluster.growth_rate,
            "significance_z": target_cluster.significance_score,
            "alert_score": target_cluster.alert_score
        }
    }
