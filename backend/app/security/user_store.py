"""
FinGraph User Store & Credential Management.
Maintains identity records and seeds initial RBAC role accounts.
"""
from typing import Dict, List, Optional
from backend.app.security.models import CreateUserRequest, Role, UpdateUserRequest, User
from backend.app.security.passwords import hash_password, verify_password


class UserStore:
    """In-memory user directory with persistent defaults."""

    def __init__(self):
        self._users_by_id: Dict[str, User] = {}
        self._users_by_username: Dict[str, str] = {}
        self._seed_default_users()

    def _seed_default_users(self):
        """Initializes default role accounts with secure password hashes."""
        default_accounts = [
            ("admin", "admin_secret_pass_2026", Role.ADMIN, "usr_admin_001"),
            ("investigator", "investigator_secret_pass_2026", Role.INVESTIGATOR, "usr_inv_002"),
            ("analyst", "analyst_secret_pass_2026", Role.ANALYST, "usr_ana_003"),
        ]
        for uname, pwd, role, uid in default_accounts:
            user = User(
                user_id=uid,
                username=uname,
                password_hash=hash_password(pwd),
                role=role,
                is_active=True,
            )
            self._users_by_id[user.user_id] = user
            self._users_by_username[uname.lower()] = user.user_id

    def get_user_by_username(self, username: str) -> Optional[User]:
        uid = self._users_by_username.get(username.lower())
        if uid:
            return self._users_by_id.get(uid)
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self._users_by_id.get(user_id)

    def list_users(self) -> List[User]:
        return list(self._users_by_id.values())

    def create_user(self, req: CreateUserRequest) -> User:
        if req.username.lower() in self._users_by_username:
            raise ValueError(f"Username '{req.username}' already exists.")

        user = User(
            username=req.username,
            password_hash=hash_password(req.password),
            role=req.role,
            is_active=req.is_active,
        )
        self._users_by_id[user.user_id] = user
        self._users_by_username[user.username.lower()] = user.user_id
        return user

    def update_user(self, user_id: str, req: UpdateUserRequest) -> Optional[User]:
        user = self._users_by_id.get(user_id)
        if not user:
            return None

        if req.role is not None:
            user.role = req.role
        if req.is_active is not None:
            user.is_active = req.is_active
        if req.password:
            user.password_hash = hash_password(req.password)

        return user

    def authenticate_user(self, username: str, plain_password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(plain_password, user.password_hash):
            return None
        return user


# Singleton instance
_global_user_store: Optional[UserStore] = None


def get_user_store() -> UserStore:
    global _global_user_store
    if _global_user_store is None:
        _global_user_store = UserStore()
    return _global_user_store
