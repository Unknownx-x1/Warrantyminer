import logging
import numpy as np
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from apps.api.models.cluster import Cluster
from apps.api.models.feedback import DefectFingerprint
from apps.api.models.claim import Claim, FailureSignature, Embedding
from apps.api.services.embeddings import embed_text

logger = logging.getLogger(__name__)

def _generate_fingerprint_vector(
    component: Optional[str],
    symptoms: List[str],
    conditions: List[str],
    description: Optional[str] = None,
    narratives: Optional[List[str]] = None
) -> List[float]:
    """
    Computes a 384-dimensional FastEmbed ONNX vector for a defect fingerprint
    combining structured taxonomy tokens and narrative descriptions.
    """
    parts = []
    if component:
        parts.append(f"Component: {component}.")
    if symptoms:
        parts.append(f"Symptoms: {', '.join(symptoms)}.")
    if conditions:
        parts.append(f"Operating Conditions: {', '.join(conditions)}.")
    if description:
        parts.append(f"Description: {description}")
    if narratives:
        parts.append(f"Observed Cases: {' '.join(narratives[:3])}")
    
    text_signature = " ".join(parts) if parts else "unspecified automotive failure pattern"
    vector = embed_text(text_signature)
    return vector.tolist()

def create_fingerprint_from_cluster(db: Session, cluster: Cluster, engineer_name: str = "Reliability Engineer") -> DefectFingerprint:
    """
    Constructs an organizational Defect Fingerprint from a confirmed cluster with FastEmbed 384D vector.
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
    sample_narratives = [c.narrative for c in claims[:3]]

    # Compute dense vector representation
    vector_list = _generate_fingerprint_vector(
        component=cluster.primary_component,
        symptoms=top_symptoms,
        conditions=top_conditions,
        description=cluster.description,
        narratives=sample_narratives
    )

    existing = db.query(DefectFingerprint).filter(DefectFingerprint.name == cluster.label).first()
    if existing:
        current_cnt = int(existing.confirmed_count) if str(existing.confirmed_count).isdigit() else 1
        existing.confirmed_count = str(current_cnt + 1)
        existing.description = cluster.description
        existing.symptoms = list(set((existing.symptoms or []) + top_symptoms))
        existing.conditions = list(set((existing.conditions or []) + top_conditions))
        existing.example_claims = list(set((existing.example_claims or []) + example_claims))
        existing.vector = vector_list
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
        vector=vector_list,
        confirmed_count="1"
    )
    db.add(fingerprint)
    db.commit()
    db.refresh(fingerprint)
    logger.info(f"Created Neural Defect Fingerprint: {fingerprint.name} with 384D vector")
    return fingerprint

def create_fingerprint_from_investigation(
    db: Session,
    investigation_id: str,
    engineer_name: str = "Reliability Engineer",
    custom_label: Optional[str] = None
) -> Optional[DefectFingerprint]:
    """
    Constructs an organizational Defect Fingerprint from a confirmed Investigation with FastEmbed 384D vector.
    """
    from apps.api.models.investigation import Investigation
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv or not inv.cluster:
        return None

    cluster = inv.cluster
    label = custom_label or cluster.label

    # Extract observed evidence from investigator findings
    obs_findings = [f for f in inv.findings if f.agent_role == "investigator"]
    comp_finding = next((f for f in obs_findings if "component" in f.statement.lower()), None)
    symp_finding = next((f for f in obs_findings if "symptom" in f.statement.lower()), None)
    cond_finding = next((f for f in obs_findings if "condition" in f.statement.lower()), None)

    component = cluster.primary_component or (comp_finding.metadata_json.get("component") if comp_finding else None)
    symptoms = [symp_finding.metadata_json.get("symptom")] if symp_finding and symp_finding.metadata_json.get("symptom") else ([cluster.primary_symptom] if cluster.primary_symptom else [])
    conditions = [cond_finding.metadata_json.get("condition")] if cond_finding and cond_finding.metadata_json.get("condition") else []

    claims = [cm.claim for cm in cluster.claim_memberships]
    example_claims = [c.external_claim_id for c in claims[:5]]
    sample_narratives = [c.narrative for c in claims[:3]]

    # Compute dense vector representation
    vector_list = _generate_fingerprint_vector(
        component=component,
        symptoms=symptoms,
        conditions=conditions,
        description=inv.summary_conclusion or cluster.description,
        narratives=sample_narratives
    )

    existing = db.query(DefectFingerprint).filter(DefectFingerprint.name == label).first()
    if existing:
        current_cnt = int(existing.confirmed_count) if str(existing.confirmed_count).isdigit() else 1
        existing.confirmed_count = str(current_cnt + 1)
        existing.description = inv.summary_conclusion or cluster.description
        existing.symptoms = list(set((existing.symptoms or []) + symptoms))
        existing.conditions = list(set((existing.conditions or []) + conditions))
        existing.example_claims = list(set((existing.example_claims or []) + example_claims))
        existing.vector = vector_list
        db.commit()
        db.refresh(existing)
        return existing

    fingerprint = DefectFingerprint(
        name=label,
        description=inv.summary_conclusion or cluster.description,
        component=component,
        symptoms=symptoms,
        conditions=conditions,
        example_claims=example_claims,
        semantic_signature=f"Component: {component} | Symptoms: {', '.join(symptoms)} | Conditions: {', '.join(conditions)}",
        vector=vector_list,
        confirmed_count="1"
    )
    db.add(fingerprint)
    db.commit()
    db.refresh(fingerprint)
    logger.info(f"Created Neural Defect Fingerprint from Investigation: {fingerprint.name}")
    return fingerprint

def match_claim_to_fingerprints(
    db: Session,
    narrative: str,
    component: Optional[str] = None,
    symptom: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Compares an incoming claim against known organizational Defect Fingerprints
    using FastEmbed 384-dimensional dense vector cosine similarity.
    """
    fingerprints = db.query(DefectFingerprint).all()
    if not fingerprints:
        return []

    # 1. Compute query vector
    query_parts = []
    if component:
        query_parts.append(f"Component: {component}.")
    if symptom:
        query_parts.append(f"Symptom: {symptom}.")
    query_parts.append(narrative)
    query_text = " ".join(query_parts)
    
    query_vec = embed_text(query_text)
    # Unit normalize query vector
    norm_q = np.linalg.norm(query_vec)
    if norm_q > 0:
        query_vec = query_vec / norm_q

    results = []
    text_lower = narrative.lower()

    for fp in fingerprints:
        # Get or compute fingerprint vector
        if fp.vector and len(fp.vector) == 384:
            fp_vec = np.array(fp.vector, dtype=np.float32)
        else:
            fp_vec = np.array(_generate_fingerprint_vector(
                component=fp.component,
                symptoms=fp.symptoms or [],
                conditions=fp.conditions or [],
                description=fp.description
            ), dtype=np.float32)
            fp.vector = fp_vec.tolist()
            db.commit()

        # Cosine similarity dot product
        norm_fp = np.linalg.norm(fp_vec)
        if norm_fp > 0:
            fp_vec = fp_vec / norm_fp

        cosine_sim = float(np.dot(query_vec, fp_vec))
        cosine_sim = max(0.0, min(1.0, cosine_sim))

        # Check keyword overlaps for explainable citations
        matched_symptoms = []
        for s in (fp.symptoms or []):
            s_lower = s.lower()
            keywords = [w for w in s_lower.replace("/", " ").replace("-", " ").split() if len(w) > 3]
            if any(k in text_lower for k in keywords) or (symptom and symptom.lower() in s_lower):
                matched_symptoms.append(s)

        # Composite score
        similarity = round(cosine_sim, 3)

        if similarity >= 0.35 or matched_symptoms:
            if similarity >= 0.70:
                rec = "High institutional match: Known failure mode recurrence. Apply verified 8D countermeasure."
            elif similarity >= 0.50:
                rec = "Moderate semantic match: Similar symptom topology to verified defect."
            else:
                rec = "Potential defect correlation based on shared subsystem acoustics/behavior."

            results.append({
                "fingerprint_id": fp.id,
                "fingerprint_name": fp.name,
                "component": fp.component,
                "similarity_score": similarity,
                "matched_symptoms": matched_symptoms,
                "confidence": similarity,
                "recommendation": rec,
                "confirmed_count": fp.confirmed_count
            })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results

