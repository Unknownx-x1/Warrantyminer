from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.db.session import get_db
from apps.api.models.cluster import Cluster, ClusterClaim
from apps.api.schemas.cluster import ClusterListItem, ClusterDetail, ClusterClaimsResponse, ClusterClaimItem, AIRationale

router = APIRouter(prefix="/clusters", tags=["Clusters"])

@router.get("", response_model=List[ClusterListItem])
def list_clusters(
    alert_level: Optional[str] = Query(None, description="Filter by alert level: CRITICAL, HIGH, WATCH, NORMAL"),
    sort_by: str = Query("alert_score", description="Sort by alert_score, claim_count, growth_rate, created_at"),
    db: Session = Depends(get_db)
):
    query = db.query(Cluster).filter(Cluster.cluster_index != -1)

    if alert_level:
        query = query.filter(Cluster.alert_level == alert_level.upper())

    if sort_by == "claim_count":
        query = query.order_by(desc(Cluster.claim_count))
    elif sort_by == "growth_rate":
        query = query.order_by(desc(Cluster.growth_rate))
    elif sort_by == "created_at":
        query = query.order_by(desc(Cluster.created_at))
    else:
        query = query.order_by(desc(Cluster.alert_score))

    clusters = query.all()
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
            top_codes=c.code_distribution or {}
        ))
    return results

@router.get("/{cluster_id}", response_model=ClusterDetail)
def get_cluster_detail(cluster_id: str, db: Session = Depends(get_db)):
    c = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cluster not found")

    fb_dict = None
    if c.feedback:
        fb_dict = {
            "decision": c.feedback.decision,
            "rationale": c.feedback.rationale,
            "reviewer": c.feedback.reviewer,
            "custom_label": c.feedback.custom_label,
            "created_at": c.feedback.created_at.isoformat() if c.feedback.created_at else None
        }

    ai_rat = None
    if c.ai_rationale:
        ai_rat = AIRationale(
            why_grouped=c.ai_rationale.get("why_grouped", ""),
            why_alerted=c.ai_rationale.get("why_alerted", ""),
            key_symptoms=c.ai_rationale.get("key_symptoms", []),
            affected_components=c.ai_rationale.get("affected_components", [])
        )

    return ClusterDetail(
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
        baseline_volume=c.baseline_volume,
        current_volume=c.current_volume,
        cusum_score=c.cusum_score,
        code_distribution=c.code_distribution or {},
        plant_distribution=c.plant_distribution or {},
        model_distribution=c.model_distribution or {},
        time_series=c.time_series or [],
        representative_claims=c.representative_claims or [],
        ai_rationale=ai_rat,
        feedback=fb_dict
    )

@router.get("/{cluster_id}/claims", response_model=ClusterClaimsResponse)
def get_cluster_claims(cluster_id: str, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    memberships = db.query(ClusterClaim).filter(ClusterClaim.cluster_id == cluster_id).all()
    claims_out = []

    for m in memberships:
        c = m.claim
        sig = c.signature
        mis = c.mismatch
        claims_out.append(ClusterClaimItem(
            claim_id=c.id,
            external_claim_id=c.external_claim_id,
            claim_date=c.claim_date.isoformat() if c.claim_date else "",
            product_model=c.product_model,
            plant=c.plant,
            failure_code=c.failure_code,
            narrative=c.narrative,
            component=sig.component if sig else None,
            symptom=sig.symptom if sig else None,
            inferred_failure=sig.inferred_failure if sig else None,
            is_mismatch=mis.is_mismatch if mis else 0,
            mismatch_severity=mis.mismatch_severity if mis else "NORMAL",
            mismatch_reason=mis.reason if mis else None,
            similarity_score=m.similarity_score
        ))

    return ClusterClaimsResponse(
        cluster_id=cluster.id,
        cluster_label=cluster.label,
        total=len(claims_out),
        claims=claims_out
    )
