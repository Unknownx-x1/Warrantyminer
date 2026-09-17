import logging
import numpy as np
from typing import Dict, Any, Tuple, Optional
from sklearn.preprocessing import normalize
from sqlalchemy.orm import Session

from apps.api.config import settings
from apps.api.models.claim import Claim, FailureSignature, CodeMismatch
from apps.api.services.embeddings import get_fastembed_model

logger = logging.getLogger(__name__)

# Standard Automotive Engineering Domain Semantic Anchors
DOMAIN_ANCHORS = {
    "SUSPENSION": {
        "name": "Suspension & Chassis Mechanical",
        "description": "Automotive mechanical chassis suspension, struts, shocks, control arms, ball joints, sway bar bushings, springs, corner knocking, clunking over bumps.",
        "expected_codes": ["SUSPENSION", "CHASSIS", "STRUT"]
    },
    "BRAKES": {
        "name": "Braking System",
        "description": "Brake friction assembly, rotors, brake pads, calipers, hydraulic lines, brake pedal pulsation, judder, squeal, grinding stops, stopping distance.",
        "expected_codes": ["BRAKES", "BRAKE", "ABS"]
    },
    "ELECTRICAL": {
        "name": "Electrical & Electronics",
        "description": "Vehicle electrical system, 12V battery, wiring harness, lighting, fuses, relays, instrument cluster, center display screen, infotainment, carplay, bms.",
        "expected_codes": ["ELECTRICAL", "BATTERY", "LIGHTING", "INFOTAINMENT"]
    },
    "STEERING": {
        "name": "Steering System",
        "description": "Power steering rack and pinion, steering column, tie rod ends, steering wheel vibration and shudder, hydraulic assist.",
        "expected_codes": ["STEERING", "RACK"]
    },
    "HVAC": {
        "name": "HVAC & Thermal Management",
        "description": "Automotive climate control, heating, air conditioning compressor, blower motor, heater core matrix coolant leak, defrost, a/c refrigeration.",
        "expected_codes": ["HVAC", "CLIMATE", "A/C", "HEATER"]
    },
    "POWERTRAIN": {
        "name": "Powertrain & Drivetrain",
        "description": "Engine mechanical, transmission gearbox, torque converter, electric drive motor, powertrain misfire, gear slippage, exhaust, axle drone.",
        "expected_codes": ["POWERTRAIN", "ENGINE", "TRANSMISSION", "MOTOR"]
    },
    "BODY": {
        "name": "Body & Exterior Hardware",
        "description": "Vehicle exterior body panels, doors, latches, weatherstripping, window regulators, wiper linkage, trim rattles, paint.",
        "expected_codes": ["BODY", "DOOR", "WIPER", "TRIM"]
    }
}

_DOMAIN_VECTORS_CACHE = None

def get_domain_vectors():
    """Returns cached, unit-normalized dense vectors for domain semantic anchors."""
    global _DOMAIN_VECTORS_CACHE
    if _DOMAIN_VECTORS_CACHE is None:
        model = get_fastembed_model()
        if model is not None:
            try:
                names = list(DOMAIN_ANCHORS.keys())
                texts = [DOMAIN_ANCHORS[k]["description"] for k in names]
                raw_vecs = list(model.embed(texts))
                arr = normalize(np.array(raw_vecs, dtype=np.float32), norm="l2")
                _DOMAIN_VECTORS_CACHE = {names[i]: arr[i] for i in range(len(names))}
            except Exception as e:
                logger.warning(f"Failed to generate domain anchor vectors: {e}")
                _DOMAIN_VECTORS_CACHE = None
    return _DOMAIN_VECTORS_CACHE

