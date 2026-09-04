"""
FinGraph Pattern Similarity Formulation.
Computes deterministic structural, entity Jaccard, and signal similarity
between discovered fraud patterns.
"""
from typing import List, Tuple
from backend.app.pattern_discovery.models import (
    DiscoveredPattern,
    PatternSimilarityResponse,
)


class PatternSimilarityEngine:
    """Computes deterministic multi-signal similarity between fraud patterns."""

    def calculate_similarity(
        self,
        p1: DiscoveredPattern,
        p2: DiscoveredPattern,
    ) -> PatternSimilarityResponse:
        """
        Formulation:
        Sim(P1, P2) = 0.40 * Jaccard(Entities) + 0.35 * Jaccard(Signals) + 0.25 * (1 - |Delta Risk|/100)
        """
        e1, e2 = set(p1.affected_entities), set(p2.affected_entities)
        shared_entities = list(e1.intersection(e2))
        union_entities = e1.union(e2)
        jaccard_entities = len(shared_entities) / max(1, len(union_entities)) if union_entities else 0.0

        s1, s2 = set(p1.supporting_signals), set(p2.supporting_signals)
        shared_signals = list(s1.intersection(s2))
        union_signals = s1.union(s2)
        jaccard_signals = len(shared_signals) / max(1, len(union_signals)) if union_signals else (
            1.0 if p1.pattern_type == p2.pattern_type else 0.3
        )

        risk_diff = abs(p1.risk_score - p2.risk_score)
        risk_sim = max(0.0, 1.0 - (risk_diff / 100.0))

        type_bonus = 0.10 if p1.pattern_type == p2.pattern_type else 0.0

        total_sim = round(
            min(1.0, 0.40 * jaccard_entities + 0.35 * jaccard_signals + 0.25 * risk_sim + type_bonus),
            3,
        )

        explanation = (
            f"Pattern similarity index is {total_sim * 100:.1f}% based on "
            f"{len(shared_entities)} shared entity(s) and {len(shared_signals)} overlapping signal(s)."
        )

        return PatternSimilarityResponse(
            pattern_a=p1.pattern_id,
            pattern_b=p2.pattern_b if hasattr(p2, 'pattern_b') else p2.pattern_id,
            similarity_score=total_sim,
            shared_signals=shared_signals,
            shared_entities=shared_entities,
            explanation=explanation,
        )
