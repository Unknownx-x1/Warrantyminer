# WarrantyPatternMiner Architecture

## High-Level System Architecture

WarrantyPatternMiner is built as a decoupled, multi-stage narrative intelligence platform:

```
[Raw Claims (CSV/JSON)] ──▶ [Ingestion & Normalizer]
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    [Structured Fields Storage]             [Deterministic/AI Extractor]
                 │                                       │
                 │                          [Structured Failure Signature]
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                        [Code Mismatch Classifier]
                                     │
                                     ▼
                        [Dense Semantic Embedding]
                                     │
                                     ▼
                        [HDBSCAN Density Clustering]
                                     │
                                     ▼
                        [Statistical Trend Engine]
                                     │
                                     ▼
                        [Composite Alert Scorer]
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
     [Baseline Comparison Engine]            [Evidence-First Drilldown]
                                                         │
                                                         ▼
                                            [Human Reliability Review]
                                                         │
                                                         ▼
                                            [Defect Fingerprint Memory]
```

## Core Modules

### 1. Ingestion Layer (`apps/api/services/ingestion.py`)
- Standardizes claim schema (`claim_id`, `date`, `product_model`, `plant`, `failure_code`, `narrative`).
- Enforces data cleaning, date normalization across 9 formats, whitespace trimming, and duplicate external ID detection.

### 2. Failure Signature Extraction (`apps/api/services/extraction.py`)
- Converts free-text complaint narratives into structured entities:
  - `component`: Automotive sub-component (e.g. `front-left suspension`, `infotainment display`)
  - `symptom`: Acoustic and physical symptoms (e.g. `clunking / knocking noise`)
  - `condition`: Operating conditions (e.g. `rough roads / uneven surface`, `speed bumps`)
  - `severity`: Failure severity (`critical`, `high`, `moderate`, `low`)
  - `inferred_failure`: Root mechanical/electrical hypothesis
- Cached by claim hash to prevent duplicate LLM/NLP computation.

### 3. Code Mismatch Engine (`apps/api/services/mismatch.py`)
- Evaluates discrepancy between assigned code and extracted narrative signature.
- Detects catch-all obscuration (e.g. `OTHER`, `RIDE QUALITY`) and contradictory coding (e.g. `ELECTRICAL-NFF` for physical suspension clunking).

### 4. Embedding & Clustering Layer (`apps/api/services/embeddings.py` & `clustering.py`)
- Transforms multi-field failure representations into dense unit vectors.
- Applies HDBSCAN across all structured codes in a single semantic space.
- Filters outlier noise (`label = -1`) and computes cluster centroids and cohesion.

### 5. Statistical Trend & Alert Scoring (`apps/api/services/trends.py` & `scoring.py`)
- Time-series monthly aggregation.
- Rolling baseline mean $\mu_{\text{base}}$ and standard deviation $\sigma_{\text{base}}$.
- Rolling Z-score ($Z = \frac{V_{\text{curr}} - \mu_{\text{base}}}{\sigma_{\text{base}} + \epsilon}$) and CUSUM shift tracking.
- 5-factor composite alert score:
  $$\text{Score} = 0.30 \cdot \text{Growth} + 0.25 \cdot \text{Z-Score} + 0.15 \cdot \text{Size} + 0.15 \cdot \text{CrossCode} + 0.15 \cdot \text{Coherence}$$

### 6. Defect Memory & Matching (`apps/api/services/fingerprints.py`)
- Converts confirmed clusters into reusable Defect Fingerprints.
- Evaluates new incoming field complaints against historical defect fingerprints.
