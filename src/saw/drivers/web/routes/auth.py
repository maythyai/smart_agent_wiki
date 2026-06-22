"""Authentication routes for Security Hardening.

Phase 39: Security Hardening — SEC-01 JWT authentication endpoints.
Provides login, register, refresh, and logout endpoints.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from saw.auth.jwt_auth import AuthService, AuthConfig, JWTHandler

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


# ── User Store (in-memory fallback, replace with DB in production) ─────


class UserStore:
    """Simple user store for authentication.

    In production, replace with database-backed implementation.
    """

    def __init__(self):
        self._users: dict[str, dict[str, Any]] = {}
        self._email_index: dict[str, str] = {}  # email -> user_id
        self._refresh_tokens: set[str] = set()  # Active refresh tokens

    def get_by_email(self, email: str) -> dict | None:
        user_id = self._email_index.get(email)
        if user_id:
            return self._users.get(user_id)
        return None

    def get_by_id(self, user_id: str) -> dict | None:
        return self._users.get(user_id)

    def create(self, user_data: dict) -> dict:
        user_id = user_data["id"]
        self._users[user_id] = user_data
        self._email_index[user_data["email"]] = user_id
        return user_data

    def store_refresh_token(self, token: str) -> None:
        self._refresh_tokens.add(token)

    def revoke_refresh_token(self, token: str) -> None:
        self._refresh_tokens.discard(token)

    def is_refresh_token_valid(self, token: str) -> bool:
        return token in self._refresh_tokens


# Global user store (singleton, injected via app.state in production)
_user_store: UserStore | None = None


def get_user_store() -> UserStore:
    """Get or create the global user store."""
    global _user_store
    if _user_store is None:
        _user_store = UserStore()
    return _user_store


def get_auth_service() -> AuthService:
    """Get the authentication service."""
    return AuthService(AuthConfig.from_env())


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

    # Create user
    user_data = auth_service.register_user(
        email=request.email,
        password=request.password,
        role=request.role,
        display_name=request.display_name,
    )

    # Store user
    user_store.create(user_data)

    # Generate tokens
    tokens = auth_service.jwt_handler.create_token_pair(
        user_data["id"],
        user_data["role"],
    )

    # Store refresh token
    user_store.store_refresh_token(tokens.refresh_token)

    logger.info("User registered: %s (role=%s)", request.email, request.role)

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
    user_store.store_refresh_token(tokens.refresh_token)

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

    # Refresh tokens
    tokens = auth_service.refresh_tokens(
        refresh_token=request.refresh_token,
        get_user_by_id=user_store.get_by_id,
    )

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Revoke old refresh token and store new one
    user_store.revoke_refresh_token(request.refresh_token)
    user_store.store_refresh_token(tokens.refresh_token)

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
