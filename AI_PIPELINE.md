# AI & Statistical Pipeline Specification

## 1. Extraction Pipeline

The extraction layer processes raw technician notes and extracts structured failure signatures according to this JSON contract:

```json
{
  "component": "front-left suspension",
  "symptom": "clunking / knocking noise",
  "condition": "rough roads / uneven surface",
  "severity": "moderate",
  "inferred_failure": "suspension bushing or ball-joint excessive clearance/wear",
  "contributing_factors": ["road surface impact loading"],
  "confidence": 0.88
}
```

## 2. Semantic Representation & Embedding

Rather than embedding only the raw narrative blindly, WarrantyPatternMiner builds a normalized semantic representation:

$$\text{SemanticText} = \text{"Component: "} c \parallel \text{" | Symptom: "} s \parallel \text{" | Condition: "} cond \parallel \text{" | Failure: "} f \parallel \text{" | Narrative: "} raw$$

The text is mapped into an $N$-dimensional vector space with unit $L_2$ norm:

$$\vec{v}_{\text{norm}} = \frac{\vec{v}}{\|\vec{v}\|_2} \implies \vec{v}_i \cdot \vec{v}_j = \cos(\theta_{ij})$$

## 3. HDBSCAN Unsupervised Clustering

HDBSCAN clusters claims across all failure codes in a unified semantic space:
- `min_cluster_size`: 4
- `min_samples`: 2
- `cluster_selection_epsilon`: 0.42
- Handles noise/outliers by labeling them as cluster `-1`.

## 4. Time-Series Trend & Anomaly Detection

### Rolling Baseline:
$$\mu_{\text{baseline}} = \frac{1}{N-1}\sum_{t=1}^{N-1} V_t$$

### Rolling Z-Score:
$$Z = \frac{V_{\text{current}} - \mu_{\text{baseline}}}{\sigma_{\text{baseline}} + \epsilon}$$

### Growth Rate Percentage:
$$\Delta\% = \frac{V_{\text{current}} - \mu_{\text{baseline}}}{\max(\mu_{\text{baseline}}, 1)} \times 100\%$$

## 5. Composite Alert Score Formula

$$\text{AlertScore} = 0.30 \cdot S_{\text{growth}} + 0.25 \cdot S_{\text{significance}} + 0.15 \cdot S_{\text{size}} + 0.15 \cdot S_{\text{cross\_code}} + 0.15 \cdot S_{\text{coherence}}$$

### Score Threshold Bands:
- `80 - 100`: **CRITICAL** (Urgent recall risk)
- `60 - 79`: **HIGH** (Surging field defect across facilities)
- `40 - 59`: **WATCH** (Emerging variation under surveillance)
- `0 - 39`: **NORMAL** (Baseline operating noise)
