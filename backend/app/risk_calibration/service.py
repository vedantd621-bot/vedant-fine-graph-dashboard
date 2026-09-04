"""
FinGraph Risk Calibration Service.
Maintains calibrated risk models, provides threshold analytics, and broadcasts calibration updates.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from backend.app.realtime.event_bus import EventBus
from backend.app.realtime.events import EventType, RealtimeEvent
from backend.app.risk_calibration.calibrator import RiskCalibrator
from backend.app.risk_calibration.models import RiskCalibrationReport
from backend.app.security.audit import AuditService


class RiskCalibrationService:
    """
    Orchestrator for empirical risk score calibration and non-destructive threshold suggestions.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self._event_bus = event_bus
        self._audit_service = audit_service
        self._calibrator = RiskCalibrator()
        self._latest_report: Optional[RiskCalibrationReport] = None

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


    def get_latest_report(self, window_days: int = 30) -> RiskCalibrationReport:
        """Returns the most recent risk calibration report, computing a new one if necessary."""
        if not self._latest_report or self._latest_report.evaluation_window_days != window_days:
            self._latest_report = self._calibrator.generate_calibration_report(window_days=window_days)
        return self._latest_report

    def refresh_calibration(self, window_days: int = 30, user_id: str = "system") -> RiskCalibrationReport:
        """Forces re-computation of empirical calibration matrices and publishes real-time event."""
        report = self._calibrator.generate_calibration_report(window_days=window_days)
        self._latest_report = report

        if self._event_bus:
            evt = RealtimeEvent(
                event=EventType.RISK_CALIBRATION_UPDATED,
                data={
                    "report_id": report.report_id,
                    "window_days": report.evaluation_window_days,
                    "overall_confirmation_rate": report.overall_confirmation_rate,
                    "drift_detected": report.drift_detected,
                    "adjustments_count": len(report.suggested_adjustments),
                }
            )
            self._dispatch_event(evt)

        if self._audit_service:
            self._audit_service.record(
                user_id=user_id,
                action="RISK_CALIBRATION_REFRESHED",
                resource_type="risk_calibration",
                resource_id=report.report_id,
                new_value=json.dumps({
                    "window_days": window_days,
                    "overall_confirmation_rate": report.overall_confirmation_rate,
                }),
            )

        return report


_global_calibration_service: Optional[RiskCalibrationService] = None

def get_risk_calibration_service() -> RiskCalibrationService:
    global _global_calibration_service
    if _global_calibration_service is None:
        from backend.app.realtime.event_bus import get_event_bus
        from backend.app.security.audit import get_audit_service
        _global_calibration_service = RiskCalibrationService(
            event_bus=get_event_bus(),
            audit_service=get_audit_service(),
        )
    return _global_calibration_service
