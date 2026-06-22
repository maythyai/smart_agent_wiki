"""Tests for RBAC permission system.

Phase 40: Test Coverage — TEST-01, SEC-02 validation.
Covers: Permission, Role, PermissionService, require_role, require_permission.
"""
from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from saw.auth.permissions import (
    Permission,
    Role,
    PermissionCheck,
    PermissionService,
    ROLE_PERMISSIONS,
    get_role_permissions,
    has_permission,
    require_role,
    require_permission,
)


# ── Mock Models ───────────────────────────────────────────────────────


@dataclass
class MockUser:
    id: str
    email: str
    role: str
    is_active: bool = True


@dataclass
class MockVault:
    id: str
    owner_id: str
    is_shared: bool = False


@dataclass
class MockVaultPermission:
    user_id: str
    permission: str


# ── Permission Enum Tests ─────────────────────────────────────────────


class TestPermission:
    def test_permission_values(self):
        assert Permission.READ == 1
        assert Permission.WRITE == 2
        assert Permission.ADMIN == 3

    def test_permission_ordering(self):
        assert Permission.READ < Permission.WRITE
        assert Permission.WRITE < Permission.ADMIN


class TestRole:
    def test_role_values(self):
        assert Role.VIEWER == 1
        assert Role.EDITOR == 2
        assert Role.ADMIN == 3


# ── Role Permission Tests ─────────────────────────────────────────────


class TestRolePermissions:
    def test_admin_permissions(self):
        perms = get_role_permissions("admin")
        assert Permission.READ in perms
        assert Permission.WRITE in perms
        assert Permission.ADMIN in perms

    def test_editor_permissions(self):
        perms = get_role_permissions("editor")
        assert Permission.READ in perms
        assert Permission.WRITE in perms
        assert Permission.ADMIN not in perms

    def test_viewer_permissions(self):
        perms = get_role_permissions("viewer")
        assert Permission.READ in perms
        assert Permission.WRITE not in perms
        assert Permission.ADMIN not in perms

    def test_unknown_role(self):
        perms = get_role_permissions("unknown_role")
        assert perms == [Permission.READ]

    def test_has_permission(self):
        assert has_permission("admin", Permission.READ) is True
        assert has_permission("admin", Permission.WRITE) is True
        assert has_permission("admin", Permission.ADMIN) is True
        assert has_permission("editor", Permission.READ) is True
        assert has_permission("editor", Permission.WRITE) is True
        assert has_permission("editor", Permission.ADMIN) is False
        assert has_permission("viewer", Permission.READ) is True
        assert has_permission("viewer", Permission.WRITE) is False
        assert has_permission("viewer", Permission.ADMIN) is False


# ── PermissionService Tests ───────────────────────────────────────────


