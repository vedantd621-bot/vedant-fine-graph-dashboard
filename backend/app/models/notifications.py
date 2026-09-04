"""
FinGraph Notification Models.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.security.models import Role


class NotificationType(str, Enum):
    """Notification classification categories."""
    CRITICAL_ALERT = "CRITICAL_ALERT"
    SLA_WARNING = "SLA_WARNING"
    SLA_BREACH = "SLA_BREACH"
    ALERT_ASSIGNED = "ALERT_ASSIGNED"
    ALERT_REASSIGNED = "ALERT_REASSIGNED"
    CASE_ESCALATED = "CASE_ESCALATED"
    NETWORK_DISCOVERY = "NETWORK_DISCOVERY"
    SYSTEM_NOTICE = "SYSTEM_NOTICE"


class NotificationSeverity(str, Enum):
    """Notification severity tiers."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AppNotification(BaseModel):
    """In-app operational notification entity."""
    notification_id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:10]}")
    user_id: Optional[str] = None  # Targeted to specific user, or None for role broadcast
    target_role: Optional[Role] = None
    type: NotificationType
    severity: NotificationSeverity = NotificationSeverity.INFO
    title: str
    message: str
    resource_type: Optional[str] = None  # "ALERT", "CASE", "NETWORK", "ACCOUNT"
    resource_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationListResponse(BaseModel):
    """User notifications list response with unread count."""
    notifications: List[AppNotification]
    unread_count: int
