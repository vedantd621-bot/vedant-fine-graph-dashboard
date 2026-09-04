"""
Unit tests for Multi-Hop Graph Threat Propagation Explorer.
"""
import pytest
from backend.app.threat_propagation.propagation import ThreatPropagationEngine
from backend.app.threat_propagation.service import ThreatPropagationService
from backend.app.threat_propagation.exceptions import OriginEntityNotFoundError


def test_threat_propagation_engine_multihop():
    engine = ThreatPropagationEngine()
    analysis = engine.analyze_propagation(origin_entity_id="acc_target_99", max_hops=3, time_window_hours=24)

    assert analysis.origin_entity_id == "acc_target_99"
    assert analysis.max_hops == 3
    assert 0.0 <= analysis.propagation_score <= 100.0
    assert analysis.total_affected_entities >= 7
    assert analysis.total_financial_exposure > 50000.0
    assert len(analysis.steps) == 4  # T0, T1, T2, T3
    assert len(analysis.affected_entities_details) == analysis.total_affected_entities
    assert len(analysis.topology.nodes) == analysis.total_affected_entities
    assert len(analysis.topology.edges) >= 6
    assert len(analysis.containment_recommendations) >= 3


def test_threat_propagation_service_validation():
    service = ThreatPropagationService()

    with pytest.raises(OriginEntityNotFoundError):
        service.analyze_entity(origin_entity_id="")

    analysis = service.analyze_entity(origin_entity_id="acc_881", max_hops=2)
    assert analysis.origin_entity_id == "acc_881"

    fetched = service.get_analysis(analysis.analysis_id)
    assert fetched.analysis_id == analysis.analysis_id

    with pytest.raises(OriginEntityNotFoundError):
        service.get_analysis("prop_invalid_000")
