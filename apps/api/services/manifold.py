import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA
from scipy.spatial import ConvexHull

from apps.api.models.claim import Claim, Embedding, CodeMismatch
from apps.api.models.cluster import Cluster, ClusterClaim

logger = logging.getLogger(__name__)

def compute_manifold_projection(
    db: Session,
    n_components: int = 2,
    method: str = "umap"
) -> Dict[str, Any]:
    """
    Projects 384-dimensional FastEmbed vectors onto a 2D coordinate space (x, y)
    with cluster centroids and boundary convex hulls for live interactive fleet visualization.
    """
    embeddings = db.query(Embedding).order_by(Embedding.claim_id).all()
    if not embeddings:
        return {"points": [], "clusters": [], "total_points": 0, "method": "none"}

    claims = db.query(Claim).order_by(Claim.id).all()
    claims_map = {c.id: c for c in claims}
    mismatches_map = {m.claim_id: m for m in db.query(CodeMismatch).all()}
    
    # Map cluster memberships
    cluster_claims = db.query(ClusterClaim).all()
    membership_map = {cc.claim_id: cc for cc in cluster_claims}
    clusters = {c.id: c for c in db.query(Cluster).all()}

    vectors = np.array([e.vector for e in embeddings], dtype=np.float32)
    n_samples = len(vectors)

    projected_coords = None
    applied_method = "pca"

    if method == "umap" and n_samples >= 10:
        try:
            import umap
            reducer = umap.UMAP(
                n_components=n_components,
                n_neighbors=min(15, max(4, n_samples - 1)),
                min_dist=0.15,
                metric="cosine",
                random_state=42
            )
            projected_coords = reducer.fit_transform(vectors)
            applied_method = "umap"
        except Exception as e:
            logger.warning(f"UMAP reduction unavailable: {e}, falling back to PCA")

    if projected_coords is None:
        pca = PCA(n_components=n_components, random_state=42)
        projected_coords = pca.fit_transform(vectors)
        applied_method = "pca"

    # Normalize coordinates to [-90, 90] grid for consistent UI canvas rendering
    min_x, max_x = float(np.min(projected_coords[:, 0])), float(np.max(projected_coords[:, 0]))
    min_y, max_y = float(np.min(projected_coords[:, 1])), float(np.max(projected_coords[:, 1]))
    
    range_x = max_x - min_x if max_x > min_x else 1.0
    range_y = max_y - min_y if max_y > min_y else 1.0

    norm_x = ((projected_coords[:, 0] - min_x) / range_x) * 180.0 - 90.0
    norm_y = ((projected_coords[:, 1] - min_y) / range_y) * 180.0 - 90.0

    points = []
    cluster_points = {}

    for idx, emb in enumerate(embeddings):
        claim = claims_map.get(emb.claim_id)
        if not claim:
            continue
        
        mem = membership_map.get(claim.id)
        cluster_obj = clusters.get(mem.cluster_id) if mem else None
        mismatch_obj = mismatches_map.get(claim.id)
        sig = claim.signature

        c_id = cluster_obj.id if cluster_obj else None
        c_label = cluster_obj.label if cluster_obj else "Noise / Unclustered"
        c_idx = cluster_obj.cluster_index if cluster_obj else -1
        is_noise = (cluster_obj is None) or (c_idx == -1)

        px = round(float(norm_x[idx]), 2)
        py = round(float(norm_y[idx]), 2)

        point_data = {
            "claim_id": claim.id,
            "external_id": claim.external_claim_id,
            "x": px,
            "y": py,
            "cluster_id": c_id,
            "cluster_index": c_idx,
            "cluster_label": c_label,
            "is_noise": is_noise,
            "is_mismatch": mismatch_obj.is_mismatch if mismatch_obj else 0,
            "mismatch_severity": mismatch_obj.mismatch_severity if mismatch_obj else "NORMAL",
            "failure_code": claim.failure_code or "UNASSIGNED",
            "plant": claim.plant or "Unknown",
            "model": claim.product_model or "Unknown",
            "date": claim.claim_date.isoformat() if claim.claim_date else None,
            "component": sig.component if sig else "unspecified",
            "symptom": sig.symptom if sig else "unspecified",
            "narrative": claim.narrative[:140] + ("..." if len(claim.narrative) > 140 else "")
        }
        points.append(point_data)

        if not is_noise and c_id:
            if c_id not in cluster_points:
                cluster_points[c_id] = {"pts": [], "obj": cluster_obj}
            cluster_points[c_id]["pts"].append((px, py))

    # Compute cluster hulls and centroids
    cluster_summaries = []
    for c_id, data in cluster_points.items():
        c_obj = data["obj"]
        pts = np.array(data["pts"])
        cx = round(float(np.mean(pts[:, 0])), 2)
        cy = round(float(np.mean(pts[:, 1])), 2)

        hull_coords = []
        if len(pts) >= 3:
            try:
                hull = ConvexHull(pts)
                hull_coords = [[round(float(pts[v, 0]), 2), round(float(pts[v, 1]), 2)] for v in hull.vertices]
            except Exception:
                hull_coords = []

        cluster_summaries.append({
            "cluster_id": c_id,
            "cluster_index": c_obj.cluster_index,
            "label": c_obj.label,
            "claim_count": c_obj.claim_count,
            "alert_score": c_obj.alert_score,
            "alert_level": c_obj.alert_level,
            "centroid": {"x": cx, "y": cy},
            "hull": hull_coords,
            "primary_component": c_obj.primary_component,
            "primary_symptom": c_obj.primary_symptom
        })

    cluster_summaries.sort(key=lambda x: x["alert_score"], reverse=True)

    return {
        "points": points,
        "clusters": cluster_summaries,
        "total_points": len(points),
        "method": applied_method,
        "grid_bounds": {"min_x": -90.0, "max_x": 90.0, "min_y": -90.0, "max_y": 90.0}
    }
