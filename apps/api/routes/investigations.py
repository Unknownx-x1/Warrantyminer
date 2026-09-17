import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.db.session import get_db
from apps.api.models.cluster import Cluster
from apps.api.models.investigation import Investigation, AgentFinding, ToolExecutionLog
from apps.api.schemas.investigation import (
    InvestigationOut,
    InvestigationDetailOut,
    AgentFindingOut,
    ToolExecutionLogOut,
    InvestigationDecisionRequest,
    RunInvestigationRequest
)
from apps.api.services.investigation_orchestrator import orchestrator
from apps.api.services.fingerprints import create_fingerprint_from_investigation
from apps.api.services.forensic_copilot import copilot

router = APIRouter(prefix="/investigations", tags=["Investigations"])

@router.get("/{cluster_id}/stream")
def stream_investigation_sse(
    cluster_id: str,
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events (SSE) stream delivering real-time agent thoughts,
    tool executions, adversarial debate challenges, and 8D report generation.
    """
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    def event_generator():
        gen = orchestrator.stream_investigation(db, cluster_id)
        for event in gen:
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@router.post("/run", response_model=Dict[str, Any])
def run_investigations(
    payload: RunInvestigationRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers an autonomous multi-agent engineering investigation for a specific cluster
    or for all high/critical alerted clusters if cluster_id is omitted.
    """
    if payload.cluster_id:
        cluster = db.query(Cluster).filter(Cluster.id == payload.cluster_id).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        inv = orchestrator.run_investigation(db, payload.cluster_id, force_recompute=payload.force_recompute)
        return {
            "status": "completed",
            "investigations_created": 1,
            "investigation_id": inv.id,
            "cluster_id": inv.cluster_id,
            "confidence": inv.confidence,
            "classification": inv.overall_classification,
            "execution_time_ms": inv.execution_time_ms
        }
    else:
        invs = orchestrator.run_all_alerted_investigations(db)
        return {
            "status": "completed",
            "investigations_created": len(invs),
            "investigation_ids": [i.id for i in invs]
        }

@router.get("", response_model=List[InvestigationOut])
def list_investigations(
    status: Optional[str] = Query(None, description="Filter by status: completed, running, needs_evidence"),
    decision: Optional[str] = Query(None, description="Filter by decision: unreviewed, confirmed, rejected"),
    db: Session = Depends(get_db)
):
    query = db.query(Investigation).order_by(desc(Investigation.created_at))
    if status:
        query = query.filter(Investigation.status == status)
    if decision:
        query = query.filter(Investigation.decision == decision)
    return query.all()

@router.get("/{investigation_id}", response_model=InvestigationDetailOut)
def get_investigation_detail(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv

@router.get("/cluster/{cluster_id}", response_model=InvestigationDetailOut)
def get_investigation_by_cluster(cluster_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.cluster_id == cluster_id).order_by(desc(Investigation.created_at)).first()
    if not inv:
        # Run investigation on demand if cluster exists
        cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        inv = orchestrator.run_investigation(db, cluster_id, force_recompute=True)
    return inv

@router.get("/{investigation_id}/findings", response_model=List[AgentFindingOut])
def get_investigation_findings(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv.findings

@router.get("/{investigation_id}/tools", response_model=List[ToolExecutionLogOut])
def get_investigation_tool_logs(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv.tool_logs

@router.get("/{investigation_id}/report-8d", response_model=Dict[str, Any])
def get_investigation_8d_report(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv.report_8d or {}

@router.get("/{investigation_id}/tsb", response_model=Dict[str, Any])
def get_investigation_tsb(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv.tsb_draft or {}

@router.post("/{investigation_id}/decision", response_model=Dict[str, Any])
def submit_investigation_decision(
    investigation_id: str,
    payload: InvestigationDecisionRequest,
    db: Session = Depends(get_db)
):
    """
    Human-in-the-loop verification gate.
    When confirmed, automatically commits verified defect signature to Defect Memory.
    """
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    inv.decision = payload.decision
    inv.decision_rationale = payload.rationale
    inv.reviewer = payload.reviewer or "Reliability Engineer"
    
    # Also update associated cluster status
    if inv.cluster:
        inv.cluster.status = payload.decision
        if payload.custom_label:
            inv.cluster.label = payload.custom_label

    db.commit()

    fingerprint_created = None
    if payload.decision == "confirmed":
        fp = create_fingerprint_from_investigation(
            db=db,
            investigation_id=inv.id,
            engineer_name=inv.reviewer,
            custom_label=payload.custom_label
        )
        if fp:
            fingerprint_created = {"id": fp.id, "name": fp.name}

    return {
        "status": "success",
        "investigation_id": inv.id,
        "decision": inv.decision,
        "reviewer": inv.reviewer,
        "defect_memory_created": fingerprint_created is not None,
        "fingerprint": fingerprint_created
    }

@router.post("/{cluster_id}/chat", response_model=Dict[str, Any])
def forensic_copilot_chat(
    cluster_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Forensic Multi-Agent Copilot: Allows engineers to cross-examine the agent mesh
    regarding defect mechanisms, statistical significance, plant bias, and CAPA actions.
    """
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    
    try:
        res = copilot.answer_query(
            cluster_id=cluster_id,
            question=question,
            db=db,
            chat_history=payload.get("chat_history")
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forensic copilot error: {str(e)}")

