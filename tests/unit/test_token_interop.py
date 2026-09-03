"""T-F-C-5-1: 前后端 token 同源核验与补齐.

SPEC-F-C-5: verify that the frontend token flow (login → store → Bearer
request → backend互验 → refresh) is same-source with the backend
AuthService/JWTHandler, and that the backend auth chain is unified.

Frontend verification (read-only, no code change needed):
  - Token storage: web/src/stores/authStore.ts:56 (Zustand persist → localStorage key 'saw-auth')
  - Bearer attachment: web/src/lib/api.ts:134-138 (request) and :186-188 (requestForm)
  - Login → TokenPair: web/src/pages/Login.tsx:42-45 (POST /api/auth/login → setTokens)
  - Refresh on 401: web/src/lib/api.ts:65-90 (refreshAccessToken → POST /api/auth/refresh)
  - Logout (revoke): web/src/App.tsx:23-27 (POST /api/auth/logout with refresh_token)
  - WebSocket auth: web/src/hooks/useWebSocket.ts:146-150 (?token= query param)

Conclusion: frontend is already same-source — stores tokens from the
backend's TokenPair, attaches ``Authorization: Bearer <access>`` to all
requests, and refreshes via ``POST /api/auth/refresh``. No frontend code
change was required.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from saw.auth.jwt_auth import AuthConfig, AuthService, JWTHandler, TokenPair
from saw.auth.user_store import InMemoryUserStore, reset_user_store
from saw.drivers.web.routes.auth import router as auth_router

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _pin_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the JWT secret so sign/verify use the same key across the test."""
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-token-interop-secret-key-32b")


