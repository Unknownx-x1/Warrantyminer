# WarrantyPatternMiner

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![HDBSCAN](https://img.shields.io/badge/Clustering-HDBSCAN-FF6F00?style=for-the-badge)
![Ollama](https://img.shields.io/badge/Local%20LLM-Ollama%20(Llama%203.2)-FB8C00?style=for-the-badge)
![Tests](https://img.shields.io/badge/Test%20Suite-17%20Passed%20(100%25)-4CAF50?style=for-the-badge)

**AI-Powered Early Warning Surveillance & Field Defect Intelligence Platform**

*Catching emerging automotive warranty failure trends across fragmented codes before they escalate into multimillion-dollar safety recalls.*

</div>

---

## 📌 The Problem: The Legacy Surveillance Blindspot

In the automotive and manufacturing industries, traditional quality and warranty monitoring systems aggregate claims by **rigid structured failure codes** (e.g., `SUSPENSION`, `RIDE QUALITY`, `STEERING`, `ELECTRICAL-NFF`, `OTHER`).

### Why Traditional Single-Code Monitoring Fails:
1. **Dealership Code Misclassification**: When a driver reports a *"metallic clunking noise from the front-left wheel over road bumps"*, technician A files it under `SUSPENSION`, technician B chooses `RIDE QUALITY`, technician C selects `OTHER`, and technician D codes it as `ELECTRICAL-NFF` (No Fault Found).
2. **Taxonomy Fragmentation**: The true single physical defect is fragmented into 5 separate buckets.
3. **Threshold Blindspot**: If each code threshold is set to 10 claims/month, but the defect has 3 claims in `SUSPENSION`, 3 in `RIDE QUALITY`, 2 in `OTHER`, and 2 in `ELECTRICAL`, **no alarm fires**.
4. **Catastrophic Delay**: By the time any individual code crosses the threshold months later, thousands of defective vehicles have shipped, resulting in massive warranty recall liability.

---

## 💡 The Solution: WarrantyPatternMiner

**WarrantyPatternMiner** bypasses misleading checkbox classifications by analyzing the **unstructured technician and customer narratives**. 

Using dense vector embeddings and unsupervised **HDBSCAN clustering**, the platform groups complaints by their true physical symptoms and mechanical failure modes across all failure codes simultaneously. A 5-factor statistical emergence engine monitors surge velocity and detects anomalies with an average **+69-day early warning lead time**.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         END-TO-END ANALYTICAL PIPELINE                           │
└──────────────────────────────────────────────────────────────────────────────────┘

   Raw Warranty Claims (CSV / DMS Database Export)
                         │
                         ▼
   ┌────────────────────────────────────────────────────────┐
   │  1. Ingestion & Field Normalization                    │
   │     • Standardizes dates, VINs, plants, failure codes  │
   └────────────────────────────────────────────────────────┘
                         │
                         ▼
   ┌────────────────────────────────────────────────────────┐
   │  2. Hybrid Narrative Failure Signature Extraction      │
   │     • Local Ollama LLM (llama3.2) / Domain Heuristic   │
   │     • Extracts: Component, Symptom, Condition, Severity│
   └────────────────────────────────────────────────────────┘
                         │
                         ▼
   ┌────────────────────────────────────────────────────────┐
   │  3. Taxonomy Mismatch Detection                        │
   │     • Flags contradictions between code & notes        │
   │     • Highlights systemic dealership misclassifications│
   └────────────────────────────────────────────────────────┘
                         │
                         ▼
   ┌────────────────────────────────────────────────────────┐
   │  4. Dense Semantic Embedding & HDBSCAN Clustering      │
   │     • Vectorizes domain text into 384D / 768D space    │
   │     • Unsupervised discovery of latent failure clusters │
   └────────────────────────────────────────────────────────┘
                         │
                         ▼
   ┌────────────────────────────────────────────────────────┐
   │  5. Statistical Emergence & Anomaly Detection          │
   │     • 6-Month Rolling Baseline Mean & StdDev           │
   │     • Statistical Z-Score Significance (Z > 3.0)       │
   │     • Non-parametric CUSUM Drift Tracking              │
   └────────────────────────────────────────────────────────┘
                         │
                         ▼
   ┌────────────────────────────────────────────────────────┐
   │  6. 5-Factor Composite Alert Score Formulation         │
   │     • Score = 30% Growth + 25% Z-Score + 15% Size +    │
   │               15% Cross-Code + 15% Semantic Coherence  │
   └────────────────────────────────────────────────────────┘
                         │
                         ▼
   ┌────────────────────────────────────────────────────────┐
   │  7. Investigation Console & Institutional Memory       │
   │     • Verbatim evidence drill-down & root-cause triage │
   │     • Human Engineer Review Gate (Confirm / Dismiss)   │
   │     • Defect Memory Fingerprint Library                │
   └────────────────────────────────────────────────────────┘
```

---

## 🔬 Core Innovation: The 5-Factor Emergence Model

Unlike simple claim counts, WarrantyPatternMiner computes a multi-dimensional composite alert score ($S \in [0, 100]$) to distinguish genuine physical defect surges from random fleet noise:

$$\text{Alert Score} = 0.30 \cdot N(\Delta \%) + 0.25 \cdot N(Z) + 0.15 \cdot N(C) + 0.15 \cdot N(K) + 0.15 \cdot N(\Phi)$$

Where:
* **$N(\Delta \%)$ Growth Surge (30%)**: Percentage surge in claim velocity relative to the 6-month historical rolling baseline.
* **$N(Z)$ Statistical Significance (25%)**: Number of standard deviations above historical noise ($Z = \frac{X - \mu}{\sigma}$). $Z \ge 3.0$ indicates statistical significance ($p < 0.001$).
* **$N(C)$ Cluster Size (15%)**: Total volume of affected vehicles in the cluster.
* **$N(K)$ Cross-Code Dispersion (15%)**: Number of distinct structured codes the defect was split across (higher dispersion indicates higher evasion of legacy monitoring).
* **$N(\Phi)$ Semantic Coherence (15%)**: Mean pairwise cosine similarity of claim vectors within the cluster.

---

## 🖥️ Application Tour & Workstations

### 1. Command Center
* **Executive Telemetry Strip**: Real-time counts for Ingested Claims, Discovered Clusters, Critical Surges, and Taxonomy Mismatches.
* **Dominant Active Anomaly Spotlight**: Instant executive briefing on the highest-priority defect surge with direct investigation drill-down.
* **Signal Emergence Timeline**: Interactive area chart comparing monthly claim progression against rolling baselines and legacy code thresholds.
* **Discovered Defect Patterns Index**: Ranked by Alert Score with severity badges, growth velocity, and review status.

### 2. Investigation Console
* **Split-Pane Triage**: Left-hand signal index + right-hand deep diagnostic workspace.
* **5 Deep Diagnostic Tabs**:
  * **Diagnostic Overview**: AI-generated *"Why Grouped Together?"* and *"Why Alerted?"* summaries with recognized symptoms.
  * **Verbatim Evidence Claims**: Traceable to exact claim IDs, repair dates, assembly plants, and technician notes.
  * **Emergence Timeline**: Month-by-month trajectory visualization.
  * **Code & Plant Spread**: Bar charts illustrating dealership code fragmentation and multi-plant geographic dispersion.
  * **Statistical Proof**: Complete mathematical score decomposition matrix.
* **Human-in-the-Loop Review Gate**: Reliability engineers can **Confirm Defect**, **Edit Scope / Label**, or **Dismiss False Alarm**.

### 3. Baseline Reveal (Showcase Comparative Analysis)
* Demonstrates why traditional single-code monitoring failed while semantic clustering detected the target anomaly with a **+69-Day Early Warning Advantage**.

### 4. Claims Explorer
* High-density searchable table with filters for failure codes, assembly plants, and a dedicated **"Mismatches Only"** toggle.
* Slide-out modal displaying raw technician notes, AI-extracted failure signatures, and taxonomy contradiction explanations.

### 5. Defect Memory & Institutional Knowledge Base
* Retains verified defect fingerprints from confirmed investigations.
* **Live Complaint Matcher**: Paste any incoming customer complaint or technician note to compute real-time cosine similarity and receive instant diagnostic recommendations.

### 6. Pipeline & Data Operations
* Multipart CSV / JSON dataset drag-and-drop ingestion.
* One-click full pipeline orchestrator with real-time step timings and live backend telemetry stream.
* **One-Click Database Reset**: Wipe pre-seeded records to test on custom fleet datasets.

---

## 🚀 Getting Started

### Prerequisites
* **Python**: 3.11, 3.12, or 3.13
* **Node.js**: 18.x or 20.x (with `npm`)
* **Ollama** *(Optional for local LLM)*: [https://ollama.com](https://ollama.com)

---

### Step 1: Clone Repository & Setup Environment

```bash
git clone https://github.com/YOUR_USERNAME/WarrantyPatternMiner.git
cd WarrantyPatternMiner
```

Create and activate a Python virtual environment:
```bash
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

Install backend dependencies:
```bash
pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables

Copy the sample environment file:
```bash
cp .env.example .env
```

Edit [`.env`](.env) with your preferences:
```ini
# Database
DATABASE_URL=sqlite:///./warranty_miner.db

# Ollama Local LLM (Optional - Set true to enable local LLM extraction)
USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Statistical Parameters
MIN_CLUSTER_SIZE=4
MIN_SAMPLES=2
ALERT_SCORE_THRESHOLD=60.0
CRITICAL_SCORE_THRESHOLD=80.0
SIGNIFICANCE_Z_THRESHOLD=2.0
```

---

### Step 3: Start the Backend API

```powershell
python -m uvicorn apps.api.main:app --port 8000 --host 127.0.0.1 --reload
```
* **API Endpoint**: `http://127.0.0.1:8000`
* **Interactive OpenAPI Swagger Docs**: `http://127.0.0.1:8000/docs`

---

### Step 4: Start the Frontend Application

In a new terminal:
```bash
cd apps/web
npm install
npm run dev
```
* **Frontend Workstation**: `http://localhost:3000`

---

## 🧪 Testing & Benchmark Verification

The repository includes a comprehensive test suite covering unit calculations, taxonomy mismatch detection, data normalization, and end-to-end pipeline execution:

```bash
# Run pytest test suite
pytest tests/ -v
```

```text
============================= test session starts =============================
tests/integration/test_pipeline.py::test_full_end_to_end_pipeline PASSED [  5%]
tests/unit/test_baseline_lead_time.py::test_case_1_traditional_eventually_triggers PASSED [ 11%]
tests/unit/test_baseline_lead_time.py::test_case_2_traditional_never_triggers PASSED [ 17%]
tests/unit/test_baseline_lead_time.py::test_case_3_traditional_triggers_before_or_same_day PASSED [ 23%]
tests/unit/test_extraction.py::test_extract_suspension_clunk PASSED      [ 29%]
tests/unit/test_extraction.py::test_extract_brake_squeak PASSED          [ 35%]
tests/unit/test_extraction.py::test_extract_electrical_screen PASSED     [ 41%]
tests/unit/test_ingestion.py::test_parse_date_safely PASSED              [ 47%]
tests/unit/test_ingestion.py::test_normalize_claim_record_valid PASSED   [ 52%]
tests/unit/test_ingestion.py::test_normalize_claim_record_missing_id PASSED [ 58%]
tests/unit/test_ingestion.py::test_normalize_claim_record_missing_narrative PASSED [ 64%]
tests/unit/test_mismatch.py::test_mismatch_electrical_nff_suspension PASSED [ 70%]
tests/unit/test_mismatch.py::test_mismatch_generic_other_with_specific_defect PASSED [ 76%]
tests/unit/test_mismatch.py::test_match_agreement_suspension PASSED      [ 82%]
tests/unit/test_scoring.py::test_critical_alert_score PASSED             [ 88%]
tests/unit/test_scoring.py::test_normal_alert_score PASSED               [ 94%]
tests/unit/test_trends.py::test_trend_growth_and_zscore PASSED           [100%]
====================== 17 passed in 3.18s ======================
```

### Canonical Benchmark Verification:
To evaluate algorithmic recovery against the 585-claim ground-truth benchmark:
```bash
python scripts/evaluate_golden_dataset.py
```
* **Ground-Truth Target**: Front-Left Suspension Knocking (35 claims spread across 5 codes)
* **Cluster Precision**: **100.00%**
* **Cluster Recall**: **100.00%**
* **Cluster F1-Score**: **100.00%**
* **Computed Alert Score**: **94.3 / 100 (CRITICAL)**
* **Surveillance Lead Time**: **+69 Days Ahead of Traditional Monitoring**

---

## 📁 Repository Structure

```text
WarrantyPatternMiner/
├── apps/
│   ├── api/                          # FastAPI Backend Engine
│   │   ├── config.py                 # Pydantic Settings & Thresholds
│   │   ├── main.py                   # FastAPI Application Entrypoint
│   │   ├── db/                       # SQLAlchemy Session & Declarative Base
│   │   ├── models/                   # Database Entities (Claims, Clusters, Feedback)
│   │   ├── routes/                   # REST API Endpoints (Alerts, Clusters, Claims)
│   │   ├── schemas/                  # Pydantic Request/Response DTOs
│   │   └── services/                 # Core Algorithmic Engines
│   │       ├── baseline.py           # Single-Code vs Semantic Lead-Time Comparator
│   │       ├── clustering.py         # HDBSCAN Cluster Discovery
│   │       ├── embeddings.py         # Vector Semantic Representation
│   │       ├── extraction.py         # Ollama / Domain Heuristic Signature Extractor
│   │       ├── ingestion.py          # CSV/JSON Normalizer & Validation
│   │       ├── labeling.py           # Cluster Label & Diagnostic Rationale Generator
│   │       ├── mismatch.py           # Taxonomy Contradiction Analyzer
│   │       ├── pipeline_orchestrator.py # Full Surveillance Pipeline Runner
│   │       ├── scoring.py            # 5-Factor Emergence Alert Scoring
│   │       └── trends.py             # Rolling Baseline, Z-Score & CUSUM Tracker
│   └── web/                          # React + Vite + TypeScript Frontend
│       ├── src/
│       │   ├── api/                  # API Client & Endpoint Bindings
│       │   ├── components/           # UI Components (Navbar, Badge, Modals)
│       │   ├── pages/                # Workstation Pages (Command Center, Detail, etc.)
│       │   ├── types/                # TypeScript Interface Definitions
│       │   ├── App.tsx               # Root Application Router
│       │   └── index.css             # Tailwind Design Tokens
│       ├── package.json
│       ├── tailwind.config.js
│       └── vite.config.ts
├── data/
│   ├── ground_truth/                 # Canonical Evaluation Benchmark
│   └── raw/                          # Raw Claim Datasets
├── scripts/
│   ├── clear_database.py             # Database Reset Utility
│   ├── evaluate_golden_dataset.py    # Ground-Truth Precision/Recall Benchmark
│   └── generate_demo_data.py         # Canonical Fleet Claims Generator
├── tests/
│   ├── integration/                  # End-to-End Pipeline Tests
│   └── unit/                         # Unit Tests (Extraction, Scoring, Trends)
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 📄 License

This project is licensed under the Apache 2.0 License.
