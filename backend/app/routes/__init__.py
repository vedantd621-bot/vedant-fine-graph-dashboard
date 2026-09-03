"""
FinGraph API Routes Package.
"""
from backend.app.routes.health import router as health_router
from backend.app.routes.alerts import router as alerts_router
from backend.app.routes.accounts import router as accounts_router
from backend.app.routes.graph import router as graph_router
from backend.app.routes.dashboard import router as dashboard_router
from backend.app.routes.investigation import router as investigation_router
from backend.app.routes.websocket import router as websocket_router

__all__ = [
    "health_router",
    "alerts_router",
    "accounts_router",
    "graph_router",
    "dashboard_router",
    "investigation_router",
    "websocket_router",
]
