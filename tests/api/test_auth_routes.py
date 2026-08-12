"""End-to-end auth route tests against a DB-backed user store (C1/C2).

Uses ``fastapi.testclient.TestClient`` against the real auth router with
``get_user_store`` patched to a SQLAlchemyUserStore on a temp DB, and
``get_auth_service`` patched with a fixed ``AuthConfig`` secret so JWTs
are deterministic.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from saw.auth.jwt_auth import AuthConfig, AuthService
from saw.auth.user_store import SQLAlchemyUserStore, reset_user_store
from saw.db.models import Base, RefreshToken, User
from saw.drivers.web.routes.auth import router as auth_router


@pytest.fixture
def app(tmp_path, monkeypatch):
    # Fixed JWT secret → deterministic, no env/file dependency.
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-fixed")
    engine = create_engine(f"sqlite:///{tmp_path}/auth.db")
    # Only the auth tables are needed (avoids the pre-existing
    # duplicate-index bug in feed_models when full metadata is created).
    Base.metadata.create_all(engine, tables=[User.__table__, RefreshToken.__table__])
    factory = sessionmaker(engine, expire_on_commit=False)
    store = SQLAlchemyUserStore(factory)

    # Force the singleton to our DB-backed store.
    import saw.drivers.web.routes.auth as auth_module
    import saw.auth.user_store as us_module

    monkeypatch.setattr(us_module, "_store_singleton", store, raising=False)
    monkeypatch.setattr(auth_module, "get_user_store", lambda: store)
    # Pin AuthService to the fixed-secret config.
    monkeypatch.setattr(
        auth_module,
        "get_auth_service",
        lambda: AuthService(AuthConfig(secret_key="test-secret-fixed")),
    )

    app = FastAPI()
    app.state.auth_mode = "team"
    app.include_router(auth_router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def _register(client, email="user@example.com", password="Password123", role="viewer"):
    return client.post("/api/auth/register", json={
        "email": email, "password": password, "role": role,
    })


class TestRegister:
    def test_register_returns_tokens(self, client):
        r = _register(client, role="editor")
        assert r.status_code == 201
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["refresh_token"]

    def test_duplicate_email_conflict(self, client):
        _register(client, email="dup@example.com")
        r = _register(client, email="dup@example.com")
        assert r.status_code == 409

    def test_weak_password_rejected(self, client):
        r = client.post("/api/auth/register", json={
            "email": "weak@example.com", "password": "short", "role": "viewer",
        })
        assert r.status_code == 422  # min_length=8


class TestLogin:
    def test_login_success(self, client):
        _register(client, email="login@example.com", password="Password123")
        r = client.post("/api/auth/login", json={
            "email": "login@example.com", "password": "Password123",
        })
        assert r.status_code == 200
        assert r.json()["access_token"]

    def test_login_wrong_password(self, client):
        _register(client, email="wrong@example.com", password="Password123")
        r = client.post("/api/auth/login", json={
            "email": "wrong@example.com", "password": "WrongPassword",
        })
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post("/api/auth/login", json={
            "email": "ghost@example.com", "password": "Password123",
        })
        assert r.status_code == 401


class TestMe:
    def test_me_with_valid_token(self, client):
        tokens = _register(client, email="me@example.com", role="editor").json()
        r = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "me@example.com"
        assert body["role"] == "editor"

    def test_me_without_token(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_me_with_bad_token(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer nope"})
        assert r.status_code == 401


class TestRefresh:
    def test_refresh_issues_new_pair_and_revokes_old(self, client):
        tokens = _register(client, email="rf@example.com").json()
        r = client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert r.status_code == 200
        new = r.json()
        assert new["access_token"] != tokens["access_token"]
        # Old refresh token must now be invalid.
        r2 = client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert r2.status_code == 401


class TestLogout:
    def test_logout_revokes_refresh(self, client):
        tokens = _register(client, email="lo@example.com").json()
        r = client.post("/api/auth/logout", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert r.status_code == 200
        # Refresh after logout must fail.
        r2 = client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"],
        })
        assert r2.status_code == 401
