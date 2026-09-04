from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from apps.api.db.session import get_db
from apps.api.services.baseline import compute_traditional_baseline_comparison

router = APIRouter(prefix="/baseline", tags=["Baseline Comparison"])

@router.get("/comparison")
def get_baseline_comparison(
    cluster_id: Optional[str] = Query(None, description="Optional cluster ID to compare against"),
    db: Session = Depends(get_db)
):
    """
    Returns side-by-side comparison of Traditional Code-Level Monitoring vs WarrantyPatternMiner Semantic Cluster.
    """
    return compute_traditional_baseline_comparison(db, target_cluster_id=cluster_id)
