"""Fraud Network & Syndicate Discovery Unit Tests."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from analytics.src.models import GraphFeatures, RiskLevel, RiskScore, RuleSignals
from backend.app.models.accounts import AccountDetail, AccountSummary
from backend.app.models.networks import (
    FraudNetwork,
    FraudNetworkMember,
    NetworkMemberRole,
    NetworkType,
)
from backend.app.services.network_intelligence_service import NetworkIntelligenceService
from detection.src.models import DetectionEvidence, DetectionResult, DetectionType, Severity


@pytest.fixture
def mock_dependencies():
    client = MagicMock()
    detection_engine = MagicMock()
    risk_engine = MagicMock()
    account_service = MagicMock()
    alert_service = MagicMock()
    case_service = MagicMock()
    audit_service = MagicMock()
    event_bus = MagicMock()

    risk_engine.determine_risk_level.side_effect = lambda score: (
        RiskLevel.CRITICAL if score >= 80 else RiskLevel.HIGH if score >= 60 else RiskLevel.MEDIUM if score >= 40 else RiskLevel.LOW
    )

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
    return {
        "service": service,
        "client": client,
        "detection_engine": detection_engine,
        "risk_engine": risk_engine,
        "account_service": account_service,
    }


def test_discover_circular_flow_ring(mock_dependencies):
    service = mock_dependencies["service"]
    detection_engine = mock_dependencies["detection_engine"]
    account_service = mock_dependencies["account_service"]

    acc_summaries = [
        AccountSummary(account_id="ACC_RING_1", owner_id="OWN_1", owner_type="PERSON", type="CHECKING", risk_score=85.0, risk_level=RiskLevel.CRITICAL, pagerank=0.045, in_degree=2, out_degree=2, total_degree=4, louvain_community_id=10, total_volume=50000.0, is_frozen=False, last_activity=datetime.now(timezone.utc)),
        AccountSummary(account_id="ACC_RING_2", owner_id="OWN_2", owner_type="PERSON", type="CHECKING", risk_score=80.0, risk_level=RiskLevel.CRITICAL, pagerank=0.045, in_degree=2, out_degree=2, total_degree=4, louvain_community_id=10, total_volume=50000.0, is_frozen=False, last_activity=datetime.now(timezone.utc)),
        AccountSummary(account_id="ACC_RING_3", owner_id="OWN_3", owner_type="PERSON", type="CHECKING", risk_score=75.0, risk_level=RiskLevel.HIGH, pagerank=0.045, in_degree=2, out_degree=2, total_degree=4, louvain_community_id=10, total_volume=50000.0, is_frozen=False, last_activity=datetime.now(timezone.utc)),
    ]
    account_service.list_accounts.return_value = (acc_summaries, 3)

    evidence = DetectionEvidence(
        reason_summary="Wash trading cycle length 3",
        metric_name="cycle_length",
        metric_value=3,
        threshold_value=3,
        source_accounts=["ACC_RING_1"],
        destination_accounts=["ACC_RING_3"],
        path_nodes=["ACC_RING_1", "ACC_RING_2", "ACC_RING_3"],
        cycle_length=3,
    )

    detection_engine.run_all.return_value = [
        DetectionResult(
            detection_id="DET_CIRC_001",
            detection_type=DetectionType.CIRCULAR_FLOW,
            severity=Severity.CRITICAL,
            confidence=0.95,
            primary_account="ACC_RING_1",
            related_accounts=["ACC_RING_2", "ACC_RING_3"],
            description="Circular flow wash trading pattern detected",
            evidence=evidence,
            transaction_ids=["TX_01", "TX_02", "TX_03"],
            total_amount=150000.0,
        )
    ]

    networks = service.discover_networks(force_refresh=True)
    assert len(networks) >= 1
    ring_net = next((n for n in networks if n.network_type == NetworkType.CIRCULAR_RING), None)
    assert ring_net is not None
    assert ring_net.member_count == 3
    assert ring_net.risk_score >= 50.0
    assert any(m.role == NetworkMemberRole.ORIGINATOR for m in ring_net.members)


def test_discover_funnel_consolidation(mock_dependencies):
    service = mock_dependencies["service"]
    detection_engine = mock_dependencies["detection_engine"]
    account_service = mock_dependencies["account_service"]

    acc_summaries = [
        AccountSummary(account_id="ACC_HUB_AGG", owner_id="OWN_H", owner_type="PERSON", type="CHECKING", risk_score=85.0, risk_level=RiskLevel.CRITICAL, pagerank=0.08, in_degree=5, out_degree=1, total_degree=6, louvain_community_id=12, total_volume=300000.0, is_frozen=False, last_activity=datetime.now(timezone.utc)),
        AccountSummary(account_id="ACC_SRC_1", owner_id="OWN_S1", owner_type="PERSON", type="CHECKING", risk_score=70.0, risk_level=RiskLevel.HIGH, pagerank=0.02, in_degree=1, out_degree=1, total_degree=2, louvain_community_id=12, total_volume=100000.0, is_frozen=False, last_activity=datetime.now(timezone.utc)),
        AccountSummary(account_id="ACC_SRC_2", owner_id="OWN_S2", owner_type="PERSON", type="CHECKING", risk_score=72.0, risk_level=RiskLevel.HIGH, pagerank=0.02, in_degree=1, out_degree=1, total_degree=2, louvain_community_id=12, total_volume=100000.0, is_frozen=False, last_activity=datetime.now(timezone.utc)),
    ]
    account_service.list_accounts.return_value = (acc_summaries, 3)

    evidence = DetectionEvidence(
        reason_summary="Fan-in funnel concentration",
        metric_name="fan_in_ratio",
        metric_value=3,
        threshold_value=3,
        source_accounts=["ACC_SRC_1", "ACC_SRC_2"],
        destination_accounts=["ACC_HUB_AGG"],
    )

    detection_engine.run_all.return_value = [
        DetectionResult(
            detection_id="DET_FUNNEL_001",
            detection_type=DetectionType.FUNNEL,
            severity=Severity.HIGH,
            confidence=0.90,
            primary_account="ACC_HUB_AGG",
            related_accounts=["ACC_SRC_1", "ACC_SRC_2"],
            description="Fan-in funnel consolidation pattern detected",
            evidence=evidence,
            transaction_ids=["TX_F1", "TX_F2"],
            total_amount=300000.0,
        )
    ]

    networks = service.discover_networks(force_refresh=True)
    funnel_net = next((n for n in networks if n.network_type == NetworkType.FAN_IN_CONSOLIDATION), None)
    assert funnel_net is not None
    agg_member = next(m for m in funnel_net.members if m.account_id == "ACC_HUB_AGG")
    assert agg_member.role == NetworkMemberRole.AGGREGATOR
