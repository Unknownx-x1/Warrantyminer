from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.db.session import get_db
from apps.api.models.cluster import Cluster
from apps.api.models.feedback import Feedback, AuditLog
from apps.api.schemas.feedback import FeedbackCreate, FeedbackOut
from apps.api.services.fingerprints import create_fingerprint_from_cluster

router = APIRouter(prefix="/clusters", tags=["Human Verification / Feedback"])

@router.post("/{cluster_id}/feedback", response_model=FeedbackOut)
def record_cluster_feedback(
    cluster_id: str,
    feedback_in: FeedbackCreate,
    db: Session = Depends(get_db)
):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Update cluster status
    cluster.status = feedback_in.decision
    if feedback_in.custom_label and feedback_in.custom_label.strip():
        cluster.label = feedback_in.custom_label.strip()

    # Save or update feedback
    feedback = db.query(Feedback).filter(Feedback.cluster_id == cluster_id).first()
    if not feedback:
        feedback = Feedback(
            cluster_id=cluster_id,
            decision=feedback_in.decision,
            rationale=feedback_in.rationale,
            reviewer=feedback_in.reviewer or "Reliability Engineer",
            custom_label=feedback_in.custom_label
        )
        db.add(feedback)
    else:
        feedback.decision = feedback_in.decision
        feedback.rationale = feedback_in.rationale
        feedback.reviewer = feedback_in.reviewer or "Reliability Engineer"
        feedback.custom_label = feedback_in.custom_label

    # If confirmed, automatically persist into organizational Defect Fingerprint Library!
    if feedback_in.decision == "confirmed":
        create_fingerprint_from_cluster(db, cluster, engineer_name=feedback_in.reviewer or "Reliability Engineer")

    # Create audit log
    audit = AuditLog(
        entity_type="cluster",
        entity_id=cluster_id,
        action=f"verification_{feedback_in.decision}",
        details={
            "decision": feedback_in.decision,
            "rationale": feedback_in.rationale,
            "reviewer": feedback_in.reviewer,
            "cluster_label": cluster.label
        }
    )
    db.add(audit)

    db.commit()
    db.refresh(feedback)
    return feedback

@router.get("/{cluster_id}/feedback")
def get_cluster_feedback(cluster_id: str, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.cluster_id == cluster_id).first()
    if not feedback:
        return {"status": "unreviewed"}
    return feedback
