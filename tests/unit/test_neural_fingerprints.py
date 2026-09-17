import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.db.session import Base
from apps.api.models.cluster import Cluster, ClusterClaim
from apps.api.models.claim import Claim, FailureSignature, Embedding
from apps.api.models.feedback import DefectFingerprint
from apps.api.services.fingerprints import (
    create_fingerprint_from_cluster,
    match_claim_to_fingerprints,
    match_cluster_to_precedents
)

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    yield db
    db.close()

def test_create_and_match_vector_fingerprint(db_session):
    # 1. Create a test cluster with claims
    cluster = Cluster(
        id="cluster-test-123",
        cluster_index=1,
        label="Front Lower Control Arm Hydrobushing Hydraulic Fluid Leakage",
        description="Hydrobushing seal failure leading to fluid leakage and clunking over bumps.",
        primary_component="Front Lower Control Arm",
        primary_symptom="Fluid Leakage / Clunking Noise",
        claim_count=5,
        alert_score=92.5,
        alert_level="CRITICAL",
        growth_rate=140.0,
        significance_score=4.2
    )
    db_session.add(cluster)

    claim1 = Claim(
        id="claim-test-1",
        external_claim_id="CLM-F1",
        claim_date=date(2025, 3, 10),
        narrative="Customer noted severe clunking over bumps, inspected front lower control arm and found hydraulic fluid leaking from bushing.",
        failure_code="SUSP-01",
        plant="Fremont"
    )
    sig1 = FailureSignature(
        claim_id="claim-test-1",
        component="Front Lower Control Arm",
        symptom="Fluid Leakage / Clunking Noise",
        condition="Bumpy Roads",
        extraction_confidence=0.95
    )
    db_session.add(claim1)
    db_session.add(sig1)

    cc1 = ClusterClaim(cluster_id="cluster-test-123", claim_id="claim-test-1", similarity_score=0.92)
    db_session.add(cc1)
    db_session.commit()

    # 2. Create Neural Defect Fingerprint
    fp = create_fingerprint_from_cluster(db_session, cluster, engineer_name="Lead Quality Engineer")
    assert fp is not None
    assert fp.name == cluster.label
    assert fp.vector is not None
    assert len(fp.vector) == 384  # FastEmbed 384-dimensional vector

    # 3. Test Vector Cosine Matching with a new claim narrative
    test_query = "Vehicle exhibiting loud knocking sound from front suspension, hydrobushing torn with oil visible."
    matches = match_claim_to_fingerprints(
        db=db_session,
        narrative=test_query,
        component="Front Suspension Bushing"
    )

    assert len(matches) > 0
    top_match = matches[0]
    assert top_match["fingerprint_id"] == fp.id
    assert top_match["similarity_score"] >= 0.50
    assert "High institutional match" in top_match["recommendation"] or "Moderate semantic match" in top_match["recommendation"]

def test_cluster_precedent_cbr(db_session):
    # Store a historical precedent
    past_fp = DefectFingerprint(
        id="past-fp-1",
        name="2024 Fremont Lower Control Arm Bushing Delamination",
        description="Severe bushing wear causing knocking over bumps.",
        component="Lower Control Arm",
        symptoms=["Knocking Noise", "Bushing Tear"],
        conditions=["Rough Road"],
        confirmed_count="3"
    )
    db_session.add(past_fp)
    db_session.commit()

    # Test cluster
    target_cluster = Cluster(
        id="cluster-target-456",
        cluster_index=2,
        label="Front Suspension Arm Knocking Under Articulation",
        description="Front suspension arm knocking noise when traversing uneven surfaces.",
        primary_component="Front Suspension Arm",
        primary_symptom="Knocking Noise",
        claim_count=8,
        alert_score=88.0,
        alert_level="CRITICAL",
        growth_rate=80.0,
        significance_score=3.8
    )
    db_session.add(target_cluster)
    db_session.commit()

    precedents = match_cluster_to_precedents(db_session, cluster_id="cluster-target-456")
    assert len(precedents) > 0
    assert precedents[0]["name"] == "2024 Fremont Lower Control Arm Bushing Delamination"
    assert precedents[0]["similarity_score"] >= 0.40
