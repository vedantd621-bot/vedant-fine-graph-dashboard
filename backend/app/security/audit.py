"""
FinGraph Audit Logging Service.
Records immutable audit entries for administrative actions, forensic mutations, and access events.
"""
from typing import List, Optional, Tuple
from backend.app.security.models import AuditLog


class AuditService:
    """In-memory thread-safe audit trail service."""

    def __init__(self):
        self._logs: List[AuditLog] = []

    def record(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        request_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> AuditLog:
        """Appends a new audit log entry."""
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            request_id=request_id,
        )
        self._logs.insert(0, log)
        return log

    def list_logs(
        self,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        """Returns paginated, filtered audit records."""
        filtered = self._logs
        if action:
            filtered = [l for l in filtered if l.action == action]
        if resource_type:
            filtered = [l for l in filtered if l.resource_type == resource_type]
        if user_id:
            filtered = [l for l in filtered if l.user_id == user_id]

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        return filtered[start:end], total


# Singleton instance
_global_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    global _global_audit_service
    if _global_audit_service is None:
        _global_audit_service = AuditService()
    return _global_audit_service
