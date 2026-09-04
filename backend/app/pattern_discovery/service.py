"""
FinGraph Pattern Discovery Service.
Discovers recurring fraud motifs across graph structures, campaigns, and cases.
"""
from datetime import datetime, timezone
import logging
import threading
from typing import Dict, List, Optional

from backend.app.pattern_discovery.exceptions import PatternNotFoundError
from backend.app.pattern_discovery.models import (
    DiscoveredPattern,
    PatternSimilarityResponse,
    PatternType,
)
from backend.app.pattern_discovery.similarity import PatternSimilarityEngine

logger = logging.getLogger("FinGraph.PatternDiscoveryService")


class PatternDiscoveryService:
    """Manages discovered fraud patterns and similarity calculations."""

    def __init__(self):
        self._lock = threading.RLock()
        self._similarity_engine = PatternSimilarityEngine()
        self._patterns: Dict[str, DiscoveredPattern] = {}
        self._seed_default_patterns()

    def _seed_default_patterns(self):
        """Seeds realistic initial recurring fraud motifs."""
        with self._lock:
            p1 = DiscoveredPattern(
                pattern_id="PAT-CIRCULAR-01",
                name="4-Node Cyclic Wash Trading Motif",
                pattern_type=PatternType.CIRCULAR_LOOP,
                frequency=12,
                confidence=0.96,
                risk_score=92.0,
                affected_entities=["A001", "A002", "A003", "A004"],
                financial_exposure=148000.0,
                explanation="Closed directed graph cycle moving high-velocity funds with >95% round-trip retention.",
                supporting_signals=[
                    "Rotational invariant cycle fingerprint match",
                    "Velocity surge (<10 min turnarounds)",
                    "Shared beneficial owner infrastructure",
                ],
                related_cases=["CASE-2026-001"],
                related_campaigns=["CMP-2026-001"],
                related_networks=["NET-001"],
            )

            p2 = DiscoveredPattern(
                pattern_id="PAT-FUNNEL-01",
                name="Multi-Inflow Mule Aggregation Motif",
                pattern_type=PatternType.MULTI_INFLOW_FUNNEL,
                frequency=8,
                confidence=0.88,
                risk_score=82.5,
                affected_entities=["A015", "A010", "A011", "A012"],
                financial_exposure=48000.0,
                explanation="Rapid funnel dispersion consolidating micro-deposits from multiple origin accounts into a single hub.",
                supporting_signals=[
                    "Fan-in ratio > 3.0",
                    "Rapid subsequent outflow to external counterparty",
                    "Statistical behavioral baseline deviation",
                ],
                related_cases=["CASE-2026-002"],
                related_campaigns=["CMP-2026-001"],
                related_networks=["NET-001"],
            )

            self._patterns[p1.pattern_id] = p1
            self._patterns[p2.pattern_id] = p2

    def list_patterns(self, pattern_type: Optional[PatternType] = None) -> List[DiscoveredPattern]:
        """Lists discovered patterns with optional type filter."""
        with self._lock:
            patterns = list(self._patterns.values())
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        patterns.sort(key=lambda x: x.risk_score, reverse=True)
        return patterns

    def get_pattern(self, pattern_id: str) -> DiscoveredPattern:
        """Retrieves a single pattern record by ID."""
        with self._lock:
            p = self._patterns.get(pattern_id)
        if not p:
            raise PatternNotFoundError(f"Pattern {pattern_id} not found")
        return p

    def get_similar_patterns(self, pattern_id: str) -> List[PatternSimilarityResponse]:
        """Finds and compares structurally similar patterns to pattern_id."""
        target = self.get_pattern(pattern_id)
        all_patterns = self.list_patterns()

        results: List[PatternSimilarityResponse] = []
        for candidate in all_patterns:
            if candidate.pattern_id == pattern_id:
                continue
            sim = self._similarity_engine.calculate_similarity(target, candidate)
            results.append(sim)

        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results


_global_pattern_discovery_service: Optional[PatternDiscoveryService] = None


def get_pattern_discovery_service() -> PatternDiscoveryService:
    """Singleton getter for PatternDiscoveryService."""
    global _global_pattern_discovery_service
    if _global_pattern_discovery_service is None:
        _global_pattern_discovery_service = PatternDiscoveryService()
    return _global_pattern_discovery_service
