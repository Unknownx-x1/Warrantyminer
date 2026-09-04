from typing import Optional, List, Any
import datetime as dt
from pydantic import BaseModel, Field, field_validator

class ClaimBase(BaseModel):
    claim_id: str = Field(..., description="External unique claim identifier, e.g. C-10021")
    date: dt.date = Field(..., description="Claim occurrence date (YYYY-MM-DD)")
    product_model: Optional[str] = Field(None, description="Vehicle or product model")
    plant: Optional[str] = Field(None, description="Assembly plant or service facility")
    failure_code: Optional[str] = Field(None, description="Assigned structured failure code")
    narrative: str = Field(..., min_length=3, description="Raw technician or customer narrative")
    source: Optional[str] = Field("upload", description="Data source identifier")

    @field_validator("narrative")
    @classmethod
    def narrative_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Narrative text cannot be empty")
        return v

    @field_validator("claim_id")
    @classmethod
    def claim_id_trim(cls, v: str) -> str:
        return v.strip()

class ClaimCreate(ClaimBase):
    pass

class FailureSignatureOut(BaseModel):
    component: Optional[str] = None
    symptom: Optional[str] = None
    condition: Optional[str] = None
    severity: Optional[str] = None
    inferred_failure: Optional[str] = None
    contributing_factors: List[str] = []
    extraction_confidence: float = 0.0

    class Config:
        from_attributes = True

class CodeMismatchOut(BaseModel):
    assigned_code: Optional[str] = None
    inferred_category: Optional[str] = None
    mismatch_severity: str = "NORMAL"
    is_mismatch: int = 0
    mismatch_score: float = 0.0
    reason: Optional[str] = None
    confidence: float = 0.0

    class Config:
        from_attributes = True

class ClaimDetailOut(BaseModel):
    id: str
    external_claim_id: str
    claim_date: dt.date
    product_model: Optional[str] = None
    plant: Optional[str] = None
    failure_code: Optional[str] = None
    narrative: str
    source: Optional[str] = None
    created_at: dt.datetime
    signature: Optional[FailureSignatureOut] = None
    mismatch: Optional[CodeMismatchOut] = None
    cluster_id: Optional[str] = None
    cluster_label: Optional[str] = None

    class Config:
        from_attributes = True

class ClaimsListResponse(BaseModel):
    total: int
    items: List[ClaimDetailOut]
    page: int
    page_size: int
