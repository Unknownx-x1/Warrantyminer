import logging
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from apps.api.models.cluster import Cluster
from apps.api.models.feedback import DefectFingerprint
from apps.api.models.claim import Claim, FailureSignature

logger = logging.getLogger(__name__)

def create_fingerprint_from_cluster(db: Session, cluster: Cluster, engineer_name: str = "Reliability Engineer") -> DefectFingerprint:
    """
    Constructs an organizational Defect Fingerprint from a confirmed cluster.
    """
    claims = [cm.claim for cm in cluster.claim_memberships]
    signatures = [c.signature for c in claims if c.signature]

    symptoms = []
    for s in signatures:
        if s.symptom and s.symptom != "unspecified operational symptom":
            symptoms.append(s.symptom)
    top_symptoms = [item[0] for item in Counter(symptoms).most_common(5)]
    if not top_symptoms and cluster.primary_symptom:
        top_symptoms = [cluster.primary_symptom]

    conditions = []
    for s in signatures:
        if s.condition and s.condition != "normal operating conditions":
            conditions.append(s.condition)
    top_conditions = [item[0] for item in Counter(conditions).most_common(3)]

    example_claims = [c.external_claim_id for c in claims[:5]]

    existing = db.query(DefectFingerprint).filter(DefectFingerprint.name == cluster.label).first()
    if existing:
        current_cnt = int(existing.confirmed_count) if str(existing.confirmed_count).isdigit() else 1
        existing.confirmed_count = str(current_cnt + 1)
        existing.description = cluster.description
        existing.symptoms = list(set((existing.symptoms or []) + top_symptoms))
        existing.conditions = list(set((existing.conditions or []) + top_conditions))
        existing.example_claims = list(set((existing.example_claims or []) + example_claims))
        db.commit()
        db.refresh(existing)
        return existing

    fingerprint = DefectFingerprint(
        name=cluster.label,
        description=cluster.description,
        component=cluster.primary_component,
        symptoms=top_symptoms,
        conditions=top_conditions,
        example_claims=example_claims,
        semantic_signature=f"Component: {cluster.primary_component} | Symptoms: {', '.join(top_symptoms)} | Conditions: {', '.join(top_conditions)}",
        confirmed_count="1"
    )
    db.add(fingerprint)
    db.commit()
    db.refresh(fingerprint)
    logger.info(f"Created Defect Fingerprint: {fingerprint.name}")
    return fingerprint

def match_claim_to_fingerprints(db: Session, narrative: str, component: Optional[str] = None, symptom: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Compares a narrative / symptom against the known organizational Defect Fingerprints.
    """
    fingerprints = db.query(DefectFingerprint).all()
    if not fingerprints:
        return []

    text = narrative.lower()
    comp_input = (component or "").lower()
    symp_input = (symptom or "").lower()

    results = []
    for fp in fingerprints:
        score = 0.0
        matched_symptoms = []
        
        # Component matching
        fp_comp = (fp.component or "").lower()
        comp_keywords = ["front left", "front-left", "suspension", "strut", "wheel", "brake", "engine", "steering", "hvac", "battery"]
        matched_comp_kw = [k for k in comp_keywords if k in fp_comp and (k in text or k.replace("-", " ") in text)]
        
        if matched_comp_kw or fp_comp in text:
            score += 0.40
        elif comp_input and (comp_input in fp_comp or fp_comp in comp_input):
            score += 0.35

        # Symptom matching
        for s in (fp.symptoms or []):
            s_lower = s.lower()
            keywords = [w for w in s_lower.replace("/", " ").replace("-", " ").split() if len(w) > 3]
            if any(k in text for k in keywords) or (symp_input and symp_input in s_lower):
                matched_symptoms.append(s)
                score += 0.35
                break

        # Condition matching
        for c in (fp.conditions or []):
            c_words = [w for w in c.lower().replace("/", " ").replace("-", " ").split() if len(w) > 3]
            if any(w in text for w in c_words):
                score += 0.20
                break

        similarity = min(0.98, round(score, 2))
        if similarity >= 0.30:
            rec = "High similarity to verified defect" if similarity >= 0.60 else "Potential defect correlation"
            results.append({
                "fingerprint_id": fp.id,
                "fingerprint_name": fp.name,
                "component": fp.component,
                "similarity_score": similarity,
                "matched_symptoms": matched_symptoms,
                "confidence": similarity,
                "recommendation": rec
            })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results
