"""
FinGraph Central Intelligence Orchestrator.
Coordinates fraud detection, risk scoring, network evolution, case intelligence, decisioning,
early warnings, threat propagation, and adaptive recommendations without duplicating algorithms.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.intelligence_orchestration.brief import InvestigationBriefGenerator
from backend.app.intelligence_orchestration.correlation import CrossAlertCorrelationEngine
from backend.app.intelligence_orchestration.evidence import EvidenceRankingEngine
from backend.app.intelligence_orchestration.models import (
    CorrelationGroup,
    InvestigationBrief,
    InvestigationPriorityScore,
    InvestigationRecommendation,
    RankedEvidenceItem,
    RelatedCase,
    UnifiedTimelineEvent,
)
from backend.app.intelligence_orchestration.priority import InvestigationPriorityEngine
from backend.app.intelligence_orchestration.recommendations import InvestigationRecommendationEngine
from backend.app.intelligence_orchestration.related_cases import RelatedCaseDiscoveryEngine
from backend.app.intelligence_orchestration.tasks import InvestigationTaskManager
from backend.app.intelligence_orchestration.timeline import UnifiedTimelineEngine
from backend.app.intelligence_orchestration.workflows import (
    WorkflowStateMachine,
    WorkflowTemplateRegistry,
)


class IntelligenceOrchestrator:
    """
    Central orchestration facade unifying all platform intelligence layers.
    """

    def __init__(self):
        self._correlation_engine = CrossAlertCorrelationEngine()
        self._priority_engine = InvestigationPriorityEngine()
        self._evidence_engine = EvidenceRankingEngine()
        self._brief_generator = InvestigationBriefGenerator()
        self._template_registry = WorkflowTemplateRegistry()
        self._state_machine = WorkflowStateMachine()
        self._task_manager = InvestigationTaskManager()
        self._timeline_engine = UnifiedTimelineEngine()
        self._related_cases_engine = RelatedCaseDiscoveryEngine()
        self._recommendation_engine = InvestigationRecommendationEngine()

    @property
    def correlation_engine(self) -> CrossAlertCorrelationEngine:
        return self._correlation_engine

    @property
    def priority_engine(self) -> InvestigationPriorityEngine:
        return self._priority_engine

    @property
    def evidence_engine(self) -> EvidenceRankingEngine:
        return self._evidence_engine

    @property
    def brief_generator(self) -> InvestigationBriefGenerator:
        return self._brief_generator

    @property
    def template_registry(self) -> WorkflowTemplateRegistry:
        return self._template_registry

    @property
    def state_machine(self) -> WorkflowStateMachine:
        return self._state_machine

    @property
    def task_manager(self) -> InvestigationTaskManager:
        return self._task_manager

    @property
    def timeline_engine(self) -> UnifiedTimelineEngine:
        return self._timeline_engine

    @property
    def related_cases_engine(self) -> RelatedCaseDiscoveryEngine:
        return self._related_cases_engine

    @property
    def recommendation_engine(self) -> InvestigationRecommendationEngine:
        return self._recommendation_engine
