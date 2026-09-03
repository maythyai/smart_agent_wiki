"""Pluggable user stores for authentication (C2 wiring).

Historically the auth routes used an in-memory ``UserStore`` that lost all
users and refresh tokens on every restart. This module provides:

* :class:`UserStore` — the duck-typed Protocol every store satisfies.
* :class:`InMemoryUserStore` — the original behaviour, kept for tests.
* :class:`SQLAlchemyUserStore` — a database-backed store reusing the
  existing ``User`` / ``RefreshToken`` ORM models. Refresh tokens are
  stored as SHA-256 hashes (never plaintext), revocable, and expirable.
* :func:`get_user_store` — factory that returns a SQLAlchemy store when
  the DB is reachable, falling back to in-memory otherwise so single-user
  / CLI usage is unaffected.

The store returns plain ``dict`` objects (not ORM instances) so that
:class:`saw.auth.jwt_auth.AuthService` — which already works with dicts —
does not need to change.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Protocol, runtime_checkable


logger = logging.getLogger(__name__)

# Default refresh-token lifetime, mirrored from AuthConfig for stores that
# don't receive an explicit expiry.
_DEFAULT_REFRESH_DAYS = 7


def _hash_token(token: str) -> str:
    """SHA-256 hex of a token for storage / lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _user_to_dict(user) -> dict:
    """Convert a ``User`` ORM row to the dict shape AuthService expects."""
    return {
        "id": user.id,
        "email": user.email,
        "hashed_password": user.hashed_password,
        "role": user.role,
        "display_name": user.display_name,
        "is_active": bool(user.is_active),
        "created_at": user.created_at,
    }


@runtime_checkable
class UserStore(Protocol):
    """Contract for auth user/refresh-token storage."""

    def get_by_email(self, email: str) -> Optional[dict]:
        ...

    def get_by_id(self, user_id: str) -> Optional[dict]:
        ...

    def create(self, user_data: dict) -> dict:
        ...

    def store_refresh_token(self, token: str, user_id: str) -> None:
        ...

    def revoke_refresh_token(self, token: str) -> None:
        ...

    def is_refresh_token_valid(self, token: str) -> bool:
        ...


class InMemoryUserStore:
    """Original in-memory store. Preserved for tests / offline fallback."""

    def __init__(self) -> None:
        self._users: dict[str, dict[str, Any]] = {}
        self._email_index: dict[str, str] = {}
        # token_hash -> {user_id, expires_at, revoked}
        self._refresh_tokens: dict[str, dict[str, Any]] = {}
        self._refresh_days: int = _DEFAULT_REFRESH_DAYS

    def get_by_email(self, email: str) -> Optional[dict]:
        user_id = self._email_index.get(email)
        return dict(self._users[user_id]) if user_id else None

    def get_by_id(self, user_id: str) -> Optional[dict]:
        user = self._users.get(user_id)
        return dict(user) if user else None

    def create(self, user_data: dict) -> dict:
        user_id = user_data["id"]
        snapshot = dict(user_data)
        self._users[user_id] = snapshot
        self._email_index[user_data["email"]] = user_id
        return dict(snapshot)

    def store_refresh_token(self, token: str, user_id: str) -> None:
        self._refresh_tokens[_hash_token(token)] = {
            "user_id": user_id,
            "expires_at": datetime.now(timezone.utc)
            + timedelta(days=self._refresh_days),
            "revoked": False,
        }

    def revoke_refresh_token(self, token: str) -> None:
        entry = self._refresh_tokens.get(_hash_token(token))
        if entry:
            entry["revoked"] = True
            entry["revoked_at"] = datetime.now(timezone.utc)

    def is_refresh_token_valid(self, token: str) -> bool:
        entry = self._refresh_tokens.get(_hash_token(token))
        if not entry or entry["revoked"]:
            return False
        return entry["expires_at"] > datetime.now(timezone.utc)