def match_cluster_to_precedents(
    db: Session,
    cluster_id: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Performs Neural Case-Based Reasoning (CBR): matches a cluster against
    stored historical Defect Fingerprints and prior 8D investigations.
    """
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        return []

    fingerprints = db.query(DefectFingerprint).filter(DefectFingerprint.name != cluster.label).all()
    if not fingerprints:
        return []

    # Get embeddings of claims in this cluster to compute centroid
    claim_ids = [cm.claim_id for cm in cluster.claim_memberships]
    embs = db.query(Embedding).filter(Embedding.claim_id.in_(claim_ids)).all()

    if embs:
        cluster_vec = np.mean([e.vector for e in embs], axis=0)
        norm_c = np.linalg.norm(cluster_vec)
        if norm_c > 0:
            cluster_vec = cluster_vec / norm_c
    else:
        cluster_vec = embed_text(f"{cluster.label} {cluster.description or ''} {cluster.primary_component or ''}")

    precedents = []
    for fp in fingerprints:
        if fp.vector and len(fp.vector) == 384:
            fp_vec = np.array(fp.vector, dtype=np.float32)
        else:
            fp_vec = np.array(_generate_fingerprint_vector(
                component=fp.component,
                symptoms=fp.symptoms or [],
                conditions=fp.conditions or [],
                description=fp.description
            ), dtype=np.float32)

        norm_fp = np.linalg.norm(fp_vec)
        if norm_fp > 0:
            fp_vec = fp_vec / norm_fp

        cosine_sim = float(np.dot(cluster_vec, fp_vec))
        cosine_sim = max(0.0, min(1.0, round(cosine_sim, 3)))

        if cosine_sim >= 0.40:
            precedents.append({
                "precedent_id": fp.id,
                "name": fp.name,
                "component": fp.component,
                "similarity_score": cosine_sim,
                "confidence_pct": round(cosine_sim * 100, 1),
                "confirmed_count": fp.confirmed_count,
                "description": fp.description,
                "symptoms": fp.symptoms,
                "conditions": fp.conditions,
                "remedy_recommendation": f"Review containment protocol established for '{fp.name}'. Cross-check supplier lot history."
            })

    precedents.sort(key=lambda x: x["similarity_score"], reverse=True)
    return precedents[:top_k]

