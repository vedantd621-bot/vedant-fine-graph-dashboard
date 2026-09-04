"""Network Risk Scoring & Promotion Tests."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from analytics.src.models import RiskLevel
from backend.app.models.cases import CasePriority, InvestigationCase
from backend.app.models.networks import (
    FraudNetwork,
    FraudNetworkMember,
    NetworkCreateCaseRequest,
    NetworkMemberRole,
    NetworkRiskFactor,
    NetworkType,
)
from backend.app.security.models import Role, User
from backend.app.services.network_intelligence_service import NetworkIntelligenceService


@pytest.fixture
def service_with_network():
    client = MagicMock()
    detection_engine = MagicMock()
    risk_engine = MagicMock()
    account_service = MagicMock()
    alert_service = MagicMock()
    case_service = MagicMock()
    audit_service = MagicMock()
    event_bus = MagicMock()

    service = NetworkIntelligenceService(
        client=client,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
        account_service=account_service,
        alert_service=alert_service,
        case_service=case_service,
        audit_service=audit_service,
        event_bus=event_bus,
    )

    now = datetime.now(timezone.utc)
    members = [
        FraudNetworkMember(account_id="ACC_01", role=NetworkMemberRole.ORIGINATOR, in_degree=2, out_degree=2, total_degree=4, pagerank=0.08, total_volume=150000.0, risk_score=90.0, risk_level=RiskLevel.CRITICAL, is_frozen=False, joined_at=now),
        FraudNetworkMember(account_id="ACC_02", role=NetworkMemberRole.MULE, in_degree=1, out_degree=1, total_degree=2, pagerank=0.02, total_volume=150000.0, risk_score=75.0, risk_level=RiskLevel.HIGH, is_frozen=False, joined_at=now),
        FraudNetworkMember(account_id="ACC_03", role=NetworkMemberRole.AGGREGATOR, in_degree=3, out_degree=1, total_degree=4, pagerank=0.12, total_volume=150000.0, risk_score=85.0, risk_level=RiskLevel.CRITICAL, is_frozen=False, joined_at=now),
    ]
    net = FraudNetwork(
        network_id="NET-TEST-001",
        name="High Velocity Laundering Ring Alpha",
        network_type=NetworkType.CIRCULAR_RING,
        risk_score=84.5,
        risk_level=RiskLevel.CRITICAL,
        member_count=3,
        transaction_count=5,
        total_volume=450000.0,
        detector_count=1,
        community_id=15,
        created_at=now,
        updated_at=now,
        members=members,
        risk_factors=[
            NetworkRiskFactor(factor_name="High-Risk Member Density", description="100% of members exceed risk threshold 60.0", weight=0.25, raw_value=100.0, contribution=25.0),
            NetworkRiskFactor(factor_name="Detector Density", description="Multiple active Cypher detectors", weight=0.25, raw_value=80.0, contribution=20.0),
            NetworkRiskFactor(factor_name="Volume Concentration", description="High dollar concentration", weight=0.20, raw_value=90.0, contribution=18.0),
            NetworkRiskFactor(factor_name="Topological Structure", description="Closed circular cycle", weight=0.20, raw_value=85.0, contribution=17.0),
            NetworkRiskFactor(factor_name="Community Risk Aggregation", description="Elevated Louvain community risk", weight=0.10, raw_value=45.0, contribution=4.5),
        ],
        evidence=[],
        linked_cases=[],
        linked_alerts=[],
    )
    service._network_cache[net.network_id] = net

    return {"service": service, "network": net, "case_service": case_service, "audit_service": audit_service}


def test_network_risk_explanation(service_with_network):
    service = service_with_network["service"]
    resp = service.get_network_risk_explanation("NET-TEST-001")
    assert resp is not None
    assert resp.network_id == "NET-TEST-001"
    assert resp.risk_score == 84.5
    assert resp.risk_level == RiskLevel.CRITICAL
    assert len(resp.factors) == 5
    total_weights = sum(f.weight for f in resp.factors)
    assert abs(total_weights - 1.0) < 0.001
    assert "High Velocity Laundering Ring Alpha" in resp.summary


def test_promote_network_to_case(service_with_network):
    service = service_with_network["service"]
    case_service = service_with_network["case_service"]
    audit_service = service_with_network["audit_service"]

    mock_case = InvestigationCase(
        case_id="CASE-NET-999",
        title="Investigation of High Velocity Laundering Ring Alpha",
        description="Automated promotion of network NET-TEST-001",
        status="OPEN",
        priority=CasePriority.CRITICAL,
        linked_accounts=["ACC_01", "ACC_02", "ACC_03"],
        created_by="investigator_jane",
    )
    case_service.create_case.return_value = mock_case

    user = User(
        user_id="u1",
        username="investigator_jane",
        password_hash="mock_hash",
        role=Role.INVESTIGATOR,
        is_active=True,
    )
    req = NetworkCreateCaseRequest(
        title="Investigation of High Velocity Laundering Ring Alpha",
        priority="CRITICAL",
        initial_notes="Automated promotion of network NET-TEST-001",
    )

    case = service.promote_network_to_case(
        network_id="NET-TEST-001",
        req=req,
        current_user=user,
    )
    assert case is not None
    assert case.case_id == "CASE-NET-999"
    net = service.get_network_by_id("NET-TEST-001")
    assert "CASE-NET-999" in net.linked_cases
    audit_service.record.assert_called()
