import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.db.session import Base
from apps.api.models import Claim, Cluster, DefectFingerprint
from apps.api.services.ingestion import ingest_claims_data
from apps.api.services.pipeline_orchestrator import execute_full_pipeline
from apps.api.services.baseline import compute_traditional_baseline_comparison
from apps.api.services.fingerprints import create_fingerprint_from_cluster, match_claim_to_fingerprints
from scripts.generate_demo_data import generate_dataset
import io
import csv

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    yield db
    db.close()

def test_full_end_to_end_pipeline(test_db):
    # 1. Ingest Canonical Demo Dataset with 35 Ground-Truth Hidden Defect Claims (17 in July surge)
    claims_list, gt = generate_dataset(n_background=500)
    expected_ids = set(gt["ground_truth_clusters"][0]["claim_ids"])
    assert len(expected_ids) == 35
    
    csv_buf = io.StringIO()
    writer = csv.DictWriter(csv_buf, fieldnames=["claim_id", "date", "product_model", "plant", "failure_code", "narrative"])
    writer.writeheader()
    writer.writerows(claims_list)
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    inserted, skipped, errors = ingest_claims_data(csv_bytes, "test_dataset.csv", test_db)
    assert inserted == len(claims_list)
    assert errors == []

    # 2. Execute Full Pipeline
    result = execute_full_pipeline(test_db, dataset_name="test_integration", force_recompute=True)
    assert result["status"] == "completed"
    assert result["clusters_found"] > 0
    assert len(result["events"]) >= 5

    # 3. Assert Algorithmic Recovery of the Hidden Defect
    clusters = test_db.query(Cluster).order_by(Cluster.alert_score.desc()).all()
    
    # Find cluster with highest overlap of ground-truth claim IDs
    best_cluster = None
    best_overlap = 0
    for c in clusters:
        member_ids = {cm.claim.external_claim_id for cm in c.claim_memberships}
        overlap = len(member_ids.intersection(expected_ids))
        if overlap > best_overlap:
            best_overlap = overlap
            best_cluster = c

    assert best_cluster is not None
    # High Recall (>= 90% of the 35 hidden claims recovered together)
    recall = best_overlap / len(expected_ids)
    assert recall >= 0.90
    precision = best_overlap / best_cluster.claim_count
    assert precision >= 0.90

    # Must span 5 misleading structured failure codes
    assert best_cluster.cross_code_count >= 4
    assert best_cluster.alert_score >= 80.0
    assert best_cluster.alert_level == "CRITICAL"
    assert best_cluster.significance_score >= 3.0
    assert best_cluster.growth_rate >= 200.0

    # 4. Verify Baseline Comparison & Dynamic Lead Time
    baseline_comp = compute_traditional_baseline_comparison(test_db, target_cluster_id=best_cluster.id)
    assert baseline_comp["has_data"] is True
    assert "ALERT" in baseline_comp["semantic_monitoring"]["status"]
    assert baseline_comp["semantic_detection_date"] is not None
    assert baseline_comp["lead_time_status"] in ("FINITE_LEAD_TIME_ADVANTAGE", "NO_ALERT_WITHIN_OBSERVATION_WINDOW")
    if baseline_comp["lead_time_days"] is not None:
        assert baseline_comp["lead_time_days"] > 0

    # 5. Verify Defect Fingerprint Creation & Future Similarity Matching
    fingerprint = create_fingerprint_from_cluster(test_db, best_cluster, "Test Lead")
    assert fingerprint.name == best_cluster.label
    assert len(fingerprint.symptoms) > 0

    # Match a new incoming claim narrative against the persistent Defect Fingerprint
    new_narrative = "Driver reports front left corner knocking sound when going over speed bumps."
    matches = match_claim_to_fingerprints(test_db, new_narrative)
    assert len(matches) > 0
    assert matches[0]["fingerprint_id"] == fingerprint.id
    assert matches[0]["similarity_score"] >= 0.50

def test_400_claim_golden_recovery():
    """
    Regression Test: 400 claims (35 canonical + 365 background) -> 35 canonical claims recovered as one single cluster.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    claims_list, gt = generate_dataset(n_background=365)
    expected_ids = set(gt["ground_truth_clusters"][0]["claim_ids"])
    assert len(claims_list) == 400
    assert len(expected_ids) == 35

    csv_buf = io.StringIO()
    writer = csv.DictWriter(csv_buf, fieldnames=["claim_id", "date", "product_model", "plant", "failure_code", "narrative"])
    writer.writeheader()
    writer.writerows(claims_list)
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    inserted, skipped, errors = ingest_claims_data(csv_bytes, "test_400.csv", db)
    assert inserted == 400

    result = execute_full_pipeline(db, dataset_name="test_400_run", force_recompute=True)
    assert result["status"] == "completed"

    clusters = db.query(Cluster).order_by(Cluster.alert_score.desc()).all()
    best_cluster = None
    best_overlap = 0
    for c in clusters:
        member_ids = {cm.claim.external_claim_id for cm in c.claim_memberships}
        overlap = len(member_ids.intersection(expected_ids))
        if overlap > best_overlap:
            best_overlap = overlap
            best_cluster = c

    assert best_cluster is not None
    # 100% Precision & 100% Recall on the 35 canonical claims
    assert best_overlap == 35
    assert best_cluster.claim_count == 35
    recall = best_overlap / len(expected_ids)
    precision = best_overlap / best_cluster.claim_count
    f1 = 2 * (precision * recall) / (precision + recall)
    assert recall == 1.0
    assert precision == 1.0
    assert f1 == 1.0

    # Verify statistical signals
    assert best_cluster.cross_code_count == 5
    assert best_cluster.alert_level == "CRITICAL"
    assert best_cluster.alert_score >= 80.0
    assert best_cluster.significance_score >= 3.0
    assert best_cluster.growth_rate >= 200.0

    db.close()