@pytest.fixture
def app() -> FastAPI:
    """Minimal FastAPI app with only the auth router mounted."""
    application = FastAPI()
    application.state.auth_mode = "team"
    application.include_router(auth_router)
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """TestClient backed by the auth-only app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def _inmemory_store(monkeypatch: pytest.MonkeyPatch) -> InMemoryUserStore:
    """Force a single in-memory store (no DB) and reset between tests.

    Returns the same instance for every ``get_user_store()`` call within a
    test so that register-then-login can find the user.
    """
    reset_user_store()
    store = InMemoryUserStore()
    monkeypatch.setattr(
        "saw.drivers.web.routes.auth.get_user_store",
        lambda: store,
    )
    return store


# ── Helpers ───────────────────────────────────────────────────────────


def _register_and_login(
    client: TestClient,
    email: str = "interop@example.com",
    password: str = "SecurePass123!",
) -> dict:
    """Register a user and then log in, returning the login JSON body."""
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "role": "editor"},
    )
    assert reg.status_code == 201, reg.text
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()


# ── test_frontend_token_interop ───────────────────────────────────────


class TestFrontendTokenInterop:
    """Simulate the frontend token flow and verify backend same-source.

    Flow: login → store token → Bearer request to /api/auth/me → backend
    互验 passes → refresh → new token works → old refresh revoked.
    """

    def test_login_returns_token_pair(self, client: TestClient) -> None:
        """Login endpoint returns access + refresh tokens (TokenPair shape)."""
        body = _register_and_login(client)
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0
        assert body["access_token"] != body["refresh_token"]

    def test_bearer_request_to_protected_endpoint(self, client: TestClient) -> None:
        """A Bearer-authenticated request to /api/auth/me is accepted."""
        body = _register_and_login(client)
        access_token: str = body["access_token"]

        # Simulate frontend: GET /api/auth/me with Authorization: Bearer
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200, resp.text
        user = resp.json()
        assert user["email"] == "interop@example.com"
        assert user["role"] == "editor"

    def test_request_without_bearer_rejected(self, client: TestClient) -> None:
        """Without a Bearer token, the protected endpoint rejects the request."""
        _register_and_login(client)
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_request_with_invalid_bearer_rejected(self, client: TestClient) -> None:
        """An invalid Bearer token is rejected by the backend."""
        _register_and_login(client)
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert resp.status_code == 401

    def test_refresh_flow_yields_new_valid_token(self, client: TestClient) -> None:
        """Refresh endpoint returns a new access token that the backend accepts."""
        body = _register_and_login(client)
        old_access: str = body["access_token"]
        refresh_token: str = body["refresh_token"]

        # Simulate frontend refreshAccessToken(): POST /api/auth/refresh
        resp = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200, resp.text
        new_body = resp.json()
        assert new_body["access_token"] != old_access
        assert new_body["refresh_token"] != refresh_token

        # The new access token must be accepted by the backend (same-source)
        me_resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_body['access_token']}"},
        )
        assert me_resp.status_code == 200

    def test_old_refresh_token_revoked_after_refresh(self, client: TestClient) -> None:
        """After refresh, the old refresh token is revoked and cannot be reused."""
        body = _register_and_login(client)
        refresh_token: str = body["refresh_token"]

        # First refresh succeeds
        resp = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200

        # Second refresh with the old (now-revoked) token fails
        resp2 = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp2.status_code == 401

    def test_logout_revokes_refresh_token(self, client: TestClient) -> None:
        """Logout endpoint revokes the refresh token (frontend App.tsx:23-27)."""
        body = _register_and_login(client)
        refresh_token: str = body["refresh_token"]

        logout = client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout.status_code == 200

        # Refresh after logout must fail
        refresh = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh.status_code == 401

    def test_backend_verifies_frontend_issued_token(
        self, client: TestClient
    ) -> None:
        """The access token issued by login is verifiable by JWTHandler (same-source).

        This confirms the backend's JWTHandler uses the same secret as the
        AuthService that issued the token — the core of 同源 (same-source).
        """
        body = _register_and_login(client)
        access_token: str = body["access_token"]

        handler = JWTHandler(AuthConfig.from_env())
        token_data = handler.verify_access_token(access_token)
        assert token_data.sub  # user ID is present
        assert token_data.role == "editor"

    def test_full_interop_cycle(self, client: TestClient) -> None:
        """End-to-end: login → Bearer request → refresh → new Bearer request → logout."""
        body = _register_and_login(client, email="cycle@example.com", password="CyclePass123!")
        access_token: str = body["access_token"]
        refresh_token: str = body["refresh_token"]

        # 1. Protected request with original access token
        me1 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me1.status_code == 200

        # 2. Refresh
        ref = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert ref.status_code == 200
        new_access = ref.json()["access_token"]
        new_refresh = ref.json()["refresh_token"]

        # 3. Protected request with new access token
        me2 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        assert me2.status_code == 200
        assert me2.json()["email"] == "cycle@example.com"

        # 4. Logout with new refresh token
        logout = client.post(
            "/api/auth/logout",
            json={"refresh_token": new_refresh},
        )
        assert logout.status_code == 200

        # 5. Refresh after logout fails
        ref2 = client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert ref2.status_code == 401


# ── test_backend_auth_unified ────────────────────────────────────────


class TestBackendAuthUnified:
    """Verify the backend auth chain is unified (AuthService/JWTHandler reuse).

    CMS §M08 drift D3: "前后端认证体系各自独立互不通信" — verify that
    the backend auth routes reuse AuthService and JWTHandler (not a
    parallel auth system), and that token creation/verification use the
    same secret and algorithm.
    """

    def test_auth_service_uses_jwt_handler(self) -> None:
        """AuthService is composed of JWTHandler (not a separate JWT impl)."""
        config = AuthConfig(secret_key="unified-test-secret")
        service = AuthService(config)
        assert isinstance(service.jwt_handler, JWTHandler)

    def test_same_secret_sign_and_verify(self) -> None:
        """Tokens signed by AuthService are verified by JWTHandler (same source)."""
        config = AuthConfig(secret_key="same-source-secret")
        service = AuthService(config)

        # AuthService.authenticate_user creates tokens via JWTHandler
        user = service.register_user(
            email="unified@example.com",
            password="Password123",
            role="admin",
        )
        tokens = service.authenticate_user(
            email="unified@example.com",
            password="Password123",
            user=user,
        )
        assert tokens is not None
        assert isinstance(tokens, TokenPair)

        # JWTHandler (same instance) verifies the access token
        token_data = service.jwt_handler.verify_access_token(tokens.access_token)
        assert token_data.sub == user["id"]
        assert token_data.role == "admin"

    def test_login_endpoint_uses_authservice(self, client: TestClient) -> None:
        """The login endpoint's tokens are verifiable by a standalone JWTHandler.

        This proves the auth routes reuse AuthService/JWTHandler — the token
        issued by the HTTP endpoint can be verified by the same JWTHandler
        that AuthService uses internally.
        """
        body = _register_and_login(client, email="endpoint@example.com", password="EndPass123!")
        access_token: str = body["access_token"]

        # A JWTHandler created independently (same env secret) verifies it
        handler = JWTHandler(AuthConfig.from_env())
        token_data = handler.verify_access_token(access_token)
        assert token_data.role == "editor"

    def test_refresh_endpoint_uses_authservice(self, client: TestClient) -> None:
        """The refresh endpoint's new tokens are verifiable by JWTHandler."""
        body = _register_and_login(
            client, email="refresh-verify@example.com", password="RefPass123!"
        )
        refresh_token: str = body["refresh_token"]

        resp = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        new_access = resp.json()["access_token"]

        handler = JWTHandler(AuthConfig.from_env())
        token_data = handler.verify_access_token(new_access)
        assert token_data.sub  # user ID present

    def test_register_endpoint_uses_authservice(self, client: TestClient) -> None:
        """The register endpoint's tokens are verifiable by JWTHandler."""
        resp = client.post(
            "/api/auth/register",
            json={
                "email": "reg-verify@example.com",
                "password": "RegPass123!",
                "role": "viewer",
            },
        )
        assert resp.status_code == 201
        access_token: str = resp.json()["access_token"]

        handler = JWTHandler(AuthConfig.from_env())
        token_data = handler.verify_access_token(access_token)
        assert token_data.role == "viewer"

    def test_auth_routes_share_authservice_factory(self) -> None:
        """auth.py:get_auth_service() returns AuthService backed by JWTHandler.

        Source: src/saw/drivers/web/routes/auth.py:80-82.
        """
        from saw.drivers.web.routes.auth import get_auth_service

        service = get_auth_service()
        assert isinstance(service, AuthService)
        assert isinstance(service.jwt_handler, JWTHandler)

    def test_token_pair_consistency(self) -> None:
        """Access and refresh tokens are distinct but signed by the same key."""
        config = AuthConfig(secret_key="consistency-secret")
        handler = JWTHandler(config)

        pair = handler.create_token_pair("user-consistency", role="editor")
        assert pair.access_token != pair.refresh_token

        # Both decode with the same secret
        access_payload = handler.decode_token(pair.access_token)
        refresh_payload = handler.decode_token(pair.refresh_token)
        assert access_payload["sub"] == refresh_payload["sub"]
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        assert access_payload["role"] == "editor"
