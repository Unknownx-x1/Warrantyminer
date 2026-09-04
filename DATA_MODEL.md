# Database Schema & Data Models

WarrantyPatternMiner uses SQLAlchemy ORM backed by SQLite (or PostgreSQL for production).

```
 ┌─────────────────┐       ┌──────────────────────┐
 │     claims      │◀──────│  failure_signatures  │
 └────────┬────────┘ 1   1 └──────────────────────┘
          │
          │ 1
          ├───────────────────────┐
          │                       │
          ▼ 1                     ▼ 1
 ┌─────────────────┐     ┌───────────────────┐
 │   embeddings    │     │  code_mismatches  │
 └─────────────────┘     └───────────────────┘
          │
          ▼ N
 ┌─────────────────┐       ┌──────────────────┐
 │ cluster_claims  │──────▶│     clusters     │
 └─────────────────┘ N   1 └────────┬─────────┘
                                    │ 1
                                    ▼ 1
                           ┌──────────────────┐
                           │     feedback     │
                           └────────┬─────────┘
                                    │
                                    ▼
                           ┌──────────────────────┐
                           │ defect_fingerprints  │
                           └──────────────────────┘
```

## Table Definitions

### `claims`
- `id` (UUID/String, Primary Key)
- `external_claim_id` (String, Unique, Indexed)
- `claim_date` (Date, Indexed)
- `product_model` (String)
- `plant` (String)
- `failure_code` (String)
- `narrative` (Text, Required)
- `source` (String)
- `created_at`, `updated_at` (DateTime)

### `failure_signatures`
- `id` (UUID/String, Primary Key)
- `claim_id` (ForeignKey `claims.id`, Unique)
- `component` (String)
- `symptom` (String)
- `condition` (String)
- `severity` (String)
- `inferred_failure` (String)
- `contributing_factors` (JSON Array)
- `extraction_confidence` (Float)
- `model_version` (String)
- `raw_output` (Text)

### `embeddings`
- `id` (UUID/String, Primary Key)
- `claim_id` (ForeignKey `claims.id`, Unique)
- `vector` (JSON Array of Floats, Unit L2 Normalized)
- `semantic_text` (Text)
- `model_name` (String)

### `code_mismatches`
- `id` (UUID/String, Primary Key)
- `claim_id` (ForeignKey `claims.id`, Unique)
- `assigned_code` (String)
- `inferred_category` (String)
- `mismatch_severity` (String: `HIGH`, `MEDIUM`, `NORMAL`)
- `is_mismatch` (Integer: 1 or 0)
- `mismatch_score` (Float)
- `reason` (Text)

### `clusters`
- `id` (UUID/String, Primary Key)
- `run_id` (String, Indexed)
- `cluster_index` (Integer)
- `label` (String)
- `description` (Text)
- `primary_component` (String)
- `primary_symptom` (String)
- `claim_count` (Integer)
- `cross_code_count` (Integer)
- `plant_count` (Integer)
- `growth_rate` (Float)
- `significance_score` (Float, Z-Score)
- `cusum_score` (Float)
- `coherence_score` (Float)
- `alert_score` (Float, 0 to 100)
- `alert_level` (String: `CRITICAL`, `HIGH`, `WATCH`, `NORMAL`)
- `code_distribution`, `plant_distribution`, `model_distribution`, `time_series`, `representative_claims`, `ai_rationale` (JSON)
- `status` (String: `unreviewed`, `confirmed`, `edited`, `dismissed`)

### `defect_fingerprints`
- `id` (UUID/String, Primary Key)
- `name` (String)
- `description` (Text)
- `component` (String)
- `symptoms` (JSON Array)
- `conditions` (JSON Array)
- `example_claims` (JSON Array)
- `confirmed_count` (String)
