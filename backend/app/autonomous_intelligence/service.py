"""
FinGraph Autonomous Fraud Intelligence Orchestration Service.
Manages discovery lifecycle, human review workflow, detector versions, and event publishing.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid

from backend.app.autonomous_intelligence.exceptions import (
    GapNotFoundError,
    InvalidStatusTransitionError,
    RecommendationNotFoundError,
    DetectorVersionNotFoundError,
)
from backend.app.autonomous_intelligence.models import (
    AutonomousIntelligenceSummary,
    DetectionGap,
    DetectorRecommendation,
    DetectorVersion,
    RecommendationReviewRequest,
    RecommendationStatus,
    StatusHistoryEntry,
    VersionStatus,
)
from backend.app.autonomous_intelligence.recommendations import AdaptiveRecommendationEngine
from backend.app.autonomous_intelligence.signals import DetectionGapFinder
from backend.app.realtime.event_bus import EventBus
from backend.app.realtime.events import EventType, RealtimeEvent
from backend.app.security.audit import AuditService


class AutonomousIntelligenceService:
    """
    Central service for autonomous fraud discovery, adaptive recommendation management,
    and detector version control.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self._event_bus = event_bus
        self._audit_service = audit_service
        self._gap_finder = DetectionGapFinder()
        self._rec_engine = AdaptiveRecommendationEngine()

        self._gaps: Dict[str, DetectionGap] = {}
        self._recommendations: Dict[str, DetectorRecommendation] = {}
        self._detector_versions: Dict[str, DetectorVersion] = {}

        self._seed_initial_state()

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


    def _seed_initial_state(self) -> None:
        """Populates baseline gaps, recommendations, and active detector versions."""
        initial_gaps = self._gap_finder.scan_gaps()
        for g in initial_gaps:
            self._gaps[g.gap_id] = g

        initial_recs = self._rec_engine.generate_recommendations(initial_gaps)
        for r in initial_recs:
            self._recommendations[r.recommendation_id] = r

        v1 = DetectorVersion(
            version_id="ver_cycle_v1",
            detector_id="det_cycle_smurfing",
            version_number="1.2.0",
            parameters={"max_cycle_hops": 3, "time_window_seconds": 300, "min_amount_threshold": 10000.0},
            status=VersionStatus.ACTIVE,
            created_by="system",
            change_rationale="Initial baseline production release",
        )
        v2 = DetectorVersion(
            version_id="ver_fanout_v1",
            detector_id="det_rapid_fanout",
            version_number="1.1.0",
            parameters={"min_fanout_count": 5, "time_window_seconds": 180},
            status=VersionStatus.ACTIVE,
            created_by="system",
            change_rationale="Initial baseline production release",
        )
        self._detector_versions[v1.version_id] = v1
        self._detector_versions[v2.version_id] = v2

    def list_gaps(self, priority: Optional[str] = None) -> List[DetectionGap]:
        """Returns active detection gaps, optionally filtered by priority."""
        gaps = list(self._gaps.values())
        if priority:
            gaps = [g for g in gaps if g.priority.value.upper() == priority.upper()]
        return sorted(gaps, key=lambda x: x.estimated_financial_exposure, reverse=True)

    def get_gap(self, gap_id: str) -> DetectionGap:
        """Retrieves a single detection gap by ID."""
        if gap_id not in self._gaps:
            raise GapNotFoundError(f"Detection gap '{gap_id}' was not found.")
        return self._gaps[gap_id]

    def trigger_gap_scan(self, user_id: str = "system") -> List[DetectionGap]:
        """Runs the detection gap analyzer and broadcasts discovered gaps."""
        fresh_gaps = self._gap_finder.scan_gaps()
        for g in fresh_gaps:
            self._gaps[g.gap_id] = g
            if self._event_bus:
                evt = RealtimeEvent(
                    event=EventType.DETECTION_GAP_DETECTED,
                    data={
                        "gap_id": g.gap_id,
                        "title": g.title,
                        "pattern_type": g.pattern_type.value,
                        "priority": g.priority.value,
                        "exposure": g.estimated_financial_exposure,
                        "uncovered_motifs": g.uncovered_motif_count,
                    }
                )
                self._dispatch_event(evt)

        new_recs = self._rec_engine.generate_recommendations(fresh_gaps)
        for r in new_recs:
            if r.recommendation_id not in self._recommendations:
                self._recommendations[r.recommendation_id] = r
                if self._event_bus:
                    evt_rec = RealtimeEvent(
                        event=EventType.DETECTION_RECOMMENDATION_CREATED,
                        data={
                            "recommendation_id": r.recommendation_id,
                            "title": r.title,
                            "recommendation_type": r.recommendation_type.value,
                            "confidence": r.confidence_score,
                            "target_detector": r.target_detector_id,
                        }
                    )
                    self._dispatch_event(evt_rec)

        if self._audit_service:
            self._audit_service.record(
                user_id=user_id,
                action="AUTONOMOUS_GAP_SCAN_TRIGGERED",
                resource_type="detection_gap",
                resource_id="scan_batch",
                new_value=json.dumps({"gaps_found": len(fresh_gaps)}),
            )

        return fresh_gaps

    def list_recommendations(
        self,
        status: Optional[str] = None,
        rec_type: Optional[str] = None,
    ) -> List[DetectorRecommendation]:
        """Lists adaptive detector recommendations with optional filtering."""
        recs = list(self._recommendations.values())
        if status:
            recs = [r for r in recs if r.status.value.upper() == status.upper()]
        if rec_type:
            recs = [r for r in recs if r.recommendation_type.value.upper() == rec_type.upper()]
        return sorted(recs, key=lambda x: x.created_at, reverse=True)

    def get_recommendation(self, recommendation_id: str) -> DetectorRecommendation:
        """Retrieves a single detector recommendation by ID."""
        if recommendation_id not in self._recommendations:
            raise RecommendationNotFoundError(f"Recommendation '{recommendation_id}' was not found.")
        return self._recommendations[recommendation_id]

    def review_recommendation(
        self,
        recommendation_id: str,
        request: RecommendationReviewRequest,
        reviewer_id: str,
    ) -> DetectorRecommendation:
        """
        Transitions recommendation through human review lifecycle:
        PROPOSED -> UNDER_REVIEW -> APPROVED / REJECTED -> DEPLOYED
        """
        rec = self.get_recommendation(recommendation_id)
        from_status = rec.status.value
        to_status = request.status.value

        valid_transitions = {
            RecommendationStatus.PROPOSED: [RecommendationStatus.UNDER_REVIEW, RecommendationStatus.REJECTED, RecommendationStatus.APPROVED],
            RecommendationStatus.UNDER_REVIEW: [RecommendationStatus.APPROVED, RecommendationStatus.REJECTED, RecommendationStatus.PROPOSED],
            RecommendationStatus.APPROVED: [RecommendationStatus.DEPLOYED, RecommendationStatus.REJECTED, RecommendationStatus.UNDER_REVIEW],
            RecommendationStatus.REJECTED: [RecommendationStatus.UNDER_REVIEW, RecommendationStatus.PROPOSED],
            RecommendationStatus.DEPLOYED: [],
        }

        if request.status not in valid_transitions.get(rec.status, []):
            raise InvalidStatusTransitionError(
                f"Cannot transition recommendation from '{rec.status.value}' to '{request.status.value}'."
            )

        if request.override_parameters:
            rec.suggested_parameters.update(request.override_parameters)

        rec.status = request.status
        rec.reviewed_by = reviewer_id
        rec.reviewed_at = datetime.now(timezone.utc)

        history_entry = StatusHistoryEntry(
            from_status=from_status,
            to_status=to_status,
            transitioned_by=reviewer_id,
            reason=request.notes,
        )
        rec.status_history.append(history_entry)

        if request.status == RecommendationStatus.DEPLOYED:
            rec.deployed_at = datetime.now(timezone.utc)
            new_version = DetectorVersion(
                detector_id=rec.target_detector_id or "det_custom_rule",
                version_number=f"2.{len(self._detector_versions) + 1}.0",
                parameters=rec.suggested_parameters,
                status=VersionStatus.ACTIVE,
                created_by=reviewer_id,
                change_rationale=f"Deployed from approved recommendation {rec.recommendation_id}: {request.notes or rec.description}",
                recommendation_id=rec.recommendation_id,
            )
            self._detector_versions[new_version.version_id] = new_version

        if self._event_bus:
            evt_type = (
                EventType.DETECTION_RECOMMENDATION_APPROVED
                if request.status == RecommendationStatus.APPROVED
                else EventType.DETECTION_RECOMMENDATION_REJECTED
                if request.status == RecommendationStatus.REJECTED
                else EventType.ALERT_UPDATED
            )
            evt = RealtimeEvent(
                event=evt_type,
                data={
                    "recommendation_id": rec.recommendation_id,
                    "status": rec.status.value,
                    "reviewer": reviewer_id,
                    "notes": request.notes,
                }
            )
            self._dispatch_event(evt)

        if self._audit_service:
            self._audit_service.record(
                user_id=reviewer_id,
                action=f"RECOMMENDATION_{request.status.value}",
                resource_type="detector_recommendation",
                resource_id=rec.recommendation_id,
                old_value=json.dumps({"status": from_status}),
                new_value=json.dumps({"status": to_status, "notes": request.notes}),
            )

        return rec

    def list_detector_versions(self, detector_id: Optional[str] = None) -> List[DetectorVersion]:
        """Lists registered detector versions."""
        versions = list(self._detector_versions.values())
        if detector_id:
            versions = [v for v in versions if v.detector_id == detector_id]
        return sorted(versions, key=lambda x: x.created_at, reverse=True)

    def get_summary(self) -> AutonomousIntelligenceSummary:
        """Aggregates executive autonomous intelligence status."""
        gaps = list(self._gaps.values())
        recs = list(self._recommendations.values())
        highest_gap = max(gaps, key=lambda x: x.estimated_financial_exposure) if gaps else None

        return AutonomousIntelligenceSummary(
            active_gaps_count=len([g for g in gaps if g.status == "OPEN"]),
            pending_recommendations_count=len([r for r in recs if r.status in (RecommendationStatus.PROPOSED, RecommendationStatus.UNDER_REVIEW)]),
            approved_recommendations_count=len([r for r in recs if r.status in (RecommendationStatus.APPROVED, RecommendationStatus.DEPLOYED)]),
            active_detector_versions_count=len([v for v in self._detector_versions.values() if v.status == VersionStatus.ACTIVE]),
            highest_priority_gap=highest_gap,
            recent_recommendations=sorted(recs, key=lambda x: x.created_at, reverse=True)[:5],
        )


_global_autonomous_service: Optional[AutonomousIntelligenceService] = None

def get_autonomous_intelligence_service() -> AutonomousIntelligenceService:
    global _global_autonomous_service
    if _global_autonomous_service is None:
        from backend.app.realtime.event_bus import get_event_bus
        from backend.app.security.audit import get_audit_service
        _global_autonomous_service = AutonomousIntelligenceService(
            event_bus=get_event_bus(),
            audit_service=get_audit_service(),
        )
    return _global_autonomous_service
