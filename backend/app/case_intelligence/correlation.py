"""
FinGraph Multi-Signal Case Correlation Engine.
Performs deterministic cross-case correlation matching shared accounts,
counterparties, fraud networks, detector patterns, behavioral anomalies,
and temporal proximity.
"""
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Set

from backend.app.case_intelligence.models import (
    CaseCorrelation,
    CaseCorrelationSignal,
)
from backend.app.models.cases import InvestigationCase

logger = logging.getLogger("FinGraph.CaseCorrelationEngine")


class CaseCorrelationEngine:
    """Computes explainable, multi-factor correlation links between cases."""

    def __init__(self):
        pass

    def correlate_cases(
        self,
        target_case: InvestigationCase,
        all_cases: List[InvestigationCase],
        min_signal_strength: float = 0.35,
    ) -> List[CaseCorrelation]:
        """Discovers and scores correlation links between target_case and other cases."""
        correlations: List[CaseCorrelation] = []
        target_accs = set(target_case.linked_accounts)
        target_alerts = set(target_case.linked_alerts)
        target_txs = set(target_case.linked_transactions)

        for candidate in all_cases:
            if candidate.case_id == target_case.case_id:
                continue

            cand_accs = set(candidate.linked_accounts)
            cand_alerts = set(candidate.linked_alerts)
            cand_txs = set(candidate.linked_transactions)

            # 1. Shared Accounts Signal
            shared_accs = target_accs.intersection(cand_accs)
            if shared_accs:
                ratio = len(shared_accs) / max(1, min(len(target_accs), len(cand_accs)))
                strength = min(1.0, 0.40 + 0.60 * ratio)
                if strength >= min_signal_strength:
                    correlations.append(
                        CaseCorrelation(
                            case_a=target_case.case_id,
                            case_b=candidate.case_id,
                            signal_type=CaseCorrelationSignal.SHARED_ACCOUNT,
                            signal_strength=round(strength, 3),
                            confidence=0.95,
                            explanation=f"Shares {len(shared_accs)} account(s): {', '.join(sorted(shared_accs)[:5])}",
                            common_entities=list(sorted(shared_accs)),
                        )
                    )

            # 2. Shared Transactions / Counterparty Flow
            shared_txs = target_txs.intersection(cand_txs)
            if shared_txs:
                strength = min(1.0, 0.60 + 0.40 * (len(shared_txs) / max(1, len(target_txs))))
                if strength >= min_signal_strength:
                    correlations.append(
                        CaseCorrelation(
                            case_a=target_case.case_id,
                            case_b=candidate.case_id,
                            signal_type=CaseCorrelationSignal.FINANCIAL_FLOW,
                            signal_strength=round(strength, 3),
                            confidence=0.98,
                            explanation=f"Shares {len(shared_txs)} direct transaction(s): {', '.join(sorted(shared_txs)[:3])}",
                            common_entities=list(sorted(shared_txs)),
                        )
                    )

            # 3. Shared Alert Topology / Detector Clustering
            shared_alerts = target_alerts.intersection(cand_alerts)
            if shared_alerts:
                strength = min(1.0, 0.50 + 0.50 * (len(shared_alerts) / max(1, len(target_alerts))))
                if strength >= min_signal_strength:
                    correlations.append(
                        CaseCorrelation(
                            case_a=target_case.case_id,
                            case_b=candidate.case_id,
                            signal_type=CaseCorrelationSignal.SHARED_DETECTOR,
                            signal_strength=round(strength, 3),
                            confidence=0.90,
                            explanation=f"Shares {len(shared_alerts)} alert trigger(s): {', '.join(sorted(shared_alerts)[:3])}",
                            common_entities=list(sorted(shared_alerts)),
                        )
                    )

            # 4. Temporal Proximity Clustering (<48 hours between case creation)
            time_diff_hours = abs((target_case.created_at - candidate.created_at).total_seconds()) / 3600.0
            if time_diff_hours <= 48.0 and (shared_accs or shared_alerts or shared_txs):
                temporal_strength = max(0.0, 1.0 - (time_diff_hours / 48.0)) * 0.8
                if temporal_strength >= min_signal_strength:
                    correlations.append(
                        CaseCorrelation(
                            case_a=target_case.case_id,
                            case_b=candidate.case_id,
                            signal_type=CaseCorrelationSignal.TEMPORAL_CLUSTERING,
                            signal_strength=round(temporal_strength, 3),
                            confidence=0.85,
                            explanation=f"Cases initiated within {time_diff_hours:.1f} hours of each other with intersecting entities.",
                            common_entities=list(sorted(shared_accs.union(shared_alerts))),
                        )
                    )

        # Sort correlations by signal strength descending
        correlations.sort(key=lambda x: x.signal_strength, reverse=True)
        return correlations