class TestPermissionService:
    @pytest.fixture
    def service(self):
        return PermissionService()

    def test_owner_always_has_access(self, service):
        user = MockUser(id="owner-1", email="owner@test.com", role="viewer")
        vault = MockVault(id="v1", owner_id="owner-1")

        result = service.check_vault_access(user, vault, Permission.ADMIN)
        assert result.allowed is True
        assert result.reason == "owner"

    def test_admin_always_has_access(self, service):
        user = MockUser(id="admin-1", email="admin@test.com", role="admin")
        vault = MockVault(id="v1", owner_id="other-user", is_shared=False)

        result = service.check_vault_access(user, vault, Permission.WRITE)
        assert result.allowed is True
        assert result.reason == "admin_role"

    def test_private_vault_blocks_non_owner(self, service):
        user = MockUser(id="viewer-1", email="viewer@test.com", role="viewer")
        vault = MockVault(id="v1", owner_id="owner-1", is_shared=False)

        result = service.check_vault_access(user, vault, Permission.READ)
        assert result.allowed is False
        assert result.reason == "private_vault"

    def test_shared_vault_role_check(self, service):
        editor = MockUser(id="editor-1", email="editor@test.com", role="editor")
        vault = MockVault(id="v1", owner_id="owner-1", is_shared=True)

        result = service.check_vault_access(editor, vault, Permission.WRITE)
        assert result.allowed is True
        assert result.reason == "role_permission"

    def test_shared_vault_viewer_no_write(self, service):
        viewer = MockUser(id="viewer-1", email="viewer@test.com", role="viewer")
        vault = MockVault(id="v1", owner_id="owner-1", is_shared=True)

        result = service.check_vault_access(viewer, vault, Permission.WRITE)
        assert result.allowed is False
        assert result.reason == "no_permission"

    def test_can_create_vault(self, service):
        admin = MockUser(id="a1", email="a@test.com", role="admin")
        editor = MockUser(id="e1", email="e@test.com", role="editor")
        viewer = MockUser(id="v1", email="v@test.com", role="viewer")
        inactive = MockUser(id="i1", email="i@test.com", role="editor", is_active=False)

        assert service.can_create_vault(admin) is True
        assert service.can_create_vault(editor) is True
        assert service.can_create_vault(viewer) is False
        assert service.can_create_vault(inactive) is False

    def test_can_delete_vault(self, service):
        owner = MockUser(id="o1", email="o@test.com", role="editor")
        admin = MockUser(id="a1", email="a@test.com", role="admin")
        other = MockUser(id="x1", email="x@test.com", role="editor")
        vault = MockVault(id="v1", owner_id="o1")

        assert service.can_delete_vault(owner, vault) is True
        assert service.can_delete_vault(admin, vault) is True
        assert service.can_delete_vault(other, vault) is False

    def test_can_share_vault(self, service):
        owner = MockUser(id="o1", email="o@test.com", role="viewer")
        admin = MockUser(id="a1", email="a@test.com", role="admin")
        other = MockUser(id="x1", email="x@test.com", role="editor")
        vault = MockVault(id="v1", owner_id="o1")

        assert service.can_share_vault(owner, vault) is True
        assert service.can_share_vault(admin, vault) is True
        assert service.can_share_vault(other, vault) is False

    def test_can_invite_user(self, service):
        admin = MockUser(id="a1", email="a@test.com", role="admin")
        editor = MockUser(id="e1", email="e@test.com", role="editor")

        assert service.can_invite_user(admin) is True
        assert service.can_invite_user(editor) is False

    def test_can_modify_user_role(self, service):
        admin1 = MockUser(id="a1", email="a1@test.com", role="admin")
        admin2 = MockUser(id="a2", email="a2@test.com", role="admin")
        editor = MockUser(id="e1", email="e@test.com", role="editor")

        assert service.can_modify_user_role(admin1, admin2) is True
        assert service.can_modify_user_role(admin1, admin1) is False  # Can't modify self
        assert service.can_modify_user_role(editor, admin1) is False


# ── Decorator Tests ───────────────────────────────────────────────────


class TestRequireRole:
    @pytest.mark.asyncio
    async def test_require_role_allowed(self):
        @require_role("admin", "editor")
        async def protected_endpoint(current_user=None):
            return "success"

        user = MockUser(id="a1", email="a@test.com", role="admin")
        result = await protected_endpoint(current_user=user)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_require_role_denied(self):
        from fastapi import HTTPException

        @require_role("admin")
        async def admin_only(current_user=None):
            return "success"

        viewer = MockUser(id="v1", email="v@test.com", role="viewer")
        with pytest.raises(HTTPException):
            await admin_only(current_user=viewer)

    @pytest.mark.asyncio
    async def test_require_role_no_user(self):
        from fastapi import HTTPException

        @require_role("admin")
        async def protected_endpoint(current_user=None):
            return "success"

        with pytest.raises(HTTPException):
            await protected_endpoint(current_user=None)


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_require_permission_allowed(self):
        @require_permission(Permission.READ)
        async def read_endpoint(current_user=None):
            return "success"

        viewer = MockUser(id="v1", email="v@test.com", role="viewer")
        result = await read_endpoint(current_user=viewer)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_require_permission_denied(self):
        from fastapi import HTTPException

        @require_permission(Permission.WRITE)
        async def write_endpoint(current_user=None):
            return "success"

        viewer = MockUser(id="v1", email="v@test.com", role="viewer")
        with pytest.raises(HTTPException):
            await write_endpoint(current_user=viewer)
