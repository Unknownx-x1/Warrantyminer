import re
import logging
from typing import List, Dict, Any, Tuple
from collections import Counter
from apps.api.models.claim import Claim, FailureSignature

logger = logging.getLogger(__name__)

# Automotive Subsystem Terms for Narrative Mining
SUBSYSTEM_NOUNS = [
    ("Front-Left Suspension", [r"front\s*left", r"left\s*front", r"driver['’]?s?\s*front\s*wheel", r"left\s*strut", r"left\s*suspension", r"driver\s*corner"]),
    ("Front Suspension & Strut", [r"front\s*suspension", r"front\s*strut", r"control\s*arm", r"bushing", r"ball\s*joint", r"sway\s*bar", r"front\s*axle"]),
    ("Rear Suspension & Shock", [r"rear\s*suspension", r"rear\s*strut", r"rear\s*shock", r"rear\s*spring", r"rear\s*bushing"]),
    ("Steering Column & Rack", [r"steering\s*column", r"steering\s*rack", r"power\s*steering", r"tie\s*rod", r"steering\s*wheel", r"steering"]),
    ("Brake Rotor & Friction Assembly", [r"brake\s*rotor", r"brake\s*pad", r"caliper", r"front\s*brake", r"brake\s*disc", r"brakes?"]),
    ("ABS & Hydraulic Control Unit", [r"abs\s*module", r"abs\s*warning", r"hydraulic", r"master\s*cylinder", r"brake\s*fluid"]),
    ("Infotainment Display & Console", [r"infotainment", r"touchscreen", r"center\s*display", r"navigation", r"carplay", r"radio", r"screen"]),
    ("12V Battery & Charging Circuit", [r"12v\s*battery", r"battery\s*discharge", r"charging\s*port", r"alternator", r"battery"]),
    ("Lighting & Electrical Harness", [r"headlight", r"taillight", r"wiring\s*harness", r"fuse\s*box", r"camera\s*glitch", r"sensor\s*fault"]),
    ("HVAC Compressor & Air Delivery", [r"air\s*condition", r"a/c", r"hvac", r"blower\s*motor", r"refrigerant", r"heater"]),
    ("Engine Ignition & Cylinder P0301", [r"p0301", r"ignition\s*coil", r"misfire", r"cylinder", r"spark\s*plug", r"check\s*engine"]),
    ("Engine Cooling Circuit", [r"coolant\s*leak", r"pink\s*coolant", r"radiator", r"water\s*pump", r"thermostat"]),
    ("Transmission Gearbox & Shifting", [r"transmission", r"gearbox", r"gear\s*shift", r"clutch", r"2nd\s*to\s*3rd", r"slipping"]),
    ("Door Latch & Panel Mechanism", [r"door\s*latch", r"door", r"panel", r"handle"]),
    ("Window Regulator & Motor", [r"window\s*regulator", r"window\s*grinding", r"passenger\s*window"]),
    ("Tire Balance & High-Speed Vibration", [r"tire\s*balance", r"rebalancing", r"tire\s*vibration", r"70\s*mph"])
]

