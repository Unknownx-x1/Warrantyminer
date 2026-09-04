import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from apps.api.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), nullable=True, index=True)
    cluster_index = Column(Integer, nullable=False) # HDBSCAN cluster ID (-1 for noise)
    label = Column(String(200), nullable=False) # Human readable label
    description = Column(Text, nullable=True) # Summary of failure patterns
    primary_component = Column(String(150), nullable=True)
    primary_symptom = Column(String(200), nullable=True)
    
    # Quantitative Metrics (All Computed Dynamically)
    claim_count = Column(Integer, default=0)
    cross_code_count = Column(Integer, default=0)
    plant_count = Column(Integer, default=0)
    model_count = Column(Integer, default=0)
    
    # Statistical and Trend Metrics
    baseline_volume = Column(Float, default=0.0)
    current_volume = Column(Float, default=0.0)
    growth_rate = Column(Float, default=0.0) # Percentage e.g. +312%
    significance_score = Column(Float, default=0.0) # Z-score
    cusum_score = Column(Float, default=0.0)
    coherence_score = Column(Float, default=0.0)
    alert_score = Column(Float, default=0.0) # 0 to 100
    alert_level = Column(String(50), default="NORMAL") # CRITICAL, HIGH, WATCH, NORMAL
    
    # Breakdown Caches (Aggregated from actual member claims)
    code_distribution = Column(JSON, default=dict)
    plant_distribution = Column(JSON, default=dict)
    model_distribution = Column(JSON, default=dict)
    time_series = Column(JSON, default=list)
    representative_claims = Column(JSON, default=list) # List of snippets/IDs
    ai_rationale = Column(JSON, default=dict) # why_grouped and why_alerted
    factor_breakdown = Column(JSON, default=dict) # 5-factor scoring model decomposition
    
    # Review status
    status = Column(String(50), default="unreviewed") # unreviewed, confirmed, edited, dismissed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    claim_memberships = relationship("ClusterClaim", back_populates="cluster", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="cluster", uselist=False, cascade="all, delete-orphan")

class ClusterClaim(Base):
    __tablename__ = "cluster_claims"

    cluster_id = Column(String(36), ForeignKey("clusters.id", ondelete="CASCADE"), primary_key=True)
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
    similarity_score = Column(Float, default=1.0)
    membership_probability = Column(Float, default=1.0)
    is_exemplar = Column(Integer, default=0)

    # Relationships
    cluster = relationship("Cluster", back_populates="claim_memberships")
    claim = relationship("Claim", back_populates="cluster_memberships")
