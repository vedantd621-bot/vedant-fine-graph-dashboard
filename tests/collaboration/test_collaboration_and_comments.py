"""
Unit tests for CaseIntelligenceService collaboration, comments, and role RBAC.
"""
import pytest
from backend.app.case_intelligence.models import (
    AddCollaboratorRequest,
    AddCommentRequest,
    CollaboratorRole,
    UpdateCommentRequest,
)
from backend.app.case_intelligence.service import CaseIntelligenceService
from backend.app.services.case_service import CaseService


def test_collaborator_management_and_roles():
    case_service = CaseService()
    service = CaseIntelligenceService(case_service=case_service)

    case_id = "CASE-2026-001"

    # Add collaborator
    collab = service.add_collaborator(
        case_id=case_id,
        req=AddCollaboratorRequest(
            user_id="usr_inv_99",
            username="investigator_specialist",
            role=CollaboratorRole.COLLABORATOR,
        ),
        actor_id="usr_admin_001",
        actor_name="admin",
    )

    assert collab.username == "investigator_specialist"
    assert collab.role == CollaboratorRole.COLLABORATOR

    collabs = service.list_collaborators(case_id)
    assert any(c.username == "investigator_specialist" for c in collabs)

    # Update role to WATCHER
    service.add_collaborator(
        case_id=case_id,
        req=AddCollaboratorRequest(
            user_id="usr_inv_99",
            username="investigator_specialist",
            role=CollaboratorRole.WATCHER,
        ),
        actor_id="usr_admin_001",
        actor_name="admin",
    )
    collabs = service.list_collaborators(case_id)
    updated = next(c for c in collabs if c.user_id == "usr_inv_99")
    assert updated.role == CollaboratorRole.WATCHER

    # Remove collaborator
    removed = service.remove_collaborator(
        case_id=case_id,
        user_id="usr_inv_99",
        actor_id="usr_admin_001",
        actor_name="admin",
    )
    assert removed is True
    assert not any(c.user_id == "usr_inv_99" for c in service.list_collaborators(case_id))


def test_comment_lifecycle_and_soft_delete():
    case_service = CaseService()
    service = CaseIntelligenceService(case_service=case_service)

    case_id = "CASE-2026-001"

    # 1. Add comment
    comment = service.add_comment(
        case_id=case_id,
        req=AddCommentRequest(content="Identified mule hub account routing $50k."),
        author_id="usr_inv_002",
        author_name="investigator",
    )
    assert comment.content == "Identified mule hub account routing $50k."
    assert comment.is_edited is False
    assert comment.is_deleted is False

    # 2. List comments
    comments = service.list_comments(case_id)
    assert any(c.comment_id == comment.comment_id for c in comments)

    # 3. Edit comment
    edited = service.update_comment(
        case_id=case_id,
        comment_id=comment.comment_id,
        req=UpdateCommentRequest(content="Corrected: Identified mule hub routing $75k."),
        actor_id="usr_inv_002",
        actor_name="investigator",
    )
    assert edited.is_edited is True
    assert edited.content == "Corrected: Identified mule hub routing $75k."

    # 4. Soft delete comment
    deleted = service.delete_comment(
        case_id=case_id,
        comment_id=comment.comment_id,
        actor_id="usr_inv_002",
        actor_name="investigator",
    )
    assert deleted is True

    # Ensure deleted comment is filtered out of active list
    active_comments = service.list_comments(case_id)
    assert not any(c.comment_id == comment.comment_id for c in active_comments)
