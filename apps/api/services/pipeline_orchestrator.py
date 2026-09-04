import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import Counter, defaultdict
import numpy as np
from sqlalchemy.orm import Session

from apps.api.config import settings
from apps.api.models.claim import Claim, FailureSignature, Embedding, CodeMismatch
from apps.api.models.cluster import Cluster, ClusterClaim
from apps.api.models.feedback import AnalysisRun, AuditLog
from apps.api.services.extraction import process_claim_extractions
from apps.api.services.mismatch import process_code_mismatches
from apps.api.services.embeddings import process_embeddings
from apps.api.services.clustering import run_density_clustering, calculate_cluster_coherence
from apps.api.services.labeling import generate_cluster_label_and_summary
from apps.api.services.trends import compute_cluster_trend_statistics
from apps.api.services.scoring import calculate_composite_alert_score, generate_ai_rationale

logger = logging.getLogger(__name__)

def execute_full_pipeline(
    db: Session,
    dataset_name: str = "warranty_claims_demo",
    min_cluster_size: Optional[int] = None,
    force_recompute: bool = False
) -> Dict[str, Any]:
    """
    Executes the entire end-to-end analytical pipeline:
    Claims -> Extraction -> Code Mismatches -> Embeddings -> HDBSCAN Clustering -> Trends -> Alert Scoring -> Persistence
    """
    start_time = time.time()
    run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    events: List[str] = []
    steps_metrics: Dict[str, Any] = {}

    def log_event(msg: str):
        logger.info(f"[{run_id}] {msg}")
        events.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    log_event(f"Initialized analytical surveillance pipeline {run_id}")

    effective_min_size = min_cluster_size or settings.MIN_CLUSTER_SIZE

    # 1. Claims Check
    t0 = time.time()
    all_claims = db.query(Claim).all()
    total_claims = len(all_claims)
    if total_claims == 0:
        log_event("Error: No claims found in database. Ingest claims first.")
        return {
            "run_id": run_id,
            "status": "failed",
            "message": "No claims available in the database. Please ingest claims first.",
            "total_claims": 0,
            "clusters_found": 0,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "events": events,
            "steps": {}
        }

    steps_metrics["ingestion_check"] = {
        "claims_loaded": total_claims,
        "duration_ms": round((time.time() - t0) * 1000, 1)
    }
    log_event(f"Step 1/7: Validated {total_claims} claim records in database ({steps_metrics['ingestion_check']['duration_ms']}ms)")

    # 2. Extract Failure Signatures
    t0 = time.time()
    n_signatures = process_claim_extractions(db, force=force_recompute)
    steps_metrics["extraction"] = {
        "signatures_processed": n_signatures,
        "duration_ms": round((time.time() - t0) * 1000, 1)
    }
    log_event(f"Step 2/7: Extracted {n_signatures} structured failure signatures ({steps_metrics['extraction']['duration_ms']}ms)")

    # 3. Evaluate Code Mismatches
    t0 = time.time()
    n_mismatches = process_code_mismatches(db, force=force_recompute)
    mismatches_flagged = db.query(CodeMismatch).filter(CodeMismatch.is_mismatch == 1).count()
    steps_metrics["mismatch_detection"] = {
        "evaluated": n_mismatches,
        "mismatches_flagged": mismatches_flagged,
        "duration_ms": round((time.time() - t0) * 1000, 1)
    }
    log_event(f"Step 3/7: Code mismatch engine identified {mismatches_flagged} taxonomy contradictions ({steps_metrics['mismatch_detection']['duration_ms']}ms)")

    # 4. Generate Semantic Embeddings
    t0 = time.time()
    n_embeddings = process_embeddings(db, force=force_recompute)
    embeddings_list = db.query(Embedding).all()
    signatures_map = {s.claim_id: s for s in db.query(FailureSignature).all()}
    claims_map = {c.id: c for c in all_claims}

    claim_order = [e.claim_id for e in embeddings_list]
    vectors = np.array([e.vector for e in embeddings_list])
    steps_metrics["embeddings"] = {
        "vectors_generated": len(vectors),
        "dimensions": vectors.shape[1] if len(vectors) > 0 else 0,
        "duration_ms": round((time.time() - t0) * 1000, 1)
    }
    log_event(f"Step 4/7: Generated {len(vectors)} dense semantic embeddings in R^{steps_metrics['embeddings']['dimensions']} space ({steps_metrics['embeddings']['duration_ms']}ms)")

    # 5. Run Unsupervised HDBSCAN Density Clustering
    t0 = time.time()
    labels, probs = run_density_clustering(
        vectors=vectors,
        min_cluster_size=effective_min_size,
        min_samples=settings.MIN_SAMPLES
    )

    clusters_dict = defaultdict(list)
    noise_count = 0
    for idx, cluster_idx in enumerate(labels):
        if cluster_idx != -1:
            clusters_dict[cluster_idx].append(idx)
        else:
            noise_count += 1

    steps_metrics["clustering"] = {
        "clusters_discovered": len(clusters_dict),
        "noise_points_filtered": noise_count,
        "duration_ms": round((time.time() - t0) * 1000, 1)
    }
    log_event(f"Step 5/7: HDBSCAN formed {len(clusters_dict)} semantic clusters ({noise_count} noise points isolated) ({steps_metrics['clustering']['duration_ms']}ms)")

    # 6. Delete old clusters before persisting new run
    db.query(ClusterClaim).delete()
    db.query(Cluster).delete()
    db.commit()

    saved_clusters = []
    critical_count = 0
    high_count = 0
    watch_count = 0

    # 7. Process Each Discovered Cluster
    t0 = time.time()
    for c_idx, member_indices in clusters_dict.items():
        member_claim_ids = [claim_order[i] for i in member_indices]
        member_claims = [claims_map[cid] for cid in member_claim_ids if cid in claims_map]
        member_signatures = [signatures_map.get(cid) for cid in member_claim_ids]
        member_vectors = vectors[member_indices]

        # Calculate semantic coherence
        coherence = calculate_cluster_coherence(member_vectors)

        # Label and Summary with narrative mining
        label, desc, comp, symp = generate_cluster_label_and_summary(member_claims, member_signatures, cluster_index=int(c_idx))

        # Trend & Time Series Statistics
        trend_stats = compute_cluster_trend_statistics(member_claims)

        # Failure Code, Plant, and Model Distributions
        code_dist = Counter([c.failure_code or "UNASSIGNED" for c in member_claims])
        plant_dist = Counter([c.plant or "Unknown" for c in member_claims])
        model_dist = Counter([c.product_model or "Unknown" for c in member_claims])

        cross_code_cnt = len(code_dist)
        plant_cnt = len(plant_dist)
        model_cnt = len(model_dist)

        # Alert Scoring
        alert_info = calculate_composite_alert_score(
            growth_rate=trend_stats["growth_rate"],
            significance_score=trend_stats["significance_score"],
            claim_count=len(member_claims),
            cross_code_count=cross_code_cnt,
            coherence_score=coherence
        )

        if alert_info["alert_level"] == "CRITICAL":
            critical_count += 1
        elif alert_info["alert_level"] == "HIGH":
            high_count += 1
        elif alert_info["alert_level"] == "WATCH":
            watch_count += 1

        # Representative claims snippets
        rep_snippets = []
        for c in member_claims[:4]:
            rep_snippets.append({
                "claim_id": c.external_claim_id,
                "failure_code": c.failure_code,
                "plant": c.plant,
                "narrative": c.narrative
            })

        # AI Rationale
        rationale = generate_ai_rationale(
            claims=member_claims,
            signatures=member_signatures,
            growth_rate=trend_stats["growth_rate"],
            cross_code_count=cross_code_cnt,
            plant_count=plant_cnt,
            primary_component=comp,
            primary_symptom=symp
        )

        cluster_obj = Cluster(
            run_id=run_id,
            cluster_index=int(c_idx),
            label=label,
            description=desc,
            primary_component=comp,
            primary_symptom=symp,
            claim_count=len(member_claims),
            cross_code_count=cross_code_cnt,
            plant_count=plant_cnt,
            model_count=model_cnt,
            baseline_volume=trend_stats["baseline_volume"],
            current_volume=trend_stats["current_volume"],
            growth_rate=trend_stats["growth_rate"],
            significance_score=trend_stats["significance_score"],
            cusum_score=trend_stats["cusum_score"],
            coherence_score=round(coherence, 3),
            alert_score=alert_info["alert_score"],
            alert_level=alert_info["alert_level"],
            code_distribution=dict(code_dist),
            plant_distribution=dict(plant_dist),
            model_distribution=dict(model_dist),
            time_series=trend_stats["time_series"],
            representative_claims=rep_snippets,
            ai_rationale=rationale,
            status="unreviewed"
        )
        db.add(cluster_obj)
        db.flush()

        for m_idx, cid in enumerate(member_claim_ids):
            prob = float(probs[member_indices[m_idx]]) if len(probs) > member_indices[m_idx] else 1.0
            cc_obj = ClusterClaim(
                cluster_id=cluster_obj.id,
                claim_id=cid,
                similarity_score=round(prob, 3),
                membership_probability=round(prob, 3),
                is_exemplar=1 if m_idx < 3 else 0
            )
            db.add(cc_obj)

        saved_clusters.append(cluster_obj)

    steps_metrics["trends_and_scoring"] = {
        "critical_alerts": critical_count,
        "high_alerts": high_count,
        "watch_alerts": watch_count,
        "duration_ms": round((time.time() - t0) * 1000, 1)
    }
    log_event(f"Step 6/7: Trend engine flagged {critical_count} critical and {high_count} high-priority surges ({steps_metrics['trends_and_scoring']['duration_ms']}ms)")

    # 8. Save AnalysisRun Record
    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    run_record = AnalysisRun(
        run_id=run_id,
        dataset_name=dataset_name,
        total_claims=str(total_claims),
        clusters_found=str(len(saved_clusters)),
        alerts_critical=str(critical_count),
        alerts_high=str(high_count),
        mismatches_detected=str(mismatches_flagged),
        status="completed",
        config_params={
            "min_cluster_size": effective_min_size,
            "algorithm": "hdbscan",
            "model_version": "v1.0"
        },
        summary_metrics={
            "processing_time_ms": elapsed_ms,
            "clusters": len(saved_clusters),
            "critical_alerts": critical_count,
            "high_alerts": high_count
        }
    )
    db.add(run_record)

    # 9. Save Audit Log
    audit = AuditLog(
        entity_type="analysis_run",
        entity_id=run_id,
        action="pipeline_executed",
        details={
            "claims": total_claims,
            "clusters": len(saved_clusters),
            "critical": critical_count,
            "high": high_count,
            "duration_ms": elapsed_ms
        }
    )
    db.add(audit)

    db.commit()
    log_event(f"Step 7/7: Pipeline execution completed in {elapsed_ms}ms. All metrics persisted.")

    return {
        "run_id": run_id,
        "status": "completed",
        "total_claims": total_claims,
        "clusters_found": len(saved_clusters),
        "alerts_critical": critical_count,
        "alerts_high": high_count,
        "mismatches_detected": mismatches_flagged,
        "processing_time_ms": elapsed_ms,
        "events": events,
        "steps": steps_metrics,
        "summary": {
            "critical_count": critical_count,
            "high_count": high_count,
            "clusters": len(saved_clusters)
        }
    }
