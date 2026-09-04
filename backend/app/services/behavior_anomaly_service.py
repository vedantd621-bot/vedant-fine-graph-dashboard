"""
FinGraph Behavioral Anomaly & Entity Similarity Service.
Establishes statistical baselines for entity volume, velocity, and counterparties,
detects temporal window deviations, and computes explainable multi-signal entity similarity.
"""
from datetime import datetime, timedelta, timezone
import logging
import math
import statistics
from typing import Any, Dict, List, Optional, Set, Tuple

from neo4j.src.client import Neo4jClient
from analytics.src.models import RiskLevel
from analytics.src.risk_engine import ExplainableRiskEngine
from detection.src.engine import DetectionEngine
from detection.src.models import Severity
from backend.app.models.behavior import (
    AnomalyType,
    BehavioralAnomaly,
    EntityBehaviorBaseline,
    EntityBehaviorResponse,
    EntitySimilarityItem,
    EntitySimilarityResponse,
    TemporalWindow,
)
from backend.app.realtime.event_bus import EventBus, get_event_bus
from backend.app.realtime.events import (
    AnomalyDetectedPayload,
    EntityBehaviorChangedPayload,
    EventType,
    create_realtime_event,
)
from backend.app.services.account_service import AccountService

logger = logging.getLogger("FinGraph.BehaviorAnomalyService")


