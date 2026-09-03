"""
FinGraph GDS Analytics & Risk Scoring Configuration.
Loads configurable thresholds, weights, and graph projection parameters.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class RiskScoringConfig:
    """Configurable weights and thresholds for explainable risk calculation."""
    # Model Version
    model_version: str = os.getenv("RISK_MODEL_VERSION", "rule-gds-v1")

    # Neo4j Connectivity
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "fingraph_secret_pass")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # GDS In-Memory Projection Name
    gds_graph_name: str = os.getenv("GDS_GRAPH_NAME", "fingraph")

    # Primary Component Weights (Must sum to 1.0)
    rule_weight: float = float(os.getenv("RISK_RULE_WEIGHT", "0.60"))
    graph_weight: float = float(os.getenv("RISK_GRAPH_WEIGHT", "0.40"))

    # Risk Level Classification Thresholds (0 - 100 scale)
    low_max_score: float = float(os.getenv("RISK_LOW_MAX", "24.99"))
    medium_max_score: float = float(os.getenv("RISK_MEDIUM_MAX", "49.99"))
    high_max_score: float = float(os.getenv("RISK_HIGH_MAX", "74.99"))

    # Rule Signal Individual Contributions (Bounded sum capped at 100)
    funnel_signal_points: float = float(os.getenv("SIGNAL_FUNNEL_POINTS", "25.0"))
    circular_signal_points: float = float(os.getenv("SIGNAL_CIRCULAR_POINTS", "30.0"))
    layered_signal_points: float = float(os.getenv("SIGNAL_LAYERED_POINTS", "30.0"))
    one_to_many_signal_points: float = float(os.getenv("SIGNAL_ONE_TO_MANY_POINTS", "15.0"))
    chain_signal_points: float = float(os.getenv("SIGNAL_CHAIN_POINTS", "15.0"))
    high_degree_signal_points: float = float(os.getenv("SIGNAL_HIGH_DEGREE_POINTS", "10.0"))

    # GDS Algorithm Weights within Graph Subscore (sum to 100)
    pagerank_subweight: float = float(os.getenv("GDS_PAGERANK_SUBWEIGHT", "40.0"))
    degree_subweight: float = float(os.getenv("GDS_DEGREE_SUBWEIGHT", "30.0"))
    community_subweight: float = float(os.getenv("GDS_COMMUNITY_SUBWEIGHT", "30.0"))


def get_risk_scoring_config() -> RiskScoringConfig:
    return RiskScoringConfig()
