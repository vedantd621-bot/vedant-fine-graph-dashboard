"""
FinGraph One-to-Many Distribution / Dispersion Detector.
Detects fan-out patterns where a single source account rapidly disburses funds
to multiple distinct recipient accounts.
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

CYPHER_ONE_TO_MANY_DETECTION = """
MATCH (src:Account)-[r:TRANSFERRED_TO]->(dst:Account)
WHERE src <> dst
  AND ($start_time IS NULL OR r.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r.timestamp <= datetime($end_time))
WITH src,
     collect(DISTINCT dst.account_id) AS destination_accounts,
     count(DISTINCT dst) AS destination_count,
     sum(r.amount) AS total_disbursed,
     collect(DISTINCT r.transaction_id) AS tx_ids,
     r.scenario_id AS scenario_id
WHERE destination_count >= $min_destinations
  AND total_disbursed >= $min_amount
RETURN
    src.account_id AS source_account,
    destination_accounts,
    destination_count,
    total_disbursed,
    tx_ids,
    scenario_id
ORDER BY destination_count DESC, total_disbursed DESC
"""


class OneToManyDetector(BaseDetector):
    """Detects rapid 1-to-many dispersion and fan-out distribution networks."""

    def detect(
        self,
        min_destinations: int = 4,
        min_total_amount: float = 0.0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> List[DetectionResult]:
        params = {
            "min_destinations": min_destinations,
            "min_amount": min_total_amount,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        }

        records = self.client.execute_query(CYPHER_ONE_TO_MANY_DETECTION, params)
        results: List[DetectionResult] = []

        for rec in records:
            src = rec["source_account"]
            destinations = rec["destination_accounts"]
            dst_count = rec["destination_count"]
            total_disbursed = float(rec["total_disbursed"])
            tx_ids = rec["tx_ids"]
            sc_id = rec.get("scenario_id")

            confidence = min(0.95, 0.70 + (dst_count * 0.04))
            severity = Severity.HIGH if dst_count >= 5 else Severity.MEDIUM

            fingerprint = generate_fingerprint(DetectionType.ONE_TO_MANY.value, src, destinations)

            evidence = DetectionEvidence(
                reason_summary=(
                    f"Source account {src} fanned out ${total_disbursed:,.2f} across {dst_count} "
                    f"distinct destination accounts."
                ),
                metric_name="destination_count",
                metric_value=dst_count,
                threshold_value=min_destinations,
                source_accounts=[src],
                destination_accounts=destinations,
                outflow_amount=total_disbursed,
            )

            result = DetectionResult(
                detection_id=f"DET_DIS_{fingerprint}",
                detection_type=DetectionType.ONE_TO_MANY,
                severity=severity,
                confidence=confidence,
                primary_account=src,
                scenario_id=sc_id,
                description=f"One-to-Many dispersion network from source {src} to {dst_count} accounts",
                evidence=evidence,
                related_accounts=destinations,
                transaction_ids=tx_ids,
                total_amount=total_disbursed,
                currency="USD",
            )
            results.append(result)

        return results
