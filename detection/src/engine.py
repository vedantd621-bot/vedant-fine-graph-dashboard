"""
FinGraph Fraud Detection Engine.
Orchestrates all topological Cypher fraud detectors, aggregates findings,
generates explainable evidence, and produces deduplicated alert records.
"""
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from neo4j.src.client import Neo4jClient
from neo4j.src.config import Neo4jConfig
from detection.src.config import DetectionConfig, get_detection_config
from detection.src.models import (
    Alert,
    AlertStatus,
    DetectionEvidence,
    DetectionResult,
    DetectionType,
    generate_fingerprint,
)
from detection.src.detectors.funnel import FunnelDetector
from detection.src.detectors.one_to_many import OneToManyDetector
from detection.src.detectors.chain import ChainDetector
from detection.src.detectors.circular import CircularFlowDetector
from detection.src.detectors.layered import LayeredNetworkDetector
from detection.src.detectors.high_degree import HighDegreeDetector
from detection.src.detectors.money_trail import MoneyTrailInvestigator

logger = logging.getLogger("FinGraph.DetectionEngine")


class DetectionEngine:
    """
    Central orchestration engine for executing graph pattern fraud detectors
    and producing structured alerts.
    """

    def __init__(
        self,
        config: Optional[DetectionConfig] = None,
        client: Optional[Neo4jClient] = None,
        auto_connect: bool = True,
    ):
        self.config = config or get_detection_config()
        if client:
            self.client = client
            self._owns_client = False
        else:
            neo4j_cfg = Neo4jConfig(
                uri=self.config.neo4j_uri,
                user=self.config.neo4j_user,
                password=self.config.neo4j_password,
                database=self.config.neo4j_database,
            )
            self.client = Neo4jClient(config=neo4j_cfg, auto_connect=auto_connect)
            self._owns_client = True

        self.funnel_detector = FunnelDetector(self.client)
        self.one_to_many_detector = OneToManyDetector(self.client)
        self.chain_detector = ChainDetector(self.client)
        self.circular_detector = CircularFlowDetector(self.client)
        self.layered_detector = LayeredNetworkDetector(self.client)
        self.high_degree_detector = HighDegreeDetector(self.client)
        self.money_trail_investigator = MoneyTrailInvestigator(self.client)

    def detect_funnels(self, **kwargs) -> List[DetectionResult]:
        min_sources = kwargs.get("min_sources", self.config.funnel_min_sources)
        min_amount = kwargs.get("min_total_amount", self.config.funnel_min_total_amount)
        return self.funnel_detector.detect(min_sources=min_sources, min_total_amount=min_amount, **kwargs)

    def detect_one_to_many(self, **kwargs) -> List[DetectionResult]:
        min_dst = kwargs.get("min_destinations", self.config.distribution_min_destinations)
        min_amount = kwargs.get("min_total_amount", self.config.distribution_min_total_amount)
        return self.one_to_many_detector.detect(min_destinations=min_dst, min_total_amount=min_amount, **kwargs)

    def detect_chains(self, **kwargs) -> List[DetectionResult]:
        min_depth = kwargs.get("min_depth", self.config.chain_min_depth)
        max_depth = kwargs.get("max_depth", self.config.chain_max_depth)
        return self.chain_detector.detect(min_depth=min_depth, max_depth=max_depth, **kwargs)

    def detect_circular_flows(self, **kwargs) -> List[DetectionResult]:
        min_len = kwargs.get("min_cycle_length", self.config.circular_min_length)
        max_len = kwargs.get("max_cycle_length", self.config.circular_max_length)
        return self.circular_detector.detect(min_cycle_length=min_len, max_cycle_length=max_len, **kwargs)

    def detect_layered_networks(self, **kwargs) -> List[DetectionResult]:
        min_src = kwargs.get("min_sources", self.config.layered_min_sources)
        min_inter = kwargs.get("min_intermediaries", self.config.layered_min_intermediaries)
        min_dst = kwargs.get("min_destinations", self.config.layered_min_destinations)
        return self.layered_detector.detect(
            min_sources=min_src,
            min_intermediaries=min_inter,
            min_destinations=min_dst,
            **kwargs,
        )

    def detect_high_degree_accounts(self, **kwargs) -> List[DetectionResult]:
        min_deg = kwargs.get("min_degree", self.config.high_degree_min_degree)
        return self.high_degree_detector.detect(min_degree=min_deg, **kwargs)

    def trace_money_trail(self, from_account: str, to_account: Optional[str] = None, max_hops: int = 4, **kwargs) -> List[DetectionResult]:
        return self.money_trail_investigator.trace(from_account=from_account, to_account=to_account, max_hops=max_hops, **kwargs)

    def run_all(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> List[DetectionResult]:
        """Runs all enabled fraud detectors and aggregates findings."""
        all_results: List[DetectionResult] = []

        logger.info("Executing Circular Flow Detector...")
        all_results.extend(self.detect_circular_flows(start_time=start_time, end_time=end_time, **kwargs))

        logger.info("Executing Funnel / Smurfing Detector...")
        all_results.extend(self.detect_funnels(start_time=start_time, end_time=end_time, **kwargs))

        logger.info("Executing One-to-Many Distribution Detector...")
        all_results.extend(self.detect_one_to_many(start_time=start_time, end_time=end_time, **kwargs))

        logger.info("Executing Intermediary Chain Detector...")
        all_results.extend(self.detect_chains(start_time=start_time, end_time=end_time, **kwargs))

        logger.info("Executing Layered Network Detector...")
        all_results.extend(self.detect_layered_networks(start_time=start_time, end_time=end_time, **kwargs))

        logger.info("Executing High-Degree Hub Detector...")
        all_results.extend(self.detect_high_degree_accounts(start_time=start_time, end_time=end_time, **kwargs))

        logger.info(f"Detection run complete. Identified {len(all_results)} suspicious patterns.")
        return all_results

    def generate_alerts(self, detections: List[DetectionResult]) -> List[Alert]:
        """
        Converts detection results into deduplicated, actionable alert objects.
        Uses deterministic fingerprinting to ensure repeated engine runs do not generate duplicate alerts.
        """
        alerts: List[Alert] = []
        seen_alert_ids = set()

        for det in detections:
            alert_fp = generate_fingerprint(
                detection_type=det.detection_type.value,
                primary_account=det.primary_account,
                related_accounts=det.related_accounts,
            )
            alert_id = f"ALT_{alert_fp}"

            if alert_id in seen_alert_ids:
                continue
            seen_alert_ids.add(alert_id)

            alert = Alert(
                alert_id=alert_id,
                detection_type=det.detection_type,
                severity=det.severity,
                confidence=det.confidence,
                primary_account=det.primary_account,
                created_at=det.detected_at,
                status=AlertStatus.OPEN,
                description=det.description,
                evidence=det.evidence,
                related_accounts=det.related_accounts,
                transaction_ids=det.transaction_ids,
                total_amount=det.total_amount,
                currency=det.currency,
            )
            alerts.append(alert)

        return alerts

    def close(self) -> None:
        if self._owns_client and self.client:
            self.client.close()
            self.client = None

    def __enter__(self) -> "DetectionEngine":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