class SQLAlchemyUserStore:
    """Database-backed user store reusing the ``User`` / ``RefreshToken`` ORM.

    Refresh tokens are persisted as SHA-256 hashes (never plaintext), are
    revocable, and respect an expiry. Falls back gracefully: if the DB is
    unreachable at construction, callers should catch and switch to
    :class:`InMemoryUserStore` (see :func:`get_user_store`).
    """

    def __init__(
        self,
        session_factory,
        refresh_days: int | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._refresh_days = refresh_days or _DEFAULT_REFRESH_DAYS

    # ── users ────────────────────────────────────────────────────────

    def get_by_email(self, email: str) -> Optional[dict]:
        from saw.db.models import User

        with self._session_factory() as session:
            user = session.query(User).filter(User.email == email).first()
            return _user_to_dict(user) if user else None

    def get_by_id(self, user_id: str) -> Optional[dict]:
        from saw.db.models import User

        with self._session_factory() as session:
            user = session.get(User, user_id)
            return _user_to_dict(user) if user else None

    def create(self, user_data: dict) -> dict:
        from saw.db.models import User

        with self._session_factory() as session:
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                hashed_password=user_data["hashed_password"],
                role=user_data.get("role", "viewer"),
                display_name=user_data.get("display_name"),
                is_active=user_data.get("is_active", True),
                created_at=user_data.get("created_at"),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return _user_to_dict(user)

    def touch_last_login(self, user_id: str) -> None:
        from saw.db.models import User

        from saw.domain.utils import utcnow

        with self._session_factory() as session:
            user = session.get(User, user_id)
            if user:
                user.last_login = utcnow()
                session.commit()

    # ── refresh tokens ──────────────────────────────────────────────

    def store_refresh_token(self, token: str, user_id: str) -> None:
        from saw.db.models import RefreshToken

        with self._session_factory() as session:
            entry = RefreshToken(
                user_id=user_id,
                token_hash=_hash_token(token),
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=self._refresh_days),
            )
            session.add(entry)
            session.commit()

    def revoke_refresh_token(self, token: str) -> None:
        from saw.db.models import RefreshToken

        from saw.domain.utils import utcnow

        with self._session_factory() as session:
            entry = (
                session.query(RefreshToken)
                .filter(RefreshToken.token_hash == _hash_token(token))
                .first()
            )
            if entry and not entry.revoked:
                entry.revoked = True
                entry.revoked_at = utcnow()
                session.commit()

    def is_refresh_token_valid(self, token: str) -> bool:
        from saw.db.models import RefreshToken

        with self._session_factory() as session:
            entry = (
                session.query(RefreshToken)
                .filter(RefreshToken.token_hash == _hash_token(token))
                .first()
            )
            if not entry or entry.revoked:
                return False
            expires_at = entry.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            return expires_at > datetime.now(timezone.utc)


_store_singleton: Optional[UserStore] = None


def get_user_store() -> UserStore:
    """Return a process-wide user store.

    Prefers :class:`SQLAlchemyUserStore` (reuses the configured DB engine
    and ORM models). If the DB is unavailable — e.g. a fresh checkout
    before ``saw init`` or a CLI run without a configured ``DATABASE_URL``
    — falls back to :class:`InMemoryUserStore` so existing single-user
    behaviour is preserved.
    """
    global _store_singleton
    if _store_singleton is not None:
        return _store_singleton

    try:
        from saw.db.config import get_engine
        from saw.db.models import init_db

        from sqlalchemy.orm import sessionmaker

        engine = get_engine()
        # Ensure auth tables exist (no-op if already present).
        init_db(engine)
        factory = sessionmaker(engine, expire_on_commit=False)
        _store_singleton = SQLAlchemyUserStore(factory)
        logger.debug("Using SQLAlchemyUserStore for authentication")
    except Exception as exc:  # pragma: no cover — environment-dependent
        logger.warning(
            "SQLAlchemyUserStore unavailable (%s); falling back to in-memory",
            exc,
        )
        _store_singleton = InMemoryUserStore()

    return _store_singleton


def reset_user_store() -> None:
    """Reset the process-wide singleton (for tests)."""
    global _store_singleton
    _store_singleton = None
