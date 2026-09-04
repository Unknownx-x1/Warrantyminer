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

def run_density_clustering(vectors: np.ndarray, min_cluster_size: int = 4, min_samples: int = 2) -> Tuple[np.ndarray, np.ndarray]:
    """
    Runs HDBSCAN clustering on normalized embeddings using euclidean/cosine distance.
    Returns: (labels, probabilities)
    """
    n_samples = len(vectors)
    if n_samples < min_cluster_size:
        return np.full(n_samples, -1), np.zeros(n_samples)

    effective_min_size = min(min_cluster_size, max(2, n_samples // 4))

    try:
        clusterer = HDBSCAN(
            min_cluster_size=effective_min_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_epsilon=0.55,
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