class BehaviorAnomalyService:
    """Manages statistical entity baselines, anomaly detection, and entity similarity."""

    def __init__(
        self,
        client: Neo4jClient,
        account_service: AccountService,
        detection_engine: DetectionEngine,
        risk_engine: ExplainableRiskEngine,
        event_bus: Optional[EventBus] = None,
    ):
        self.client = client
        self.account_service = account_service
        self.detection_engine = detection_engine
        self.risk_engine = risk_engine
        self.event_bus = event_bus or get_event_bus()

    def get_entity_baseline(self, entity_id: str) -> EntityBehaviorBaseline:
        """Calculates historical statistical baseline for an entity."""
        now = datetime.now(timezone.utc)
        tx_items, _ = self.account_service.get_account_transactions(account_id=entity_id, page=1, page_size=100)

        if not tx_items:
            return EntityBehaviorBaseline(
                entity_id=entity_id,
                historical_transaction_count=0,
                historical_volume=0.0,
                avg_transaction_amount=0.0,
                std_dev_amount=0.0,
                max_transaction_amount=0.0,
                avg_velocity_per_hour=0.0,
                incoming_volume_ratio=0.5,
                outgoing_volume_ratio=0.5,
                unique_counterparties_count=0,
                common_counterparties=[],
                baseline_window_days=30,
                last_computed_at=now,
            )

        amounts = [t.amount for t in tx_items]
        total_vol = sum(amounts)
        avg_amt = statistics.mean(amounts) if amounts else 0.0
        std_amt = statistics.stdev(amounts) if len(amounts) > 1 else 0.0
        max_amt = max(amounts) if amounts else 0.0

        incoming_vol = sum(t.amount for t in tx_items if t.direction == "INCOMING")
        outgoing_vol = sum(t.amount for t in tx_items if t.direction == "OUTGOING")
        in_ratio = (incoming_vol / total_vol) if total_vol > 0 else 0.5
        out_ratio = (outgoing_vol / total_vol) if total_vol > 0 else 0.5

        cps = list(set(t.counterparty for t in tx_items if t.counterparty))

        # Velocity per hour (assuming 30 day window)
        velocity_per_hour = round(len(tx_items) / (30 * 24), 3)

        return EntityBehaviorBaseline(
            entity_id=entity_id,
            historical_transaction_count=len(tx_items),
            historical_volume=round(total_vol, 2),
            avg_transaction_amount=round(avg_amt, 2),
            std_dev_amount=round(std_amt, 2),
            max_transaction_amount=round(max_amt, 2),
            avg_velocity_per_hour=velocity_per_hour,
            incoming_volume_ratio=round(in_ratio, 3),
            outgoing_volume_ratio=round(out_ratio, 3),
            unique_counterparties_count=len(cps),
            common_counterparties=cps[:5],
            baseline_window_days=30,
            last_computed_at=now,
        )

    def get_entity_behavior(
        self,
        entity_id: str,
        window: TemporalWindow = TemporalWindow.WINDOW_24H,
    ) -> Optional[EntityBehaviorResponse]:
        """Evaluates behavioral profile and detects window-based anomalies."""
        acc = self.account_service.get_account_by_id(entity_id)
        if not acc:
            return None

        baseline = self.get_entity_baseline(entity_id)
        tx_items, _ = self.account_service.get_account_transactions(account_id=entity_id, page=1, page_size=50)

        # Filter recent transactions within window
        window_deltas = {
            TemporalWindow.WINDOW_5M: timedelta(minutes=5),
            TemporalWindow.WINDOW_1H: timedelta(hours=1),
            TemporalWindow.WINDOW_24H: timedelta(hours=24),
            TemporalWindow.WINDOW_7D: timedelta(days=7),
            TemporalWindow.WINDOW_30D: timedelta(days=30),
        }
        cutoff = datetime.now(timezone.utc) - window_deltas.get(window, timedelta(hours=24))

        recent_txs = [t for t in tx_items if (t.timestamp >= cutoff if t.timestamp.tzinfo else t.timestamp.replace(tzinfo=timezone.utc) >= cutoff)]
        recent_count = len(recent_txs)
        recent_vol = sum(t.amount for t in recent_txs)

        anomalies: List[BehavioralAnomaly] = []

        # 1. Volume Spike Anomaly
        if baseline.historical_volume > 0:
            expected_vol_window = (baseline.historical_volume / baseline.baseline_window_days) * (window_deltas[window].total_seconds() / 86400)
            if expected_vol_window > 0 and recent_vol > (expected_vol_window * 3.0) and recent_vol >= 10000.0:
                dev = recent_vol / expected_vol_window
                anomalies.append(
                    BehavioralAnomaly(
                        anomaly_id=f"ANOM-VOL-{entity_id[:6]}",
                        anomaly_type=AnomalyType.VOLUME_SPIKE,
                        severity=Severity.HIGH if dev > 5.0 else Severity.MEDIUM,
                        anomaly_score=min(100.0, round(dev * 15.0, 1)),
                        window=window,
                        metric_name="transaction_volume",
                        observed_value=round(recent_vol, 2),
                        baseline_value=round(expected_vol_window, 2),
                        deviation_ratio=round(dev, 2),
                        description=f"Observed volume (${recent_vol:,.2f}) is {dev:.1f}x the expected baseline window volume.",
                        evidence_reference=f"WINDOW_{window.value}",
                    )
                )

        # 2. Velocity Burst Anomaly
        hours_in_window = max(0.1, window_deltas[window].total_seconds() / 3600.0)
        recent_velocity = recent_count / hours_in_window
        if baseline.avg_velocity_per_hour > 0 and recent_velocity > (baseline.avg_velocity_per_hour * 4.0) and recent_count >= 5:
            dev = recent_velocity / baseline.avg_velocity_per_hour
            anomalies.append(
                BehavioralAnomaly(
                    anomaly_id=f"ANOM-VEL-{entity_id[:6]}",
                    anomaly_type=AnomalyType.VELOCITY_BURST,
                    severity=Severity.HIGH,
                    anomaly_score=min(100.0, round(dev * 12.0, 1)),
                    window=window,
                    metric_name="transaction_velocity_per_hour",
                    observed_value=round(recent_velocity, 2),
                    baseline_value=round(baseline.avg_velocity_per_hour, 3),
                    deviation_ratio=round(dev, 2),
                    description=f"Transaction velocity ({recent_velocity:.1f} tx/hr) is {dev:.1f}x above baseline rate.",
                    evidence_reference=f"BURST_{window.value}",
                )
            )

        # 3. High Value Deviation Anomaly
        if baseline.max_transaction_amount > 0:
            for tx in recent_txs:
                if tx.amount > (baseline.max_transaction_amount * 2.0) and tx.amount >= 20000.0:
                    dev = tx.amount / baseline.max_transaction_amount
                    anomalies.append(
                        BehavioralAnomaly(
                            anomaly_id=f"ANOM-VAL-{tx.transaction_id[:8]}",
                            anomaly_type=AnomalyType.HIGH_VALUE_DEVIATION,
                            severity=Severity.CRITICAL if dev >= 3.0 else Severity.HIGH,
                            anomaly_score=min(100.0, round(dev * 20.0, 1)),
                            window=window,
                            metric_name="single_transaction_amount",
                            observed_value=round(tx.amount, 2),
                            baseline_value=round(baseline.max_transaction_amount, 2),
                            deviation_ratio=round(dev, 2),
                            description=f"Transaction {tx.transaction_id} (${tx.amount:,.2f}) exceeds historical max amount by {dev:.1f}x.",
                            evidence_reference=tx.transaction_id,
                        )
                    )
                    break

        # Calculate composite anomaly score
        if anomalies:
            max_anom = max(a.anomaly_score for a in anomalies)
            avg_anom = sum(a.anomaly_score for a in anomalies) / len(anomalies)
            composite_anom_score = round(0.7 * max_anom + 0.3 * avg_anom, 1)
        else:
            composite_anom_score = 0.0

        is_anomalous = len(anomalies) > 0 and composite_anom_score >= 40.0
        summary = (
            f"Account '{entity_id}' has {len(anomalies)} active behavioral anomaly signals in window '{window.value}' "
            f"with an anomaly score of {composite_anom_score:.1f}/100."
            if is_anomalous
            else f"Account '{entity_id}' behaves within normal statistical baseline variance in window '{window.value}'."
        )

        return EntityBehaviorResponse(
            entity_id=entity_id,
            baseline=baseline,
            recent_transaction_count=recent_count,
            recent_volume=round(recent_vol, 2),
            active_window=window,
            anomalies=anomalies,
            anomaly_score=composite_anom_score,
            is_anomalous=is_anomalous,
            summary=summary,
        )

    def get_similar_entities(self, entity_id: str, limit: int = 5) -> EntitySimilarityResponse:
        """Discovers similar suspect entities using counterparty overlap and graph features."""
        target_acc = self.account_service.get_account_by_id(entity_id)
        if not target_acc:
            return EntitySimilarityResponse(entity_id=entity_id, similar_entities=[], total_matches=0)

        all_accounts, _ = self.account_service.list_accounts(page=1, page_size=50)
        target_txs, _ = self.account_service.get_account_transactions(account_id=entity_id, page=1, page_size=50)
        target_cps = set(t.counterparty for t in target_txs if t.counterparty)

        matches: List[EntitySimilarityItem] = []
        for other in all_accounts:
            if other.account_id == entity_id:
                continue

            other_txs, _ = self.account_service.get_account_transactions(account_id=other.account_id, page=1, page_size=50)
            other_cps = set(t.counterparty for t in other_txs if t.counterparty)

            # Jaccard counterparty overlap
            union_cps = target_cps.union(other_cps)
            inter_cps = target_cps.intersection(other_cps)
            jaccard_cp = (len(inter_cps) / len(union_cps)) if union_cps else 0.0

            # Community similarity
            same_comm = 1.0 if (target_acc.features.louvain_community_id is not None and target_acc.features.louvain_community_id == other.louvain_community_id) else 0.0

            # Volume proximity
            v1 = max(1.0, target_acc.features.total_volume)
            v2 = max(1.0, other.total_volume)
            vol_sim = min(v1, v2) / max(v1, v2)

            # Risk proximity
            r1 = target_acc.risk_score
            r2 = other.risk_score
            risk_sim = 1.0 - (abs(r1 - r2) / 100.0)

            # Composite similarity score
            sim_score = (0.40 * jaccard_cp) + (0.25 * same_comm) + (0.20 * risk_sim) + (0.15 * vol_sim)
            sim_score = round(min(1.0, max(0.0, sim_score)), 3)

            if sim_score >= 0.25:
                explanation = (
                    f"Shares {len(inter_cps)} counterparties with {entity_id}"
                    + (f", co-member in Community #{target_acc.features.louvain_community_id}" if same_comm else "")
                    + f" and similar risk profile ({other.risk_score:.1f})."
                )
                matches.append(
                    EntitySimilarityItem(
                        target_entity_id=other.account_id,
                        similarity_score=sim_score,
                        shared_counterparties=list(inter_cps),
                        shared_communities=[target_acc.features.louvain_community_id] if same_comm and target_acc.features.louvain_community_id is not None else [],
                        shared_detectors=[],
                        volume_similarity=round(vol_sim, 3),
                        explanation=explanation,
                    )
                )

        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        top_matches = matches[:limit]
        return EntitySimilarityResponse(
            entity_id=entity_id,
            similar_entities=top_matches,
            total_matches=len(matches),
        )
