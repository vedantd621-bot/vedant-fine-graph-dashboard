"""
FinGraph Funnel / Smurfing Pattern Detector.
Detects structuring patterns where multiple distinct accounts transfer funds into an intermediary mule,
which then consolidates and sweeps the funds to an exit/beneficiary account.
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

CYPHER_FUNNEL_DETECTION = """
MATCH (src:Account)-[r1:TRANSFERRED_TO]->(mule:Account)-[r2:TRANSFERRED_TO]->(dst:Account)
WHERE src <> dst AND src <> mule AND mule <> dst
  AND ($start_time IS NULL OR r1.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r1.timestamp <= datetime($end_time))
  AND ($start_time IS NULL OR r2.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r2.timestamp <= datetime($end_time))
WITH mule, dst,
     collect(DISTINCT src.account_id) AS source_accounts,
     count(DISTINCT src) AS source_count,
     sum(r1.amount) AS total_inflow,
     r2.amount AS sweep_outflow,
     collect(DISTINCT r1.transaction_id) + [r2.transaction_id] AS tx_ids,
     r1.scenario_id AS scenario_id
WHERE source_count >= $min_sources
  AND total_inflow >= $min_amount
RETURN
    mule.account_id AS mule_account,
    dst.account_id AS destination_account,
    source_accounts,
    source_count,
    total_inflow,
    sweep_outflow,
    tx_ids,
    scenario_id
ORDER BY source_count DESC, total_inflow DESC
"""


class FunnelDetector(BaseDetector):
    """Detects funnel aggregation and structuring smurfing patterns."""

    def detect(
        self,
        min_sources: int = 3,
        min_total_amount: float = 0.0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> List[DetectionResult]:
        params = {
            "min_sources": min_sources,
            "min_amount": min_total_amount,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        }

        records = self.client.execute_query(CYPHER_FUNNEL_DETECTION, params)
        results: List[DetectionResult] = []

        for rec in records:
            mule = rec["mule_account"]
            dst = rec["destination_account"]
            sources = rec["source_accounts"]
            src_count = rec["source_count"]
            inflow = float(rec["total_inflow"])
            outflow = float(rec["sweep_outflow"])
            tx_ids = rec["tx_ids"]
            sc_id = rec.get("scenario_id")

            # Confidence scoring based on source aggregation strength
            confidence = min(0.98, 0.70 + (src_count * 0.05))
            severity = Severity.CRITICAL if (inflow >= 30000.0 or src_count >= 5) else Severity.HIGH

            all_related = sources + [dst]
            fingerprint = generate_fingerprint(DetectionType.FUNNEL.value, mule, all_related)

            evidence = DetectionEvidence(
                reason_summary=(
                    f"Account {mule} received structured inflows from {src_count} distinct source accounts "
                    f"(total ${inflow:,.2f}) and consolidated a sweep outflow of ${outflow:,.2f} to {dst}."
                ),
                metric_name="source_count",
                metric_value=src_count,
                threshold_value=min_sources,
                source_accounts=sources,
                destination_accounts=[dst],
                intermediary_accounts=[mule],
                inflow_amount=inflow,
                outflow_amount=outflow,
            )

            result = DetectionResult(
                detection_id=f"DET_FUN_{fingerprint}",
                detection_type=DetectionType.FUNNEL,
                severity=severity,
                confidence=confidence,
                primary_account=mule,
                scenario_id=sc_id,
                description=f"Funnel / Smurfing aggregation pattern on intermediary account {mule}",
                evidence=evidence,
                related_accounts=all_related,
                transaction_ids=tx_ids,
                total_amount=inflow,
                currency="USD",
            )
            results.append(result)

        return results
