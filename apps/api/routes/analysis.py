from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.db.session import get_db
from apps.api.models.feedback import AnalysisRun
from apps.api.schemas.feedback import AnalysisRunRequest, AnalysisRunResponse
from apps.api.services.pipeline_orchestrator import execute_full_pipeline

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.post("/run", response_model=AnalysisRunResponse)
def trigger_analysis(
    request: AnalysisRunRequest = AnalysisRunRequest(),
    db: Session = Depends(get_db)
):
    """
    Executes the analytical pipeline: Ingestion validation -> Extraction -> Embeddings -> HDBSCAN -> Trend Analysis -> Alerts.
    """
    try:
        result = execute_full_pipeline(
            db=db,
            dataset_name=request.dataset_name or "claims_dataset",
            min_cluster_size=request.min_cluster_size,
            force_recompute=request.force_recompute
        )
        return AnalysisRunResponse(
            run_id=result["run_id"],
            status=result["status"],
            total_claims=result["total_claims"],
            clusters_found=result["clusters_found"],
            alerts_critical=result.get("alerts_critical", 0),
            alerts_high=result.get("alerts_high", 0),
            mismatches_detected=result.get("mismatches_detected", 0),
            processing_time_ms=result["processing_time_ms"],
            summary=result.get("summary", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

@router.get("/runs")
def list_analysis_runs(db: Session = Depends(get_db)):
    runs = db.query(AnalysisRun).order_by(desc(AnalysisRun.created_at)).limit(20).all()
    return runs
