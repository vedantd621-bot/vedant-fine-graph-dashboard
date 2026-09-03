"""
FinGraph Layered Multi-Tier Syndicate Network Detector.
Detects advanced multi-tier money laundering networks spanning sources, intermediary mules,
central aggregation pools, and destination exit accounts.
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

CYPHER_LAYERED_DETECTION = """
MATCH (src:Account)-[r1:TRANSFERRED_TO]->(inter:Account)-[r2:TRANSFERRED_TO]->(agg:Account)-[r3:TRANSFERRED_TO]->(dst:Account)
WHERE src <> inter AND inter <> agg AND agg <> dst AND src <> dst AND src <> agg AND inter <> dst
  AND ($start_time IS NULL OR r1.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r1.timestamp <= datetime($end_time))
  AND ($start_time IS NULL OR r2.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r2.timestamp <= datetime($end_time))
  AND ($start_time IS NULL OR r3.timestamp >= datetime($start_time))
  AND ($end_time IS NULL OR r3.timestamp <= datetime($end_time))
WITH agg,
     collect(DISTINCT src.account_id) AS sources,
     collect(DISTINCT inter.account_id) AS intermediaries,
     collect(DISTINCT dst.account_id) AS destinations,
     collect(DISTINCT r1.transaction_id) + collect(DISTINCT r2.transaction_id) + collect(DISTINCT r3.transaction_id) AS tx_ids,
     sum(r1.amount) AS total_inflow,
     r1.scenario_id AS scenario_id
WHERE size(sources) >= $min_sources
  AND size(intermediaries) >= $min_intermediaries
  AND size(destinations) >= $min_destinations
RETURN
    agg.account_id AS aggregator_account,
    sources,
    size(sources) AS source_count,
    intermediaries,
    size(intermediaries) AS intermediary_count,
    destinations,
    size(destinations) AS destination_count,
    total_inflow,
    tx_ids,
    scenario_id
ORDER BY total_inflow DESC
"""


class LayeredNetworkDetector(BaseDetector):
    """Detects multi-tier syndicates with layered intermediary aggregation."""

    def detect(
        self,
        min_sources: int = 2,
        min_intermediaries: int = 2,
        min_destinations: int = 2,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> List[DetectionResult]:
        params = {
            "min_sources": min_sources,
            "min_intermediaries": min_intermediaries,
            "min_destinations": min_destinations,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        }

        records = self.client.execute_query(CYPHER_LAYERED_DETECTION, params)
        results: List[DetectionResult] = []

        for rec in records:
            agg = rec["aggregator_account"]
            sources = rec["sources"]
            inters = rec["intermediaries"]
            dsts = rec["destinations"]
            total_inflow = float(rec["total_inflow"])
            tx_ids = rec["tx_ids"]
            sc_id = rec.get("scenario_id")

            all_involved = sources + inters + [agg] + dsts
            confidence = 0.96
            severity = Severity.CRITICAL

            fingerprint = generate_fingerprint(DetectionType.LAYERED_NETWORK.value, agg, all_involved)

            evidence = DetectionEvidence(
                reason_summary=(
                    f"Multi-tier layered syndicate identified around aggregator {agg}: "
                    f"{len(sources)} sources -> {len(inters)} intermediaries -> aggregator {agg} -> {len(dsts)} destinations."
                ),
                metric_name="layered_tier_count",
                metric_value=4,
                threshold_value=3,
                source_accounts=sources,
                intermediary_accounts=inters + [agg],
                destination_accounts=dsts,
                inflow_amount=total_inflow,
            )

            result = DetectionResult(
                detection_id=f"DET_LAY_{fingerprint}",
                detection_type=DetectionType.LAYERED_NETWORK,
                severity=severity,
                confidence=confidence,
                primary_account=agg,
                scenario_id=sc_id,
                description=f"Multi-tier layered syndicate with central pool {agg}",
                evidence=evidence,
                related_accounts=sources + inters + dsts,
                transaction_ids=tx_ids,
                total_amount=total_inflow,
                currency="USD",
            )
            results.append(result)

        return results
