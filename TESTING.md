# Testing & Verification Guide

WarrantyPatternMiner includes automated unit, integration, and golden-dataset algorithmic validation tests.

---

## 1. Running the Automated Test Suite

```bash
pytest tests/ -v
```

### Test Structure:
- **`tests/unit/test_ingestion.py`**:
  - Validates 9-format date parser (`YYYY-MM-DD`, `YYYY/MM/DD`, `DD-MM-YYYY`, etc.).
  - Enforces claim schema and whitespace trimming.
  - Rejects empty narratives and missing external claim IDs.
- **`tests/unit/test_extraction.py`**:
  - Tests structured failure signature extraction across mechanical suspension, braking friction, and infotainment display domains.
  - Verifies Pydantic schema validation for all extracted fields.
- **`tests/unit/test_mismatch.py`**:
  - Tests taxonomy contradiction detection (e.g. `ELECTRICAL-NFF` or `OTHER` assigned to mechanical suspension knocking).
- **`tests/unit/test_trends.py`**:
  - Tests time-series monthly aggregation, rolling baseline mean, standard deviation, Z-score formulas, and growth rate percentages.
- **`tests/unit/test_scoring.py`**:
  - Tests the 5-factor composite Alert Score formula:
    $$\text{AlertScore} = 0.30 \cdot S_{\text{growth}} + 0.25 \cdot S_{\text{significance}} + 0.15 \cdot S_{\text{size}} + 0.15 \cdot S_{\text{cross\_code}} + 0.15 \cdot S_{\text{coherence}}$$
  - Tests classification thresholds: `CRITICAL` (80–100), `HIGH` (60–79), `WATCH` (40–59), `NORMAL` (0–39).
- **`tests/integration/test_pipeline.py`**:
  - Runs the full pipeline end-to-end on an in-memory SQLite database.
  - Verifies algorithmic recovery of the 17 hidden ground-truth claims with Recall $\ge 80\%$.
  - Asserts that traditional code-level monitoring triggers 0 alerts while semantic surveillance triggers an alert.
  - Verifies Defect Fingerprint creation and live similarity matching on new incoming complaints.

---

## 2. Running Algorithmic Golden-Dataset Diagnostics

A dedicated CLI evaluation tool is provided to inspect all intermediate pipeline metrics:

```bash
python scripts/evaluate_golden_dataset.py
```

### Evaluated Diagnostics:
- Total Claims Ingested
- Valid Claim Signatures & Embeddings
- HDBSCAN Discovered Clusters
- Overlap with Ground-Truth Injected Defect
- Precision, Recall, and F1 Score
- Rolling Baseline, Recent Surge Volume, and Growth Percentage
- Z-Score Significance and Semantic Coherence
- Composite Alert Score & Severity Band
- Traditional Baseline Breakdown & Dynamic Lead Time (in Days)

---

## 3. Frontend Build Verification

To verify that the React/TypeScript frontend builds cleanly without TypeScript or bundling errors:

```bash
cd apps/web
npm run build
```
Output bundle is written to `apps/web/dist/`.
