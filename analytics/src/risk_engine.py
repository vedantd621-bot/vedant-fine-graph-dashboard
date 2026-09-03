"""
FinGraph Explainable Risk Scoring Engine.
Blends Phase 6 topological rule detections (60%) with Phase 7 GDS graph analytics (40%)
to produce a deterministic, explainable 0–100 composite risk score for each account.
"""
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from neo4j.src.client import Neo4jClient
from detection.src.engine import DetectionEngine
from detection.src.models import DetectionResult, DetectionType
from analytics.src.config import RiskScoringConfig, get_risk_scoring_config
from analytics.src.gds_manager import GDSManager
from analytics.src.models import (
    GraphFeatures,
    RiskAssessment,
    RiskLevel,
    RiskScore,
    RuleSignals,
)

logger = logging.getLogger("FinGraph.RiskEngine")


class ExplainableRiskEngine:
    """
    Computes composite, explainable risk scores for bank accounts by combining
    symbolic graph pattern detections and GDS centrality/community features.
    """

    def __init__(
        self,
        client: Neo4jClient,
        config: Optional[RiskScoringConfig] = None,
        detection_engine: Optional[DetectionEngine] = None,
        gds_manager: Optional[GDSManager] = None,
    ):
        self.client = client
        self.config = config or get_risk_scoring_config()
        self.detection_engine = detection_engine or DetectionEngine(client=self.client)
        self.gds_manager = gds_manager or GDSManager(client=self.client, config=self.config)

    def determine_risk_level(self, score: float) -> RiskLevel:
        """Maps a 0 - 100 continuous risk score to a categorical risk band."""
        if score <= self.config.low_max_score:
            return RiskLevel.LOW
        elif score <= self.config.medium_max_score:
            return RiskLevel.MEDIUM
        elif score <= self.config.high_max_score:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def evaluate_rule_signals(
        self, account_id: str, detections: List[DetectionResult]
    ) -> RuleSignals:
        """
        Aggregates rule-based detection signals for an account from Phase 6 detections.
        """
        funnel = False
        circular = False
        layered = False
        one_to_many = False
        chain = False
        high_degree = False
        matching_types: List[str] = []
        raw_points = 0.0

        for det in detections:
            is_primary = det.primary_account == account_id
            is_related = account_id in det.related_accounts

            if not (is_primary or is_related):
                continue

            dtype = det.detection_type
            if dtype not in matching_types:
                matching_types.append(dtype.value)

            if dtype == DetectionType.FUNNEL and not funnel:
                funnel = True
                raw_points += self.config.funnel_signal_points
            elif dtype == DetectionType.CIRCULAR_FLOW and not circular:
                circular = True
                raw_points += self.config.circular_signal_points
            elif dtype == DetectionType.LAYERED_NETWORK and not layered:
                layered = True
                raw_points += self.config.layered_signal_points
            elif dtype == DetectionType.ONE_TO_MANY and not one_to_many:
                one_to_many = True
                raw_points += self.config.one_to_many_signal_points
            elif dtype == DetectionType.CHAIN and not chain:
                chain = True
                raw_points += self.config.chain_signal_points
            elif dtype == DetectionType.HIGH_DEGREE and not high_degree:
                high_degree = True
                raw_points += self.config.high_degree_signal_points

        bounded_rule_score = min(100.0, max(0.0, raw_points))

        return RuleSignals(
            account_id=account_id,
            funnel_flag=funnel,
            circular_flag=circular,
            layered_flag=layered,
            one_to_many_flag=one_to_many,
            chain_flag=chain,
            high_degree_flag=high_degree,
            active_detections_count=len(matching_types),
            raw_rule_score=bounded_rule_score,
            detection_types=matching_types,
        )

    def evaluate_graph_signals(self, features: GraphFeatures) -> float:
        """
        Normalizes and blends GDS PageRank, total degree, and community clustering features.
        Returns a normalized graph subscore in the range 0.0 - 100.0.
        """
        # 1. PageRank Centrality: Normalize relative to typical baseline (~0.15 - 1.0+)
        # For PageRank >= 1.0, scales to 100. For lower values, linear scale.
        norm_pr = min(100.0, features.pagerank * 100.0) if features.pagerank > 0.0 else min(100.0, features.total_degree * 12.0)

        # 2. Total Degree: Normalize against high-connectivity threshold (8 connections = 100)
        norm_degree = min(100.0, (features.total_degree / 8.0) * 100.0)

        # 3. Community Density: Larger syndicate clusters contribute higher community risk
        norm_community = 0.0
        if features.community_size >= 4:
            norm_community = 85.0
        elif features.community_size >= 2:
            norm_community = 50.0

        # Weighted combination of graph signals (40% PR, 30% Degree, 30% Community)
        graph_subscore = (
            (norm_pr * (self.config.pagerank_subweight / 100.0))
            + (norm_degree * (self.config.degree_subweight / 100.0))
            + (norm_community * (self.config.community_subweight / 100.0))
        )

        return min(100.0, max(0.0, graph_subscore))

    def generate_reasons(
        self,
        rule_signals: RuleSignals,
        features: GraphFeatures,
        score: float,
        level: RiskLevel,
    ) -> List[str]:
        """
        Generates human-readable, explainable audit rationale explaining the score.
        Adheres to strict compliance terminology (risk signal / investigation candidate).
        """
        reasons: List[str] = []

        if rule_signals.circular_flag:
            reasons.append("Account participates in a closed circular wash-trading loop.")
        if rule_signals.funnel_flag:
            reasons.append("Account functions as an intermediary aggregation mule in a structured funneling pattern.")
        if rule_signals.layered_flag:
            reasons.append("Account is part of a multi-tier layered syndicate network.")
        if rule_signals.one_to_many_flag:
            reasons.append("Account rapidly disburses funds across multiple distinct recipient counterparties.")
        if rule_signals.chain_flag:
            reasons.append("Account serves as an intermediary transit hop in a linear pass-through layering chain.")
        if rule_signals.high_degree_flag or features.total_degree >= 5:
            reasons.append(f"High network connectivity ({features.total_degree} distinct counterparty links).")

        if features.pagerank >= 0.5:
            reasons.append(f"Elevated PageRank centrality ({features.pagerank:.3f}) identifies account as a structural liquidity transit hub.")
        if features.community_size >= 4:
            reasons.append(f"Belongs to a dense transaction community cluster of {features.community_size} accounts.")
        if features.total_volume >= 50000.0:
            reasons.append(f"Substantial cumulative transaction volume (${features.total_volume:,.2f} USD).")

        if not reasons:
            reasons.append("Normal transactional baseline with low topological risk indicators.")

        return reasons

    def calculate_account_risk(
        self,
        account_id: str,
        features: GraphFeatures,
        detections: List[DetectionResult],
    ) -> RiskScore:
        """Calculates the composite risk score for a single account."""
        rule_signals = self.evaluate_rule_signals(account_id, detections)
        graph_subscore = self.evaluate_graph_signals(features)

        # Composite Formula: (Rule * 0.60) + (Graph * 0.40)
        final_score = (rule_signals.raw_rule_score * self.config.rule_weight) + (
            graph_subscore * self.config.graph_weight
        )
        final_score = round(min(100.0, max(0.0, final_score)), 1)
        risk_lvl = self.determine_risk_level(final_score)
        reasons = self.generate_reasons(rule_signals, features, final_score, risk_lvl)

        return RiskScore(
            account_id=account_id,
            score=final_score,
            risk_level=risk_lvl,
            rule_subscore=round(rule_signals.raw_rule_score, 1),
            graph_subscore=round(graph_subscore, 1),
            model_version=self.config.model_version,
            features=features,
            rule_signals=rule_signals,
            reasons=reasons,
        )

    def calculate_all_risks(
        self,
        account_ids: Optional[List[str]] = None,
        refresh_gds: bool = False,
    ) -> List[RiskScore]:
        """
        Executes complete risk scoring pipeline across accounts:
        1. (Optional) Refreshes GDS projection and runs GDS algorithms.
        2. Executes Phase 6 Cypher rule detectors.
        3. Extracts GDS and topological graph features.
        4. Calculates composite explainable risk scores.
        """
        if refresh_gds and self.gds_manager.is_gds_available():
            try:
                self.gds_manager.refresh_projection()
                self.gds_manager.run_all_algorithms()
            except Exception as exc:
                logger.warning(f"GDS execution note (continuing with topological metrics): {exc}")

        # Execute Phase 6 rule detectors
        detections = self.detection_engine.run_all()

        # Extract features for target accounts
        features_map = self.gds_manager.extract_graph_features(account_ids=account_ids)

        risk_scores: List[RiskScore] = []
        for acc_id, feats in features_map.items():
            r_score = self.calculate_account_risk(acc_id, feats, detections)
            risk_scores.append(r_score)

        # Sort descending by risk score
        risk_scores.sort(key=lambda x: x.score, reverse=True)
        return risk_scores

    def persist_risk_scores(self, risk_scores: List[RiskScore]) -> int:
        """
        Batch writes calculated risk scores and GDS features back into Neo4j Account nodes.
        Uses parameterized Cypher batch execution.
        """
        if not risk_scores:
            return 0

        batch_data = []
        for rs in risk_scores:
            batch_data.append({
                "account_id": rs.account_id,
                "risk_score": rs.score,
                "risk_level": rs.risk_level.value,
                "model_version": rs.model_version,
                "pagerank_score": rs.features.pagerank,
                "louvain_community_id": rs.features.louvain_community_id,
                "wcc_id": rs.features.wcc_id,
                "reasons": rs.reasons,
            })

        cypher = """
        UNWIND $batch AS item
        MATCH (a:Account {account_id: item.account_id})
        SET a.risk_score = item.risk_score,
            a.risk_level = item.risk_level,
            a.risk_calculated_at = datetime(),
            a.risk_model_version = item.model_version,
            a.pagerank_score = item.pagerank_score,
            a.louvain_community_id = item.louvain_community_id,
            a.wcc_id = item.wcc_id,
            a.risk_reasons = item.reasons
        RETURN count(a) AS updated_count
        """
        records = self.client.execute_query(cypher, {"batch": batch_data})
        count = records[0]["updated_count"] if records else len(batch_data)
        logger.info(f"Persisted {count} account risk scores to Neo4j.")
        return count
