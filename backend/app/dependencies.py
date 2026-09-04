"""
FinGraph FastAPI Dependency Injection Provider.
Provides singleton Neo4j client, DetectionEngine, GDSManager, RiskEngine, and service instances to route handlers.
"""
import logging
import sys
from pathlib import Path
from typing import Generator
from fastapi import Depends

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from neo4j.src.client import Neo4jClient
from neo4j.src.config import Neo4jConfig
from detection.src.engine import DetectionEngine
from analytics.src.gds_manager import GDSManager
from analytics.src.risk_engine import ExplainableRiskEngine
from backend.app.config import ApiConfig, get_api_config
from backend.app.security.audit import AuditService, get_audit_service
from backend.app.services.alert_service import AlertService
from backend.app.services.account_service import AccountService
from backend.app.services.graph_service import GraphService
from backend.app.services.dashboard_service import DashboardService
from backend.app.services.investigation_service import InvestigationService
from backend.app.services.case_service import CaseService, get_case_service
from backend.app.services.intelligence_service import IntelligenceService
from backend.app.services.network_intelligence_service import NetworkIntelligenceService
from backend.app.services.behavior_anomaly_service import BehaviorAnomalyService
from backend.app.services.feature_service import FeatureService
from backend.app.services.alert_prioritization_service import AlertPrioritizationService
from backend.app.services.operations_service import OperationsService
from backend.app.services.notification_service import NotificationService

logger = logging.getLogger("FinGraph.Dependencies")

_global_client: Neo4jClient = None
_global_detection_engine: DetectionEngine = None
_global_gds_manager: GDSManager = None
_global_risk_engine: ExplainableRiskEngine = None
_global_prioritization_service: AlertPrioritizationService = None
_global_notification_service: NotificationService = None


def get_neo4j_client() -> Neo4jClient:
    """Returns singleton Neo4j database client."""
    global _global_client
    if _global_client is None:
        cfg = get_api_config()
        neo4j_cfg = Neo4jConfig(
            uri=cfg.neo4j_uri,
            user=cfg.neo4j_user,
            password=cfg.neo4j_password,
            database=cfg.neo4j_database,
        )
        _global_client = Neo4jClient(config=neo4j_cfg, auto_connect=False)
    return _global_client


def get_detection_engine(client: Neo4jClient = Depends(get_neo4j_client)) -> DetectionEngine:
    """Returns singleton DetectionEngine."""
    global _global_detection_engine
    if _global_detection_engine is None:
        _global_detection_engine = DetectionEngine(client=client)
    return _global_detection_engine


def get_gds_manager(client: Neo4jClient = Depends(get_neo4j_client)) -> GDSManager:
    """Returns singleton GDSManager."""
    global _global_gds_manager
    if _global_gds_manager is None:
        _global_gds_manager = GDSManager(client=client)
    return _global_gds_manager


def get_risk_engine(
    client: Neo4jClient = Depends(get_neo4j_client),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    gds_manager: GDSManager = Depends(get_gds_manager),
) -> ExplainableRiskEngine:
    """Returns singleton ExplainableRiskEngine."""
    global _global_risk_engine
    if _global_risk_engine is None:
        _global_risk_engine = ExplainableRiskEngine(
            client=client,
            detection_engine=detection_engine,
            gds_manager=gds_manager,
        )
    return _global_risk_engine


def get_alert_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    risk_engine: ExplainableRiskEngine = Depends(get_risk_engine),
) -> AlertService:
    """Returns AlertService instance."""
    return AlertService(
        client=client,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
    )


def get_account_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    risk_engine: ExplainableRiskEngine = Depends(get_risk_engine),
) -> AccountService:
    """Returns AccountService instance."""
    return AccountService(
        client=client,
        risk_engine=risk_engine,
    )


def get_graph_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    risk_engine: ExplainableRiskEngine = Depends(get_risk_engine),
) -> GraphService:
    """Returns GraphService instance."""
    return GraphService(
        client=client,
        risk_engine=risk_engine,
    )


def get_dashboard_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    account_service: AccountService = Depends(get_account_service),
    alert_service: AlertService = Depends(get_alert_service),
) -> DashboardService:
    """Returns DashboardService instance."""
    return DashboardService(
        client=client,
        account_service=account_service,
        alert_service=alert_service,
    )


def get_investigation_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    account_service: AccountService = Depends(get_account_service),
    alert_service: AlertService = Depends(get_alert_service),
) -> InvestigationService:
    """Returns InvestigationService instance."""
    return InvestigationService(
        client=client,
        detection_engine=detection_engine,
        account_service=account_service,
        alert_service=alert_service,
    )


def get_intelligence_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    risk_engine: ExplainableRiskEngine = Depends(get_risk_engine),
    account_service: AccountService = Depends(get_account_service),
    alert_service: AlertService = Depends(get_alert_service),
    case_service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> IntelligenceService:
    """Returns IntelligenceService instance."""
    return IntelligenceService(
        client=client,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
        account_service=account_service,
        alert_service=alert_service,
        case_service=case_service,
        audit_service=audit_service,
    )


