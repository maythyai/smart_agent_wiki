"""Permission management for team deployment.

Phase 5: Team Deployment — Permissions.
Per TEAM-05~07: Role system, Vault permissions.

Integrates with Cedar policy engine from Phase 3-01.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saw.db.models import User, Vault


class Permission(IntEnum):
    """Permission levels."""
    READ = 1
    WRITE = 2
    ADMIN = 3


class Role(IntEnum):
    """User roles."""
    VIEWER = 1
    EDITOR = 2
    ADMIN = 3


@dataclass
class PermissionCheck:
    """Result of a permission check."""
    allowed: bool
    reason: str = ""


ROLE_PERMISSIONS = {
    "admin": [Permission.READ, Permission.WRITE, Permission.ADMIN],
    "editor": [Permission.READ, Permission.WRITE],
    "viewer": [Permission.READ],
}


def get_role_permissions(role: str) -> list[Permission]:
    """Get permissions for a role."""
    return ROLE_PERMISSIONS.get(role, [Permission.READ])


def has_permission(role: str, required: Permission) -> bool:
    """Check if a role has a specific permission."""
    return required in get_role_permissions(role)


class PermissionService:
    """Service for permission management."""

    def __init__(self, cedar_engine: "CedarPolicyEngine | None" = None) -> None:
        # Cedar policy engine (from Phase 3-01). If a policy file is
        # configured, resource-level policy checks are available.
        self._cedar = cedar_engine
        self._cedar_enabled = cedar_engine is not None

    def check_cedar(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> PermissionCheck:
        """Evaluate a Cedar policy rule (D-14 default deny)."""
        if not self._cedar:
            return PermissionCheck(allowed=True, reason="cedar_disabled")
        try:
            allowed = self._cedar.is_authorized(principal, action, resource, context)
            return PermissionCheck(allowed=allowed, reason="cedar_policy")
        except Exception:
            return PermissionCheck(allowed=False, reason="cedar_error")

    def check_vault_access(
        self,
        user: "User",
        vault: "Vault",
        required: Permission,
    ) -> PermissionCheck:
        """Check if user can access a vault.

        Rules:
        1. Owner always has full access
        2. Shared vaults check vault_permissions table
        3. Private vaults only allow owner
        """
        # Owner check
        if vault.owner_id == user.id:
            return PermissionCheck(allowed=True, reason="owner")

        # Admin role override
        if user.role == "admin":
            return PermissionCheck(allowed=True, reason="admin_role")

        # Private vault - only owner
        if not vault.is_shared:
            return PermissionCheck(
                allowed=False,
                reason="private_vault"
            )

        # Check role-based permission
        user_perms = get_role_permissions(user.role)
        if required in user_perms:
            return PermissionCheck(allowed=True, reason="role_permission")

        return PermissionCheck(allowed=False, reason="no_permission")

    def check_vault_permission(
        self,
        user: "User",
        vault: "Vault",
        vault_permissions: list,  # List of VaultPermission
        required: Permission,
    ) -> PermissionCheck:
        """Check vault-specific permissions."""
        # Owner check first
        if vault.owner_id == user.id:
            return PermissionCheck(allowed=True, reason="owner")

        # Private vault
        if not vault.is_shared:
            return PermissionCheck(allowed=False, reason="private")

        # Check explicit permission
        for perm in vault_permissions:
            if perm.user_id == user.id:
                perm_level = Permission[perm.permission.upper()]
                if perm_level >= required:
                    return PermissionCheck(
                        allowed=True,
                        reason=f"granted:{perm.permission}"
                    )

        return PermissionCheck(allowed=False, reason="not_granted")

    def can_create_vault(self, user: "User") -> bool:
        """Check if user can create vaults."""
        return user.role in ("admin", "editor") and user.is_active

    def can_delete_vault(
        self,
        user: "User",
        vault: "Vault",
    ) -> bool:
        """Check if user can delete a vault."""
        # Only owner or admin can delete
        return vault.owner_id == user.id or user.role == "admin"

    def can_share_vault(
        self,
        user: "User",
        vault: "Vault",
    ) -> bool:
        """Check if user can share a vault."""
        # Only owner or admin can share
        return vault.owner_id == user.id or user.role == "admin"

    def can_invite_user(self, user: "User") -> bool:
        """Check if user can invite new users."""
        return user.role == "admin"

    def can_modify_user_role(
        self,
        actor: "User",
        target: "User",
    ) -> bool:
        """Check if actor can modify target's role."""
        # Only admin can change roles
        if actor.role != "admin":
            return False
        # Can't modify own role
        if actor.id == target.id:
            return False
        return True


def require_role(*roles: str):
    """Decorator to require specific roles for API endpoints.

    Usage:
        @require_role("admin", "editor")
        async def create_vault(request):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs or args
            user = kwargs.get("current_user")
            if user is None:
                from fastapi import HTTPException
                raise HTTPException(401, "Not authenticated")

            if user.role not in roles:
                from fastapi import HTTPException
                raise HTTPException(403, f"Requires role: {roles}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if user is None:
                from fastapi import HTTPException
                raise HTTPException(401, "Not authenticated")

            user_perms = get_role_permissions(user.role)
            if permission not in user_perms:
                from fastapi import HTTPException
                raise HTTPException(403, f"Requires permission: {permission.name}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
