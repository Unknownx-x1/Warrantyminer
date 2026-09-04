import os
import json
import random
import csv
from typing import Tuple, List, Dict, Any
from datetime import datetime, date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

# Random seed for determinism in generation
random.seed(42)

MODELS = ["Model X", "Model Y", "Sedan Alpha", "Cruiser Pro", "Titan EV", "Apex SUV"]
PLANTS = ["Plant A - Fremont", "Plant B - Austin", "Plant C - Leipzig", "Plant D - Yokohama"]

# Background Normal Failure Modes & Narratives
BACKGROUND_TEMPLATES = [
    # Brakes
    ("BRAKES", "front brake assembly", "Customer states front brakes squeak loudly when coming to a gentle stop at low speeds."),
    ("BRAKES", "brake rotor", "Technician inspected brake pads; found uneven rotor wear and slight pulsation under braking."),
    ("BRAKES", "abs module", "Intermittent ABS warning indicator illuminated on cluster during highway braking test."),
    # Electrical
    ("ELECTRICAL", "infotainment / display", "Center infotainment touchscreen went black and rebooted spontaneously while driving."),
    ("ELECTRICAL", "lighting / wiring", "Left headlight intermittent operation; replaced wiring harness connection pin."),
    ("ELECTRICAL", "battery / charging", "12V auxiliary battery discharge warning triggered; replaced battery and sensor."),
    ("ELECTRICAL-NFF", "sensor fault", "Customer reported intermittent camera glitch; tested system on diagnostic bench, no fault found (NFF)."),
    # HVAC
    ("HVAC", "hvac compressor / blower", "A/C blower motor making high-pitch whistling noise when fan set to maximum speed."),
    ("HVAC", "hvac compressor / blower", "Air conditioning not blowing cold air on hot afternoons; recharged refrigerant system."),
    # Powertrain
    ("POWERTRAIN", "engine / motor", "Engine check light on with code P0301; inspected cylinder 1 ignition coil and replaced."),
    ("POWERTRAIN", "transmission", "Transmission hesitation and slight jerk when shifting from 2nd to 3rd gear under acceleration."),
    ("POWERTRAIN", "coolant leak", "Customer observed small puddle of pink coolant under vehicle after parking overnight."),
    # Steering
    ("STEERING", "steering column / rack", "Steering wheel feels stiff when turning at standstill or low speed parking maneuvers."),
    # Body
    ("BODY", "door latch", "Driver side door latch requires extra force to shut completely."),
    ("BODY", "window regulator", "Passenger window makes grinding sound when rolling down."),
    # Ride Quality
    ("RIDE QUALITY", "tire balance", "Slight highway vibration felt through seat at 70 mph; performed tire rebalancing."),
]

