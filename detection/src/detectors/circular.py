"""
FinGraph Circular Flow / Wash Trading Loop Detector.
Detects closed-loop transaction cycles (A -> B -> C -> A) with canonical rotational deduplication.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from neo4j.src.client import Neo4jClient
from detection.src.detectors.base import BaseDetector
from detection.src.models import (
    DetectionEvidence,
    DetectionResult,
    DetectionType,
    Severity,
    generate_fingerprint,
)


def canonicalize_cycle(cycle_nodes: List[str]) -> Tuple[List[str], str]:
    """
    Normalizes a cycle path to a canonical rotation by placing the lexicographically
    smallest node ID at the first position.
    Example: ['B', 'C', 'A', 'B'] -> (['A', 'B', 'C', 'A'], 'A-B-C')
    """
    if not cycle_nodes or cycle_nodes[0] != cycle_nodes[-1]:
        return cycle_nodes, "-".join(cycle_nodes)

    inner = cycle_nodes[:-1]
    if not inner:
        return cycle_nodes, ""

    min_val = min(inner)
    min_idx = inner.index(min_val)
    rotated = inner[min_idx:] + inner[:min_idx]
    canonical_path = rotated + [rotated[0]]
    canonical_key = "-".join(rotated)
    return canonical_path, canonical_key


class CircularFlowDetector(BaseDetector):
    """Detects closed circular money flows and round-trip wash trading."""

    def detect(
        self,
        min_cycle_length: int = 2,
        max_cycle_length: int = 5,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> List[DetectionResult]:
        cypher_cycle = f"""
        MATCH path = (a:Account)-[rels:TRANSFERRED_TO*{min_cycle_length}..{max_cycle_length}]->(a)
        WHERE ($start_time IS NULL OR ALL(r IN rels WHERE r.timestamp >= datetime($start_time)))
          AND ($end_time IS NULL OR ALL(r IN rels WHERE r.timestamp <= datetime($end_time)))
        WITH [node IN nodes(path) | node.account_id] AS cycle_nodes,
             [rel IN rels | rel.transaction_id] AS tx_ids,
             [rel IN rels | rel.amount] AS amounts,
             [rel IN rels | rel.scenario_id] AS scenarios,
             length(path) AS cycle_length
        RETURN DISTINCT
            cycle_nodes,
            cycle_length,
            tx_ids,
            amounts,
            scenarios[0] AS scenario_id
        ORDER BY cycle_length ASC
        """
        params = {
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        }

        records = self.client.execute_query(cypher_cycle, params)
        results: List[DetectionResult] = []
        seen_canonical_cycles = set()

        for rec in records:
            raw_nodes = rec["cycle_nodes"]
            cycle_len = rec["cycle_length"]
            tx_ids = rec["tx_ids"]
            amounts = [float(a) for a in rec["amounts"]]
            sc_id = rec.get("scenario_id")

            canonical_nodes, canonical_key = canonicalize_cycle(raw_nodes)
            if canonical_key in seen_canonical_cycles:
                continue
            seen_canonical_cycles.add(canonical_key)

            primary = canonical_nodes[0]
            total_vol = sum(amounts)
            unique_involved = list(dict.fromkeys(canonical_nodes[:-1]))

            # Circular flows indicate high-probability synthetic wash trading or circular layering
            confidence = min(0.99, 0.85 + (cycle_len * 0.03))
            severity = Severity.CRITICAL

            fingerprint = generate_fingerprint(DetectionType.CIRCULAR_FLOW.value, primary, unique_involved)

            evidence = DetectionEvidence(
                reason_summary=(
                    f"Closed wash trading loop of length {cycle_len} detected: {' -> '.join(canonical_nodes)} "
                    f"(Total cyclical volume: ${total_vol:,.2f})."
                ),
                metric_name="cycle_length",
                metric_value=cycle_len,
                threshold_value=min_cycle_length,
                source_accounts=[primary],
                destination_accounts=[primary],
                intermediary_accounts=unique_involved[1:],
                path_nodes=canonical_nodes,
                cycle_length=cycle_len,
                inflow_amount=total_vol,
            )

            result = DetectionResult(
                detection_id=f"DET_CYC_{fingerprint}",
                detection_type=DetectionType.CIRCULAR_FLOW,
                severity=severity,
                confidence=confidence,
                primary_account=primary,
                scenario_id=sc_id,
                description=f"Closed circular flow wash trading loop ({cycle_len} nodes): {' -> '.join(canonical_nodes)}",
                evidence=evidence,
                related_accounts=unique_involved[1:],
                transaction_ids=tx_ids,
                total_amount=total_vol,
                currency="USD",
            )
            results.append(result)

        return results
