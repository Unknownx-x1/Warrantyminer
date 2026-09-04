import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from apps.api.db.session import get_db
from apps.api.models.claim import Claim, FailureSignature, CodeMismatch
from apps.api.models.cluster import ClusterClaim, Cluster
from apps.api.schemas.claim import ClaimDetailOut, ClaimsListResponse, FailureSignatureOut, CodeMismatchOut
from apps.api.services.ingestion import ingest_claims_data
from apps.api.config import settings, RAW_DATA_DIR

router = APIRouter(prefix="/claims", tags=["Claims"])

@router.post("/upload")
async def upload_claims_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Ingests claims from an uploaded CSV or JSON file.
    """
    contents = await file.read()
    inserted, skipped, errors = ingest_claims_data(contents, file.filename or "uploaded_claims.csv", db)
    return {
        "filename": file.filename,
        "inserted": inserted,
        "skipped_or_existing": skipped,
        "errors": errors[:10],
        "total_errors": len(errors)
    }

@router.get("", response_model=ClaimsListResponse)
def list_claims(
    search: Optional[str] = Query(None, description="Search term in narrative or claim ID"),
    failure_code: Optional[str] = Query(None, description="Filter by failure code"),
    product_model: Optional[str] = Query(None, description="Filter by vehicle/product model"),
    plant: Optional[str] = Query(None, description="Filter by plant"),
    mismatch_only: bool = Query(False, description="Show only claims with code mismatch"),
    cluster_id: Optional[str] = Query(None, description="Filter by cluster ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Claim)

    if cluster_id:
        query = query.join(ClusterClaim).filter(ClusterClaim.cluster_id == cluster_id)

    if mismatch_only:
        query = query.join(CodeMismatch).filter(CodeMismatch.is_mismatch == 1)

    if search:
        search_filter = or_(
            Claim.external_claim_id.ilike(f"%{search}%"),
            Claim.narrative.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if failure_code:
        query = query.filter(Claim.failure_code == failure_code)

    if product_model:
        query = query.filter(Claim.product_model == product_model)

    if plant:
        query = query.filter(Claim.plant == plant)

    total = query.count()
    claims = query.order_by(desc(Claim.claim_date)).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for c in claims:
        # Check cluster membership
        cluster_membership = db.query(ClusterClaim).filter(ClusterClaim.claim_id == c.id).first()
        cluster_label = None
        c_id = None
        if cluster_membership and cluster_membership.cluster:
            cluster_label = cluster_membership.cluster.label
            c_id = cluster_membership.cluster_id

        sig_out = None
        if c.signature:
            sig_out = FailureSignatureOut(
                component=c.signature.component,
                symptom=c.signature.symptom,
                condition=c.signature.condition,
                severity=c.signature.severity,
                inferred_failure=c.signature.inferred_failure,
                contributing_factors=c.signature.contributing_factors or [],
                extraction_confidence=c.signature.extraction_confidence or 0.0
            )
        else:
            from apps.api.services.extraction import extract_signature_rule_based
            fallback_sig = extract_signature_rule_based(c.narrative)
            sig_out = FailureSignatureOut(
                component=fallback_sig.get("component"),
                symptom=fallback_sig.get("symptom"),
                condition=fallback_sig.get("condition"),
                severity=fallback_sig.get("severity"),
                inferred_failure=fallback_sig.get("inferred_failure"),
                contributing_factors=fallback_sig.get("contributing_factors", []),
                extraction_confidence=fallback_sig.get("confidence", 0.85)
            )

        mismatch_out = None
        if c.mismatch:
            mismatch_out = CodeMismatchOut(
                assigned_code=c.mismatch.assigned_code,
                inferred_category=c.mismatch.inferred_category,
                mismatch_severity=c.mismatch.mismatch_severity or "NORMAL",
                is_mismatch=c.mismatch.is_mismatch or 0,
                mismatch_score=c.mismatch.mismatch_score or 0.0,
                reason=c.mismatch.reason,
                confidence=c.mismatch.confidence or 0.0
            )
        else:
            from apps.api.services.mismatch import evaluate_code_mismatch
            fallback_mismatch = evaluate_code_mismatch(
                c.failure_code,
                sig_out.component if sig_out else "",
                sig_out.symptom if sig_out else "",
                c.narrative
            )
            mismatch_out = CodeMismatchOut(
                assigned_code=fallback_mismatch.get("assigned_code"),
                inferred_category=fallback_mismatch.get("inferred_category"),
                mismatch_severity=fallback_mismatch.get("mismatch_severity", "NORMAL"),
                is_mismatch=fallback_mismatch.get("is_mismatch", 0),
                mismatch_score=fallback_mismatch.get("mismatch_score", 0.0),
                reason=fallback_mismatch.get("reason"),
                confidence=0.85
            )

        items.append(ClaimDetailOut(
            id=c.id,
            external_claim_id=c.external_claim_id,
            claim_date=c.claim_date,
            product_model=c.product_model,
            plant=c.plant,
            failure_code=c.failure_code,
            narrative=c.narrative,
            source=c.source,
            created_at=c.created_at,
            signature=sig_out,
            mismatch=mismatch_out,
            cluster_id=c_id,
            cluster_label=cluster_label
        ))

    return ClaimsListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size
    )

@router.get("/{claim_id}", response_model=ClaimDetailOut)
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    c = db.query(Claim).filter(or_(Claim.id == claim_id, Claim.external_claim_id == claim_id)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Claim not found")

    cluster_membership = db.query(ClusterClaim).filter(ClusterClaim.claim_id == c.id).first()
    cluster_label = None
    c_id = None
    if cluster_membership and cluster_membership.cluster:
        cluster_label = cluster_membership.cluster.label
        c_id = cluster_membership.cluster_id

    sig_out = None
    if c.signature:
        sig_out = FailureSignatureOut(
            component=c.signature.component,
            symptom=c.signature.symptom,
            condition=c.signature.condition,
            severity=c.signature.severity,
            inferred_failure=c.signature.inferred_failure,
            contributing_factors=c.signature.contributing_factors or [],
            extraction_confidence=c.signature.extraction_confidence or 0.0
        )
    else:
        from apps.api.services.extraction import extract_signature_rule_based
        fallback_sig = extract_signature_rule_based(c.narrative)
        sig_out = FailureSignatureOut(
            component=fallback_sig.get("component"),
            symptom=fallback_sig.get("symptom"),
            condition=fallback_sig.get("condition"),
            severity=fallback_sig.get("severity"),
            inferred_failure=fallback_sig.get("inferred_failure"),
            contributing_factors=fallback_sig.get("contributing_factors", []),
            extraction_confidence=fallback_sig.get("confidence", 0.85)
        )

    mismatch_out = None
    if c.mismatch:
        mismatch_out = CodeMismatchOut(
            assigned_code=c.mismatch.assigned_code,
            inferred_category=c.mismatch.inferred_category,
            mismatch_severity=c.mismatch.mismatch_severity or "NORMAL",
            is_mismatch=c.mismatch.is_mismatch or 0,
            mismatch_score=c.mismatch.mismatch_score or 0.0,
            reason=c.mismatch.reason,
            confidence=c.mismatch.confidence or 0.0
        )
    else:
        from apps.api.services.mismatch import evaluate_code_mismatch
        fallback_mismatch = evaluate_code_mismatch(
            c.failure_code,
            sig_out.component if sig_out else "",
            sig_out.symptom if sig_out else "",
            c.narrative
        )
        mismatch_out = CodeMismatchOut(
            assigned_code=fallback_mismatch.get("assigned_code"),
            inferred_category=fallback_mismatch.get("inferred_category"),
            mismatch_severity=fallback_mismatch.get("mismatch_severity", "NORMAL"),
            is_mismatch=fallback_mismatch.get("is_mismatch", 0),
            mismatch_score=fallback_mismatch.get("mismatch_score", 0.0),
            reason=fallback_mismatch.get("reason"),
            confidence=0.85
        )

    return ClaimDetailOut(
        id=c.id,
        external_claim_id=c.external_claim_id,
        claim_date=c.claim_date,
        product_model=c.product_model,
        plant=c.plant,
        failure_code=c.failure_code,
        narrative=c.narrative,
        source=c.source,
        created_at=c.created_at,
        signature=sig_out,
        mismatch=mismatch_out,
        cluster_id=c_id,
        cluster_label=cluster_label
    )

@router.post("/reset")
@router.delete("/reset")
def reset_database(db: Session = Depends(get_db)):
    """
    Clears all seeded/ingested claims, clusters, embeddings, signatures, mismatches, and runs.
    """
    from apps.api.models.claim import Embedding
    from apps.api.models.feedback import Feedback, AnalysisRun, AuditLog, DefectFingerprint
    
    deleted_counts = {}
    deleted_counts["cluster_claims"] = db.query(ClusterClaim).delete()
    deleted_counts["clusters"] = db.query(Cluster).delete()
    deleted_counts["code_mismatches"] = db.query(CodeMismatch).delete()
    deleted_counts["embeddings"] = db.query(Embedding).delete()
    deleted_counts["failure_signatures"] = db.query(FailureSignature).delete()
    deleted_counts["feedback"] = db.query(Feedback).delete()
    deleted_counts["defect_fingerprints"] = db.query(DefectFingerprint).delete()
    deleted_counts["analysis_runs"] = db.query(AnalysisRun).delete()
    deleted_counts["audit_logs"] = db.query(AuditLog).delete()
    deleted_counts["claims"] = db.query(Claim).delete()
    db.commit()
    
    return {
        "status": "success",
        "message": "All pre-seeded claims, clusters, and surveillance records removed successfully.",
        "deleted": deleted_counts
    }
