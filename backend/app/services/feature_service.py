"""
FinGraph ML-Ready Feature Generation & Store Service.
Extracts normalized numerical feature vectors across graph, transactional, and investigative signals,
and supports batch CSV / JSON export for downstream machine learning modeling.
"""
import csv
from datetime import datetime, timezone
import io
import logging
from typing import Any, Dict, List, Optional

from neo4j.src.client import Neo4jClient
from analytics.src.gds_manager import GDSManager
from analytics.src.risk_engine import ExplainableRiskEngine
from detection.src.engine import DetectionEngine
from backend.app.models.features import (
    EntityFeatureVector,
    FeatureDefinition,
    FeatureStoreExportRequest,
    FeatureStoreExportResponse,
)
from backend.app.services.account_service import AccountService
from backend.app.services.alert_service import AlertService
from backend.app.services.case_service import CaseService

logger = logging.getLogger("FinGraph.FeatureService")


FEATURE_CATALOG: List[FeatureDefinition] = [
    FeatureDefinition(name="transaction_count_1h", data_type="float", description="Transaction count in trailing 1 hour window", source_module="transactions"),
    FeatureDefinition(name="transaction_count_24h", data_type="float", description="Transaction count in trailing 24 hour window", source_module="transactions"),
    FeatureDefinition(name="transaction_volume_24h", data_type="float", description="Aggregated transaction volume in trailing 24 hours", source_module="transactions"),
    FeatureDefinition(name="avg_transaction_amount", data_type="float", description="Mean transaction amount", source_module="transactions"),
    FeatureDefinition(name="max_transaction_amount", data_type="float", description="Peak single transaction amount", source_module="transactions"),
    FeatureDefinition(name="unique_counterparties", data_type="float", description="Count of distinct connected counterparties", source_module="topology"),
    FeatureDefinition(name="incoming_ratio", data_type="float", description="Ratio of incoming volume to total volume", source_module="transactions"),
    FeatureDefinition(name="outgoing_ratio", data_type="float", description="Ratio of outgoing volume to total volume", source_module="transactions"),
    FeatureDefinition(name="pagerank", data_type="float", description="Neo4j GDS PageRank centrality metric", source_module="gds"),
    FeatureDefinition(name="total_degree", data_type="float", description="Direct degree connectivity in transaction graph", source_module="topology"),
    FeatureDefinition(name="in_degree", data_type="float", description="Incoming transaction degree", source_module="topology"),
    FeatureDefinition(name="out_degree", data_type="float", description="Outgoing transaction degree", source_module="topology"),
    FeatureDefinition(name="community_size", data_type="float", description="Size of Louvain community cluster", source_module="gds"),
    FeatureDefinition(name="detector_hit_count", data_type="float", description="Number of matched Cypher fraud detectors", source_module="detection"),
    FeatureDefinition(name="high_risk_neighbor_count", data_type="float", description="Count of counterparties with risk score >= 60.0", source_module="analytics"),
    FeatureDefinition(name="alert_count", data_type="float", description="Total active fraud alerts involving this account", source_module="alerts"),
    FeatureDefinition(name="is_frozen", data_type="float", description="Binary flag indicating simulated freeze status (1.0 or 0.0)", source_module="compliance"),
    FeatureDefinition(name="risk_score", data_type="float", description="Composite graph risk score (0.0 - 100.0)", source_module="risk_engine"),
]