# Canonical Hidden Defect Narratives (Front-Left Suspension Bushing / Knocking)
# Full 7-Month Canonical Surge Timeline: Jan: 1, Feb: 1, Mar: 2, Apr: 2, May: 4, Jun: 8, Jul: 17 (Total = 35 claims)
# July Surging Month has exactly 17 claims across 5 misleading codes:
# OTHER: 5, RIDE QUALITY: 4, SUSPENSION: 3, ELECTRICAL-NFF: 3, STEERING: 2
HIDDEN_CLUSTER_CLAIMS = [
    # Month 1 (Jan 2026) - 1 claim
    {
        "claim_id": "C-9001",
        "date": "2026-01-14",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Customer reports faint clunking sound from front left when driving over rough neighborhood roads."
    },
    # Month 2 (Feb 2026) - 1 claim
    {
        "claim_id": "C-9002",
        "date": "2026-02-18",
        "failure_code": "RIDE QUALITY",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Driver notes unusual metallic tap near driver's front wheel when traversing speed bumps."
    },
    # Month 3 (Mar 2026) - 2 claims
    {
        "claim_id": "C-9003",
        "date": "2026-03-05",
        "failure_code": "SUSPENSION",
        "product_model": "Model X",
        "plant": "Plant B - Austin",
        "narrative": "Intermittent clunk from left front suspension assembly over uneven road surfaces."
    },
    {
        "claim_id": "C-9004",
        "date": "2026-03-22",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Loud knocking noise in front driver corner during low speed turns over bumpy parking lots."
    },
    # Month 4 (Apr 2026) - 2 claims
    {
        "claim_id": "C-9005",
        "date": "2026-04-10",
        "failure_code": "ELECTRICAL-NFF",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Customer suspected sensor issue due to rattle; no electrical fault found, technician heard mechanical tapping from front left suspension."
    },
    {
        "claim_id": "C-9006",
        "date": "2026-04-27",
        "failure_code": "STEERING",
        "product_model": "Model X",
        "plant": "Plant C - Leipzig",
        "narrative": "Steering-side front assembly produces knocking noise when driving across railroad tracks."
    },
    # Month 5 (May 2026) - 4 claims
    {
        "claim_id": "C-9007",
        "date": "2026-05-04",
        "failure_code": "RIDE QUALITY",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Heavy metallic clunking felt in floorboard around driver-side front strut when going over potholes."
    },
    {
        "claim_id": "C-9008",
        "date": "2026-05-12",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant B - Austin",
        "narrative": "Front end knocks severely over speed humps. Technician inspected front left control arm area."
    },
    {
        "claim_id": "C-9009",
        "date": "2026-05-19",
        "failure_code": "SUSPENSION",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Front-left suspension knocking noise when decelerating on rough pavement."
    },
    {
        "claim_id": "C-9010",
        "date": "2026-05-28",
        "failure_code": "STEERING",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Customer reports front driver side knocking when turning into uneven driveways."
    },
    # Month 6 (Jun 2026) - 8 claims
    {
        "claim_id": "C-9011",
        "date": "2026-06-02",
        "failure_code": "RIDE QUALITY",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Driver hears persistent knocking sound from left front wheel area on uneven asphalt."
    },
    {
        "claim_id": "C-9012",
        "date": "2026-06-06",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant B - Austin",
        "narrative": "Metallic tapping noise audible inside cabin originating from front left strut assembly."
    },
    {
        "claim_id": "C-9013",
        "date": "2026-06-10",
        "failure_code": "SUSPENSION",
        "product_model": "Model X",
        "plant": "Plant C - Leipzig",
        "narrative": "Front-left lower control arm / bushing exhibiting excessive play and clunking over bumps."
    },
    {
        "claim_id": "C-9014",
        "date": "2026-06-15",
        "failure_code": "ELECTRICAL-NFF",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Scanned for suspension control module error; no active DTCs, verified mechanical clunking from front-left strut."
    },
    {
        "claim_id": "C-9015",
        "date": "2026-06-18",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant B - Austin",
        "narrative": "Driver states sharp metallic pop/knock from left front wheel well when hitting road dips."
    },
    {
        "claim_id": "C-9016",
        "date": "2026-06-22",
        "failure_code": "RIDE QUALITY",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Rough ride complaint: prominent knocking and clunking from front driver side corner on rough surfaces."
    },
    {
        "claim_id": "C-9017",
        "date": "2026-06-25",
        "failure_code": "STEERING",
        "product_model": "Model X",
        "plant": "Plant C - Leipzig",
        "narrative": "Knocking vibration felt through steering column when going over potholes; front left strut loose."
    },
    {
        "claim_id": "C-9018",
        "date": "2026-06-29",
        "failure_code": "SUSPENSION",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Front left suspension bushing worn; loud clunk over uneven railway crossings."
    },
    # Month 7 (Jul 2026) - 17 claims (Surge Month: OTHER: 5, RIDE QUALITY: 4, SUSPENSION: 3, ELECTRICAL-NFF: 3, STEERING: 2)
    {
        "claim_id": "C-9019",
        "date": "2026-07-02",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Front-left suspension produces heavy clunking noise over speed bumps at low speeds."
    },
    {
        "claim_id": "C-9020",
        "date": "2026-07-04",
        "failure_code": "RIDE QUALITY",
        "product_model": "Model X",
        "plant": "Plant B - Austin",
        "narrative": "Continuous knocking noise from front left corner when driving on gravel or uneven pavement."
    },
    {
        "claim_id": "C-9021",
        "date": "2026-07-06",
        "failure_code": "SUSPENSION",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Technician reproduced knocking/clunking from front left suspension strut mount over bumps."
    },
    {
        "claim_id": "C-9022",
        "date": "2026-07-08",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant C - Leipzig",
        "narrative": "Metallic clunk sound near driver front wheel when crossing driveway curb."
    },
    {
        "claim_id": "C-9023",
        "date": "2026-07-10",
        "failure_code": "ELECTRICAL-NFF",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Customer suspected front radar loose; technician verified noise is front-left suspension ball joint clunk."
    },
    {
        "claim_id": "C-9024",
        "date": "2026-07-12",
        "failure_code": "STEERING",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Customer complained of front steering area rattle; inspection showed front-left suspension bushing knocking."
    },
    {
        "claim_id": "C-9025",
        "date": "2026-07-14",
        "failure_code": "RIDE QUALITY",
        "product_model": "Model X",
        "plant": "Plant B - Austin",
        "narrative": "Severe clunking and knocking in front left wheel area during low-speed maneuvers."
    },
    {
        "claim_id": "C-9026",
        "date": "2026-07-16",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Clunk noise on left front side during speed bump compression."
    },
    {
        "claim_id": "C-9027",
        "date": "2026-07-18",
        "failure_code": "SUSPENSION",
        "product_model": "Model X",
        "plant": "Plant C - Leipzig",
        "narrative": "Left front suspension control arm bushing deteriorated, causing loud mechanical thud."
    },
    {
        "claim_id": "C-9028",
        "date": "2026-07-20",
        "failure_code": "ELECTRICAL-NFF",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Customer heard knocking near driver wheel; tested electronic damper, no error code, mechanical clunking confirmed."
    },
    {
        "claim_id": "C-9029",
        "date": "2026-07-22",
        "failure_code": "RIDE QUALITY",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Pronounced knocking vibration from left front suspension over cobblestone road."
    },
    {
        "claim_id": "C-9030",
        "date": "2026-07-24",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant B - Austin",
        "narrative": "Driver reports audible clunking in driver front wheel well when accelerating over road dips."
    },
    {
        "claim_id": "C-9031",
        "date": "2026-07-26",
        "failure_code": "STEERING",
        "product_model": "Model X",
        "plant": "Plant C - Leipzig",
        "narrative": "Steering wheel twitch and knocking sound from front-left suspension area on uneven roads."
    },
    {
        "claim_id": "C-9032",
        "date": "2026-07-27",
        "failure_code": "OTHER",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Front left suspension makes sharp popping/clunking noise over neighborhood speed bumps."
    },
    {
        "claim_id": "C-9033",
        "date": "2026-07-28",
        "failure_code": "SUSPENSION",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Front-left strut mount assembly knocking during rebound on undulating pavement."
    },
    {
        "claim_id": "C-9034",
        "date": "2026-07-29",
        "failure_code": "ELECTRICAL-NFF",
        "product_model": "Model X",
        "plant": "Plant B - Austin",
        "narrative": "Customer stated front suspension sensor alert; diagnostics clear, physical knocking from front-left lower control arm."
    },
    {
        "claim_id": "C-9035",
        "date": "2026-07-30",
        "failure_code": "RIDE QUALITY",
        "product_model": "Model X",
        "plant": "Plant A - Fremont",
        "narrative": "Excessive front-left suspension clunk and harsh ride over railroad tracks."
    }
]

