"""
FinGraph Money Trail Forensic Investigation Utility.
Allows compliance and fraud investigators to trace multi-hop money trails between specified accounts
or explore fund dispersion outwards from a target account.
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


class MoneyTrailInvestigator(BaseDetector):
    """Traces multi-hop directed fund transfer trails for forensic investigations."""

    def trace(
        self,
        from_account: str,
        to_account: Optional[str] = None,
        max_hops: int = 4,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 25,
    ) -> List[DetectionResult]:
        if to_account:
            cypher = f"""
            MATCH path = (src:Account {{account_id: $from_account}})-[rels:TRANSFERRED_TO*1..{max_hops}]->(dst:Account {{account_id: $to_account}})
            WHERE ($start_time IS NULL OR ALL(r IN rels WHERE r.timestamp >= datetime($start_time)))
              AND ($end_time IS NULL OR ALL(r IN rels WHERE r.timestamp <= datetime($end_time)))
            WITH [node IN nodes(path) | node.account_id] AS path_nodes,
                 [rel IN rels | rel.transaction_id] AS tx_ids,
                 [rel IN rels | rel.amount] AS amounts,
                 [rel IN rels | rel.scenario_id] AS scenarios,
                 length(path) AS path_len
            RETURN DISTINCT
                path_nodes,
                path_len,
                tx_ids,
                amounts,
                scenarios[0] AS scenario_id
            LIMIT $limit
            """
        else:
            cypher = f"""
            MATCH path = (src:Account {{account_id: $from_account}})-[rels:TRANSFERRED_TO*1..{max_hops}]->(dst:Account)
            WHERE ($start_time IS NULL OR ALL(r IN rels WHERE r.timestamp >= datetime($start_time)))
              AND ($end_time IS NULL OR ALL(r IN rels WHERE r.timestamp <= datetime($end_time)))
            WITH [node IN nodes(path) | node.account_id] AS path_nodes,
                 [rel IN rels | rel.transaction_id] AS tx_ids,
                 [rel IN rels | rel.amount] AS amounts,
                 [rel IN rels | rel.scenario_id] AS scenarios,
                 length(path) AS path_len
            RETURN DISTINCT
                path_nodes,
                path_len,
                tx_ids,
                amounts,
                scenarios[0] AS scenario_id
            LIMIT $limit
            """

        params = {
            "from_account": from_account,
            "to_account": to_account,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "limit": limit,
        }

        records = self.client.execute_query(cypher, params)
        results: List[DetectionResult] = []

        for rec in records:
            nodes = rec["path_nodes"]
            path_len = rec["path_len"]
            tx_ids = rec["tx_ids"]
            amounts = [float(a) for a in rec["amounts"]]
            sc_id = rec.get("scenario_id")

            origin = nodes[0]
            target = nodes[-1]
            total_transferred = sum(amounts)

            fingerprint = generate_fingerprint(DetectionType.MONEY_TRAIL.value, origin, nodes)

            evidence = DetectionEvidence(
                reason_summary=(
                    f"Direct money trail of {path_len} hops traced: {' -> '.join(nodes)} "
                    f"(Total path volume: ${total_transferred:,.2f})."
                ),
                metric_name="path_length",
                metric_value=path_len,
                threshold_value=max_hops,
                source_accounts=[origin],
                destination_accounts=[target],
                intermediary_accounts=nodes[1:-1] if path_len > 1 else [],
                path_nodes=nodes,
                hop_count=path_len,
                inflow_amount=total_transferred,
            )

            result = DetectionResult(
                detection_id=f"DET_TRL_{fingerprint}",
                detection_type=DetectionType.MONEY_TRAIL,
                severity=Severity.LOW,
                confidence=1.0,
                primary_account=origin,
                scenario_id=sc_id,
                description=f"Forensic money trail ({path_len} hops): {' -> '.join(nodes)}",
                evidence=evidence,
                related_accounts=nodes[1:],
                transaction_ids=tx_ids,
                total_amount=total_transferred,
                currency="USD",
            )
            results.append(result)

        return results

    def detect(self, from_account: str = "A001", to_account: Optional[str] = None, max_hops: int = 4, **kwargs) -> List[DetectionResult]:
        return self.trace(from_account=from_account, to_account=to_account, max_hops=max_hops, **kwargs)
