"""
FinGraph High-Degree Hub Account Detector.
Detects accounts with unusually high graph connectivity (in-degree + out-degree) serving as
potential central money hubs or mule brokers.
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

CYPHER_HIGH_DEGREE_DETECTION = """
MATCH (a:Account)
OPTIONAL MATCH (a)<-[in_r:TRANSFERRED_TO]-()
  WHERE ($start_time IS NULL OR in_r.timestamp >= datetime($start_time))
    AND ($end_time IS NULL OR in_r.timestamp <= datetime($end_time))
OPTIONAL MATCH (a)-[out_r:TRANSFERRED_TO]->()
  WHERE ($start_time IS NULL OR out_r.timestamp >= datetime($start_time))
    AND ($end_time IS NULL OR out_r.timestamp <= datetime($end_time))
WITH a, count(DISTINCT in_r) AS in_degree, count(DISTINCT out_r) AS out_degree
WITH a, in_degree, out_degree, (in_degree + out_degree) AS total_degree
WHERE total_degree >= $min_degree
RETURN
    a.account_id AS account_id,
    a.account_type AS account_type,
    a.risk_score AS risk_score,
    in_degree,
    out_degree,
    total_degree
ORDER BY total_degree DESC, a.risk_score DESC
LIMIT $limit
"""


class HighDegreeDetector(BaseDetector):
    """Detects unusually connected hub accounts in the transaction network."""

    def detect(
        self,
        min_degree: int = 4,
        limit: int = 25,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> List[DetectionResult]:
        params = {
            "min_degree": min_degree,
            "limit": limit,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        }

        records = self.client.execute_query(CYPHER_HIGH_DEGREE_DETECTION, params)
        results: List[DetectionResult] = []

        for rec in records:
            acc_id = rec["account_id"]
            in_deg = rec["in_degree"]
            out_deg = rec["out_degree"]
            tot_deg = rec["total_degree"]

            confidence = min(0.90, 0.60 + (tot_deg * 0.05))
            severity = Severity.HIGH if tot_deg >= 8 else Severity.MEDIUM

            fingerprint = generate_fingerprint(DetectionType.HIGH_DEGREE.value, acc_id, [])

            evidence = DetectionEvidence(
                reason_summary=(
                    f"Account {acc_id} exhibits an unusually high network degree of {tot_deg} "
                    f"(in-degree: {in_deg}, out-degree: {out_deg})."
                ),
                metric_name="total_degree",
                metric_value=tot_deg,
                threshold_value=min_degree,
                source_accounts=[acc_id],
                intermediary_accounts=[acc_id] if (in_deg > 0 and out_deg > 0) else [],
            )

            result = DetectionResult(
                detection_id=f"DET_DEG_{fingerprint}",
                detection_type=DetectionType.HIGH_DEGREE,
                severity=severity,
                confidence=confidence,
                primary_account=acc_id,
                description=f"High-degree hub account {acc_id} (degree: {tot_deg})",
                evidence=evidence,
                related_accounts=[],
                transaction_ids=[],
                currency="USD",
            )
            results.append(result)

        return results
