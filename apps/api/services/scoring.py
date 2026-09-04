import logging
from typing import Dict, Any, List
from collections import Counter
from apps.api.models.claim import Claim, FailureSignature

logger = logging.getLogger(__name__)

def calculate_composite_alert_score(
    growth_rate: float,
    significance_score: float,
    claim_count: int,
    cross_code_count: int,
    coherence_score: float
) -> Dict[str, Any]:
    """
    Computes composite alert score based on the 5-factor weighted formula from specification:
    alert_score = 0.30 * normalized_growth + 0.25 * significance + 0.15 * cluster_size_score + 0.15 * cross_code_score + 0.15 * coherence_score
    """
    # 1. Normalized Growth Score (0 to 100)
    # +100% growth or above reaches maximum growth scale
    norm_growth = min(100.0, max(0.0, growth_rate))
    norm_sig = min(100.0, max(0.0, significance_score * 35.0))
    norm_size = min(100.0, max(0.0, claim_count * 5.0))
    norm_cross_code = min(100.0, max(0.0, cross_code_count * 20.0))
    norm_coherence = min(100.0, max(0.0, coherence_score * 100.0))

    pts_growth = round(0.30 * norm_growth, 1)
    pts_sig = round(0.25 * norm_sig, 1)
    pts_size = round(0.15 * norm_size, 1)
    pts_cross_code = round(0.15 * norm_cross_code, 1)
    pts_coherence = round(0.15 * norm_coherence, 1)

    raw_alert_score = (
        0.30 * norm_growth +
        0.25 * norm_sig +
        0.15 * norm_size +
        0.15 * norm_cross_code +
        0.15 * norm_coherence
    )

    alert_score = round(min(100.0, max(0.0, raw_alert_score)), 1)

    if alert_score >= 80.0:
        alert_level = "CRITICAL"
    elif alert_score >= 60.0:
        alert_level = "HIGH"
    elif alert_score >= 40.0:
        alert_level = "WATCH"
    else:
        alert_level = "NORMAL"

    factor_breakdown = {
        "growth_velocity": {
            "name": "Growth Velocity",
            "weight_pct": 30,
            "max_points": 30.0,
            "raw_value": f"+{growth_rate:.1f}%",
            "normalized_score": round(norm_growth, 1),
            "points_earned": pts_growth,
            "benchmark": "Surge vs 6-mo baseline (>100% surge = 30.0 pts)",
            "methodology": "Quantifies the acceleration of incident reports over the historical baseline mean."
        },
        "statistical_significance": {
            "name": "Statistical Significance",
            "weight_pct": 25,
            "max_points": 25.0,
            "raw_value": f"Z = {significance_score:.2f}",
            "normalized_score": round(norm_sig, 1),
            "points_earned": pts_sig,
            "benchmark": "Poisson-normal Z-score (Z ≥ 2.86 = 25.0 pts, p < 0.001)",
            "methodology": "Validates that the claim surge is statistically anomalous rather than random noise."
        },
        "cluster_volume": {
            "name": "Cluster Volume",
            "weight_pct": 15,
            "max_points": 15.0,
            "raw_value": f"{claim_count} claims",
            "normalized_score": round(norm_size, 1),
            "points_earned": pts_size,
            "benchmark": "Consolidated cluster size (≥20 claims = 15.0 pts)",
            "methodology": "Measures total fleet-wide defect incidence consolidated by semantic clustering."
        },
        "cross_code_dispersion": {
            "name": "Cross-Code Dispersion",
            "weight_pct": 15,
            "max_points": 15.0,
            "raw_value": f"{cross_code_count} dealer codes",
            "normalized_score": round(norm_cross_code, 1),
            "points_earned": pts_cross_code,
            "benchmark": "Dealer taxonomy fragmentation (≥5 codes = 15.0 pts)",
            "methodology": "Measures fragmentation across checkbox codes that conceals defects from legacy alarms."
        },
        "semantic_coherence": {
            "name": "Semantic Coherence",
            "weight_pct": 15,
            "max_points": 15.0,
            "raw_value": f"{coherence_score * 100:.1f}%",
            "normalized_score": round(norm_coherence, 1),
            "points_earned": pts_coherence,
            "benchmark": "Mean pairwise cosine cohesion (100% cohesion = 15.0 pts)",
            "methodology": "Evaluates embedding cosine similarity across verbatim technician narratives."
        }
    }

    return {
        "alert_score": alert_score,
        "alert_level": alert_level,
        "factor_breakdown": factor_breakdown,
        "factors": {
            "growth_score": round(norm_growth, 1),
            "significance_score": round(norm_sig, 1),
            "size_score": round(norm_size, 1),
            "cross_code_score": round(norm_cross_code, 1),
            "coherence_score": round(norm_coherence, 1)
        }
    }

def generate_ai_rationale(
    claims: List[Claim],
    signatures: List[FailureSignature],
    growth_rate: float,
    cross_code_count: int,
    plant_count: int,
    primary_component: str,
    primary_symptom: str
) -> Dict[str, Any]:
    """
    Constructs explainable AI reasoning for why this cluster was grouped together and why it alerted.
    """
    n_claims = len(claims)
    
    # Key symptoms
    symptoms = [s.symptom for s in signatures if s and s.symptom and s.symptom != "unspecified operational symptom"]
    top_symptoms = [item[0] for item in Counter(symptoms).most_common(3)]
    if not top_symptoms:
        top_symptoms = [primary_symptom]

    # Components
    components = [s.component for s in signatures if s and s.component and s.component != "unspecified component"]
    top_components = [item[0] for item in Counter(components).most_common(2)]
    if not top_components:
        top_components = [primary_component]

    why_grouped = (
        f"Semantic analysis discovered high vector similarity across {n_claims} technician narratives describing "
        f"{', '.join(top_symptoms)} localized to the {', '.join(top_components)}. "
        f"The diagnostic signal was obscured across {cross_code_count} distinct structured failure codes."
    )

    if growth_rate > 50:
        why_alerted = (
            f"Monthly claim rate surged +{growth_rate:.0f}% over the rolling baseline across {plant_count} assembly plants. "
            f"Cross-code dispersion ({cross_code_count} codes) combined with high semantic coherence exceeds alert threshold."
        )
    else:
        why_alerted = (
            f"Cluster volume is currently stable (+{growth_rate:.0f}% vs baseline). "
            f"Tracked under normal operational monitoring."
        )

    return {
        "why_grouped": why_grouped,
        "why_alerted": why_alerted,
        "key_symptoms": top_symptoms,
        "affected_components": top_components
    }