def generate_dataset(n_background: int = 550) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    claims = []
    
    # 1. Add Canonical Injected Defect Claims (35 claims total, 17 in July surge)
    for c in HIDDEN_CLUSTER_CLAIMS:
        claims.append({
            "claim_id": c["claim_id"],
            "date": c["date"],
            "product_model": c["product_model"],
            "plant": c["plant"],
            "failure_code": c["failure_code"],
            "narrative": c["narrative"]
        })

    # 2. Add Realistic Background Claims Across 7 Months (Jan 2026 to Jul 2026)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 7, 31)
    total_days = (end_date - start_date).days

    for i in range(1, n_background + 1):
        rand_days = random.randint(0, total_days)
        claim_date = start_date + timedelta(days=rand_days)
        code, component, narrative_tmpl = random.choice(BACKGROUND_TEMPLATES)
        model = random.choice(MODELS)
        plant = random.choice(PLANTS)

        prefixes = ["Customer reports: ", "Tech notes: ", "Driver stated ", "Field complaint: ", ""]
        narrative = f"{random.choice(prefixes)}{narrative_tmpl}"

        claims.append({
            "claim_id": f"C-{10000 + i}",
            "date": claim_date.strftime("%Y-%m-%d"),
            "product_model": model,
            "plant": plant,
            "failure_code": code,
            "narrative": narrative
        })

    # Shuffle claims
    random.shuffle(claims)

    ground_truth = {
        "dataset_name": "canonical_warranty_claims_v1",
        "generated_at": datetime.now().isoformat(),
        "total_claims": len(claims),
        "ground_truth_clusters": [
            {
                "name": "front_left_suspension_knocking",
                "description": "Front-left suspension bushing excessive clearance causing clunking/knocking",
                "claim_ids": [c["claim_id"] for c in HIDDEN_CLUSTER_CLAIMS],
                "expected_total_count": 35,
                "expected_july_count": 17,
                "expected_july_code_distribution": {
                    "OTHER": 5,
                    "RIDE QUALITY": 4,
                    "SUSPENSION": 3,
                    "ELECTRICAL-NFF": 3,
                    "STEERING": 2
                },
                "expected_timeline": {
                    "2026-01": 1,
                    "2026-02": 1,
                    "2026-03": 2,
                    "2026-04": 2,
                    "2026-05": 4,
                    "2026-06": 8,
                    "2026-07": 17
                }
            }
        ]
    }

    return claims, ground_truth

def main():
    claims, ground_truth = generate_dataset(n_background=550)

    csv_path = RAW_DATA_DIR / "canonical_warranty_claims.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["claim_id", "date", "product_model", "plant", "failure_code", "narrative"])
        writer.writeheader()
        writer.writerows(claims)

    gt_path = GROUND_TRUTH_DIR / "ground_truth_clusters.json"
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Generated {len(claims)} claims saved to {csv_path}")
    print(f"Saved ground truth evaluation to {gt_path}")

if __name__ == "__main__":
    main()
