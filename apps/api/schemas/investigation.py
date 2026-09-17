from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ToolExecutionLogOut(BaseModel):
    id: str
    investigation_id: str
    agent_role: str
    tool_name: str
    input_params: Dict[str, Any] = {}
    output_summary: Optional[str] = None
    output_data: Dict[str, Any] = {}
    status: str
    duration_ms: float
    evidence_refs: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

class AgentFindingOut(BaseModel):
    id: str
    investigation_id: str
    agent_role: str
    agent_name: str
    statement: str
    classification: str # OBSERVED, INFERRED, UNKNOWN
    confidence: float
    evidence_claim_ids: List[str] = []
    contradiction_claim_ids: List[str] = []
    metadata_json: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True

class DSection(BaseModel):
    title: str
    content: str
    status: str # ESTABLISHED, INFERRED, NOT_ESTABLISHED
    evidence: List[str] = []

class Report8D(BaseModel):
    cluster_id: str
    cluster_label: str
    generated_at: str
    d1_team: DSection
    d2_problem_description: DSection
    d3_containment_action: DSection
    d4_root_cause: DSection
    d5_corrective_action: DSection
    d6_validation_plan: DSection
    d7_prevention_action: DSection
    d8_closure_and_cost: DSection

class TSBDraft(BaseModel):
    tsb_id: str
    cluster_id: str
    title: str
    issue_date: str
    condition: str
    affected_vehicles: str
    symptoms_observed: List[str] = []
    diagnostic_procedure: str
    interim_repair_recommendation: str
    parts_information: str
    warranty_coding_guidance: str
    evidence_claims: List[str] = []

class InvestigationOut(BaseModel):
    id: str
    cluster_id: str
    status: str
    decision: str
    decision_rationale: Optional[str] = None
    reviewer: str
    summary_conclusion: Optional[str] = None
    confidence: float
    overall_classification: str
    supporting_claims_count: int
    contradicting_claims_count: int
    unknowns: List[str] = []
    recommendations: List[str] = []
    metrics_snapshot: Dict[str, Any] = {}
    execution_time_ms: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InvestigationDetailOut(InvestigationOut):
    findings: List[AgentFindingOut] = []
    tool_logs: List[ToolExecutionLogOut] = []
    report_8d: Optional[Dict[str, Any]] = None
    tsb_draft: Optional[Dict[str, Any]] = None

class InvestigationDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(confirmed|rejected|needs_evidence)$", description="Engineer verification decision")
    rationale: Optional[str] = Field(None, description="Engineer technical rationale")
    reviewer: Optional[str] = Field("Reliability Engineer", description="Reviewer name")
    custom_label: Optional[str] = Field(None, description="Optional updated defect label")

class RunInvestigationRequest(BaseModel):
    cluster_id: Optional[str] = None
    force_recompute: bool = False