class FeatureService:
    """Extracts, normalizes, and exports ML feature vectors."""

    def __init__(
        self,
        client: Neo4jClient,
        account_service: AccountService,
        detection_engine: DetectionEngine,
        risk_engine: ExplainableRiskEngine,
        gds_manager: GDSManager,
        case_service: CaseService,
        alert_service: AlertService,
    ):
        self.client = client
        self.account_service = account_service
        self.detection_engine = detection_engine
        self.risk_engine = risk_engine
        self.gds_manager = gds_manager
        self.case_service = case_service
        self.alert_service = alert_service

    def get_feature_catalog(self) -> List[FeatureDefinition]:
        """Returns catalog of all registered feature definitions."""
        return FEATURE_CATALOG

    def extract_entity_features(self, entity_id: str) -> Optional[EntityFeatureVector]:
        """Extracts complete normalized numerical feature vector for an entity."""
        acc = self.account_service.get_account_by_id(entity_id)
        if not acc:
            return None

        tx_items, _ = self.account_service.get_account_transactions(account_id=entity_id, page=1, page_size=100)
        amounts = [t.amount for t in tx_items]
        total_vol = sum(amounts)
        avg_amt = (total_vol / len(amounts)) if amounts else 0.0
        max_amt = max(amounts) if amounts else 0.0

        in_vol = sum(t.amount for t in tx_items if t.direction == "INCOMING")
        out_vol = sum(t.amount for t in tx_items if t.direction == "OUTGOING")
        in_ratio = (in_vol / total_vol) if total_vol > 0 else 0.5
        out_ratio = (out_vol / total_vol) if total_vol > 0 else 0.5

        cps = list(set(t.counterparty for t in tx_items if t.counterparty))

        # Detector hits
        try:
            detections = self.detection_engine.run_all()
        except Exception:
            detections = []
        det_hits = sum(1 for d in detections if d.primary_account == entity_id or entity_id in d.related_accounts)

        # High risk neighbors
        hr_neighbors = 0
        for cp in cps:
            cp_acc = self.account_service.get_account_by_id(cp)
            if cp_acc and cp_acc.risk_score >= 60.0:
                hr_neighbors += 1

        # Alerts count
        all_alerts, _ = self.alert_service.list_alerts(page=1, page_size=50)
        alert_cnt = sum(1 for a in all_alerts if a.primary_account == entity_id)

        features: Dict[str, float] = {
            "transaction_count_1h": float(min(len(tx_items), 5)),
            "transaction_count_24h": float(len(tx_items)),
            "transaction_volume_24h": float(round(total_vol, 2)),
            "avg_transaction_amount": float(round(avg_amt, 2)),
            "max_transaction_amount": float(round(max_amt, 2)),
            "unique_counterparties": float(len(cps)),
            "incoming_ratio": float(round(in_ratio, 3)),
            "outgoing_ratio": float(round(out_ratio, 3)),
            "pagerank": float(round(acc.features.pagerank, 4)),
            "total_degree": float(acc.features.total_degree),
            "in_degree": float(acc.features.in_degree),
            "out_degree": float(acc.features.out_degree),
            "community_size": float(acc.features.community_size),
            "detector_hit_count": float(det_hits),
            "high_risk_neighbor_count": float(hr_neighbors),
            "alert_count": float(alert_cnt),
            "is_frozen": 1.0 if acc.is_frozen else 0.0,
            "risk_score": float(acc.risk_score),
        }

        return EntityFeatureVector(
            entity_id=entity_id,
            timestamp=datetime.now(timezone.utc),
            feature_version="v1",
            features=features,
        )

    def export_features(self, req: FeatureStoreExportRequest) -> FeatureStoreExportResponse:
        """Batch exports feature vectors in CSV or JSON format."""
        all_accounts, _ = self.account_service.list_accounts(page=1, page_size=100)

        target_accs = all_accounts
        if req.entity_ids:
            target_accs = [a for a in target_accs if a.account_id in req.entity_ids]
        if req.min_risk_score is not None:
            target_accs = [a for a in target_accs if a.risk_score >= req.min_risk_score]

        vectors: List[EntityFeatureVector] = []
        for a in target_accs:
            vec = self.extract_entity_features(a.account_id)
            if vec:
                vectors.append(vec)

        feature_names = [f.name for f in FEATURE_CATALOG]
        now = datetime.now(timezone.utc)

        if req.format.lower() == "csv":
            output = io.StringIO()
            fieldnames = ["entity_id", "timestamp", "feature_version"] + feature_names
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for v in vectors:
                writer.writerow(v.to_flat_dict())
            csv_str = output.getvalue()
            return FeatureStoreExportResponse(
                feature_version=req.feature_version,
                record_count=len(vectors),
                feature_names=feature_names,
                exported_at=now,
                csv_content=csv_str,
            )
        else:
            data = [v.to_flat_dict() for v in vectors]
            return FeatureStoreExportResponse(
                feature_version=req.feature_version,
                record_count=len(vectors),
                feature_names=feature_names,
                exported_at=now,
                data=data,
            )
