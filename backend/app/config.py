"""
FinGraph Backend API Configuration.
Loads environment variables for FastAPI server, CORS, WebSocket real-time bus, and Neo4j connectivity.
"""
import os
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class ApiConfig(BaseModel):
    """Configuration parameters for the FinGraph FastAPI server."""
    app_name: str = "FinGraph API"
    app_version: str = "1.0.0"
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    api_host: str = Field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = Field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    debug: bool = Field(default_factory=lambda: os.getenv("API_DEBUG", "false").lower() == "true")

    # CORS settings
    frontend_origins: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "FRONTEND_ORIGINS",
                "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
            ).split(",")
            if origin.strip()
        ]
    )

    # Neo4j Connectivity
    neo4j_uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    neo4j_password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", "fingraph_secret_pass"))
    neo4j_database: str = Field(default_factory=lambda: os.getenv("NEO4J_DATABASE", "neo4j"))

    # Kafka Real-Time Streaming Consumer
    kafka_bootstrap_servers: str = Field(default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    kafka_topic: str = Field(default_factory=lambda: os.getenv("KAFKA_TOPIC", "transactions"))
    kafka_realtime_enabled: bool = Field(default_factory=lambda: os.getenv("KAFKA_REALTIME_ENABLED", "true").lower() == "true")
    kafka_realtime_group: str = Field(default_factory=lambda: os.getenv("KAFKA_REALTIME_GROUP", "fingraph-realtime-api"))

    # Real-Time & WebSocket Configuration
    realtime_enabled: bool = Field(default_factory=lambda: os.getenv("REALTIME_ENABLED", "true").lower() == "true")
    websocket_path: str = Field(default_factory=lambda: os.getenv("WEBSOCKET_PATH", "/api/v1/ws"))
    realtime_heartbeat_seconds: int = Field(default_factory=lambda: int(os.getenv("REALTIME_HEARTBEAT_SECONDS", "30")))
    realtime_max_clients: int = Field(default_factory=lambda: int(os.getenv("REALTIME_MAX_CLIENTS", "100")))
    realtime_queue_size: int = Field(default_factory=lambda: int(os.getenv("REALTIME_QUEUE_SIZE", "1000")))

    # Safety limits for graph queries
    max_graph_depth: int = Field(default_factory=lambda: int(os.getenv("MAX_GRAPH_DEPTH", "3")))
    max_graph_nodes: int = Field(default_factory=lambda: int(os.getenv("MAX_GRAPH_NODES", "100")))
    max_graph_edges: int = Field(default_factory=lambda: int(os.getenv("MAX_GRAPH_EDGES", "250")))
    default_page_size: int = 20
    max_page_size: int = 100


def get_api_config() -> ApiConfig:
    return ApiConfig()
