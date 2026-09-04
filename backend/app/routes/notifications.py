"""
FinGraph In-App Notifications REST Endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.dependencies import get_notification_service
from backend.app.models.common import ApiResponse
from backend.app.models.notifications import (
    AppNotification,
    NotificationListResponse,
)
from backend.app.security.dependencies import get_current_user
from backend.app.security.models import Role, User
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["In-App Notifications"])


@router.get(
    "",
    response_model=ApiResponse[NotificationListResponse],
    summary="List user notifications",
)
def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Returns notifications targeted to the authenticated user or their role."""
    data = service.list_user_notifications(
        user_id=current_user.user_id,
        user_role=current_user.role,
        limit=limit,
    )
    return ApiResponse(data=data)


@router.post(
    "/{notification_id}/read",
    response_model=ApiResponse[AppNotification],
    summary="Mark notification as read",
)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Marks a single notification as read."""
    updated = service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.user_id,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notification_id}' not found.",
        )
    return ApiResponse(data=updated)


@router.post(
    "/read-all",
    response_model=ApiResponse[dict],
    summary="Mark all user notifications as read",
)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Marks all notifications for current user as read."""
    count = service.mark_all_as_read(
        user_id=current_user.user_id,
        user_role=current_user.role,
    )
    return ApiResponse(data={"marked_read_count": count})
