"""Admin policy reload Web endpoint tests — T-F-J-4 (AC-SEC-6)."""
from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from saw.drivers.web.middleware.security import get_current_user, require_role
from saw.drivers.web.routes.admin import router as admin_router

_ADMIN_DEP = [Depends(get_current_user), Depends(require_role("admin"))]


def _app_with_cedar(cedar, user=None):
    """Build a minimal FastAPI app mounting the admin router with auth dep."""
    app = FastAPI()
    app.state.cedar = cedar
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    app.include_router(admin_router, dependencies=_ADMIN_DEP)
    return app


def test_admin_reload_invokes_cedar():
    """AC-SEC-6: admin POST /api/admin/policy/reload calls cedar.reload()."""
    cedar = MagicMock()
    cedar.reload.return_value = True
    app = _app_with_cedar(cedar, user={"sub": "admin", "role": "admin"})
    res = TestClient(app).post("/api/admin/policy/reload")
    assert res.status_code == 200, res.text
    assert res.json()["reloaded"] is True
    cedar.reload.assert_called_once()


def test_admin_reload_404_when_no_cedar():
    """AC-SEC-6: no Cedar engine configured → 404 (RBAC default still active)."""
    app = _app_with_cedar(None, user={"sub": "admin", "role": "admin"})
    res = TestClient(app).post("/api/admin/policy/reload")
    assert res.status_code == 404


def test_non_admin_forbidden():
    """AC-SEC-6: a non-admin role is rejected (403) by require_role."""
    cedar = MagicMock()
    app = _app_with_cedar(cedar, user={"sub": "u", "role": "viewer"})
    res = TestClient(app).post("/api/admin/policy/reload")
    assert res.status_code == 403
    cedar.reload.assert_not_called()
