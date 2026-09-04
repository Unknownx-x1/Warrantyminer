# WarrantyPatternMiner — Comprehensive Repository Audit & Gap Analysis

**Date:** 2026-08-31  
**Auditor:** Lead Systems & ML Reliability Engineer  
**Specification:** `WarrantyPatternMiner_Build_Roadmap.pdf`

---

## 1. Architectural Overview & Current Status

WarrantyPatternMiner is architected with a **FastAPI / SQLAlchemy backend** and a **React 18 / TypeScript / Vite / Tailwind CSS frontend**.

```
[CSV / JSON Claims] ──▶ Ingestion & Validation ──▶ Failure Signature Extraction
                                                          │
           ┌──────────────────────────────────────────────┘
           ▼
Code Mismatch Detector ──▶ Semantic Embeddings (TF-IDF + SVD)
                                  │
           ┌──────────────────────┘
           ▼
HDBSCAN Density Clustering ──▶ Trend Detection (Z-Score & CUSUM)
                                  │
           ┌──────────────────────┘
           ▼
Composite Alert Scoring ──▶ Evidence Engine ──▶ Human Review ──▶ Defect Memory
```

---

## 2. Audit Findings Breakdown

### A. Existing Architecture
- **Backend**: Python 3.13+, FastAPI, SQLAlchemy, SQLite (default file `warranty_miner.db`), Scikit-learn (HDBSCAN, TF-IDF, TruncatedSVD), NumPy, SciPy, Pydantic 2.12.
- **Frontend**: React 18, Vite 5, TypeScript 5, Tailwind CSS 3, Recharts 2, Lucide Icons.
- **Data Stores**: SQLite relational schema with 9 tables (`claims`, `failure_signatures`, `embeddings`, `code_mismatches`, `clusters`, `cluster_claims`, `feedback`, `defect_fingerprints`, `analysis_runs`, `audit_logs`).

### B. What is Functional
- Database session and ORM relationships work with SQLite.
- Claim ingestion and normalization validates required fields and dates.
- Pydantic schema validation for Failure Signatures.
- Code Mismatch engine detects discrepancies.
- Dense semantic vector generation and cosine distance calculations.
- HDBSCAN density clustering groups vector embeddings without predefining cluster counts.
- Time-series monthly aggregation, rolling baseline mean, standard deviation, Z-score, and growth rate calculations.
- Defect Fingerprint persistence upon engineer confirmation.
- 14 automated unit/integration tests running with `pytest`.
- Frontend production build compiles cleanly into `dist/`.

### C. What Was Mocked / Simulated
1. **Pipeline Execution Logs in UI**:
   - `IngestionPage.tsx` previously used frontend `setTimeout()` intervals to push predetermined log strings while waiting for the pipeline request.
   - **Remedy**: Replaced with real step-by-step telemetry events generated and broadcasted directly from the backend execution pipeline.

### D. What Was Hardcoded
1. **Lead Time in Baseline Comparison**:
   - `apps/api/services/baseline.py` had `lead_time_days = 18` as a fixed integer.
   - **Remedy**: Replaced with actual time-series calculation: $T_{\text{traditional}} - T_{\text{semantic}}$ based on real claim timestamps.

### E. What Was Incomplete
1. **Cluster Labeling & Disambiguation**:
   - Clusters whose signatures had generic values defaulted to `"Chassis Subsystem Abnormal Behavior"`, leading to repeated duplicate labels in the Discovered Clusters table.
   - **Remedy**: Enhanced labeling engine to synthesize distinct subsystem noun phrases, acoustic symptoms, and frequency-ranked n-grams directly from the underlying member narratives.
2. **Canonical Injected Defect Alignment**:
   - `scripts/generate_demo_data.py` contained 22 claims for the hidden defect instead of the exact 17 claims across 5 structured codes (`OTHER: 5`, `RIDE QUALITY: 4`, `SUSPENSION: 3`, `ELECTRICAL-NFF: 3`, `STEERING: 2`) specified on Pages 10 & 23 of the roadmap.
   - **Remedy**: Realigned the canonical dataset generator to 17 ground-truth claims with accelerating timeline.

### F. What Was Incorrect
- Trend baseline and alert score normalization on smaller sample sets needed epsilon protection to prevent variance dampening.

### G. What Conflicts with the Roadmap
- Roadmap Section 25 & 34: Baseline comparison must calculate lead time and individual code thresholds dynamically from real data.

### H. What Must Be Rebuilt / Refined
- `apps/api/services/labeling.py`: Full overhaul for rich semantic cluster labeling.
- `apps/api/services/baseline.py`: Dynamic lead time date difference calculation.
- `apps/api/services/pipeline_orchestrator.py`: Real event logging and step timing breakdown.
- `scripts/generate_demo_data.py`: Exact 17-claim canonical hidden defect dataset.
- `scripts/evaluate_golden_dataset.py`: Comprehensive debugging & algorithmic validation script.
- `apps/web/src/pages/IngestionPage.tsx`: Real-time pipeline step progress binding.

### I. What Can Be Retained
- Clean industrial dark UI design system.
- Database relational architecture & foreign keys.
- HDBSCAN clustering engine and Scikit-learn vectorization pipeline.
- Fast, typed API contracts.

---

## 3. Implementation Gap Matrix

| Requirement | Current State | Problem | Required Change | Priority | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Canonical Defect Dataset** | 22 claims injected in demo script | Roadmap calls for 17 claims across 5 specific codes (`OTHER: 5`, `RIDE: 4`, `SUSP: 3`, `ELEC: 3`, `STEER: 2`) | Realign canonical dataset generator to exactly 17 ground-truth claims | **P0** | In Progress |
| **Cluster Labeling** | Generic labels repeat (`Chassis Subsystem Abnormal Behavior`) | Poor narrative term extraction on generic signatures | Implement narrative n-gram and domain subsystem extraction in `labeling.py` | **P0** | In Progress |
| **Baseline Lead Time** | `lead_time_days = 18` fixed constant | Not calculated from real timestamps | Compute $T_{\text{traditional}} - T_{\text{semantic}}$ dynamically from claim dates | **P0** | In Progress |
| **Pipeline Telemetry** | Frontend `setTimeout` logs | Simulated progress | Return real backend execution step durations and metrics | **P0** | In Progress |
| **Algorithmic Evaluation Script** | Missing standalone CLI evaluation tool | Hard to inspect cluster precision, recall, and Z-score metrics in one view | Build `scripts/evaluate_golden_dataset.py` with full metric diagnostics | **P1** | In Progress |
| **Defect Memory Matcher** | Basic stem matcher | Needs robust multi-token and semantic scoring | Enhance similarity scoring with component, symptom, and condition weights | **P1** | In Progress |
