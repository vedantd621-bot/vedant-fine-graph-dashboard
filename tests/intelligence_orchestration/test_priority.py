"""
Tests for Investigation Priority Engine in Phase 19.
"""
import pytest
from backend.app.intelligence_orchestration.priority import InvestigationPriorityEngine
from backend.app.intelligence_orchestration.models import PriorityBand

@pytest.fixture
def priority_engine():
    return InvestigationPriorityEngine()

def test_calculate_priority_deterministic(priority_engine):
    score1 = priority_engine.calculate_priority(
        risk_score=85.0,
        financial_exposure=125000.0,
        alert_severity="CRITICAL",
        sla_hours_remaining=2.5,
        threat_propagation_score=82.0,
        has_active_campaign=True
    )
    score2 = priority_engine.calculate_priority(
        risk_score=85.0,
        financial_exposure=125000.0,
        alert_severity="CRITICAL",
        sla_hours_remaining=2.5,
        threat_propagation_score=82.0,
        has_active_campaign=True
    )
    assert score1.priority_score == score2.priority_score
    assert score1.priority_score >= 0.0 and score1.priority_score <= 100.0
    assert score1.priority_band in [PriorityBand.CRITICAL, PriorityBand.HIGH, PriorityBand.MEDIUM, PriorityBand.LOW]
    assert len(score1.factors) == 6
    assert score1.explanation != ""

def test_priority_bands_levels(priority_engine):
    crit = priority_engine.calculate_priority(risk_score=95.0, financial_exposure=200000.0, alert_severity="CRITICAL", sla_hours_remaining=0.5, threat_propagation_score=95.0, has_active_campaign=True)
    assert crit.priority_band == PriorityBand.CRITICAL
    
    low = priority_engine.calculate_priority(risk_score=10.0, financial_exposure=500.0, alert_severity="LOW", sla_hours_remaining=24.0, threat_propagation_score=5.0, has_active_campaign=False)
    assert low.priority_band == PriorityBand.LOW
