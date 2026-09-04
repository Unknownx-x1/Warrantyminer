import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Column, String, Date, DateTime, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from apps.api.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    external_claim_id = Column(String(64), unique=True, nullable=False, index=True)
    claim_date = Column(Date, nullable=False, index=True)
    product_model = Column(String(100), nullable=True, index=True)
    plant = Column(String(100), nullable=True, index=True)
    failure_code = Column(String(100), nullable=True, index=True)
    narrative = Column(Text, nullable=False)
    source = Column(String(100), default="upload")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    signature = relationship("FailureSignature", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    embedding = relationship("Embedding", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    mismatch = relationship("CodeMismatch", back_populates="claim", uselist=False, cascade="all, delete-orphan")
    cluster_memberships = relationship("ClusterClaim", back_populates="claim", cascade="all, delete-orphan")

class FailureSignature(Base):
    __tablename__ = "failure_signatures"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    component = Column(String(150), nullable=True, index=True)
    symptom = Column(String(200), nullable=True, index=True)
    condition = Column(String(200), nullable=True)
    severity = Column(String(50), nullable=True)
    inferred_failure = Column(String(250), nullable=True)
    contributing_factors = Column(JSON, default=list)
    extraction_confidence = Column(Float, default=0.0)
    model_version = Column(String(100), default="v1.0")
    raw_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    claim = relationship("Claim", back_populates="signature")

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    vector = Column(JSON, nullable=False)  # Serialized float array / list
    semantic_text = Column(Text, nullable=True)
    model_name = Column(String(100), default="semantic-v1")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    claim = relationship("Claim", back_populates="embedding")

class CodeMismatch(Base):
    __tablename__ = "code_mismatches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    assigned_code = Column(String(100), nullable=True)
    inferred_category = Column(String(150), nullable=True)
    mismatch_severity = Column(String(50), default="NORMAL") # HIGH, MEDIUM, NORMAL
    is_mismatch = Column(Integer, default=0) # 1 if mismatch, 0 if match
    mismatch_score = Column(Float, default=0.0) # 0.0 to 1.0
    reason = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    claim = relationship("Claim", back_populates="mismatch")
