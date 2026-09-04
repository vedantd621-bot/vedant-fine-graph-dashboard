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
from backend.app.routes.auth import router as auth_router
from backend.app.routes.admin import router as admin_router
from backend.app.routes.metrics import router as metrics_router
from backend.app.routes.cases import router as cases_router
from backend.app.routes.intelligence import router as intelligence_router
from backend.app.routes.networks import router as networks_router
from backend.app.routes.behavior import router as behavior_router
from backend.app.routes.features import router as features_router

__all__ = [
    "health_router",
    "alerts_router",
    "accounts_router",
    "graph_router",
    "dashboard_router",
    "investigation_router",
    "websocket_router",
    "auth_router",
    "admin_router",
    "metrics_router",
    "cases_router",
    "intelligence_router",
    "networks_router",
    "behavior_router",
    "features_router",
]

