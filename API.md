# WarrantyPatternMiner API Reference

Base URL: `http://127.0.0.1:8000/api`

---

## 1. Claims Endpoints

### `POST /claims/upload`
Uploads a CSV or JSON file containing warranty claim records.
- **Form Data**: `file` (Multipart file)
- **Response**:
  ```json
  {
    "filename": "canonical_warranty_claims.csv",
    "inserted": 572,
    "skipped_or_existing": 0,
    "errors": [],
    "total_errors": 0
  }
  ```

### `GET /claims`
Lists and filters warranty claim records with enriched AI failure signatures and cluster links.
- **Query Parameters**:
  - `search` (string): Text search across narrative and claim ID
  - `failure_code` (string): Filter by structured failure code (e.g. `OTHER`, `SUSPENSION`)
  - `product_model` (string): Filter by vehicle model
  - `plant` (string): Filter by assembly facility
  - `mismatch_only` (boolean): Filter only claims where code contradicts narrative
  - `cluster_id` (string): Filter claims belonging to a specific cluster
  - `page` (int, default: 1), `page_size` (int, default: 50)
- **Response**: `ClaimsListResponse`

### `GET /claims/{id}`
Returns full detail for a single claim, including its failure signature, mismatch evaluation, and cluster membership.

---

## 2. Analysis & Pipeline Endpoints

### `POST /analysis/run`
Triggers the full pipeline execution (Extraction -> Mismatch -> Embeddings -> HDBSCAN Clustering -> Trends -> Scoring).
- **Body**:
  ```json
  {
    "dataset_name": "canonical_claims_v1",
    "min_cluster_size": 4,
    "force_recompute": true
  }
  ```
- **Response**:
  ```json
  {
    "run_id": "RUN-20260830-170000-a1b2c3",
    "status": "completed",
    "total_claims": 572,
    "clusters_found": 24,
    "alerts_critical": 0,
    "alerts_high": 1,
    "mismatches_detected": 12,
    "processing_time_ms": 1369.23
  }
  ```

---

## 3. Clusters & Alerts Endpoints

### `GET /alerts/summary`
Returns high-level KPI metrics for the Command Center.
- **Response**:
  ```json
  {
    "claims_analyzed": 572,
    "emerging_patterns": 24,
    "high_risk_patterns": 1,
    "critical_patterns": 0,
    "high_patterns": 1,
    "watch_patterns": 4,
    "miscoded_claims": 12,
    "hero_cluster": { ... }
  }
  ```

### `GET /clusters`
Returns all discovered semantic clusters sorted by alert score, volume, or growth.
- **Query Parameters**:
  - `alert_level` (string): `CRITICAL`, `HIGH`, `WATCH`, `NORMAL`
  - `sort_by` (string): `alert_score`, `claim_count`, `growth_rate`, `created_at`

### `GET /clusters/{id}`
Returns complete cluster metadata, including AI rationale, time series, distributions (by code, plant, model), and representative claims.

### `GET /clusters/{id}/claims`
Returns all individual claims assigned to this cluster with membership similarity scores.

---

## 4. Baseline Comparison Endpoints

### `GET /baseline/comparison`
Computes side-by-side comparison between traditional code-level monitoring and semantic cluster consolidation.
- **Query Parameters**: `cluster_id` (optional)
- **Response**:
  ```json
  {
    "has_data": true,
    "cluster_label": "Front-Left Suspension Clunking / Knocking Noise",
    "alert_level": "HIGH",
    "alert_score": 68.4,
    "growth_rate": 76.5,
    "total_cluster_claims": 22,
    "cross_code_count": 5,
    "lead_time_days": 18,
    "traditional_monitoring": {
      "status": "NO ALERT TRIGGERED",
      "code_buckets": [ ... ]
    },
    "semantic_monitoring": {
      "status": "ALERT: HIGH",
      "growth_percentage": 76.5,
      "alert_score": 68.4
    }
  }
  ```

---

## 5. Human Verification & Feedback

### `POST /clusters/{id}/feedback`
Records an engineer's verification decision (`confirmed`, `edited`, `dismissed`). If confirmed, automatically saves the defect to the Defect Fingerprint Library.
- **Body**:
  ```json
  {
    "decision": "confirmed",
    "rationale": "Confirmed supplier bushing batch wear defect on Model X.",
    "custom_label": "Front-Left Suspension Bushing Wear",
    "reviewer": "Reliability Lead Engineer"
  }
  ```

---

## 6. Defect Fingerprint Memory

### `GET /fingerprints`
Returns all confirmed defect fingerprints in organizational memory.

### `POST /fingerprints/match`
Evaluates an incoming complaint narrative against saved organizational defect knowledge.
- **Body**:
  ```json
  {
    "narrative": "Customer reports metallic clunking noise from front left wheel area when going over speed bumps."
  }
  ```
- **Response**:
  ```json
  [
    {
      "fingerprint_id": "...",
      "fingerprint_name": "Front-Left Suspension Clunking / Knocking Noise",
      "component": "front-left suspension",
      "similarity_score": 0.90,
      "matched_symptoms": ["clunking / knocking noise"],
      "confidence": 0.90,
      "recommendation": "High similarity to verified defect"
    }
  ]
  ```
