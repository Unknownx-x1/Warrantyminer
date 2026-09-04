from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class TimePoint(BaseModel):
    period: str # e.g. "2026-01" or "Week 14"
    claim_count: int
    baseline: Optional[float] = None
    z_score: Optional[float] = None

class AIRationale(BaseModel):
    why_grouped: str
    why_alerted: str
    key_symptoms: List[str] = []
    affected_components: List[str] = []

class ClusterListItem(BaseModel):
    id: str
    run_id: Optional[str] = None
    cluster_index: int
    label: str
    description: Optional[str] = None
    primary_component: Optional[str] = None
    primary_symptom: Optional[str] = None
    claim_count: int
    cross_code_count: int
    plant_count: int
    model_count: int
    growth_rate: float
    significance_score: float
    coherence_score: float
    alert_score: float
    alert_level: str
    status: str
    created_at: datetime
    top_codes: Dict[str, int] = {}

    class Config:
        from_attributes = True

class ClusterDetail(ClusterListItem):
    baseline_volume: float
    current_volume: float
    cusum_score: float
    code_distribution: Dict[str, int] = {}
    plant_distribution: Dict[str, int] = {}
    model_distribution: Dict[str, int] = {}
    time_series: List[Dict[str, Any]] = []
    representative_claims: List[Dict[str, Any]] = []
    ai_rationale: Optional[AIRationale] = None
    feedback: Optional[Dict[str, Any]] = None

class ClusterClaimItem(BaseModel):
    claim_id: str
    external_claim_id: str
    claim_date: str
    product_model: Optional[str] = None
    plant: Optional[str] = None
    failure_code: Optional[str] = None
    narrative: str
    component: Optional[str] = None
    symptom: Optional[str] = None
    inferred_failure: Optional[str] = None
    is_mismatch: int = 0
    mismatch_severity: str = "NORMAL"
    mismatch_reason: Optional[str] = None
    similarity_score: float = 1.0

class ClusterClaimsResponse(BaseModel):
    cluster_id: str
    cluster_label: str
    total: int
    claims: List[ClusterClaimItem]
