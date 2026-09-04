"""
Unit tests for Shadow Detector Simulation Sandbox.
"""
import pytest
from backend.app.shadow_detection.models import (
    GroundTruthStatus,
    ShadowSimulationRequest,
)
from backend.app.shadow_detection.simulator import ShadowDetectorSimulator
from backend.app.shadow_detection.service import ShadowDetectionService
from backend.app.shadow_detection.exceptions import SimulationNotFoundError


def test_shadow_simulation_insufficient_ground_truth():
    simulator = ShadowDetectorSimulator()
    req = ShadowSimulationRequest(
        detector_id="det_cycle_smurfing",
        time_window_hours=24,
        parameters={"max_cycle_hops": 4, "time_window_seconds": 60, "min_amount_threshold": 9000.0},
    )
    result = simulator.run_simulation(req, confirmed_labels=None)

    assert result.detector_id == "det_cycle_smurfing"
    assert result.ground_truth_status == GroundTruthStatus.INSUFFICIENT_GROUND_TRUTH
    assert result.estimated_precision is None
    assert result.estimated_recall is None
    assert result.alerts_would_fire_count > 0
    assert result.novel_detections_count > 0
    assert result.estimated_fpr <= 0.05
    assert result.execution_time_ms > 0


def test_shadow_simulation_sufficient_ground_truth():
    simulator = ShadowDetectorSimulator()
    req = ShadowSimulationRequest(
        detector_id="det_cycle_smurfing",
        time_window_hours=48,
        parameters={"max_cycle_hops": 4, "time_window_seconds": 60, "min_amount_threshold": 9000.0},
    )
    labels = [{"id": f"lbl_{i}", "verdict": "CONFIRMED_FRAUD"} for i in range(10)]
    result = simulator.run_simulation(req, confirmed_labels=labels)

    assert result.ground_truth_status == GroundTruthStatus.SUFFICIENT_GROUND_TRUTH
    assert result.estimated_precision is not None
    assert result.estimated_precision > 0.75
    assert result.estimated_recall is not None
    assert result.estimated_recall > 0.80


def test_shadow_service_storage_and_retrieval():
    service = ShadowDetectionService()
    req = ShadowSimulationRequest(
        detector_id="det_rapid_fanout",
        time_window_hours=12,
        parameters={"min_fanout_count": 4},
    )
    res = service.run_simulation(req, user_id="usr_inv_002")
    assert res.simulation_id.startswith("sim_")

    fetched = service.get_simulation(res.simulation_id)
    assert fetched.simulation_id == res.simulation_id
    assert fetched.detector_id == "det_rapid_fanout"

    history = service.list_simulations(detector_id="det_rapid_fanout")
    assert len(history) == 1

    with pytest.raises(SimulationNotFoundError):
        service.get_simulation("sim_nonexistent_999")
