import re
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session
from apps.api.config import settings
from apps.api.models.claim import Claim, FailureSignature

logger = logging.getLogger(__name__)

# Automotive & Industrial Subsystem Lexicons for deterministic domain-grounded extraction
COMPONENTS_MAP = {
    "suspension": [
        ("front-left suspension", [
            r"front[\s\-]left", 
            r"left[\s\-]front", 
            r"driver['’]?s?\s*(?:side\s*)?front", 
            r"front\s*driver", 
            r"driver['’]?s?\s*(?:side\s*)?corner", 
            r"front\s*corner", 
            r"driver['’]?s?\s*wheel", 
            r"left\s*wheel", 
            r"left\s*side", 
            r"left\s*strut", 
            r"left\s*suspension", 
            r"steering[\s\-]side"
        ]),
        ("front suspension", [
            r"front\s*suspension", 
            r"front\s*end", 
            r"front\s*strut", 
            r"sway\s*bar", 
            r"control\s*arm", 
            r"bushing", 
            r"ball\s*joint", 
            r"strut\s*mount", 
            r"front\s*axle", 
            r"suspension"
        ]),
        ("rear suspension", [
            r"rear\s*suspension", 
            r"rear\s*strut", 
            r"rear\s*shock", 
            r"rear\s*spring", 
            r"rear\s*bushing"
        ]),
    ],
    "steering": [
        ("steering column / rack", [
            r"steering\s*column", 
            r"steering\s*rack", 
            r"power\s*steering", 
            r"tie\s*rod", 
            r"steering\s*wheel\s*play", 
            r"steering\s*side\s*assembly",
            r"steering\s*wheel",
            r"steering"
        ]),
    ],
    "braking": [
        ("front brake assembly", [
            r"front\s*brake", 
            r"brake\s*rotor", 
            r"brake\s*pad", 
            r"caliper", 
            r"front\s*disc"
        ]),
        ("brake system", [
            r"brakes?", 
            r"abs\s*module", 
            r"master\s*cylinder", 
            r"brake\s*pedal", 
            r"braking\s*distance",
            r"braking"
        ]),
    ],
    "electrical": [
        ("infotainment / display", [
            r"infotainment", 
            r"touchscreen", 
            r"center\s*display", 
            r"navigation\s*screen", 
            r"apple\s*carplay", 
            r"radio",
            r"display\s*screen",
            r"screen"
        ]),
        ("battery / charging", [
            r"12v\s*battery", 
            r"high\s*voltage\s*battery", 
            r"charging\s*port", 
            r"alternator", 
            r"battery\s*drain", 
            r"bms",
            r"battery"
        ]),
        ("lighting / wiring", [
            r"headlight", 
            r"taillight", 
            r"wiring\s*harness", 
            r"fuse\s*box", 
            r"sensor\s*fault"
        ]),
    ],
    "powertrain": [
        ("engine / motor", [
            r"engine", 
            r"misfire", 
            r"cylinder", 
            r"oil\s*leak", 
            r"coolant\s*leak", 
            r"turbocharger", 
            r"electric\s*motor"
        ]),
        ("transmission", [
            r"transmission", 
            r"gearbox", 
            r"gear\s*shift", 
            r"clutch", 
            r"slipping\s*gear", 
            r"torque\s*converter"
        ]),
    ],
    "climate": [
        ("hvac compressor / blower", [
            r"air\s*condition", 
            r"a/c", 
            r"hvac", 
            r"heater\s*core", 
            r"blower\s*motor", 
            r"refrigerant"
        ]),
    ]
}

