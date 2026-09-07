"""
Tests for Fraud Decisioning, Human Overrides & What-If Simulation Sandbox.
"""
import pytest
from backend.app.decisioning.exceptions import DecisionNotFoundException
from backend.app.decisioning.models import (
    CreateDecisionRequest, CreateOverrideRequest, DecisionVerdict,
    SimulationParameter, SimulationRequest
)
from backend.app.decisioning.service import DecisionService


@pytest.fixture
def service():
    return DecisionService()


def test_deterministic_decision_verdicts(service):
    # Score >= 85 -> BLOCK
    d_block = service.create_decision(
        CreateDecisionRequest(entity_id="acc_901", risk_score=92.0, contributing_signals=["Loop", "Hub"]),
        tenant_id="tnt_test",
        created_by="tester",
    )
    assert d_block.verdict == DecisionVerdict.BLOCK
    assert "block" in d_block.recommendation.lower()

    # Score >= 70 -> ESCALATE
    d_esc = service.create_decision(
        CreateDecisionRequest(entity_id="acc_902", risk_score=75.0, contributing_signals=["Funnel"]),
        tenant_id="tnt_test",
        created_by="tester",
    )
    assert d_esc.verdict == DecisionVerdict.ESCALATE

    # Score >= 50 -> REVIEW
    d_rev = service.create_decision(
        CreateDecisionRequest(entity_id="acc_903", risk_score=55.0),
        tenant_id="tnt_test",
        created_by="tester",
    )
    assert d_rev.verdict == DecisionVerdict.REVIEW

    # Score < 50 -> ALLOW
    d_allow = service.create_decision(
        CreateDecisionRequest(entity_id="acc_904", risk_score=20.0),
        tenant_id="tnt_test",
        created_by="tester",
    )
    assert d_allow.verdict == DecisionVerdict.ALLOW


def test_human_in_the_loop_override(service):
    d = service.create_decision(
        CreateDecisionRequest(entity_id="acc_910", risk_score=90.0),
        tenant_id="tnt_test",
        created_by="tester",
    )
    assert d.verdict == DecisionVerdict.BLOCK
    assert not d.is_override

    # Apply override
    ovr = service.create_override(
        decision_id=d.decision_id,
        req=CreateOverrideRequest(
            override_verdict=DecisionVerdict.REVIEW,
            reason="Verified VIP commercial account with documented high-volume seasonal payroll",
            evidence_references=["payroll_doc_2026"],
        ),
        tenant_id="tnt_test",
        actor="lead_investigator",
    )
    assert ovr.original_verdict == DecisionVerdict.BLOCK
    assert ovr.override_verdict == DecisionVerdict.REVIEW
    assert ovr.actor == "lead_investigator"

    # Updated decision state
    updated_d = service.get_decision(d.decision_id, "tnt_test")
    assert updated_d.is_override
    assert updated_d.verdict == DecisionVerdict.REVIEW
    assert updated_d.override_reference == ovr.override_id

    # Overrides audit history
    history = service.get_overrides(d.decision_id, "tnt_test")
    assert len(history) == 1
    assert history[0].override_id == ovr.override_id


def test_what_if_simulation_sandbox_safety(service):
    # Record current count
    before_count = len(service.list_decisions("tnt_test"))

    req = SimulationRequest(
        scenario_name="Stress Test Risk Weights",
        description="Hypothetical +20 threshold increase",
        parameters=[
            SimulationParameter(name="risk_threshold", current_value=50, hypothetical_value=70)
        ],
        alert_ids=["alt_1", "alt_2", "alt_3"],
        case_ids=["cas_1"],
    )

    result = service.run_simulation(req, tenant_id="tnt_test", executed_by="tester")

    assert result.is_production_safe is True
    assert result.predicted_risk_change == 20.0
    assert result.predicted_alerts_changed == 3
    assert len(result.recommendation_changes) > 0

    # Verify ZERO production mutation
    after_count = len(service.list_decisions("tnt_test"))
    assert after_count == before_count


def test_decision_tenant_isolation(service):
    d = service.create_decision(
        CreateDecisionRequest(entity_id="acc_isolated", risk_score=80.0),
        tenant_id="tnt_alpha",
        created_by="tester_alpha",
    )
    # Can access in tnt_alpha
    assert service.get_decision(d.decision_id, "tnt_alpha").decision_id == d.decision_id

    # Cannot access from tnt_beta
    with pytest.raises(DecisionNotFoundException):
        service.get_decision(d.decision_id, "tnt_beta")
