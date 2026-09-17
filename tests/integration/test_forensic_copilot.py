import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from apps.api.main import app
from apps.api.db.session import Base, get_db
from apps.api.models.cluster import Cluster, ClusterClaim
from apps.api.models.claim import Claim, FailureSignature
from apps.api.models.investigation import Investigation

@pytest.fixture
def clean_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    yield db
    db.close()

def test_forensic_copilot_chat_endpoint(clean_db):
    app.dependency_overrides[get_db] = lambda: clean_db
    client = TestClient(app)

    # Setup test cluster and investigation
    cluster = Cluster(
        id="cluster-copilot-test",
        cluster_index=1,
        label="High Voltage Inverter Phase Isolation Fault",
        description="Phase isolation breakdown in inverter module causing power limit warning.",
        primary_component="High Voltage Inverter",
        primary_symptom="Power Limit Warning / Isolation Fault",
        claim_count=12,
        alert_score=95.0,
        alert_level="CRITICAL",
        growth_rate=210.0,
        significance_score=5.1,
        cross_code_count=4,
        plant_count=3
    )
    clean_db.add(cluster)

    claim = Claim(
        id="claim-inv-1",
        external_claim_id="CLM-HV-01",
        claim_date=date(2025, 2, 20),
        narrative="Vehicle threw turtle mode warning on highway, technician measured low phase isolation resistance in inverter power stage.",
        failure_code="ELEC-09",
        plant="Austin",
        product_model="Model Y"
    )
    clean_db.add(claim)

    cc = ClusterClaim(cluster_id="cluster-copilot-test", claim_id="claim-inv-1", similarity_score=0.94)
    clean_db.add(cc)

    inv = Investigation(
        id="inv-copilot-test",
        cluster_id="cluster-copilot-test",
        status="completed",
        confidence=0.92,
        overall_classification="EMERGING_DEFECT",
        summary_conclusion="Inverter phase isolation defect verified with 92% confidence."
    )
    clean_db.add(inv)
    clean_db.commit()

    # Call /api/investigations/{cluster_id}/chat
    response = client.post(
        "/api/investigations/cluster-copilot-test/chat",
        json={"question": "What evidence indicates this is an inverter phase fault rather than a 12V battery failure?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["cluster_id"] == "cluster-copilot-test"
    assert "answer" in data
    assert len(data["agent_contributions"]) == 4
    
    agent_roles = [a["role"] for a in data["agent_contributions"]]
    assert "investigator" in agent_roles
    assert "analytics" in agent_roles
    assert "red_team" in agent_roles
    assert "capa" in agent_roles
    assert data["confidence"] == 0.92

    app.dependency_overrides.clear()
