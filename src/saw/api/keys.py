"""API Key authentication for third-party integration.

Phase 6: API Platform — API Key management.
Per APIP-02: API key authentication.

API Keys are stored as SHA256 hashes for security.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship

from saw.db.models import Base, generate_uuid


def generate_api_key(prefix: str = "saw") -> str:
    """Generate a new API key.

    Format: {prefix}_{random_32_char_hex}
    Example: saw_abc123def456...
    """
    random_part = secrets.token_hex(16)
    return f"{prefix}_{random_part}"


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA256.

    We store hashes instead of plaintext for security.
    """
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, hashed: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(key) == hashed


class APIKey(Base):
    """API Key model for third-party authentication."""
    __tablename__ = "api_keys"

    id: str = Column(String, primary_key=True, default=lambda: generate_uuid())
    user_id: str = Column(String, nullable=False, index=True)
    key_hash: str = Column(String(64), unique=True, nullable=False, index=True)
    name: str = Column(String(255), nullable=False)  # User-visible name
    prefix: str = Column(String(10), default="saw")  # Key prefix for identification
    permissions: str = Column(String(255), default="read,write")  # Comma-separated
    rate_limit_hour: int = Column(Integer, default=100)
    rate_limit_day: int = Column(Integer, default=1000)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Column(DateTime, nullable=True)
    last_used_at: Optional[datetime] = Column(DateTime, nullable=True)
    usage_count: int = Column(Integer, default=0)

    def verify(self, key: str) -> bool:
        """Verify a key against this record."""
        return verify_api_key(key, self.key_hash)


@dataclass
class APIKeyData:
    """API Key data for responses."""
    id: str
    name: str
    prefix: str
    permissions: list[str]
    rate_limit_hour: int
    rate_limit_day: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0

    @classmethod
    def from_model(cls, model: APIKey) -> APIKeyData:
        """Create from SQLAlchemy model."""
        return cls(
            id=model.id,
            name=model.name,
            prefix=model.prefix,
            permissions=model.permissions.split(",") if model.permissions else [],
            rate_limit_hour=model.rate_limit_hour,
            rate_limit_day=model.rate_limit_day,
            is_active=model.is_active,
            created_at=model.created_at,
            expires_at=model.expires_at,
            last_used_at=model.last_used_at,
            usage_count=model.usage_count,
        )


@dataclass
class CreatedAPIKey:
    """Response for newly created API key."""
    id: str
    name: str
    key: str  # Full key (shown only once!)
    prefix: str
    created_at: datetime

    @classmethod
    def from_model(cls, model: APIKey, full_key: str) -> CreatedAPIKey:
        """Create from model with full key."""
        return cls(
            id=model.id,
            name=model.name,
            key=full_key,
            prefix=model.prefix,
            created_at=model.created_at,
        )


class APIKeyService:
    """Service for managing API keys."""

    def __init__(self, session=None):
        self.session = session

    def create_key(
        self,
        user_id: str,
        name: str,
        permissions: list[str] | None = None,
        rate_limit_hour: int = 100,
        rate_limit_day: int = 1000,
        expires_days: int | None = None,
        prefix: str = "saw",
    ) -> tuple[APIKey, str]:
        """Create a new API key.

        Returns tuple of (APIKey model, full key string).
        The full key is only shown once - store it securely!
        """
        # Generate full key
        full_key = generate_api_key(prefix)

        # Parse permissions from key prefix
        if permissions is None:
            permissions = ["read", "write"]
        permissions_str = ",".join(permissions)

        # Calculate expiry
        expires_at = None
        if expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

        # Create model
        api_key = APIKey(
            user_id=user_id,
            key_hash=hash_api_key(full_key),
            name=name,
            prefix=prefix,
            permissions=permissions_str,
            rate_limit_hour=rate_limit_hour,
            rate_limit_day=rate_limit_day,
            expires_at=expires_at,
        )

        if self.session:
            self.session.add(api_key)
            self.session.commit()

        return api_key, full_key

    def get_key_by_hash(self, key_hash: str) -> APIKey | None:
        """Get an API key by its hash."""
        if not self.session:
            return None

        return self.session.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        ).first()

    def get_key_by_id(self, key_id: str) -> APIKey | None:
        """Get an API key by ID."""
        if not self.session:
            return None

        return self.session.query(APIKey).filter(
            APIKey.id == key_id,
        ).first()

    def list_keys(self, user_id: str) -> list[APIKey]:
        """List all API keys for a user."""
        if not self.session:
            return []

        return self.session.query(APIKey).filter(
            APIKey.user_id == user_id,
        ).order_by(APIKey.created_at.desc()).all()

    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if not self.session:
            return False

        key = self.session.query(APIKey).filter(APIKey.id == key_id).first()
        if not key:
            return False

        key.is_active = False
        self.session.commit()
        return True

    def verify_key(self, full_key: str) -> APIKey | None:
        """Verify a full API key string.

        Returns the APIKey if valid, None otherwise.
        """
        key_hash = hash_api_key(full_key)
        api_key = self.get_key_by_hash(key_hash)

        if not api_key:
            return None

        # Check expiry
        if api_key.expires_at and datetime.now(timezone.utc) > api_key.expires_at:
            return None

        # Update usage
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.usage_count += 1
        if self.session:
            self.session.commit()

        return api_key

    def has_permission(self, api_key: APIKey, permission: str) -> bool:
        """Check if an API key has a specific permission."""
        permissions = api_key.permissions.split(",") if api_key.permissions else []
        return permission in permissions or "admin" in permissions


def verify_api_key_header(request) -> str | None:
    """Extract a rate-limit key identifier from the ``Authorization`` header.

    ``RateLimitMiddleware`` calls this as its ``get_api_key_func`` callback.
    Returns the key prefix (``saw_xxx...``) for per-key rate limiting, or
    ``None`` when the request uses bearer auth / no auth.
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("ApiKey "):
        return auth[7:]
    return None


def verify_api_key_sync(key_str: str) -> "APIKey | None":
    """Verify an API key against the database (sync).

    Looks up the SHA-256 hash, checks active + expiry, and returns the
    ``APIKey`` model or ``None``. This is the actual authentication authority
    for the ``Authorization: ApiKey <key>`` scheme — both
    ``get_current_user_from_token`` and ``RateLimitMiddleware`` call it.
    """
    if not key_str:
        return None
    from saw.db.config import DatabaseConfig, get_engine
    from sqlalchemy.orm import sessionmaker

    try:
        engine = get_engine(DatabaseConfig.from_env())
        factory = sessionmaker(engine, expire_on_commit=False)
        with factory() as session:
            return APIKeyService(session).verify_key(key_str)
    except Exception:
        return None


async def verify_api_key_for_rate_limit(key_str: str) -> "APIKey | None":
    """Rate limiter callback: verify a key and return the model.

    ``RateLimitMiddleware`` calls this as ``get_api_key_func`` and expects an
    object with ``.id``/``.rate_limit_hour``/``.rate_limit_day``. The DB
    lookup is sync SQLAlchemy, so run it in a threadpool to avoid blocking
    the event loop.
    """
    import asyncio

    return await asyncio.to_thread(verify_api_key_sync, key_str)
