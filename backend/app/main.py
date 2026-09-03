"""
FinGraph FastAPI Main Application.
Provides RESTful APIs for real-time fraud syndicate detection, GDS analytics,
account dossiers, interactive network visualization, and forensic case management.
"""
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
from backend.app.models.common import ApiErrorDetail, ApiErrorResponse
from backend.app.routes.health import router as health_router
from backend.app.routes.alerts import router as alerts_router
from backend.app.routes.accounts import router as accounts_router
from backend.app.routes.graph import router as graph_router
from backend.app.routes.dashboard import router as dashboard_router
from backend.app.routes.investigation import router as investigation_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [FinGraphAPI] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FinGraph.API")
config = get_api_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {config.app_name} v{config.app_version} ({config.app_env})...")
    client = get_neo4j_client()
    try:
        if client.verify_connectivity():
            logger.info("Successfully connected to Neo4j graph database.")
        else:
            logger.warning("Neo4j database connection could not be established at startup.")
    except Exception as exc:
        logger.warning(f"Neo4j startup check note: {exc}")

    yield

    logger.info("Shutting down FinGraph API...")
    if client:
        client.close()


app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="Real-Time Fraud Syndicate Analytics & Graph Investigation REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS for React UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_log(request: Request, call_next):
    """Logs incoming requests with response latency without logging sensitive payloads."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000.0

    # Add header
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles standard HTTPExceptions with consistent ApiErrorResponse envelope."""
    msg = exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", "Request error")
    code = exc.detail.get("code", "HTTP_ERROR") if isinstance(exc.detail, dict) else "HTTP_ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": msg}},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled server exceptions safely without leaking internal stacktraces."""
    logger.error(f"Unhandled error processing {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}},
    )


# Mount Routers
app.include_router(health_router)
app.include_router(alerts_router)
app.include_router(accounts_router)
app.include_router(graph_router)
app.include_router(dashboard_router)
app.include_router(investigation_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=config.api_host, port=config.api_port, reload=config.debug)