def get_network_intelligence_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    risk_engine: ExplainableRiskEngine = Depends(get_risk_engine),
    account_service: AccountService = Depends(get_account_service),
    alert_service: AlertService = Depends(get_alert_service),
    case_service: CaseService = Depends(get_case_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> NetworkIntelligenceService:
    """Returns NetworkIntelligenceService instance."""
    return NetworkIntelligenceService(
        client=client,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
        account_service=account_service,
        alert_service=alert_service,
        case_service=case_service,
        audit_service=audit_service,
    )


def get_behavior_anomaly_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    account_service: AccountService = Depends(get_account_service),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    risk_engine: ExplainableRiskEngine = Depends(get_risk_engine),
) -> BehaviorAnomalyService:
    """Returns BehaviorAnomalyService instance."""
    return BehaviorAnomalyService(
        client=client,
        account_service=account_service,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
    )


def get_feature_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    account_service: AccountService = Depends(get_account_service),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    risk_engine: ExplainableRiskEngine = Depends(get_risk_engine),
    gds_manager: GDSManager = Depends(get_gds_manager),
    alert_service: AlertService = Depends(get_alert_service),
    case_service: CaseService = Depends(get_case_service),
) -> FeatureService:
    """Returns FeatureService instance."""
    return FeatureService(
        client=client,
        account_service=account_service,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
        gds_manager=gds_manager,
        alert_service=alert_service,
        case_service=case_service,
    )


def get_alert_prioritization_service() -> AlertPrioritizationService:
    """Returns singleton AlertPrioritizationService instance."""
    global _global_prioritization_service
    if _global_prioritization_service is None:
        _global_prioritization_service = AlertPrioritizationService()
    return _global_prioritization_service


def get_notification_service() -> NotificationService:
    """Returns singleton NotificationService instance."""
    global _global_notification_service
    if _global_notification_service is None:
        _global_notification_service = NotificationService()
    return _global_notification_service


def get_operations_service(
    client: Neo4jClient = Depends(get_neo4j_client),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    risk_engine: ExplainableRiskEngine = Depends(get_risk_engine),
    account_service: AccountService = Depends(get_account_service),
    alert_service: AlertService = Depends(get_alert_service),
    case_service: CaseService = Depends(get_case_service),
    network_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
    prioritization_service: AlertPrioritizationService = Depends(get_alert_prioritization_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> OperationsService:
    """Returns OperationsService instance."""
    return OperationsService(
        client=client,
        detection_engine=detection_engine,
        risk_engine=risk_engine,
        account_service=account_service,
        alert_service=alert_service,
        case_service=case_service,
        network_service=network_service,
        prioritization_service=prioritization_service,
        audit_service=audit_service,
    )


def get_case_intelligence_service() -> CaseIntelligenceService:
    """Returns singleton CaseIntelligenceService instance."""
    from backend.app.case_intelligence.service import get_case_intelligence_service as _get_cis
    return _get_cis()


def get_network_evolution_service() -> NetworkEvolutionService:
    """Returns singleton NetworkEvolutionService."""
    from backend.app.network_evolution.service import get_network_evolution_service as _get_nes
    return _get_nes()


def get_early_warning_service() -> EarlyWarningService:
    """Returns singleton EarlyWarningService."""
    from backend.app.early_warning.service import get_early_warning_service as _get_ews
    return _get_ews()


def get_pattern_discovery_service() -> PatternDiscoveryService:
    """Returns singleton PatternDiscoveryService."""
    from backend.app.pattern_discovery.service import get_pattern_discovery_service as _get_pds
    return _get_pds()


def get_autonomous_intelligence_service() -> "AutonomousIntelligenceService":
    """Returns singleton AutonomousIntelligenceService."""
    from backend.app.autonomous_intelligence.service import get_autonomous_intelligence_service as _get_ais
    return _get_ais()


def get_shadow_detection_service() -> "ShadowDetectionService":
    """Returns singleton ShadowDetectionService."""
    from backend.app.shadow_detection.service import get_shadow_detection_service as _get_sds
    return _get_sds()


def get_risk_calibration_service() -> "RiskCalibrationService":
    """Returns singleton RiskCalibrationService."""
    from backend.app.risk_calibration.service import get_risk_calibration_service as _get_rcs
    return _get_rcs()


def get_threat_propagation_service() -> "ThreatPropagationService":
    """Returns singleton ThreatPropagationService."""
    from backend.app.threat_propagation.service import get_threat_propagation_service as _get_tps
    return _get_tps()


def get_intelligence_orchestration_service() -> "IntelligenceOrchestrationService":
    """Returns singleton IntelligenceOrchestrationService."""
    from backend.app.intelligence_orchestration.service import get_intelligence_orchestration_service as _get_ios
    return _get_ios()
