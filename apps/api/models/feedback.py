import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from apps.api.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    cluster_id = Column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    decision = Column(String(50), nullable=False)  # confirmed, edited, dismissed
    rationale = Column(Text, nullable=True)
    reviewer = Column(String(100), default="Reliability Engineer")
    custom_label = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    cluster = relationship("Cluster", back_populates="feedback")

class DefectFingerprint(Base):
    __tablename__ = "defect_fingerprints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    component = Column(String(150), nullable=True, index=True)
    symptoms = Column(JSON, default=list) # List of string symptoms
    conditions = Column(JSON, default=list) # List of operating conditions
    example_claims = Column(JSON, default=list) # List of claim external IDs
    semantic_signature = Column(Text, nullable=True) # Normalized semantic text
    vector = Column(JSON, nullable=True) # Centroid embedding vector
    confirmed_count = Column(String(50), default="1")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    dataset_name = Column(String(200), default="claims_dataset")
    total_claims = Column(String(50), default="0")
    clusters_found = Column(String(50), default="0")
    alerts_critical = Column(String(50), default="0")
    alerts_high = Column(String(50), default="0")
    mismatches_detected = Column(String(50), default="0")
    status = Column(String(50), default="completed") # running, completed, failed
    config_params = Column(JSON, default=dict)
    summary_metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False) # cluster, claim, feedback, run
    entity_id = Column(String(64), nullable=False)
    action = Column(String(100), nullable=False) # ingested, analyzed, confirmed, dismissed, edited
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