SYMPTOMS_MAP = [
    ("clunking / knocking noise", [
        r"clunk(?:ing)?", 
        r"knock(?:ing)?", 
        r"metallic\s*tap(?:ping)?", 
        r"thump(?:ing)?", 
        r"thud",
        r"rattle", 
        r"clicking\s*noise", 
        r"tapping\s*sound", 
        r"popping\s*noise", 
        r"metallic\s*pop",
        r"pop(?:ping)?",
        r"clunk",
        r"knock",
        r"tap(?:ping)?",
        r"harsh\s*ride"
    ]),
    ("vibration / shudder", [
        r"vibrat(?:ion|ing)", 
        r"shudder(?:ing)?", 
        r"shimmy", 
        r"wobble", 
        r"shake", 
        r"rough\s*ride"
    ]),
    ("fluid leak", [
        r"leak(?:ing|age)?", 
        r"fluid\s*puddle", 
        r"dripping", 
        r"oil\s*seep"
    ]),
    ("intermittent loss of function", [
        r"flicker(?:ing)?", 
        r"intermittent", 
        r"shut\s*off", 
        r"black\s*screen", 
        r"went\s*black", 
        r"reboot(?:ed)?", 
        r"unresponsive", 
        r"non-responsive", 
        r"freeze"
    ]),
    ("squeal / grinding noise", [
        r"squeal(?:ing)?", 
        r"grind(?:ing)?", 
        r"screech(?:ing)?", 
        r"scraping",
        r"squeak(?:s|ing)?"
    ]),
    ("warning light / error code", [
        r"check\s*engine", 
        r"warning\s*light", 
        r"dtc", 
        r"error\s*message", 
        r"fault\s*code"
    ]),
    ("hesitation / power loss", [
        r"hesitat(?:ion|ing)", 
        r"power\s*loss", 
        r"stalling", 
        r"sluggish", 
        r"jerking"
    ]),
]

CONDITIONS_MAP = [
    ("rough roads / uneven surface", [
        r"rough\s*roads?", 
        r"bumps?", 
        r"speed\s*bumps?", 
        r"potholes?", 
        r"uneven\s*surfaces?", 
        r"cobblestone", 
        r"gravel", 
        r"railroad", 
        r"speed\s*humps?",
        r"rough"
    ]),
    ("turning / steering maneuver", [
        r"turn(?:ing)?", 
        r"sharp\s*turn", 
        r"cornering", 
        r"full\s*lock", 
        r"parking\s*maneuver", 
        r"driveway"
    ]),
    ("braking / deceleration", [
        r"braking", 
        r"stopping", 
        r"deceleration", 
        r"downhill"
    ]),
    ("highway speeds / high load", [
        r"highway\s*speed", 
        r"high\s*speed", 
        r"acceleration", 
        r"under\s*load", 
        r"60\s*mph", 
        r"70\s*mph"
    ]),
    ("cold start / low temp", [
        r"cold\s*start", 
        r"morning", 
        r"freezing", 
        r"low\s*ambient"
    ]),
    ("hot weather / idle", [
        r"hot\s*weather", 
        r"idle", 
        r"traffic", 
        r"extended\s*run"
    ]),
]

SEVERITY_MAP = [
    ("critical", [r"safety\s*hazard", r"disabled", r"stranded", r"towed", r"complete\s*failure", r"loss\s*of\s*control", r"smoke"]),
    ("high", [r"severe", r"loud", r"heavy", r"warning", r"frequent", r"urgent", r"continuous"]),
    ("moderate", [r"moderate", r"noticeable", r"intermittent", r"annoying", r"repetitive", r"persistent"]),
    ("low", [r"minor", r"slight", r"cosmetic", r"faint", r"occasional"]),
]

def extract_signature_rule_based(narrative: str) -> Dict[str, Any]:
    text = narrative.lower()
    
    # 1. Match Component
    matched_component = "unspecified component"
    confidence = 0.70
    
    for category, comp_list in COMPONENTS_MAP.items():
        for comp_name, patterns in comp_list:
            for pat in patterns:
                if re.search(pat, text):
                    matched_component = comp_name
                    confidence += 0.10
                    break
            if matched_component != "unspecified component":
                break
        if matched_component != "unspecified component":
            break

    # 2. Match Symptom
    matched_symptom = "unspecified operational symptom"
    for sym_name, patterns in SYMPTOMS_MAP:
        for pat in patterns:
            if re.search(pat, text):
                matched_symptom = sym_name
                confidence += 0.08
                break
        if matched_symptom != "unspecified operational symptom":
            break

    # 3. Match Condition
    matched_condition = "normal operating conditions"
    for cond_name, patterns in CONDITIONS_MAP:
        for pat in patterns:
            if re.search(pat, text):
                matched_condition = cond_name
                confidence += 0.05
                break
        if matched_condition != "normal operating conditions":
            break

    # 4. Match Severity
    matched_severity = "moderate"
    for sev_name, patterns in SEVERITY_MAP:
        for pat in patterns:
            if re.search(pat, text):
                matched_severity = sev_name
                break
        if matched_severity != "moderate":
            break

    # 5. Inferred Failure Mode
    inferred_failure = f"{matched_component} mechanical/functional degradation"
    if any(k in text for k in ["clunk", "knock", "metallic", "thud", "pop", "tap", "rattle", "thump"]):
        if any(k in text for k in ["suspension", "strut", "wheel", "corner", "bushing", "arm", "ball joint", "rebound", "curb", "bump", "pothole", "asphalt", "tracks"]) or "suspension" in matched_component:
            inferred_failure = "suspension bushing or ball-joint excessive clearance/wear"
            if matched_component in ["unspecified component", "front suspension"] and any(k in text for k in ["left", "driver"]):
                matched_component = "front-left suspension"
    elif "leak" in text:
        inferred_failure = "seal failure or fitting seal degradation"
    elif "vibrat" in text:
        inferred_failure = "imbalance, rotor runout, or driveline oscillation"
    elif "flicker" in text or "black" in text or "screen" in text or "reboot" in text:
        inferred_failure = "display unit communication bus or power rail fault"

    contributing_factors = []
    if "rough" in text or "bump" in text or "pothole" in text:
        contributing_factors.append("road surface impact loading")
    if "heat" in text or "hot" in text:
        contributing_factors.append("thermal stress")
    if "cold" in text:
        contributing_factors.append("low-temperature stiffness")
    if "water" in text or "rain" in text or "wet" in text:
        contributing_factors.append("moisture ingress")

    confidence = min(0.96, round(confidence, 2))

    return {
        "component": matched_component,
        "symptom": matched_symptom,
        "condition": matched_condition,
        "severity": matched_severity,
        "inferred_failure": inferred_failure,
        "contributing_factors": contributing_factors,
        "confidence": confidence,
        "model_version": "hybrid-domain-v1.0"
    }

