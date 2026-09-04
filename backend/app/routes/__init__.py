from backend.app.routes.advanced_intelligence import router as advanced_intelligence_router
"""
FinGraph API Route Modules.
"""
from backend.app.routes.accounts import router as accounts_router
from backend.app.routes.admin import router as admin_router
from backend.app.routes.alerts import router as alerts_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.behavior import router as behavior_router
from backend.app.routes.cases import router as cases_router
from backend.app.routes.case_intelligence import router as case_intelligence_router
from backend.app.routes.dashboard import router as dashboard_router
from backend.app.routes.features import router as features_router
from backend.app.routes.graph import router as graph_router
from backend.app.routes.health import router as health_router
from backend.app.routes.intelligence import router as intelligence_router
from backend.app.routes.investigation import router as investigation_router
from backend.app.routes.metrics import router as metrics_router
from backend.app.routes.networks import router as networks_router
from backend.app.routes.notifications import router as notifications_router
from backend.app.routes.operations import router as operations_router
from backend.app.routes.websocket import router as websocket_router

__all__ = [
    "advanced_intelligence_router",
    "accounts_router",
    "admin_router",
    "alerts_router",
    "auth_router",
    "behavior_router",
    "case_intelligence_router",
    "cases_router",
    "dashboard_router",
    "features_router",
    "graph_router",
    "health_router",
    "intelligence_router",
    "investigation_router",
    "metrics_router",
    "networks_router",
    "notifications_router",
    "operations_router",
    "websocket_router",
]
from backend.app.routes.autonomous_intelligence import router as autonomous_intelligence_router
