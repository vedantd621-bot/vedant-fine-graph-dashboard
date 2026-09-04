"""
FinGraph Threat Propagation Service.
Coordinates propagation simulation, escalates high contagion threats, and publishes real-time telemetry.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from backend.app.realtime.event_bus import EventBus
from backend.app.realtime.events import EventType, RealtimeEvent
from backend.app.security.audit import AuditService
from backend.app.threat_propagation.exceptions import OriginEntityNotFoundError
from backend.app.threat_propagation.models import ThreatPropagationAnalysis
from backend.app.threat_propagation.propagation import ThreatPropagationEngine


class ThreatPropagationService:
    """
    Service managing multi-hop threat propagation simulations and automated containment alerts.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self._event_bus = event_bus
        self._audit_service = audit_service
        self._engine = ThreatPropagationEngine()
        self._analyses: Dict[str, ThreatPropagationAnalysis] = {}

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


    def analyze_entity(
        self,
        origin_entity_id: str,
        max_hops: int = 3,
        time_window_hours: int = 24,
        user_id: str = "system",
    ) -> ThreatPropagationAnalysis:
        """
        Executes propagation analysis from origin entity and publishes real-time events.
        """
        if not origin_entity_id or not origin_entity_id.strip():
            raise OriginEntityNotFoundError("Origin entity ID must not be empty.")

        analysis = self._engine.analyze_propagation(
            origin_entity_id=origin_entity_id,
            max_hops=max_hops,
            time_window_hours=time_window_hours,
        )
        self._analyses[analysis.analysis_id] = analysis

        # Broadcast event
        if self._event_bus:
            evt_type = (
                EventType.THREAT_PROPAGATION_ESCALATED
                if analysis.propagation_score >= 75.0
                else EventType.THREAT_PROPAGATION_DETECTED
            )
            evt = RealtimeEvent(
                event=evt_type,
                data={
                    "analysis_id": analysis.analysis_id,
                    "origin_entity_id": analysis.origin_entity_id,
                    "propagation_score": analysis.propagation_score,
                    "total_affected_entities": analysis.total_affected_entities,
                    "total_exposure": analysis.total_financial_exposure,
                }
            )
            self._dispatch_event(evt)

        # Audit log
        if self._audit_service:
            self._audit_service.record(
                user_id=user_id,
                action="THREAT_PROPAGATION_ANALYSIS_EXECUTED",
                resource_type="threat_propagation",
                resource_id=analysis.analysis_id,
                new_value=json.dumps({
                    "origin_entity_id": analysis.origin_entity_id,
                    "propagation_score": analysis.propagation_score,
                    "affected_entities": analysis.total_affected_entities,
                }),
            )

        return analysis

    def get_analysis(self, analysis_id: str) -> ThreatPropagationAnalysis:
        """Retrieves a past propagation analysis by ID."""
        if analysis_id not in self._analyses:
            raise OriginEntityNotFoundError(f"Propagation analysis '{analysis_id}' not found.")
        return self._analyses[analysis_id]


_global_propagation_service: Optional[ThreatPropagationService] = None

def get_threat_propagation_service() -> ThreatPropagationService:
    global _global_propagation_service
    if _global_propagation_service is None:
        from backend.app.realtime.event_bus import get_event_bus
        from backend.app.security.audit import get_audit_service
        _global_propagation_service = ThreatPropagationService(
            event_bus=get_event_bus(),
            audit_service=get_audit_service(),
        )
    return _global_propagation_service
