"""
FinGraph Health, Liveness & Readiness Endpoints.
Reports operational state of FastAPI application, Neo4j graph connectivity, Kafka, and WebSocket streams.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.config import get_api_config
from backend.app.dependencies import get_neo4j_client
from backend.app.realtime.connection_manager import get_connection_manager
from backend.app.realtime.kafka_consumer import get_realtime_kafka_consumer
from neo4j.src.client import Neo4jClient

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Basic service health check."""
    config = get_api_config()
    return {
        "status": "ok",
        "service": config.app_name,
        "version": config.app_version,
        "environment": config.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/live")
def liveness_probe():
    """Kubernetes / Container Liveness Probe verifying application process is responsive."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/ready")
def readiness_probe(
    client: Neo4jClient = Depends(get_neo4j_client),
):
    """Kubernetes / Container Readiness Probe verifying database dependencies are accessible."""
    is_connected = False
    try:
        is_connected = client.verify_connectivity()
    except Exception:
        is_connected = False

    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "NOT_READY", "message": "Neo4j graph database is not connected."},
        )

    return {
        "status": "ready",
        "neo4j": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/neo4j")
def neo4j_health_check(
    client: Neo4jClient = Depends(get_neo4j_client),
):
    """Deep health check verifying Neo4j Bolt connectivity and basic query execution."""
    try:
        if client.verify_connectivity():
            records = client.execute_query("RETURN 1 AS ping")
            if records and records[0]["ping"] == 1:
                return {
                    "status": "ok",
                    "database": "connected",
                    "latency_ms": "<5.0",
                }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "NEO4J_UNAVAILABLE", "message": str(exc)},
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "NEO4J_UNAVAILABLE", "message": "Failed to connect to Neo4j graph database."},
    )


@router.get("/health/kafka")
def kafka_health_check():
    """Checks streaming Kafka consumer broker reachability."""
    consumer = get_realtime_kafka_consumer()
    cfg = get_api_config()
    return {
        "status": "ok" if consumer.is_connected else "degraded",
        "broker": cfg.kafka_bootstrap_servers,
        "topic": cfg.kafka_topic,
        "consumer_group": cfg.kafka_realtime_group,
        "connected": consumer.is_connected,
    }
