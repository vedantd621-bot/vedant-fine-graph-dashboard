"""
FinGraph Operational Notification Service.
Manages in-app notifications, unread tracking, role-scoped dispatching,
and real-time WebSocket broadcasting.
"""
import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
import uuid

logger = logging.getLogger("FinGraph.NotificationService")

from backend.app.models.notifications import (
    AppNotification,
    NotificationListResponse,
    NotificationSeverity,
    NotificationType,
)
from backend.app.realtime.event_bus import EventBus, get_event_bus
from backend.app.realtime.events import (
    EventType,
    NotificationCreatedPayload,
    create_realtime_event,
)
from backend.app.security.models import Role

# In-memory thread-safe notifications store: notification_id -> AppNotification
_notifications_store: Dict[str, AppNotification] = {}


class NotificationService:
    """Service providing in-app notifications and WebSocket dispatching."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()

    def create_notification(
        self,
        type: NotificationType,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        user_id: Optional[str] = None,
        target_role: Optional[Role] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> AppNotification:
        """Creates, stores, and broadcasts an operational notification."""
        notif_id = f"notif_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)

        notif = AppNotification(
            notification_id=notif_id,
            user_id=user_id,
            target_role=target_role,
            type=type,
            severity=severity,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            is_read=False,
            created_at=now,
        )
        _notifications_store[notif_id] = notif

        # Emit Real-time Notification event
        payload = NotificationCreatedPayload(
            notification_id=notif_id,
            user_id=user_id,
            target_role=target_role.value if target_role else None,
            type=type.value,
            severity=severity.value,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            created_at=now,
        )
        evt = create_realtime_event(EventType.NOTIFICATION_CREATED, payload)
        try:
            asyncio.create_task(self.event_bus.publish(evt))
        except RuntimeError:
            pass

        return notif

    def list_user_notifications(
        self,
        user_id: str,
        user_role: Role,
        limit: int = 50,
    ) -> NotificationListResponse:
        """Lists notifications targeted to a user or their role."""
        matched: List[AppNotification] = []
        for notif in _notifications_store.values():
            # Check user target
            if notif.user_id and notif.user_id != user_id:
                continue
            # Check role target
            if notif.target_role and notif.target_role != user_role and user_role != Role.ADMIN:
                continue

            matched.append(notif)

        # Sort descending by created_at
        matched.sort(key=lambda x: x.created_at, reverse=True)
        unread_count = len([n for n in matched if not n.is_read])
        paginated = matched[:limit]

        return NotificationListResponse(
            notifications=paginated,
            unread_count=unread_count,
        )

    def mark_as_read(self, notification_id: str, user_id: str) -> Optional[AppNotification]:
        """Marks a notification as read."""
        notif = _notifications_store.get(notification_id)
        if not notif:
            return None

        # Update in place
        updated = notif.model_copy(update={"is_read": True})
        _notifications_store[notification_id] = updated
        return updated

    def mark_all_as_read(self, user_id: str, user_role: Role) -> int:
        """Marks all notifications for user as read."""
        count = 0
        for nid, notif in list(_notifications_store.items()):
            if notif.user_id == user_id or (notif.target_role == user_role and not notif.user_id):
                if not notif.is_read:
                    _notifications_store[nid] = notif.model_copy(update={"is_read": True})
                    count += 1
        return count