SYMPTOM_PHRASES = [
    ("Clunking / Knocking Noise", [r"clunk(?:ing)?", r"knock(?:ing)?", r"metallic\s*tap(?:ping)?", r"thump(?:ing)?", r"rattle", r"clicking", r"tapping", r"pop(?:ping)?"]),
    ("Squeal & Pulsation Under Braking", [r"squeal(?:ing)?", r"squeak(?:s|ing)?", r"pulsation", r"grind(?:ing)?", r"screech(?:ing)?"]),
    ("Intermittent Reboot & Blank Screen", [r"went\s*black", r"reboot(?:ed)?", r"black\s*screen", r"freeze", r"flicker", r"unresponsive"]),
    ("High-Pitch Whistling & Warm Airflow", [r"whistling", r"high-pitch", r"not\s*blowing\s*cold", r"warm\s*air", r"blower"]),
    ("Misfire & Diagnostic Fault Code", [r"p0301", r"check\s*engine", r"misfire", r"warning\s*indicator", r"dtc"]),
    ("Shift Hesitation & Jerking", [r"hesitat(?:ion|ing)", r"jerk(?:ing)?", r"rough\s*shift", r"slipping"]),
    ("Fluid Seepage & Overnight Leak", [r"puddle", r"leak(?:ing|age)?", r"dripping", r"seep(?:age)?"]),
    ("Steering Stiffness & High Turning Effort", [r"stiff", r"hard\s*to\s*turn", r"turning\s*maneuver", r"standstill"]),
    ("High-Speed Floorboard Vibration", [r"vibrat(?:ion|ing)", r"shudder", r"shimmy", r"wobble", r"70\s*mph"]),
    ("Mechanical Latch Resistance", [r"extra\s*force", r"shut\s*completely", r"latch\s*grinding"])
]

def extract_domain_topic_from_narratives(narratives: List[str]) -> Tuple[str, str]:
    combined = " ".join(narratives).lower()

    # 1. Best matching Subsystem Noun
    best_component = "Chassis & Mechanical System"
    max_comp_matches = 0
    for name, patterns in SUBSYSTEM_NOUNS:
        matches = sum(len(re.findall(pat, combined)) for pat in patterns)
        if matches > max_comp_matches:
            max_comp_matches = matches
            best_component = name

    # 2. Best matching Symptom Phrase
    best_symptom = "Operational Discrepancy"
    max_symp_matches = 0
    for name, patterns in SYMPTOM_PHRASES:
        matches = sum(len(re.findall(pat, combined)) for pat in patterns)
        if matches > max_symp_matches:
            max_symp_matches = matches
            best_symptom = name

    return best_component, best_symptom

def generate_cluster_label_and_summary(claims: List[Claim], signatures: List[FailureSignature], cluster_index: int = 0) -> Tuple[str, str, str, str]:
    """
    Synthesizes a distinct, human-readable, domain-truthful cluster label and engineering summary.
    """
    narratives = [c.narrative for c in claims if c.narrative]
    comp_extracted, symp_extracted = extract_domain_topic_from_narratives(narratives)

    # Component & Symptom from signatures if available and specific
    valid_comps = [s.component for s in signatures if s and s.component and "unspecified" not in s.component.lower()]
    valid_symps = [s.symptom for s in signatures if s and s.symptom and "unspecified" not in s.symptom.lower()]

    primary_component = comp_extracted
    if valid_comps:
        most_common_comp = Counter(valid_comps).most_common(1)[0][0].title()
        if len(most_common_comp) > 4 and most_common_comp != "Unspecified Component":
            primary_component = most_common_comp

    primary_symptom = symp_extracted
    if valid_symps:
        most_common_symp = Counter(valid_symps).most_common(1)[0][0].title()
        if len(most_common_symp) > 4 and most_common_symp != "Unspecified Operational Symptom":
            primary_symptom = most_common_symp

    # Format Human-Readable Label
    label = f"{primary_component} {primary_symptom}"

    # Find dominant operating condition
    conditions = [s.condition for s in signatures if s and s.condition and "normal" not in s.condition.lower()]
    dominant_condition = Counter(conditions).most_common(1)[0][0] if conditions else ""

    # Build engineering narrative description
    n_claims = len(claims)
    distinct_codes = len(set(c.failure_code for c in claims if c.failure_code))
    distinct_plants = len(set(c.plant for c in claims if c.plant))

    cond_clause = f" primarily observed under {dominant_condition}" if dominant_condition else ""
    description = (
        f"Consolidated cluster of {n_claims} claims reporting {primary_symptom.lower()} localized to the {primary_component.lower()}{cond_clause}. "
        f"Signal is distributed across {distinct_codes} structured failure codes and {distinct_plants} manufacturing/service facilities."
    )

    return label, description, primary_component, primary_symptom
