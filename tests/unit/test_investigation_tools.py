import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.db.session import Base
from apps.api.models.claim import Claim, FailureSignature
from apps.api.models.cluster import Cluster, ClusterClaim
from apps.api.services.investigation_tools import registry
from datetime import date

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # Seed sample cluster with 10 claims
    cluster = Cluster(
        id="test-cluster-123",
        cluster_index=0,
        label="Front Suspension Bushing Wear",
        primary_component="front suspension",
        primary_symptom="clunking / knocking noise",
        claim_count=10,
        cross_code_count=4,
        plant_count=2,
        model_count=2,
        growth_rate=150.0,
        significance_score=3.2,
        alert_score=88.5,
        alert_level="CRITICAL"
    )
    db.add(cluster)

    for i in range(1, 11):
        c = Claim(
            id=f"claim-uuid-{i}",
            external_claim_id=f"C-TEST-{i:03d}",
            claim_date=date(2026, 6 if i <= 3 else 7, 10 + i),
            product_model="Model X" if i % 2 == 0 else "Model Y",
            plant="Plant A - Fremont" if i <= 7 else "Plant B - Austin",
            failure_code=["SUSPENSION", "OTHER", "RIDE QUALITY", "ELECTRICAL-NFF"][i % 4],
            narrative=f"Technician report: Front suspension knocking noise over speed bumps on claim {i}"
        )
        db.add(c)
        db.flush()

        sig = FailureSignature(
            claim_id=c.id,
            component="front suspension",
            symptom="clunking / knocking noise",
            condition="rough roads / speed bumps",
            severity="high",
            inferred_failure="suspension bushing wear",
            extraction_confidence=0.92
        )
        db.add(sig)

        cc = ClusterClaim(
            cluster_id=cluster.id,
            claim_id=c.id,
            similarity_score=0.95
        )
        db.add(cc)

    db.commit()
    yield db
    db.close()

def test_tool_get_cluster_claims(test_db):
    res = registry.execute("get_cluster_claims", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert res.data["count"] == 10
    assert len(res.evidence_refs) == 10
    assert "Front Suspension" in res.summary

def test_tool_get_cluster_metadata(test_db):
    res = registry.execute("get_cluster_metadata", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert res.data["alert_score"] == 88.5
    assert res.data["alert_level"] == "CRITICAL"
    assert res.data["claim_count"] == 10

def test_tool_semantic_claim_search(test_db):
    res = registry.execute("semantic_claim_search", db=test_db, query="knocking noise", cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert res.data["total_matches"] == 10
    assert len(res.evidence_refs) == 10

def test_tool_calculate_cluster_trend(test_db):
    res = registry.execute("calculate_cluster_trend", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert "months" in res.data
    assert res.data["growth_rate_pct"] > 0

def test_tool_calculate_z_score(test_db):
    res = registry.execute("calculate_z_score", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert "z_score" in res.data
    assert res.data["z_score"] >= 0.0

def test_tool_analyze_code_fragmentation(test_db):
    res = registry.execute("analyze_code_fragmentation", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert res.data["distinct_code_count"] == 4
    assert res.data["shannon_entropy"] > 1.0
    assert res.data["is_fragmented"] is True

def test_tool_analyze_plant_distribution(test_db):
    res = registry.execute("analyze_plant_distribution", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert res.data["plant_count"] == 2
    assert "Plant A - Fremont" in res.data["plant_distribution"]

def test_tool_check_data_quality(test_db):
    res = registry.execute("check_data_quality", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert res.data["quality_score"] > 0.80
    assert res.data["missing_dates"] == 0

def test_tool_query_nhtsa_recalls_honest_reporting(test_db):
    res = registry.execute("query_nhtsa_recalls", db=test_db, component="suspension")
    # Must report SUCCESS or UNAVAILABLE honestly without fabricating fake recalls
    assert res.status in ("SUCCESS", "UNAVAILABLE")
    if res.status == "UNAVAILABLE":
        assert "offline" in res.summary.lower() or "unreachable" in res.summary.lower()

def test_tool_query_supplier_manufacturing_records_honest(test_db):
    res = registry.execute("query_supplier_manufacturing_records", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "UNAVAILABLE"
    assert "unavailable" in res.summary.lower()

def test_tool_estimate_warranty_exposure(test_db):
    res = registry.execute("estimate_warranty_exposure", db=test_db, cluster_id="test-cluster-123")
    assert res.status == "SUCCESS"
    assert res.data["unit_repair_cost"] > 0
    assert res.data["incurred_cost"] > 0
