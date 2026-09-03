"""
FinGraph Fraud Detection Configuration.
Loads default threshold parameters and Neo4j connection settings for the Cypher detection engine.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DetectionConfig:
    """Configurable threshold and connectivity parameters for fraud detectors."""
    # Neo4j Connectivity
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "fingraph_secret_pass")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # Funnel Detector Thresholds
    funnel_min_sources: int = int(os.getenv("DETECTION_FUNNEL_MIN_SOURCES", "3"))
    funnel_min_total_amount: float = float(os.getenv("DETECTION_FUNNEL_MIN_AMOUNT", "1000.0"))

    # One-to-Many Distribution Thresholds
    distribution_min_destinations: int = int(os.getenv("DETECTION_DISTRIB_MIN_DESTINATIONS", "4"))
    distribution_min_total_amount: float = float(os.getenv("DETECTION_DISTRIB_MIN_AMOUNT", "1000.0"))

    # Chain Layering Thresholds
    chain_min_depth: int = int(os.getenv("DETECTION_CHAIN_MIN_DEPTH", "3"))
    chain_max_depth: int = int(os.getenv("DETECTION_CHAIN_MAX_DEPTH", "6"))

    # Circular Flow Thresholds
    circular_min_length: int = int(os.getenv("DETECTION_CIRCULAR_MIN_LENGTH", "2"))
    circular_max_length: int = int(os.getenv("DETECTION_CIRCULAR_MAX_LENGTH", "5"))

    # Layered Network Thresholds
    layered_min_sources: int = int(os.getenv("DETECTION_LAYERED_MIN_SOURCES", "2"))
    layered_min_intermediaries: int = int(os.getenv("DETECTION_LAYERED_MIN_INTERMEDIARIES", "2"))
    layered_min_destinations: int = int(os.getenv("DETECTION_LAYERED_MIN_DESTINATIONS", "2"))

    # High-Degree Hub Thresholds
    high_degree_min_degree: int = int(os.getenv("DETECTION_HIGH_DEGREE_MIN", "4"))


def get_detection_config() -> DetectionConfig:
    return DetectionConfig()