def evaluate_code_mismatch(
    assigned_code: Optional[str],
    component: Optional[str],
    symptom: Optional[str],
    narrative: str,
    claim_vec: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Evaluates semantic divergence between dealer failure codes and technician narrative
    using continuous neural embedding similarity against domain engineering anchors.
    """
    code = (assigned_code or "OTHER").upper().strip()
    comp = (component or "").lower().strip()
    symp = (symptom or "").lower().strip()
    narr = (narrative or "").lower().strip()

    # Construct rich semantic representation
    semantic_parts = []
    if comp and comp != "unspecified component":
        semantic_parts.append(f"Component: {comp}")
    if symp and symp != "unspecified operational symptom":
        semantic_parts.append(f"Symptom: {symp}")
    semantic_parts.append(f"Narrative: {narr}")
    claim_text = " | ".join(semantic_parts)

    domain_vectors = get_domain_vectors()
    model = get_fastembed_model()

    if domain_vectors and (model or claim_vec is not None):
        try:
            if claim_vec is None and model is not None:
                claim_vec = normalize(np.array(list(model.embed([claim_text])), dtype=np.float32), norm="l2")[0]

            if claim_vec is not None:
                sims = {name: float(np.dot(claim_vec, domain_vectors[name])) for name in domain_vectors}
                
                best_domain_key = max(sims, key=sims.get)
                best_sim = sims[best_domain_key]
                best_domain_info = DOMAIN_ANCHORS[best_domain_key]

                # Find similarity to assigned code domain
                assigned_clean = code.split("-")[0].strip()
                assigned_domain_key = None
                for d_key, d_info in DOMAIN_ANCHORS.items():
                    if any(exp in code for exp in d_info["expected_codes"]):
                        assigned_domain_key = d_key
                        break

                assigned_sim = sims.get(assigned_domain_key, 0.0) if assigned_domain_key else 0.0

                # 1. Catchall / Generic Checkbox Code concealment
                if code in ["OTHER", "UNASSIGNED", "RIDE QUALITY", "UNKNOWN_CODE", "NFF"]:
                    if best_sim >= settings.NLI_MISMATCH_THRESHOLD:
                        return {
                            "assigned_code": code,
                            "inferred_category": best_domain_info["name"],
                            "is_mismatch": 1,
                            "mismatch_severity": "HIGH" if best_sim >= 0.70 else "MEDIUM",
                            "mismatch_score": round(min(0.96, best_sim), 2),
                            "reason": f"Generic catch-all code '{code}' used for distinct {best_domain_info['name']} defect (semantic affinity: {best_sim*100:.0f}%)."
                        }
                    else:
                        return {
                            "assigned_code": code,
                            "inferred_category": comp or "General Field Issue",
                            "is_mismatch": 0,
                            "mismatch_severity": "NORMAL",
                            "mismatch_score": 0.25,
                            "reason": f"Assigned generic code '{code}' aligns with general field observation."
                        }

                # 2. Cross-Domain Direct Contradiction
                if assigned_domain_key and assigned_domain_key != best_domain_key:
                    divergence = best_sim - assigned_sim
                    if divergence >= 0.08 or (assigned_sim < 0.55 and divergence >= 0.05):
                        severity = "HIGH" if ((best_sim >= 0.60 and divergence >= 0.10) or "NFF" in code) else "MEDIUM"
                        mismatch_score = round(min(0.98, max(0.65, divergence * 2.0 + 0.50)), 2)
                        return {
                            "assigned_code": code,
                            "inferred_category": f"{best_domain_info['name']} (Misclassified as {assigned_domain_key})",
                            "is_mismatch": 1,
                            "mismatch_severity": severity,
                            "mismatch_score": mismatch_score,
                            "reason": f"Assigned code '{code}' ({assigned_sim*100:.0f}% affinity) contradicts technician narrative describing {best_domain_info['name']} ({best_sim*100:.0f}% affinity)."
                        }

                # 3. Domain Agreement
                return {
                    "assigned_code": code,
                    "inferred_category": best_domain_info["name"],
                    "is_mismatch": 0,
                    "mismatch_severity": "NORMAL",
                    "mismatch_score": round(max(0.0, 0.40 - assigned_sim), 2),
                    "reason": f"Assigned failure code '{code}' agrees with narrative domain ({best_domain_info['name']})."
                }
        except Exception as e:
            logger.warning(f"Neural mismatch evaluation error: {e}, using rule fallback")

    # Deterministic Rule-Based Fallback
    if code in ["OTHER", "UNASSIGNED", "RIDE QUALITY"]:
        if "suspension" in comp or "strut" in comp or "bushing" in comp:
            return {
                "assigned_code": code,
                "inferred_category": "Suspension & Chassis Mechanical",
                "is_mismatch": 1,
                "mismatch_severity": "HIGH",
                "mismatch_score": 0.88,
                "reason": f"Generic code '{code}' used for mechanical suspension defect: '{comp}'."
            }
        elif "brake" in comp or "rotor" in comp:
            return {
                "assigned_code": code,
                "inferred_category": "Braking System",
                "is_mismatch": 1,
                "mismatch_severity": "MEDIUM",
                "mismatch_score": 0.75,
                "reason": f"Generic code '{code}' used for distinct brake symptom."
            }
        else:
            return {
                "assigned_code": code,
                "inferred_category": comp or "General Field Issue",
                "is_mismatch": 0,
                "mismatch_severity": "NORMAL",
                "mismatch_score": 0.30,
                "reason": f"Assigned generic code '{code}'."
            }

    if "ELECTRICAL" in code and ("suspension" in comp or "clunk" in narr or "strut" in comp):
        return {
            "assigned_code": code,
            "inferred_category": "Suspension Mechanical (Misclassified as Electrical)",
            "is_mismatch": 1,
            "mismatch_severity": "HIGH",
            "mismatch_score": 0.94,
            "reason": f"Assigned code '{code}' contradicts mechanical suspension narrative."
        }

    return {
        "assigned_code": code,
        "inferred_category": comp or code,
        "is_mismatch": 0,
        "mismatch_severity": "NORMAL",
        "mismatch_score": 0.05,
        "reason": f"Assigned code '{code}' is consistent with narrative."
    }

def process_code_mismatches(db: Session, force: bool = False) -> int:
    """
    Evaluates and records code mismatches for all claims with failure signatures using batch embeddings.
    """
    if force:
        db.query(CodeMismatch).delete()
        db.commit()

    query = db.query(Claim).join(FailureSignature)
    if not force:
        query = query.outerjoin(CodeMismatch).filter(CodeMismatch.id == None)
    
    claims = query.all()
    if not claims:
        return 0

    model = get_fastembed_model()
    domain_vectors = get_domain_vectors()

    # Pre-batch embeddings for high-speed evaluation
    claim_texts = []
    for claim in claims:
        sig = claim.signature
        comp = (sig.component or "").lower().strip() if sig else ""
        symp = (sig.symptom or "").lower().strip() if sig else ""
        parts = []
        if comp and comp != "unspecified component":
            parts.append(f"Component: {comp}")
        if symp and symp != "unspecified operational symptom":
            parts.append(f"Symptom: {symp}")
        parts.append(f"Narrative: {claim.narrative}")
        claim_texts.append(" | ".join(parts))

    claim_vecs = None
    if domain_vectors and model:
        try:
            raw_embs = list(model.embed(claim_texts, batch_size=64))
            claim_vecs = normalize(np.array(raw_embs, dtype=np.float32), norm="l2")
        except Exception as e:
            logger.warning(f"Batch embedding for code mismatches failed: {e}")
            claim_vecs = None

    mismatches_to_add = []
    for idx, claim in enumerate(claims):
        sig = claim.signature
        cvec = claim_vecs[idx] if claim_vecs is not None else None
        eval_result = evaluate_code_mismatch(
            assigned_code=claim.failure_code,
            component=sig.component if sig else None,
            symptom=sig.symptom if sig else None,
            narrative=claim.narrative,
            claim_vec=cvec
        )

        mismatch_obj = CodeMismatch(
            claim_id=claim.id,
            assigned_code=eval_result["assigned_code"],
            inferred_category=eval_result["inferred_category"],
            mismatch_severity=eval_result["mismatch_severity"],
            is_mismatch=eval_result["is_mismatch"],
            mismatch_score=eval_result["mismatch_score"],
            reason=eval_result["reason"],
            confidence=0.92
        )
        mismatches_to_add.append(mismatch_obj)

    if mismatches_to_add:
        db.bulk_save_objects(mismatches_to_add)
        db.commit()

    logger.info(f"Processed {len(mismatches_to_add)} code mismatch evaluations.")
    return len(mismatches_to_add)
