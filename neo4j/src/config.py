"""
FinGraph Neo4j Configuration.
Loads environment variables for Neo4j Bolt connection URI, credentials, database, and pooling parameters.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Neo4jConfig:
    """Neo4j client connection and operational configuration."""
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.getenv("NEO4J_USER", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "fingraph_secret_pass")
    database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    max_connection_pool_size: int = int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50"))
    connection_timeout: int = int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30"))


def get_neo4j_config() -> Neo4jConfig:
    return Neo4jConfig()
