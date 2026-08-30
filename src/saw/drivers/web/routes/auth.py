"""Authentication routes for Security Hardening.

Phase 39: Security Hardening — SEC-01 JWT authentication endpoints.
Provides login, register, refresh, and logout endpoints.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from saw.auth.jwt_auth import AuthService, AuthConfig, JWTHandler
from saw.auth.user_store import get_user_store, SQLAlchemyUserStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# ── Request/Response Models ───────────────────────────────────────────


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=100)
    role: str = Field("viewer", pattern="^(admin|editor|viewer)$")


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


# ── User Store ────────────────────────────────────────────────────────
# C2: user / refresh-token storage is now DB-backed. The implementation
# lives in ``saw.auth.user_store`` and transparently falls back to an
# in-memory store when the DB is unavailable. The legacy ``UserStore``
# name is kept as an alias for backwards compatibility with any code that
# imported it from here.
from saw.auth.user_store import InMemoryUserStore as UserStore  # noqa: F401

__all_user_store_helpers__ = ("get_user_store",)


def get_auth_service() -> AuthService:
    """Get the authentication service."""
    return AuthService(AuthConfig.from_env())


# F-AUTH-03: equalize the user-not-found path with the wrong-password path
# (which runs a bcrypt compare) to prevent user enumeration via response
# timing. The dummy verify always fails; best-effort if bcrypt is missing.
_DUMMY_HASH: str | None = None


def _timing_dummy_verify(auth_service: AuthService, password: str) -> None:
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        try:
            _DUMMY_HASH = auth_service.hasher.hash_password("dummy-timing-equalizer")
        except Exception:
            _DUMMY_HASH = ""
    if _DUMMY_HASH:
        try:
            auth_service.hasher.verify_password(password, _DUMMY_HASH)
        except Exception:
            pass


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user.

    SEC-01: User registration with password hashing and JWT issuance.
    """
    auth_service = get_auth_service()
    user_store = get_user_store()

    # Check if email already exists
    if user_store.get_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # F-AUTH-01: never allow self-grant of the admin role via the public
    # register endpoint. Silently downgrade admin -> viewer; admin must be
    # promoted through a privileged flow, not self-registration.
    requested_role = request.role
    if requested_role == "admin":
        requested_role = "viewer"
        logger.warning(
            "Register request asked for admin role; downgraded to viewer: %s",
            request.email,
        )

    # Create user
    user_data = auth_service.register_user(
        email=request.email,
        password=request.password,
        role=requested_role,
        display_name=request.display_name,
    )

    # Store user
    user_store.create(user_data)

    # Generate tokens
    tokens = auth_service.jwt_handler.create_token_pair(
        user_data["id"],
        user_data["role"],
    )

    # Store refresh token (hashed at rest in the DB-backed store)
    user_store.store_refresh_token(tokens.refresh_token, user_data["id"])

    logger.info("User registered: %s (role=%s)", request.email, requested_role)

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return tokens.

    SEC-01: JWT-based authentication with access/refresh token pair.
    """
    auth_service = get_auth_service()
    user_store = get_user_store()

    # Find user
    user = user_store.get_by_email(request.email)
    if not user:
        # F-AUTH-03: burn a bcrypt compare so user-not-found takes about as
        # long as wrong-password (prevents enumeration via timing).
        _timing_dummy_verify(auth_service, request.password)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Authenticate
    tokens = auth_service.authenticate_user(
        email=request.email,
        password=request.password,
        user=user,
    )

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Store refresh token
    user_store.store_refresh_token(tokens.refresh_token, user["id"])

    # C2: persist last_login for the authenticated user.
    if isinstance(user_store, SQLAlchemyUserStore):
        try:
            user_store.touch_last_login(user["id"])
        except Exception:
            # Non-critical: best-effort audit timestamp.
            pass

    logger.info("User logged in: %s", request.email)

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest):
    """Refresh access token using refresh token.

    SEC-01: Token refresh mechanism.
    """
    auth_service = get_auth_service()
    user_store = get_user_store()

    # Verify refresh token is stored
    if not user_store.is_refresh_token_valid(request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
        )

    # Refresh tokens: AuthService verifies the JWT and returns a new pair.
    tokens = auth_service.refresh_tokens(
        refresh_token=request.refresh_token,
        get_user_by_id=user_store.get_by_id,
    )

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Determine the user_id for the new refresh-token record.
    try:
        user_id = auth_service.jwt_handler.verify_refresh_token(request.refresh_token)
    except ValueError:
        user_id = ""

    # Revoke old refresh token and store the new one (hashed at rest)
    user_store.revoke_refresh_token(request.refresh_token)
    if user_id:
        user_store.store_refresh_token(tokens.refresh_token, user_id)

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(request: RefreshRequest):
    """Logout by revoking refresh token.

    SEC-01: Token revocation on logout.
    """
    user_store = get_user_store()
    user_store.revoke_refresh_token(request.refresh_token)

    logger.info("User logged out (token revoked)")

    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=dict)
async def get_current_user(request: Request):
    """Get current authenticated user info.

    SEC-02: Returns user info based on JWT token.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header[7:]
    jwt_handler = JWTHandler(AuthConfig.from_env())

    try:
        token_data = jwt_handler.verify_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Get user from store
    user_store = get_user_store()
    user = user_store.get_by_id(token_data.sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "display_name": user.get("display_name"),
        "is_active": user.get("is_active", True),
    }


@router.get("/mode")
async def get_auth_mode(request: Request):
    """Return the server's auth mode (F-WEB-04).

    Lets the frontend decide whether to enforce a route guard: local mode
    trusts tokenless requests (single-user, local-first), so a hard guard
    would break that usage. Public — no auth required.
    """
    mode = getattr(request.app.state, "auth_mode", "local")
    return {"auth_mode": mode, "authenticated": mode == "local"}
