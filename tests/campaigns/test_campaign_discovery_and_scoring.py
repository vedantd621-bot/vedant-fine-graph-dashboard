"""
Unit tests for CampaignEngine deterministic 6-factor risk scoring.
"""
import pytest
from backend.app.case_intelligence.campaigns import CampaignEngine, FACTOR_WEIGHTS
from backend.app.models.cases import CasePriority, CaseStatus, EvidenceItem, EvidenceType, InvestigationCase


def test_campaign_risk_score_formulation():
    engine = CampaignEngine()

    case_1 = InvestigationCase(
        case_id="CASE-C1",
        title="Syndicate Front",
        description="Front companies moving volume",
        priority=CasePriority.CRITICAL,
        status=CaseStatus.IN_PROGRESS,
        linked_accounts=["A1", "A2"],
        evidence=[
            EvidenceItem(
                evidence_id="E1",
                case_id="CASE-C1",
                type=EvidenceType.GRAPH_PATH,
                source="Neo4j",
                related_entity="A1",
                title="Circular loop",
                created_by="investigator",
            )
        ],
        created_by="investigator",
    )

    case_2 = InvestigationCase(
        case_id="CASE-C2",
        title="Mule Cluster",
        description="Mule cluster receiving dispersion",
        priority=CasePriority.HIGH,
        status=CaseStatus.OPEN,
        linked_accounts=["A2", "A3"],
        evidence=[
            EvidenceItem(
                evidence_id="E2",
                case_id="CASE-C2",
                type=EvidenceType.TRANSACTION,
                source="Kafka",
                related_entity="A2",
                title="Rapid dispersion",
                created_by="investigator",
            )
        ],
        created_by="investigator",
    )

    risk_score, confidence, factors = engine.calculate_campaign_risk(
        cases=[case_1, case_2],
        correlations=[],
        financial_exposure=150000.0,
        network_risk_score=85.0,
    )

    # 1. Bounds verification
    assert 0.0 <= risk_score <= 100.0
    assert 0.0 <= confidence <= 1.0
    assert len(factors) == 6

    # 2. Factor weights sum to 1.0
    total_weight = sum(f.weight for f in factors)
    assert abs(total_weight - 1.0) < 0.001

    # 3. Factor contributions sum to risk_score
    total_contrib = sum(f.contribution for f in factors)
    assert abs(total_contrib - risk_score) < 0.1

    # 4. Check factor names
    factor_names = [f.factor_name for f in factors]
    assert "Network Strength" in factor_names
    assert "Case Correlation" in factor_names
    assert "Financial Exposure" in factor_names
    assert "Behavioral Similarity" in factor_names
    assert "Temporal Concentration" in factor_names
    assert "Evidence Strength" in factor_names
