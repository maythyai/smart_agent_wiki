"""Authentication package for Smart Agent Wiki.

Phase 5: Team Deployment — Authentication.
"""

from saw.auth.jwt_auth import (
    AuthConfig,
    AuthService,
    JWTHandler,
    PasswordHasher,
    TokenData,
    TokenPair,
    hash_token,
)
from saw.auth.permissions import (
    Permission,
    Role,
    PermissionCheck,
    PermissionService,
    get_role_permissions,
    has_permission,
    require_role,
    require_permission,
)

__all__ = [
    # JWT Auth
    "AuthConfig",
    "AuthService",
    "JWTHandler",
    "PasswordHasher",
    "TokenData",
    "TokenPair",
    "hash_token",
    # Permissions
    "Permission",
    "Role",
    "PermissionCheck",
    "PermissionService",
    "get_role_permissions",
    "has_permission",
    "require_role",
    "require_permission",
]