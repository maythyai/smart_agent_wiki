"""JWT authentication for team deployment.

Phase 5: Team Deployment — Authentication.
Per TEAM-04: Multi-user registration and authentication.

Uses JWT for stateless authentication with refresh tokens.
Password hashing via bcrypt.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any

# Lazy imports for optional dependencies


class AuthConfig:
    """Authentication configuration."""

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key or AuthConfig._resolve_secret_key()
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    @staticmethod
    def _resolve_secret_key(key_path: Path | None = None) -> str:
        """Resolve the JWT HMAC secret with persistence.

        Order: ``AUTH_SECRET_KEY`` env var → ``.saw/keys/jwt.key`` file
        (generated + persisted on first use). A persistent key is required
        so that access/refresh tokens stay valid across restarts.
        """
        env = os.environ.get("AUTH_SECRET_KEY")
        if env:
            return env
        from pathlib import Path

        from saw.adapters.crypto._keyfiles import load_or_create

        path = key_path or Path(".saw/keys/jwt.key")
        return load_or_create(path, lambda: secrets.token_hex(32))

    @classmethod
    def from_env(cls) -> AuthConfig:
        """Create config from environment + persistent key file."""
        return cls(
            secret_key=os.environ.get("AUTH_SECRET_KEY"),
            algorithm=os.environ.get("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        )


@dataclass
class TokenData:
    """Token payload data."""
    sub: str  # User ID
    exp: datetime
    iat: datetime
    role: str = "viewer"

    def to_dict(self) -> dict:
        return {
            "sub": self.sub,
            "exp": int(self.exp.timestamp()),
            "iat": int(self.iat.timestamp()),
            "role": self.role,
        }


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class PasswordHasher:
    """Password hashing using bcrypt."""

    def __init__(self):
        self._bcrypt = None

    def _get_bcrypt(self):
        if self._bcrypt is None:
            try:
                import bcrypt
                self._bcrypt = bcrypt
            except ImportError:
                raise ImportError(
                    "bcrypt not installed. Install: pip install bcrypt"
                )
        return self._bcrypt

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        bcrypt = self._get_bcrypt()
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        bcrypt = self._get_bcrypt()
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            return False


class JWTHandler:
    """JWT token handling."""

    def __init__(self, config: AuthConfig | None = None):
        self.config = config or AuthConfig.from_env()
        self._jwt = None

    def _get_jwt(self):
        if self._jwt is None:
            try:
                import jwt
                self._jwt = jwt
            except ImportError:
                raise ImportError(
                    "PyJWT not installed. Install: pip install PyJWT"
                )
        return self._jwt

    def create_access_token(
        self,
        user_id: str,
        role: str = "viewer",
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create an access token."""
        jwt_lib = self._get_jwt()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.config.access_token_expire_minutes
            )

        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "role": role,
            "type": "access",
            "jti": secrets.token_hex(16),
        }

        return jwt_lib.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a refresh token.

        Includes a random ``jti`` (JWT ID) so that two refresh tokens
        issued within the same second are still distinct — required because
        the DB-backed store enforces a UNIQUE constraint on the token hash.
        """
        jwt_lib = self._get_jwt()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.config.refresh_token_expire_days
            )

        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "type": "refresh",
            "jti": secrets.token_hex(16),
        }

        return jwt_lib.encode(payload, self.config.secret_key, algorithm=self.config.algorithm)

    def create_token_pair(self, user_id: str, role: str = "viewer") -> TokenPair:
        """Create access and refresh token pair."""
        access_token = self.create_access_token(user_id, role)
        refresh_token = self.create_refresh_token(user_id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.access_token_expire_minutes * 60,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and verify a token."""
        jwt_lib = self._get_jwt()

        try:
            payload = jwt_lib.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
            )
            return payload
        except jwt_lib.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt_lib.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

    def verify_access_token(self, token: str) -> TokenData:
        """Verify an access token and return token data."""
        payload = self.decode_token(token)

        if payload.get("type") != "access":
            raise ValueError("Not an access token")

        return TokenData(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            role=payload.get("role", "viewer"),
        )

    def verify_refresh_token(self, token: str) -> str:
        """Verify a refresh token and return user ID."""
        payload = self.decode_token(token)

        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")

        return payload["sub"]


class AuthService:
    """Authentication service."""

    def __init__(
        self,
        config: AuthConfig | None = None,
    ):
        self.config = config or AuthConfig.from_env()
        self.hasher = PasswordHasher()
        self.jwt_handler = JWTHandler(self.config)

    def register_user(
        self,
        email: str,
        password: str,
        role: str = "viewer",
        display_name: str | None = None,
    ) -> dict:
        """Register a new user."""
        from saw.db.models import generate_uuid, utcnow

        # Hash password
        hashed_password = self.hasher.hash_password(password)

        # Create user dict
        user_id = generate_uuid()
        user_data = {
            "id": user_id,
            "email": email,
            "hashed_password": hashed_password,
            "role": role,
            "display_name": display_name,
            "is_active": True,
            "created_at": utcnow(),
        }

        return user_data

    def authenticate_user(
        self,
        email: str,
        password: str,
        user: dict,
    ) -> TokenPair | None:
        """Authenticate a user and return tokens."""
        if not user.get("is_active", True):
            return None

        # Verify password
        if not self.hasher.verify_password(password, user["hashed_password"]):
            return None

        # Create tokens
        return self.jwt_handler.create_token_pair(
            user["id"],
            user.get("role", "viewer"),
        )

    def refresh_tokens(
        self,
        refresh_token: str,
        get_user_by_id: callable,
    ) -> TokenPair | None:
        """Refresh access token using refresh token."""
        try:
            user_id = self.jwt_handler.verify_refresh_token(refresh_token)
            user = get_user_by_id(user_id)

            if not user or not user.get("is_active", True):
                return None

            return self.jwt_handler.create_token_pair(
                user["id"],
                user.get("role", "viewer"),
            )
        except ValueError:
            return None

    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
        user: dict,
    ) -> str:
        """Change user password."""
        if not self.hasher.verify_password(old_password, user["hashed_password"]):
            raise ValueError("Invalid old password")

        return self.hasher.hash_password(new_password)


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()