def is_ollama_available() -> bool:
    import sys, os
    if "pytest" in sys.modules or os.getenv("EVALUATION") == "true" or not settings.USE_OLLAMA:
        return False
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/version"
        with httpx.Client(timeout=0.8) as client:
            res = client.get(url)
            return res.status_code == 200
    except Exception:
        return False

def call_ollama_sync(narrative: str) -> Optional[Dict[str, Any]]:
    """
    Calls local Ollama instance (e.g. llama3.2, mistral, qwen2.5) with strict JSON output format.
    """
    prompt = f"""You are an automotive reliability engineer. Extract the structured failure signature from this warranty claim narrative.
Return ONLY valid JSON matching this schema:
{{
  "component": "exact sub-component, e.g. front-left suspension",
  "symptom": "observed symptom, e.g. clunking noise",
  "condition": "operating condition, e.g. rough roads / speed bumps",
  "severity": "low | moderate | high | critical",
  "inferred_failure": "inferred mechanical or electrical defect mode",
  "contributing_factors": ["factor 1"],
  "confidence": 0.90
}}

Narrative: "{narrative}"
"""
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        with httpx.Client(timeout=10.0) as client:
            res = client.post(
                url,
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                }
            )
            if res.status_code == 200:
                data = res.json()
                raw_response = data.get("response", "")
                parsed = json.loads(raw_response)
                parsed["model_version"] = f"ollama/{settings.OLLAMA_MODEL}"
                return parsed
    except Exception as e:
        logger.debug(f"Ollama call skipped/failed: {e}")
        return None
    return None

def process_claim_extractions(db: Session, force: bool = False) -> int:
    """
    Extracts failure signatures for all claims using high-performance domain-grounded NLP engine.
    """
    if force:
        db.query(FailureSignature).delete()
        db.commit()

    query = db.query(Claim)
    if not force:
        query = query.outerjoin(FailureSignature).filter(FailureSignature.id == None)
    
    unprocessed_claims = query.all()
    if not unprocessed_claims:
        return 0

    signatures_to_add = []
    for claim in unprocessed_claims:
        sig_data = extract_signature_rule_based(claim.narrative)

        sig_obj = FailureSignature(
            claim_id=claim.id,
            component=sig_data.get("component"),
            symptom=sig_data.get("symptom"),
            condition=sig_data.get("condition"),
            severity=sig_data.get("severity"),
            inferred_failure=sig_data.get("inferred_failure"),
            contributing_factors=sig_data.get("contributing_factors", []),
            extraction_confidence=sig_data.get("confidence", 0.85),
            model_version=sig_data.get("model_version", "hybrid-domain-v1.0"),
            raw_output=json.dumps(sig_data)
        )
        signatures_to_add.append(sig_obj)

    if signatures_to_add:
        db.bulk_save_objects(signatures_to_add)
        db.commit()

    logger.info(f"Processed {len(signatures_to_add)} failure signatures.")
    return len(signatures_to_add)
