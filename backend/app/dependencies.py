"""
FinGraph FastAPI Dependency Injection Provider.
Provides singleton Neo4j client, DetectionEngine, GDSManager, and RiskEngine instances to route handlers.
"""
import logging
import sys
from pathlib import Path
from typing import Generator

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

logger = logging.getLogger("FinGraph.Dependencies")

_global_client: Neo4jClient = None
_global_detection_engine: DetectionEngine = None
_global_gds_manager: GDSManager = None
_global_risk_engine: ExplainableRiskEngine = None


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


def get_detection_engine() -> DetectionEngine:
    """Returns singleton DetectionEngine."""
    global _global_detection_engine
    if _global_detection_engine is None:
        client = get_neo4j_client()
        _global_detection_engine = DetectionEngine(client=client)
    return _global_detection_engine


def get_gds_manager() -> GDSManager:
    """Returns singleton GDSManager."""
    global _global_gds_manager
    if _global_gds_manager is None:
        client = get_neo4j_client()
        _global_gds_manager = GDSManager(client=client)
    return _global_gds_manager


def get_risk_engine() -> ExplainableRiskEngine:
    """Returns singleton ExplainableRiskEngine."""
    global _global_risk_engine
    if _global_risk_engine is None:
        client = get_neo4j_client()
        det_eng = get_detection_engine()
        gds_mgr = get_gds_manager()
        _global_risk_engine = ExplainableRiskEngine(
            client=client,
            detection_engine=det_eng,
            gds_manager=gds_mgr,
        )
    return _global_risk_engine
