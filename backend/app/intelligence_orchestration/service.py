"""
FinGraph Intelligence Orchestration Service.
Provides caching, idempotency, event broadcasting, and audit logging for orchestration workflows.
"""
import asyncio
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid

from backend.app.intelligence_orchestration.exceptions import (
    InvalidWorkflowTransitionError,
    TaskNotFoundError,
    TemplateNotFoundError,
)
from backend.app.intelligence_orchestration.models import (
    CaseChecklistItem,
    ChecklistItemCreateRequest,
    ChecklistItemUpdateRequest,
    CorrelationGroup,
    InvestigationBrief,
    InvestigationPriorityScore,
    InvestigationRecommendation,
    InvestigationTask,
    InvestigationWorkflowTemplate,
    RankedEvidenceItem,
    RelatedCase,
    TaskCreateRequest,
    TaskUpdateRequest,
    UnifiedTimelineEvent,
    WorkflowState,
    WorkflowStateTransitionRequest,
)
from backend.app.intelligence_orchestration.orchestrator import IntelligenceOrchestrator
from backend.app.realtime.event_bus import EventBus
from backend.app.realtime.events import EventType, RealtimeEvent
from backend.app.security.audit import AuditService


class IntelligenceOrchestrationService:
    """
    Central orchestration service managing investigation workflows, briefs, tasks, and real-time events.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self._event_bus = event_bus
        self._audit_service = audit_service
        self._orchestrator = IntelligenceOrchestrator()

        # Cache for deterministic read-heavy assets
        self._brief_cache: Dict[str, InvestigationBrief] = {}
        self._case_states: Dict[str, WorkflowState] = {
            "CASE-2026-001": WorkflowState.INVESTIGATING,
            "CASE-2026-002": WorkflowState.INVESTIGATING,
        }

    def _dispatch_event(self, event: RealtimeEvent) -> None:
        if not self._event_bus:
            return
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(self._event_bus.publish(event))
        except RuntimeError:
            pass

    def correlate_alert(self, alert_id: str) -> CorrelationGroup:
        """Computes multi-signal explainable alert correlation and broadcasts event."""
        group = self._orchestrator.correlation_engine.correlate_alert(alert_id)
        
        evt = RealtimeEvent(
            event=EventType.CORRELATION_CREATED,
            data={
                "group_id": group.group_id,
                "primary_alert_id": group.primary_alert_id,
                "correlated_count": len(group.correlated_alert_ids),
                "score": group.correlation_score,
            }
        )
        self._dispatch_event(evt)
        return group

    def calculate_priority(
        self,
        risk_score: float = 85.0,
        financial_exposure: float = 125000.0,
        alert_severity: str = "CRITICAL",
        sla_hours_remaining: float = 2.5,
        threat_propagation_score: float = 82.0,
        has_active_campaign: bool = True,
    ) -> InvestigationPriorityScore:
        """Calculates deterministic investigation priority score."""
        score = self._orchestrator.priority_engine.calculate_priority(
            risk_score=risk_score,
            financial_exposure=financial_exposure,
            alert_severity=alert_severity,
            sla_hours_remaining=sla_hours_remaining,
            threat_propagation_score=threat_propagation_score,
            has_active_campaign=has_active_campaign,
        )
        evt = RealtimeEvent(
            event=EventType.PRIORITY_UPDATED,
            data={
                "priority_score": score.priority_score,
                "priority_band": score.priority_band.value,
            }
        )
        self._dispatch_event(evt)
        return score

    def rank_evidence(self, case_id: str) -> List[RankedEvidenceItem]:
        """Ranks multi-category forensic evidence for a case."""
        return self._orchestrator.evidence_engine.rank_evidence_for_case(case_id)

    def generate_brief(self, case_or_alert_id: str, force_refresh: bool = False) -> InvestigationBrief:
        """Synthesizes or retrieves cached investigation brief."""
        if not force_refresh and case_or_alert_id in self._brief_cache:
            return self._brief_cache[case_or_alert_id]

        brief = self._orchestrator.brief_generator.generate_brief(case_or_alert_id)
        self._brief_cache[case_or_alert_id] = brief

        evt = RealtimeEvent(
            event=EventType.INVESTIGATION_BRIEF_READY,
            data={
                "brief_id": brief.brief_id,
                "case_or_alert_id": brief.case_or_alert_id,
                "priority": brief.priority_assessment.priority_band.value,
                "exposure": brief.financial_exposure,
            }
        )
        self._dispatch_event(evt)
        return brief

    def list_templates(self) -> List[InvestigationWorkflowTemplate]:
        """Lists procedural workflow templates."""
        return self._orchestrator.template_registry.list_templates()

    def get_template(self, template_id: str) -> InvestigationWorkflowTemplate:
        """Retrieves a single workflow template by ID."""
        return self._orchestrator.template_registry.get_template(template_id)

    def transition_workflow_state(
        self,
        case_id: str,
        request: WorkflowStateTransitionRequest,
        actor_id: str,
    ) -> WorkflowState:
        """Enforces legal workflow state transition with audit trail."""
        current_state = self._case_states.get(case_id, WorkflowState.CREATED)
        self._orchestrator.state_machine.validate_transition(current_state, request.to_state)

        self._case_states[case_id] = request.to_state

        if self._audit_service:
            self._audit_service.record(
                user_id=actor_id,
                action="WORKFLOW_STATE_TRANSITION",
                resource_type="case_workflow",
                resource_id=case_id,
                old_value=json.dumps({"state": current_state.value}),
                new_value=json.dumps({"state": request.to_state.value, "notes": request.notes}),
            )

        evt = RealtimeEvent(
            event=EventType.WORKFLOW_STATE_CHANGED,
            data={
                "case_id": case_id,
                "from_state": current_state.value,
                "to_state": request.to_state.value,
                "actor": actor_id,
                "notes": request.notes,
            }
        )
        self._dispatch_event(evt)
        return request.to_state

    def get_case_state(self, case_id: str) -> WorkflowState:
        """Gets current workflow state for a case."""
        return self._case_states.get(case_id, WorkflowState.CREATED)

    def create_task(self, request: TaskCreateRequest, creator_id: str) -> InvestigationTask:
        """Creates and assigns an investigation task."""
        task = self._orchestrator.task_manager.create_task(request, creator_id)

        if self._audit_service:
            self._audit_service.record(
                user_id=creator_id,
                action="TASK_CREATED",
                resource_type="investigation_task",
                resource_id=task.task_id,
                new_value=json.dumps({"case_id": task.case_id, "title": task.title, "assignee": task.assignee}),
            )

        evt = RealtimeEvent(
            event=EventType.TASK_CREATED,
            data={
                "task_id": task.task_id,
                "case_id": task.case_id,
                "title": task.title,
                "assignee": task.assignee,
                "priority": task.priority.value,
            }
        )
        self._dispatch_event(evt)
        return task

    def update_task(self, task_id: str, request: TaskUpdateRequest, actor_id: str) -> InvestigationTask:
        """Updates task state or assignee with audit trail."""
        old_task = self._orchestrator.task_manager.get_task(task_id)
        old_status = old_task.status.value

        updated = self._orchestrator.task_manager.update_task(task_id, request, actor_id)

        if self._audit_service:
            self._audit_service.record(
                user_id=actor_id,
                action="TASK_UPDATED",
                resource_type="investigation_task",
                resource_id=task_id,
                old_value=json.dumps({"status": old_status}),
                new_value=json.dumps({"status": updated.status.value, "assignee": updated.assignee}),
            )

        evt_type = EventType.TASK_COMPLETED if updated.status.value == "COMPLETED" else EventType.TASK_ASSIGNED
        evt = RealtimeEvent(
            event=evt_type,
            data={
                "task_id": updated.task_id,
                "status": updated.status.value,
                "assignee": updated.assignee,
            }
        )
        self._dispatch_event(evt)
        return updated

    def list_tasks(
        self,
        case_id: Optional[str] = None,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[InvestigationTask]:
        """Lists investigation tasks with filtering."""
        return self._orchestrator.task_manager.list_tasks(case_id=case_id, assignee=assignee, status=status)

    def get_task(self, task_id: str) -> InvestigationTask:
        """Gets a single task by ID."""
        return self._orchestrator.task_manager.get_task(task_id)

    def get_checklist(self, case_id: str) -> List[CaseChecklistItem]:
        """Retrieves checklist for a case."""
        return self._orchestrator.task_manager.get_checklist(case_id)

    def add_checklist_item(self, case_id: str, request: ChecklistItemCreateRequest, actor_id: str) -> CaseChecklistItem:
        """Adds an item to case checklist."""
        item = self._orchestrator.task_manager.add_checklist_item(case_id, request)
        if self._audit_service:
            self._audit_service.record(
                user_id=actor_id,
                action="CHECKLIST_ITEM_ADDED",
                resource_type="case_checklist",
                resource_id=item.item_id,
                new_value=json.dumps({"case_id": case_id, "title": item.title}),
            )
        return item

    def update_checklist_item(
        self,
        case_id: str,
        item_id: str,
        request: ChecklistItemUpdateRequest,
        actor_id: str,
    ) -> CaseChecklistItem:
        """Marks a checklist item complete or incomplete."""
        item = self._orchestrator.task_manager.update_checklist_item(case_id, item_id, request, actor_id)
        if self._audit_service:
            self._audit_service.record(
                user_id=actor_id,
                action="CHECKLIST_ITEM_TOGGLED",
                resource_type="case_checklist",
                resource_id=item_id,
                new_value=json.dumps({"case_id": case_id, "is_completed": item.is_completed}),
            )
        return item

    def generate_timeline(self, case_or_entity_id: str, limit: int = 50) -> List[UnifiedTimelineEvent]:
        """Generates unified forensic timeline."""
        return self._orchestrator.timeline_engine.generate_timeline(case_or_entity_id, limit=limit)

    def discover_related_cases(self, case_id: str) -> List[RelatedCase]:
        """Discovers linked cases based on shared signals."""
        return self._orchestrator.related_cases_engine.discover_related_cases(case_id)

    def generate_recommendations(self, case_id: str) -> List[InvestigationRecommendation]:
        """Generates advisory investigation next-step recommendations."""
        recs = self._orchestrator.recommendation_engine.generate_recommendations(case_id)
        for r in recs:
            evt = RealtimeEvent(
                event=EventType.RECOMMENDATION_CREATED,
                data={
                    "recommendation_id": r.recommendation_id,
                    "case_id": r.case_id,
                    "title": r.title,
                    "priority": r.priority.value,
                }
            )
            self._dispatch_event(evt)
        return recs


_global_orchestration_service: Optional[IntelligenceOrchestrationService] = None


def get_intelligence_orchestration_service() -> IntelligenceOrchestrationService:
    global _global_orchestration_service
    if _global_orchestration_service is None:
        from backend.app.realtime.event_bus import get_event_bus
        from backend.app.security.audit import get_audit_service
        _global_orchestration_service = IntelligenceOrchestrationService(
            event_bus=get_event_bus(),
            audit_service=get_audit_service(),
        )
    return _global_orchestration_service
