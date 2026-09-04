import logging
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from apps.api.models.claim import Claim, FailureSignature, CodeMismatch

logger = logging.getLogger(__name__)

# Standard Code Domain Definitions
CODE_DOMAIN_MAP = {
    "SUSPENSION": {"domain": "suspension", "expected_components": ["suspension", "strut", "shock", "bushing", "control arm", "sway bar"]},
    "BRAKES": {"domain": "braking", "expected_components": ["brake", "rotor", "pad", "caliper", "abs"]},
    "ELECTRICAL": {"domain": "electrical", "expected_components": ["electrical", "battery", "wiring", "fuse", "sensor", "display", "infotainment", "light"]},
    "ELECTRICAL-NFF": {"domain": "electrical", "expected_components": ["electrical", "wiring", "sensor", "module"], "is_nff": True},
    "STEERING": {"domain": "steering", "expected_components": ["steering", "rack", "column", "tie rod"]},
    "HVAC": {"domain": "climate", "expected_components": ["hvac", "air condition", "compressor", "blower", "heater"]},
    "POWERTRAIN": {"domain": "powertrain", "expected_components": ["engine", "transmission", "motor", "gearbox", "clutch", "exhaust"]},
    "BODY": {"domain": "body", "expected_components": ["door", "window", "panel", "latch", "paint", "trim"]},
    "RIDE QUALITY": {"domain": "generic", "expected_components": []},
    "OTHER": {"domain": "generic", "expected_components": []},
    "UNASSIGNED": {"domain": "generic", "expected_components": []},
}

def evaluate_code_mismatch(assigned_code: Optional[str], component: Optional[str], symptom: Optional[str], narrative: str) -> Dict[str, Any]:
    code = (assigned_code or "OTHER").upper().strip()
    comp = (component or "").lower().strip()
    symp = (symptom or "").lower().strip()
    narr = (narrative or "").lower().strip()

    code_info = CODE_DOMAIN_MAP.get(code, {"domain": "generic", "expected_components": []})
    expected_domain = code_info.get("domain", "generic")
    
    # Check if code is generic / catch-all
    if code in ["OTHER", "UNASSIGNED", "RIDE QUALITY"]:
        if "suspension" in comp or "strut" in comp or "bushing" in comp:
            return {
                "assigned_code": code,
                "inferred_category": "Suspension & Chassis Mechanical",
                "is_mismatch": 1,
                "mismatch_severity": "HIGH",
                "mismatch_score": 0.88,
                "reason": f"Claim assigned generic code '{code}', but narrative describes specific mechanical suspension defect: '{comp}' with '{symp}'."
            }
        elif "brake" in comp or "rotor" in comp:
            return {
                "assigned_code": code,
                "inferred_category": "Braking System",
                "is_mismatch": 1,
                "mismatch_severity": "MEDIUM",
                "mismatch_score": 0.75,
                "reason": f"Generic code '{code}' used for distinct brake system symptom: '{symp}'."
            }
        else:
            return {
                "assigned_code": code,
                "inferred_category": comp or "General Field Issue",
                "is_mismatch": 0,
                "mismatch_severity": "NORMAL",
                "mismatch_score": 0.30,
                "reason": f"Assigned generic code '{code}' with general narrative observations."
            }

    # Check for direct cross-domain contradictions (e.g. ELECTRICAL-NFF when narrative is suspension noise)
    if "ELECTRICAL" in code:
        if "suspension" in comp or "clunk" in narr or "knock" in narr or "strut" in comp:
            return {
                "assigned_code": code,
                "inferred_category": "Suspension Mechanical (Misclassified as Electrical)",
                "is_mismatch": 1,
                "mismatch_severity": "HIGH",
                "mismatch_score": 0.94,
                "reason": f"Assigned code '{code}' contradicts technician narrative describing mechanical suspension noise ('{symp}' over rough surfaces)."
            }
        elif expected_domain == "electrical" and ("battery" in comp or "display" in comp or "light" in comp or "flicker" in symp):
            return {
                "assigned_code": code,
                "inferred_category": "Electrical & Electronics",
                "is_mismatch": 0,
                "mismatch_severity": "NORMAL",
                "mismatch_score": 0.05,
                "reason": "Assigned electrical code matches extracted electrical component and symptoms."
            }

    if "STEERING" in code:
        if "suspension" in comp and "knock" in narr:
            return {
                "assigned_code": code,
                "inferred_category": "Front Suspension Assembly",
                "is_mismatch": 1,
                "mismatch_severity": "MEDIUM",
                "mismatch_score": 0.65,
                "reason": f"Coded as '{code}', but underlying defect originates from front suspension strut/bushing clearance."
            }
        elif "steering" in comp:
            return {
                "assigned_code": code,
                "inferred_category": "Steering System",
                "is_mismatch": 0,
                "mismatch_severity": "NORMAL",
                "mismatch_score": 0.05,
                "reason": "Assigned steering code agrees with steering failure signature."
            }

    if "SUSPENSION" in code:
        if "suspension" in comp:
            return {
                "assigned_code": code,
                "inferred_category": "Suspension Mechanical",
                "is_mismatch": 0,
                "mismatch_severity": "NORMAL",
                "mismatch_score": 0.0,
                "reason": "Assigned failure code agrees with suspension failure signature."
            }
        else:
            return {
                "assigned_code": code,
                "inferred_category": comp or "Suspension",
                "is_mismatch": 0,
                "mismatch_severity": "NORMAL",
                "mismatch_score": 0.20,
                "reason": "Consistent with suspension domain."
            }

    return {
        "assigned_code": code,
        "inferred_category": comp or code,
        "is_mismatch": 0,
        "mismatch_severity": "NORMAL",
        "mismatch_score": 0.10,
        "reason": f"Assigned code '{code}' is consistent with narrative."
    }

def process_code_mismatches(db: Session, force: bool = False) -> int:
    """
    Evaluates and records code mismatches for all claims with failure signatures.
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

    mismatches_to_add = []
    for claim in claims:
        sig = claim.signature
        eval_result = evaluate_code_mismatch(
            assigned_code=claim.failure_code,
            component=sig.component if sig else None,
            symptom=sig.symptom if sig else None,
            narrative=claim.narrative
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
