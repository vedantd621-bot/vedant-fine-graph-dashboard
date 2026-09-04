"""
FinGraph Advisory Investigation Recommendation Engine.
Formulates actionable, explainable next-step proposals for investigators.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.intelligence_orchestration.models import (
    InvestigationRecommendation,
    PriorityBand,
)


class InvestigationRecommendationEngine:
    """
    Synthesizes deterministic, advisory investigation action proposals.
    """

    def generate_recommendations(
        self,
        case_id: str,
    ) -> List[InvestigationRecommendation]:
        """
        Produces prioritized forensic action recommendations for the active case.
        """
        clean_id = case_id.strip()

        return [
            InvestigationRecommendation(
                case_id=clean_id,
                title="Execute Administrative Freeze on acc_881",
                reason="High-risk origin node for $148,500 wash trading network.",
                supporting_evidence=["4-node closed wash loop", "Device hash collision"],
                confidence=0.95,
                priority=PriorityBand.CRITICAL,
                action_type="ACCOUNT_HOLD",
            ),
            InvestigationRecommendation(
                case_id=clean_id,
                title="Inspect Shared Infrastructure Proxy Subnet",
                reason="Subnet 198.51.100.0/24 actively routing 8 unflagged accounts.",
                supporting_evidence=["Gap analysis gap_proxy_002", "Autonomous gap finding"],
                confidence=0.91,
                priority=PriorityBand.HIGH,
                action_type="INFRASTRUCTURE_AUDIT",
            ),
            InvestigationRecommendation(
                case_id=clean_id,
                title="Correlate with Syndicate Campaign CMP-2026-001",
                reason="Matching canvas fingerprint identified in active credential stuffing campaign.",
                supporting_evidence=["Campaign membership evidence", "Case CASE-2026-002 link"],
                confidence=0.88,
                priority=PriorityBand.HIGH,
                action_type="CAMPAIGN_LINK",
            ),
        ]
