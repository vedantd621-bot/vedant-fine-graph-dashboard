"""
Tests for User Lifecycle & Identity Store in Phase 20.
"""
import pytest
from backend.app.security.models import CreateUserRequest, Role, UpdateUserRequest
from backend.app.security.user_store import UserStore

@pytest.fixture
def store():
    return UserStore()

def test_user_creation_and_authentication(store):
    req = CreateUserRequest(
        username="john_doe",
        password="secure_password_123",
        role=Role.INVESTIGATOR,
        tenant_id="tnt_alpha",
        organization_id="org_alpha",
    )
    user = store.create_user(req)
    assert user.user_id.startswith("usr_")
    assert user.tenant_id == "tnt_alpha"
    assert user.role == Role.INVESTIGATOR

    auth_user = store.authenticate_user("john_doe", "secure_password_123")
    assert auth_user is not None
    assert auth_user.user_id == user.user_id

    # Wrong password
    assert store.authenticate_user("john_doe", "wrong_pass") is None

def test_user_status_suspension(store):
    req = CreateUserRequest(username="jane_doe", password="pwd", role=Role.ANALYST)
    user = store.create_user(req)
    assert user.is_active is True

    # Suspend user
    store.update_user(user.user_id, UpdateUserRequest(is_active=False))
    # Authenticate should fail for inactive user
    assert store.authenticate_user("jane_doe", "pwd") is None
