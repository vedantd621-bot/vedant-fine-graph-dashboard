"""
Unit tests for deterministic multi-signal CaseCorrelationEngine.
"""
from datetime import datetime, timezone
import pytest
from backend.app.case_intelligence.correlation import CaseCorrelationEngine
from backend.app.case_intelligence.models import CaseCorrelationSignal
from backend.app.models.cases import CasePriority, CaseStatus, InvestigationCase


def test_case_correlation_shared_accounts():
    engine = CaseCorrelationEngine()

    case_a = InvestigationCase(
        case_id="CASE-001",
        title="Primary Account Ring",
        description="Suspicious activity on A001 and A002",
        priority=CasePriority.HIGH,
        status=CaseStatus.OPEN,
        linked_accounts=["A001", "A002", "A003"],
        created_by="investigator",
    )

    case_b = InvestigationCase(
        case_id="CASE-002",
        title="Mule Operation",
        description="Mule accounts linked to A002",
        priority=CasePriority.HIGH,
        status=CaseStatus.OPEN,
        linked_accounts=["A002", "A004"],
        created_by="investigator",
    )

    case_c = InvestigationCase(
        case_id="CASE-003",
        title="Unrelated Case",
        description="Completely separate accounts",
        priority=CasePriority.LOW,
        status=CaseStatus.OPEN,
        linked_accounts=["A999"],
        created_by="investigator",
    )

    correlations = engine.correlate_cases(case_a, [case_a, case_b, case_c])

    assert len(correlations) >= 1
    # Check that case_b is correlated with case_a via SHARED_ACCOUNT
    account_corrs = [c for c in correlations if c.case_b == "CASE-002" and c.signal_type == CaseCorrelationSignal.SHARED_ACCOUNT]
    assert len(account_corrs) == 1
    assert "A002" in account_corrs[0].common_entities
    assert account_corrs[0].signal_strength > 0.4
    assert account_corrs[0].confidence >= 0.90

    # Ensure case_c is not correlated
    c_corrs = [c for c in correlations if c.case_b == "CASE-003"]
    assert len(c_corrs) == 0


def test_case_correlation_financial_flow():
    engine = CaseCorrelationEngine()

    case_a = InvestigationCase(
        case_id="CASE-010",
        title="Source Ring",
        description="Transactions flow",
        priority=CasePriority.CRITICAL,
        status=CaseStatus.IN_PROGRESS,
        linked_accounts=["A100"],
        linked_transactions=["TX-100", "TX-101"],
        created_by="admin",
    )

    case_b = InvestigationCase(
        case_id="CASE-020",
        title="Destination Sink",
        description="Receiving funds",
        priority=CasePriority.HIGH,
        status=CaseStatus.OPEN,
        linked_accounts=["A200"],
        linked_transactions=["TX-101", "TX-102"],
        created_by="investigator",
    )

    correlations = engine.correlate_cases(case_a, [case_a, case_b])
    flow_corrs = [c for c in correlations if c.signal_type == CaseCorrelationSignal.FINANCIAL_FLOW]
    assert len(flow_corrs) == 1
    assert "TX-101" in flow_corrs[0].common_entities
    assert flow_corrs[0].confidence == 0.98
