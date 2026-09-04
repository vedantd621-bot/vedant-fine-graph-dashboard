"""
FinGraph Shadow Detection Service.
Coordinates shadow simulation runs, retains historical evaluation logs, and publishes completion events.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid

from backend.app.realtime.event_bus import EventBus
from backend.app.realtime.events import EventType, RealtimeEvent
from backend.app.security.audit import AuditService
from backend.app.shadow_detection.exceptions import (
    SimulationExecutionError,
    SimulationNotFoundError,
)
from backend.app.shadow_detection.models import (
    ShadowSimulationRequest,
    ShadowSimulationResult,
)
from backend.app.shadow_detection.simulator import ShadowDetectorSimulator


class ShadowDetectionService:
    """
    Service managing sandbox detector simulations and historical benchmark results.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self._event_bus = event_bus
        self._audit_service = audit_service
        self._simulator = ShadowDetectorSimulator()
        self._simulation_history: Dict[str, ShadowSimulationResult] = {}

    def _dispatch_event(self, event: RealtimeEvent) -> None:
        if not self._event_bus:
            return
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(self._event_bus.publish(event))
        except RuntimeError:
            pass


    def run_simulation(
        self,
        request: ShadowSimulationRequest,
        user_id: str = "system",
    ) -> ShadowSimulationResult:
        """
        Executes a shadow simulation and registers the result in audit logs and history.
        """
        result = self._simulator.run_simulation(request)
        self._simulation_history[result.simulation_id] = result

        if self._event_bus:
            evt = RealtimeEvent(
                event=EventType.DETECTOR_SHADOW_COMPLETED,
                data={
                    "simulation_id": result.simulation_id,
                    "detector_id": result.detector_id,
                    "alerts_would_fire": result.alerts_would_fire_count,
                    "novel_detections": result.novel_detections_count,
                    "ground_truth_status": result.ground_truth_status.value,
                    "execution_time_ms": result.execution_time_ms,
                }
            )
            self._dispatch_event(evt)

        if self._audit_service:
            self._audit_service.record(
                user_id=user_id,
                action="SHADOW_SIMULATION_EXECUTED",
                resource_type="shadow_simulation",
                resource_id=result.simulation_id,
                new_value=json.dumps({
                    "detector_id": result.detector_id,
                    "window_hours": result.time_window_hours,
                    "alerts_fired": result.alerts_would_fire_count,
                }),
            )

        return result

    def get_simulation(self, simulation_id: str) -> ShadowSimulationResult:
        """Retrieves past simulation result by ID."""
        if simulation_id not in self._simulation_history:
            raise SimulationNotFoundError(f"Simulation '{simulation_id}' not found.")
        return self._simulation_history[simulation_id]

    def list_simulations(self, detector_id: Optional[str] = None) -> List[ShadowSimulationResult]:
        """Lists past simulation results, optionally filtered by detector."""
        sims = list(self._simulation_history.values())
        if detector_id:
            sims = [s for s in sims if s.detector_id == detector_id]
        return sorted(sims, key=lambda x: x.executed_at, reverse=True)


_global_shadow_service: Optional[ShadowDetectionService] = None

def get_shadow_detection_service() -> ShadowDetectionService:
    global _global_shadow_service
    if _global_shadow_service is None:
        from backend.app.realtime.event_bus import get_event_bus
        from backend.app.security.audit import get_audit_service
        _global_shadow_service = ShadowDetectionService(
            event_bus=get_event_bus(),
            audit_service=get_audit_service(),
        )
    return _global_shadow_service
