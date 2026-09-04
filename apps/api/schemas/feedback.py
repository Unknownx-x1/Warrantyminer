from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class FeedbackCreate(BaseModel):
    decision: str = Field(..., pattern="^(confirmed|edited|dismissed)$", description="Human verification decision")
    rationale: Optional[str] = Field(None, description="Engineer justification or note")
    reviewer: Optional[str] = Field("Reliability Engineer", description="Engineer name/ID")
    custom_label: Optional[str] = Field(None, description="Updated pattern label if edited")

class FeedbackOut(BaseModel):
    id: str
    cluster_id: str
    decision: str
    rationale: Optional[str] = None
    reviewer: str
    custom_label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DefectFingerprintCreate(BaseModel):
    name: str
    description: Optional[str] = None
    component: Optional[str] = None
    symptoms: List[str] = []
    conditions: List[str] = []
    example_claims: List[str] = []
    semantic_signature: Optional[str] = None

class DefectFingerprintOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    component: Optional[str] = None
    symptoms: List[str] = []
    conditions: List[str] = []
    example_claims: List[str] = []
    confirmed_count: str = "1"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MatchRequest(BaseModel):
    narrative: str
    component: Optional[str] = None
    symptom: Optional[str] = None

class MatchResult(BaseModel):
    fingerprint_id: str
    fingerprint_name: str
    component: Optional[str] = None
    similarity_score: float
    matched_symptoms: List[str] = []
    confidence: float
    recommendation: str

class AnalysisRunRequest(BaseModel):
    dataset_name: Optional[str] = "claims_dataset"
    min_cluster_size: Optional[int] = None
    alert_threshold: Optional[float] = None
    force_recompute: bool = False

class AnalysisRunResponse(BaseModel):
    run_id: str
    status: str
    total_claims: int
    clusters_found: int
    alerts_critical: int
    alerts_high: int
    mismatches_detected: int
    processing_time_ms: float
    summary: Dict[str, Any] = {}
    events: List[str] = []
    steps: Dict[str, Any] = {}
