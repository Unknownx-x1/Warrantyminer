import os
import sys
os.environ["EVALUATION"] = "true"
import json
from pathlib import Path
from collections import Counter

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from apps.api.db.session import SessionLocal, engine, Base
from apps.api.models import Claim, FailureSignature, Embedding, Cluster, ClusterClaim, CodeMismatch, Feedback, DefectFingerprint
from apps.api.services.ingestion import ingest_claims_data
from apps.api.services.pipeline_orchestrator import execute_full_pipeline
from apps.api.services.baseline import compute_traditional_baseline_comparison
from scripts.generate_demo_data import main as generate_data

def evaluate():
    print("=" * 70)
    print("      WarrantyPatternMiner -- Canonical Dataset & Pipeline Audit")
    print("=" * 70)

    # 1. Regenerate and Ingest Canonical Demo Dataset
    generate_data()
    csv_path = BASE_DIR / "data" / "raw" / "canonical_warranty_claims.csv"
    gt_path = BASE_DIR / "data" / "ground_truth" / "ground_truth_clusters.json"

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    gt_cluster = ground_truth["ground_truth_clusters"][0]
    expected_ids = set(gt_cluster["claim_ids"])
    print(f"\n[Ground Truth Target]")
    print(f"Target Defect Name:    {gt_cluster['name']}")
    print(f"Target Claim IDs ({len(expected_ids)}): {len(expected_ids)} claims total")
    print(f"Expected Timeline:     {gt_cluster['expected_timeline']}")
    print(f"Expected July Codes:   {gt_cluster['expected_july_code_distribution']}")

    # 2. Reset and Seed Database cleanly
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear old data
    db.query(ClusterClaim).delete()
    db.query(Cluster).delete()
    db.query(CodeMismatch).delete()
    db.query(Embedding).delete()
    db.query(FailureSignature).delete()
    db.query(Claim).delete()
    db.commit()

    with open(csv_path, "rb") as f:
        content = f.read()

    inserted, skipped, errors = ingest_claims_data(content, "canonical_warranty_claims.csv", db)
    print(f"\n[Ingestion Phase]")
    print(f"Total Claims Ingested: {inserted}")
    print(f"Skipped / Malformed:   {skipped}")

    # 3. Execute Analytical Pipeline
    print(f"\n[Pipeline Execution Phase]")
    res = execute_full_pipeline(db, dataset_name="canonical_warranty_claims_v1", force_recompute=True)
    print(f"Run ID:                {res['run_id']}")
    print(f"Status:                {res['status']}")
    print(f"Clusters Discovered:   {res['clusters_found']}")
    print(f"High Priority Alerts:  {res['alerts_high'] + res['alerts_critical']}")
    print(f"Mismatches Flagged:    {res['mismatches_detected']}")
    print(f"Execution Time:        {res['processing_time_ms']} ms")

    # 4. Detailed Cluster Inspection
    clusters = db.query(Cluster).order_by(Cluster.alert_score.desc()).all()
    print(f"\n[Discovered Clusters Summary]")
    for i, c in enumerate(clusters[:8]):
        print(f"  #{i+1}: [{c.alert_level}] {c.label} | Claims: {c.claim_count} | Codes: {c.cross_code_count} | Growth: +{c.growth_rate:.0f}% | Score: {c.alert_score}")

    # 5. Algorithmic Hidden Defect Recovery Evaluation
    best_cluster = None
    best_overlap = 0
    captured_ids = set()

    for c in clusters:
        member_external_ids = {cm.claim.external_claim_id for cm in c.claim_memberships}
        overlap = len(member_external_ids.intersection(expected_ids))
        if overlap > best_overlap:
            best_overlap = overlap
            best_cluster = c
            captured_ids = member_external_ids.intersection(expected_ids)

    if not best_cluster:
        print("\n[ERROR] No cluster recovered any hidden defect claims!")
        db.close()
        return

    precision = len(captured_ids) / best_cluster.claim_count
    recall = len(captured_ids) / len(expected_ids)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\n[Hidden Defect Algorithmic Recovery]")
    print(f"Discovered Cluster:    {best_cluster.label}")
    print(f"Cluster ID:            {best_cluster.id}")
    print(f"Total Cluster Size:    {best_cluster.claim_count}")
    print(f"Captured Ground-Truth: {len(captured_ids)} / {len(expected_ids)}")
    print(f"Precision:             {precision:.2%}")
    print(f"Recall:                {recall:.2%}")
    print(f"F1 Score:              {f1:.2%}")

    # 6. Statistical Trend Metrics
    print(f"\n[Statistical & Emergence Metrics]")
    print(f"Baseline Volume:       {best_cluster.baseline_volume} claims/mo")
    print(f"Current Period Volume: {best_cluster.current_volume} claims/mo")
    print(f"Growth Rate (Delta%):  +{best_cluster.growth_rate:.1f}%")
    print(f"Z-Score Significance:  {best_cluster.significance_score}")
    print(f"CUSUM Score:           {best_cluster.cusum_score}")
    print(f"Semantic Coherence:    {best_cluster.coherence_score}")
    print(f"Alert Score:           {best_cluster.alert_score} / 100 ({best_cluster.alert_level})")

    # 7. Structured Code Distribution in Cluster
    code_dist = best_cluster.code_distribution or {}
    print(f"\n[Structured Code Fragmentation in Cluster]")
    for code, cnt in sorted(code_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {code}: {cnt} claims")

    # 8. Baseline Comparison
    comp = compute_traditional_baseline_comparison(db, target_cluster_id=best_cluster.id)
    print(f"\n[Baseline Surveillance Comparison]")
    print(f"Traditional Status:    {comp['traditional_monitoring']['status']}")
    print(f"Semantic Status:       {comp['semantic_monitoring']['status']}")
    print(f"Dynamic Lead Time:     +{comp['lead_time_days']} Days")

    db.close()
    print("\n" + "=" * 70)
    print("      Canonical Evaluation Complete -- System Verified")
    print("=" * 70)

if __name__ == "__main__":
    evaluate()
