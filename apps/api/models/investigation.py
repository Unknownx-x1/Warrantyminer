import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from apps.api.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    cluster_id = Column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="completed") # running, completed, failed, needs_evidence
    decision = Column(String(50), default="unreviewed") # unreviewed, confirmed, rejected, needs_evidence
    decision_rationale = Column(Text, nullable=True)
    reviewer = Column(String(100), default="Reliability Engineer")
    
    # Synthesis & Conclusions
    summary_conclusion = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0) # 0.0 to 1.0
    overall_classification = Column(String(50), default="EMERGING_DEFECT") # EMERGING_DEFECT, FALSE_POSITIVE, DATA_ARTIFACT, INSUFFICIENT_EVIDENCE
    
    # Evidence counts
    supporting_claims_count = Column(Integer, default=0)
    contradicting_claims_count = Column(Integer, default=0)
    unknowns = Column(JSON, default=list) # List of string descriptions of unknowns
    recommendations = Column(JSON, default=list) # List of recommended actions
    
    # Deliverables (Computed from verified findings)
    report_8d = Column(JSON, default=dict) # Structured D1-D8 report sections
    tsb_draft = Column(JSON, default=dict) # Draft Technical Service Bulletin
    metrics_snapshot = Column(JSON, default=dict) # Snapshot of cluster stats at investigation time
    
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cluster = relationship("Cluster", backref="investigations")
    findings = relationship("AgentFinding", back_populates="investigation", cascade="all, delete-orphan", order_by="AgentFinding.created_at")
    tool_logs = relationship("ToolExecutionLog", back_populates="investigation", cascade="all, delete-orphan", order_by="ToolExecutionLog.created_at")

class AgentFinding(Base):
    __tablename__ = "agent_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_role = Column(String(50), nullable=False) # investigator, analytics, red_team, regulatory, capa
    agent_name = Column(String(100), nullable=False)
    statement = Column(Text, nullable=False)
    classification = Column(String(50), default="OBSERVED") # OBSERVED, INFERRED, UNKNOWN
    confidence = Column(Float, default=0.0) # 0.0 to 1.0
    
    # Evidence linkages (Claims cited)
    evidence_claim_ids = Column(JSON, default=list) # List of external claim IDs
    contradiction_claim_ids = Column(JSON, default=list) # List of contradicting claim IDs
    metadata_json = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    investigation = relationship("Investigation", back_populates="findings")

class ToolExecutionLog(Base):
    __tablename__ = "tool_execution_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_role = Column(String(50), nullable=False)
    tool_name = Column(String(100), nullable=False)
    input_params = Column(JSON, default=dict)
    output_summary = Column(Text, nullable=True)
    output_data = Column(JSON, default=dict)
    status = Column(String(50), default="SUCCESS") # SUCCESS, UNAVAILABLE, ERROR
    duration_ms = Column(Float, default=0.0)
    evidence_refs = Column(JSON, default=list) # List of relevant claim IDs or entities
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    investigation = relationship("Investigation", back_populates="tool_logs")
