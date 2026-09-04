import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from sklearn.cluster import HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from apps.api.config import settings
from apps.api.models.claim import Claim, FailureSignature, Embedding
from apps.api.models.cluster import Cluster, ClusterClaim

logger = logging.getLogger(__name__)

def run_density_clustering(
    vectors: np.ndarray, 
    min_cluster_size: Optional[int] = None, 
    min_samples: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Runs HDBSCAN clustering on normalized embeddings using euclidean/cosine distance.
    Returns: (labels, probabilities)
    """
    n_samples = len(vectors)
    if n_samples == 0:
        return np.empty(0, dtype=int), np.empty(0, dtype=float)

    effective_min_size = min_cluster_size or max(6, min(10, n_samples // 35))
    if n_samples < effective_min_size:
        return np.full(n_samples, -1), np.zeros(n_samples)

    effective_min_samples = min_samples or 2

    try:
        clusterer = HDBSCAN(
            min_cluster_size=effective_min_size,
            min_samples=effective_min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
            cluster_selection_epsilon=0.35,
            copy=True
        )
        labels = clusterer.fit_predict(vectors)
        probs = getattr(clusterer, "probabilities_", np.ones(n_samples))
        return labels, probs
    except Exception as e:
        logger.warning(f"HDBSCAN clustering failed: {e}, falling back to distance threshold clustering")
        sim_mat = cosine_similarity(vectors)
        labels = np.full(n_samples, -1)
        visited = set()
        c_id = 0
        for i in range(n_samples):
            if i in visited:
                continue
            matches = [j for j in range(n_samples) if sim_mat[i, j] >= 0.70]
            if len(matches) >= effective_min_size:
                for m in matches:
                    labels[m] = c_id
                    visited.add(m)
                c_id += 1
        return labels, np.ones(n_samples)

def calculate_cluster_coherence(vectors: np.ndarray) -> float:
    if len(vectors) <= 1:
        return 1.0
    sims = cosine_similarity(vectors)
    triu_indices = np.triu_indices(len(vectors), k=1)
    if len(triu_indices[0]) == 0:
        return 1.0
    return float(np.mean(sims[triu_indices]))
