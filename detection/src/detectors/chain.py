"""
FinGraph Intermediary Chain / Multi-Hop Layering Detector.
Detects extended linear pass-through chains (A -> B -> C -> D -> E) designed to obscure
the origin of illicit funds through intermediary shell accounts.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from neo4j.src.client import Neo4jClient
from detection.src.detectors.base import BaseDetector
from detection.src.models import (
    DetectionEvidence,
    DetectionResult,
    DetectionType,
    Severity,
    generate_fingerprint,
)


class ChainDetector(BaseDetector):
    """Detects multi-hop pass-through and layering chains."""

    def detect(
        self,
        min_depth: int = 3,
        max_depth: int = 6,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> List[DetectionResult]:
        # Parameterized variable length path range
        cypher_chain = f"""
        MATCH path = (origin:Account)-[rels:TRANSFERRED_TO*{min_depth}..{max_depth}]->(exit:Account)
        WHERE origin <> exit
          AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE x = y))
          AND ($start_time IS NULL OR ALL(r IN rels WHERE r.timestamp >= datetime($start_time)))
          AND ($end_time IS NULL OR ALL(r IN rels WHERE r.timestamp <= datetime($end_time)))
        WITH [node IN nodes(path) | node.account_id] AS chain_nodes,
             [rel IN rels | rel.transaction_id] AS tx_ids,
             [rel IN rels | rel.amount] AS amounts,
             [rel IN rels | rel.scenario_id] AS scenarios,
             length(path) AS hop_count
        RETURN DISTINCT
            chain_nodes,
            hop_count,
            tx_ids,
            amounts,
            scenarios[0] AS scenario_id
        ORDER BY hop_count DESC
        LIMIT 50
        """
        params = {
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        }

        records = self.client.execute_query(cypher_chain, params)
        results: List[DetectionResult] = []

        for rec in records:
            nodes = rec["chain_nodes"]
            hop_count = rec["hop_count"]
            tx_ids = rec["tx_ids"]
            amounts = [float(a) for a in rec["amounts"]]
            sc_id = rec.get("scenario_id")

            origin = nodes[0]
            exit_node = nodes[-1]
            intermediaries = nodes[1:-1]
            total_flow = amounts[0] if amounts else 0.0

            confidence = min(0.95, 0.70 + (hop_count * 0.06))
            severity = Severity.HIGH if hop_count >= 4 else Severity.MEDIUM

            fingerprint = generate_fingerprint(DetectionType.CHAIN.value, origin, nodes)

            evidence = DetectionEvidence(
                reason_summary=(
                    f"Linear pass-through chain of {hop_count} hops detected from origin {origin} "
                    f"through {len(intermediaries)} intermediaries to exit {exit_node}."
                ),
                metric_name="hop_count",
                metric_value=hop_count,
                threshold_value=min_depth,
                source_accounts=[origin],
                destination_accounts=[exit_node],
                intermediary_accounts=intermediaries,
                path_nodes=nodes,
                hop_count=hop_count,
                inflow_amount=total_flow,
            )

            result = DetectionResult(
                detection_id=f"DET_CHN_{fingerprint}",
                detection_type=DetectionType.CHAIN,
                severity=severity,
                confidence=confidence,
                primary_account=origin,
                scenario_id=sc_id,
                description=f"{hop_count}-hop intermediary pass-through chain: {' -> '.join(nodes)}",
                evidence=evidence,
                related_accounts=nodes[1:],
                transaction_ids=tx_ids,
                total_amount=total_flow,
                currency="USD",
            )
            results.append(result)

        return results
