from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.db.session import get_db
from apps.api.models.claim import Claim, CodeMismatch
from apps.api.models.cluster import Cluster
from apps.api.schemas.cluster import ClusterListItem

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Computes live high-level KPI metrics for the Command Center.
    """
    total_claims = db.query(Claim).count()
    
    # Active clusters excluding noise
    clusters = db.query(Cluster).filter(Cluster.cluster_index != -1).all()
    total_clusters = len(clusters)
    
    critical_alerts = sum(1 for c in clusters if c.alert_level == "CRITICAL")
    high_alerts = sum(1 for c in clusters if c.alert_level == "HIGH")
    watch_alerts = sum(1 for c in clusters if c.alert_level == "WATCH")
    
    miscoded_claims = db.query(CodeMismatch).filter(CodeMismatch.is_mismatch == 1).count()
    
    # Highest priority emerging cluster for hero card
    hero_cluster = None
    sorted_clusters = sorted(clusters, key=lambda x: x.alert_score, reverse=True)
    if sorted_clusters:
        top = sorted_clusters[0]
        hero_cluster = {
            "id": top.id,
            "label": top.label,
            "alert_level": top.alert_level,
            "alert_score": top.alert_score,
            "growth_rate": top.growth_rate,
            "claim_count": top.claim_count,
            "cross_code_count": top.cross_code_count,
            "plant_count": top.plant_count,
            "description": top.description,
            "primary_component": top.primary_component,
            "primary_symptom": top.primary_symptom,
            "significance_score": top.significance_score,
            "cusum_score": top.cusum_score,
            "baseline_volume": top.baseline_volume,
            "current_volume": top.current_volume,
            "code_distribution": top.code_distribution or {},
            "why_alerted": top.ai_rationale.get("why_alerted") if top.ai_rationale else "",
            "time_series": top.time_series or [],
            "representative_claims": top.representative_claims[:3] if top.representative_claims else [],
            "factor_breakdown": top.factor_breakdown or {}
        }

    return {
        "claims_analyzed": total_claims,
        "emerging_patterns": total_clusters,
        "high_risk_patterns": critical_alerts + high_alerts,
        "critical_patterns": critical_alerts,
        "high_patterns": high_alerts,
        "watch_patterns": watch_alerts,
        "miscoded_claims": miscoded_claims,
        "hero_cluster": hero_cluster
    }

@router.get("", response_model=List[ClusterListItem])
def get_active_alerts(db: Session = Depends(get_db)):
    """
    Returns emerging clusters with alert_score >= 40 (WATCH, HIGH, CRITICAL).
    """
    clusters = db.query(Cluster).filter(
        Cluster.cluster_index != -1,
        Cluster.alert_score >= 40.0
    ).order_by(desc(Cluster.alert_score)).all()

    results = []
    for c in clusters:
        results.append(ClusterListItem(
            id=c.id,
            run_id=c.run_id,
            cluster_index=c.cluster_index,
            label=c.label,
            description=c.description,
            primary_component=c.primary_component,
            primary_symptom=c.primary_symptom,
            claim_count=c.claim_count,
            cross_code_count=c.cross_code_count,
            plant_count=c.plant_count,
            model_count=c.model_count,
            growth_rate=c.growth_rate,
            significance_score=c.significance_score,
            coherence_score=c.coherence_score,
            alert_score=c.alert_score,
            alert_level=c.alert_level,
            status=c.status,
            created_at=c.created_at,
            top_codes=c.code_distribution or {},
            factor_breakdown=c.factor_breakdown or {}
        ))
    return results
