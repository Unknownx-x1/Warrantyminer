# 3-Minute Hackathon Demo Script

## 🎯 Pitch Narrative
> *"Every warranty claim has a structured failure code and a free-text narrative. Manufacturers monitor the code because it is easy to aggregate. But the true diagnostic signal lives in the narrative. Today, we demonstrate how WarrantyPatternMiner discovers hidden defect surges that traditional failure taxonomy conceals."*

---

### Step 1: The Problem — Structured Codes Hide The Defect (0:00 - 0:40)
- **Screen**: Navigate to **Baseline Reveal** (`/comparison`).
- **Narrative**: 
  *"Look at the standard failure code dashboard on the left. The claims are fragmented: 7 in `OTHER`, 5 in `RIDE QUALITY`, 4 in `SUSPENSION`, 3 in `STEERING`, and 3 in `ELECTRICAL-NFF`. None cross the alert threshold of 10 claims. Traditional monitoring triggers zero alerts. Management thinks the vehicle is healthy."*

---

### Step 2: The Pipeline — Looking Underneath The Codes (0:40 - 1:15)
- **Screen**: Navigate to **Pipeline & Data** (`/pipeline`) and click **Execute Full Pipeline**.
- **Narrative**: 
  *"WarrantyPatternMiner extracts structured failure signatures from messy technician notes, evaluates coding contradictions, maps narratives into dense semantic embeddings, and runs unsupervised HDBSCAN clustering."*
- **Action**: Show live execution logs finishing in ~1.3 seconds.

---

### Step 3: The Discovery — Unified Cross-Code Cluster (1:15 - 1:50)
- **Screen**: Navigate to **Command Center** (`/`).
- **Narrative**:
  *"Immediately, the system flags a High-Risk Defect Surge: **Front-Left Suspension Clunking / Knocking Noise** (Alert Score: 68.4/100, +76% growth). It has unified 22 claims across 5 distinct failure codes and 3 manufacturing facilities."*

---

### Step 4: The Evidence — Traceability & Root Cause (1:50 - 2:30)
- **Screen**: Click **Investigate Defect** to open the **Investigation Console** (`/pattern/:id`).
- **Narrative**:
  - Point to the **Defect Volume Timeline**: *"Notice the accelerating surge over recent months compared to rolling baseline."*
  - Point to **Signal Fragmentation Bar Chart**: *"Here is the proof — 5 different codes describing the exact same bushing/strut knocking noise."*
  - Click on a claim row in the **Evidence Table**: *"We can inspect the exact raw technician narrative: 'Driver notes unusual metallic tap near driver front wheel when traversing speed bumps'."*

---

### Step 5: The Human Gate & Organizational Memory (2:30 - 3:00)
- **Screen**: Click **Confirm Defect**.
- **Action**: Enter engineer rationale (*"Confirmed supplier bushing batch wear defect on Model X"*) and submit.
- **Screen**: Navigate to **Defect Memory** (`/fingerprints`).
- **Narrative**:
  *"The system never takes autonomous recall actions. When the reliability engineer confirms the finding, it enters the Defect Fingerprint Library. Future field complaints can now be tested against this organizational memory instantly. We catch defect trends weeks before they become multimillion-dollar recalls."*
