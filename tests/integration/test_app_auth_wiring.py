"""Integration tests: auth wiring on protected app routes (C1).

Verifies that ``create_app(auth_mode=...)`` actually gates the protected
routers with the mode-aware dependency.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from saw.auth.jwt_auth import AuthConfig, JWTHandler
from saw.drivers.web.app import create_app


def _mock_query() -> MagicMock:
    """A query engine mock whose ``list_pages`` returns [] (handler → 200)."""
    engine = MagicMock()
    wiki = MagicMock()
    wiki.list_pages.return_value = []
    engine._wiki_repo = wiki
    return engine


def _make_app(auth_mode: str) -> TestClient:
    app = create_app(
        query=_mock_query(),
        collaborate=MagicMock(),
        write_queue=MagicMock(),
        auth_mode=auth_mode,
    )
    return TestClient(app)


def _token(role: str = "viewer", secret: str = "test-secret") -> str:
    return JWTHandler(AuthConfig(secret_key=secret)).create_access_token("u", role=role)


@pytest.fixture(autouse=True)
def _pin_jwt_secret(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret")


class TestTeamMode:
    def test_protected_route_no_token_401(self):
        client = _make_app("team")
        assert client.get("/api/pages").status_code == 401

    def test_protected_route_valid_token_200(self):
        client = _make_app("team")
        r = client.get("/api/pages", headers={"Authorization": f"Bearer {_token()}"})
        assert r.status_code == 200

    def test_protected_route_bad_token_401(self):
        client = _make_app("team")
        r = client.get("/api/pages", headers={"Authorization": "Bearer bad"})
        assert r.status_code == 401

    def test_auth_router_still_public(self):
        client = _make_app("team")
        # /api/auth/register is exempt — 422 (validation) rather than 401.
        r = client.post("/api/auth/register", json={"email": "bad"})
        assert r.status_code == 422


class TestLocalMode:
    def test_protected_route_no_token_200(self):
        client = _make_app("local")
        assert client.get("/api/pages").status_code == 200

    def test_protected_route_valid_token_200(self):
        client = _make_app("local")
        r = client.get("/api/pages", headers={"Authorization": f"Bearer {_token()}"})
        assert r.status_code == 200
