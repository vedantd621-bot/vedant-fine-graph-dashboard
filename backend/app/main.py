from backend.app.routes.orchestration import router as orchestration_router
from backend.app.routes.autonomous_intelligence import router as autonomous_intelligence_router
from backend.app.routes.control_plane import router as control_plane_router
"""
FinGraph FastAPI Main Application.
Provides hardened RESTful APIs and real-time WebSockets with JWT Authentication, RBAC,
Rate Limiting, Security Headers, Prometheus Observability, and Graph Investigation tools.
"""
import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure project root in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import get_api_config
from backend.app.dependencies import get_neo4j_client
from backend.app.logging import setup_logging
from backend.app.metrics.prometheus import get_metrics
from backend.app.middleware.body_limit import BodySizeLimitMiddleware
from backend.app.middleware.rate_limiter import RateLimiterMiddleware
from backend.app.middleware.request_id import RequestIdMiddleware
from backend.app.middleware.security_headers import SecurityHeadersMiddleware
from backend.app.realtime.connection_manager import get_connection_manager
from backend.app.realtime.kafka_consumer import get_realtime_kafka_consumer
from backend.app.routes import (
    accounts_router,
    admin_router,
    alerts_router,
    auth_router,
    behavior_router,
    advanced_intelligence_router,
    case_intelligence_router,
    cases_router,
    dashboard_router,
    features_router,
    graph_router,
    health_router,
    intelligence_router,
    investigation_router,
    metrics_router,
    networks_router,
    notifications_router,
    operations_router,
    websocket_router,
)

config = get_api_config()
setup_logging(
    level=config.app_env.upper() if config.debug else "INFO",
    json_format=config.app_env.lower() == "production",
)
logger = logging.getLogger("FinGraph.API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {config.app_name} v{config.app_version} [{config.app_env}]...")
    client = get_neo4j_client()
    try:
        if client.verify_connectivity():
            logger.info("Successfully connected to Neo4j graph database.")
        else:
            logger.warning("Neo4j database connection could not be established at startup.")
    except Exception as exc:
        logger.warning(f"Neo4j startup check note: {exc}")

    # Start Realtime Connection Manager & Kafka Consumer
    conn_mgr = get_connection_manager()
    await conn_mgr.start()

    kafka_consumer = get_realtime_kafka_consumer()
    try:
        loop = asyncio.get_running_loop()
        kafka_consumer.start(loop=loop)
    except Exception as exc:
        logger.warning(f"Kafka consumer startup note: {exc}")

    yield

    logger.info("Shutting down FinGraph API...")
    kafka_consumer.stop()
    await conn_mgr.stop()
    if client:
        client.close()


app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="Production-Grade Real-Time Fraud Syndicate Analytics & Graph Investigation Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 1. Attach Request ID Middleware
app.add_middleware(RequestIdMiddleware)

# 2. Attach Security Hardening Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 3. Attach Rate Limiter Middleware
app.add_middleware(RateLimiterMiddleware)

# 4. Attach Request Body Size Limiter
app.add_middleware(BodySizeLimitMiddleware)

# 5. Configure Strict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time-Ms", "Retry-After"],
)


@app.middleware("http")
async def record_metrics_and_log(request: Request, call_next):
    """Measures latency, updates Prometheus telemetry, and logs request correlation."""
    start_time = time.time()
    response = await call_next(request)
    duration_sec = time.time() - start_time
    duration_ms = duration_sec * 1000.0

    # Record in Prometheus
    metrics = get_metrics()
    metrics.record_http_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=duration_sec,
    )

    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    req_id = getattr(request.state, "request_id", "-")

    logger.info(
        f"[{req_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles HTTPExceptions with consistent error envelope and request correlation ID."""
    req_id = getattr(request.state, "request_id", "unknown")
    msg = exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", "Request error")
    code = exc.detail.get("code", "HTTP_ERROR") if isinstance(exc.detail, dict) else "HTTP_ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={"error": {"code": code, "message": msg, "request_id": req_id}},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Centralized unhandled exception handler without leaking stack traces."""
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{req_id}] Unhandled server exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please contact support with request_id.",
                "request_id": req_id,
            }
        },
    )


# Mount Hardened Routers
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(alerts_router)
app.include_router(accounts_router)
app.include_router(cases_router)
app.include_router(case_intelligence_router)
app.include_router(advanced_intelligence_router)
app.include_router(intelligence_router)
app.include_router(operations_router)
app.include_router(notifications_router)
app.include_router(networks_router)
app.include_router(behavior_router)
app.include_router(features_router)
app.include_router(graph_router)
app.include_router(dashboard_router)
app.include_router(investigation_router)
app.include_router(websocket_router)
app.include_router(autonomous_intelligence_router)
app.include_router(orchestration_router)
app.include_router(control_plane_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=config.api_host, port=config.api_port, reload=config.debug)
