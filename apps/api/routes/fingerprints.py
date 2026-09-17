from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.db.session import get_db
from apps.api.models.feedback import DefectFingerprint
from apps.api.schemas.feedback import DefectFingerprintOut, DefectFingerprintCreate, MatchRequest, MatchResult
from apps.api.services.fingerprints import match_claim_to_fingerprints, match_cluster_to_precedents

router = APIRouter(prefix="/fingerprints", tags=["Defect Fingerprints"])

@router.get("", response_model=List[DefectFingerprintOut])
def list_fingerprints(db: Session = Depends(get_db)):
    """
    Returns all organizational defect fingerprints stored in persistent memory.
    """
    fps = db.query(DefectFingerprint).order_by(desc(DefectFingerprint.updated_at)).all()
    return fps

@router.post("", response_model=DefectFingerprintOut)
def create_fingerprint(fp_in: DefectFingerprintCreate, db: Session = Depends(get_db)):
    fp = DefectFingerprint(
        name=fp_in.name,
        description=fp_in.description,
        component=fp_in.component,
        symptoms=fp_in.symptoms,
        conditions=fp_in.conditions,
        example_claims=fp_in.example_claims,
        semantic_signature=fp_in.semantic_signature,
        confirmed_count="1"
    )
    db.add(fp)
    db.commit()
    db.refresh(fp)
    return fp

@router.post("/match", response_model=List[MatchResult])
def match_narrative(req: MatchRequest, db: Session = Depends(get_db)):
    """
    Tests an incoming narrative or claim against the organization's defect knowledge base.
    """
    return match_claim_to_fingerprints(
        db=db,
        narrative=req.narrative,
        component=req.component,
        symptom=req.symptom
    )

@router.get("/precedents/{cluster_id}", response_model=List[Dict[str, Any]])
def get_cluster_precedents(cluster_id: str, db: Session = Depends(get_db)):
    """
    Performs Neural Case-Based Reasoning (CBR): finds verified historical defect precedents
    and prior 8D dossiers matching the target defect cluster.
    """
    return match_cluster_to_precedents(db=db, cluster_id=cluster_id)

