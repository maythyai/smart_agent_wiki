"""Tests for the FastAPI auth dependencies (C1 wiring).

Covers:
- get_current_user_from_token: valid / missing / bad-scheme / invalid / wrong type
- get_current_user_local: no token → local admin; bad token → 401; valid → honoured
- get_current_user: dispatches on app.state.auth_mode
- require_role: allows matching role, 403 on mismatch, 401 when unauthenticated in team mode
"""
from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from saw.auth.jwt_auth import AuthConfig, JWTHandler
from saw.drivers.web.middleware.security import (
    get_current_user,
    get_current_user_from_token,
    get_current_user_local,
    require_role,
)


def _app_with_routes(routes, auth_mode: str = "local") -> FastAPI:
    app = FastAPI()
    app.state.auth_mode = auth_mode
    for path, dep in routes:
        def make(dep=dep):
            def endpoint(user: dict = Depends(dep)):
                return user
            return endpoint
        app.add_api_route(path, make(), methods=["GET"])
    return app


def _make_token(role: str = "viewer", secret: str = "test-secret") -> str:
    handler = JWTHandler(AuthConfig(secret_key=secret))
    return handler.create_access_token("user-1", role=role)


@pytest.fixture(autouse=True)
def _pin_jwt_secret(monkeypatch):
    """Pin the JWT secret so sign/verify use the same key as _make_token."""
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret")


# ── get_current_user_from_token ─────────────────────────────────────


class TestGetCurrentUserFromToken:
    def test_valid_token(self):
        app = _app_with_routes([("/p", get_current_user_from_token)])
        client = TestClient(app)
        token = _make_token(role="editor")
        r = client.get("/p", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["role"] == "editor"
        assert r.json()["user_id"] == "user-1"

    def test_missing_header(self):
        app = _app_with_routes([("/p", get_current_user_from_token)])
        client = TestClient(app)
        assert client.get("/p").status_code == 401

    def test_bad_scheme(self):
        app = _app_with_routes([("/p", get_current_user_from_token)])
        client = TestClient(app)
        r = client.get("/p", headers={"Authorization": "Basic abc"})
        assert r.status_code == 401

    def test_invalid_token(self):
        app = _app_with_routes([("/p", get_current_user_from_token)])
        client = TestClient(app)
        r = client.get("/p", headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code == 401


# ── get_current_user_local ──────────────────────────────────────────


class TestGetCurrentUserLocal:
    def test_no_header_trusts_local_admin(self):
        app = _app_with_routes([("/p", get_current_user_local)])
        client = TestClient(app)
        r = client.get("/p")
        assert r.status_code == 200
        body = r.json()
        assert body["role"] == "admin"
        assert body["user_id"] == "local"

    def test_valid_header_honoured(self):
        app = _app_with_routes([("/p", get_current_user_local)])
        client = TestClient(app)
        token = _make_token(role="viewer")
        r = client.get("/p", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["role"] == "viewer"

    def test_invalid_header_rejected(self):
        app = _app_with_routes([("/p", get_current_user_local)])
        client = TestClient(app)
        r = client.get("/p", headers={"Authorization": "Bearer bad"})
        assert r.status_code == 401


# ── get_current_user (mode dispatch) ────────────────────────────────


class TestGetCurrentUserModeDispatch:
    def test_local_mode_no_token_passes(self):
        app = _app_with_routes([("/p", get_current_user)], auth_mode="local")
        assert TestClient(app).get("/p").status_code == 200

    def test_team_mode_no_token_blocked(self):
        app = _app_with_routes([("/p", get_current_user)], auth_mode="team")
        assert TestClient(app).get("/p").status_code == 401

    def test_team_mode_valid_token_passes(self):
        app = _app_with_routes([("/p", get_current_user)], auth_mode="team")
        token = _make_token(role="editor")
        r = TestClient(app).get("/p", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


# ── require_role ────────────────────────────────────────────────────


class TestRequireRole:
    def test_matching_role_allowed(self):
        app = _app_with_routes([("/p", require_role("admin", "editor"))], auth_mode="team")
        token = _make_token(role="editor")
        r = TestClient(app).get("/p", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_mismatch_role_forbidden(self):
        app = _app_with_routes([("/p", require_role("admin"))], auth_mode="team")
        token = _make_token(role="viewer")
        r = TestClient(app).get("/p", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_unauthenticated_in_team_mode(self):
        app = _app_with_routes([("/p", require_role("admin"))], auth_mode="team")
        assert TestClient(app).get("/p").status_code == 401

    def test_local_mode_admin_role_satisfied(self):
        # In local mode the default user is admin, so require_role("admin") passes.
        app = _app_with_routes([("/p", require_role("admin"))], auth_mode="local")
        assert TestClient(app).get("/p").status_code == 200
