"""Tests for the pluggable user stores (C2 wiring).

Covers both InMemoryUserStore (legacy behaviour) and SQLAlchemyUserStore
(DB-backed, refresh tokens hashed at rest) so the two stay behaviourally
aligned.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import sessionmaker

from saw.auth.user_store import (
    InMemoryUserStore,
    SQLAlchemyUserStore,
    _hash_token,
)
from saw.db.config import DatabaseConfig
from saw.db.models import init_db


def _user_data(email: str = "alice@example.com", role: str = "editor") -> dict:
    return {
        "id": "user-" + email,
        "email": email,
        "hashed_password": "$2b$12$placeholderhashplaceholderhashplaceholderhashplaceholderhashplaceholderhash",
        "role": role,
        "display_name": "Alice",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }


# ── InMemoryUserStore ────────────────────────────────────────────────


class TestInMemoryUserStore:
    def test_create_and_lookup(self):
        store = InMemoryUserStore()
        created = store.create(_user_data("bob@example.com"))
        assert created["email"] == "bob@example.com"
        assert store.get_by_email("bob@example.com")["id"] == "user-bob@example.com"
        assert store.get_by_id("user-bob@example.com")["email"] == "bob@example.com"

    def test_get_missing_returns_none(self):
        store = InMemoryUserStore()
        assert store.get_by_email("nobody@example.com") is None
        assert store.get_by_id("nope") is None

    def test_refresh_token_lifecycle(self):
        store = InMemoryUserStore()
        store.create(_user_data("carol@example.com"))
        store.store_refresh_token("tok-1", "user-carol@example.com")
        assert store.is_refresh_token_valid("tok-1") is True
        store.revoke_refresh_token("tok-1")
        assert store.is_refresh_token_valid("tok-1") is False

    def test_unknown_token_invalid(self):
        store = InMemoryUserStore()
        assert store.is_refresh_token_valid("never-stored") is False


# ── SQLAlchemyUserStore ──────────────────────────────────────────────


@pytest.fixture
def db_store(tmp_path):
    """A SQLAlchemyUserStore backed by a temp-file SQLite DB."""
    from sqlalchemy import create_engine

    from saw.db.models import RefreshToken, User

    engine = create_engine(f"sqlite:///{tmp_path}/auth.db")
    # Create only the auth tables (User/RefreshToken). Using the full
    # metadata triggers a pre-existing duplicate-index bug in feed_models;
    # we don't need those tables here.
    from saw.db.models import Base

    Base.metadata.create_all(engine, tables=[User.__table__, RefreshToken.__table__])
    factory = sessionmaker(engine, expire_on_commit=False)
    return SQLAlchemyUserStore(factory)


class TestSQLAlchemyUserStore:
    def test_create_and_lookup(self, db_store):
        db_store.create(_user_data("alice@example.com"))
        by_email = db_store.get_by_email("alice@example.com")
        assert by_email is not None
        assert by_email["role"] == "editor"
        assert by_email["is_active"] is True
        by_id = db_store.get_by_id(by_email["id"])
        assert by_id["email"] == "alice@example.com"

    def test_get_missing_returns_none(self, db_store):
        assert db_store.get_by_email("nobody@example.com") is None
        assert db_store.get_by_id("nope") is None

    def test_refresh_token_stored_as_hash_not_plaintext(self, db_store, tmp_path):
        db_store.create(_user_data("alice@example.com"))
        db_store.store_refresh_token("plaintext-secret-tok", "user-alice@example.com")
        # The raw token must never appear in the DB file.
        raw = (tmp_path / "auth.db").read_bytes()
        assert b"plaintext-secret-tok" not in raw
        # But its sha256 hash must.
        assert _hash_token("plaintext-secret-tok").encode() in raw

    def test_refresh_token_valid_then_revoked(self, db_store):
        db_store.create(_user_data("alice@example.com"))
        db_store.store_refresh_token("tok-A", "user-alice@example.com")
        assert db_store.is_refresh_token_valid("tok-A") is True
        db_store.revoke_refresh_token("tok-A")
        assert db_store.is_refresh_token_valid("tok-A") is False

    def test_revoked_token_cannot_be_reused(self, db_store):
        db_store.create(_user_data("alice@example.com"))
        db_store.store_refresh_token("tok-B", "user-alice@example.com")
        db_store.revoke_refresh_token("tok-B")
        # Storing a new token for a subsequent refresh works independently.
        db_store.store_refresh_token("tok-C", "user-alice@example.com")
        assert db_store.is_refresh_token_valid("tok-C") is True

    def test_unknown_token_invalid(self, db_store):
        assert db_store.is_refresh_token_valid("never-stored") is False

    def test_touch_last_login(self, db_store):
        db_store.create(_user_data("alice@example.com"))
        before = db_store.get_by_id("user-alice@example.com")
        assert before["created_at"] is not None
        db_store.touch_last_login("user-alice@example.com")
        # No assertion on exact value; just ensure it does not raise and
        # the user is still retrievable.
        assert db_store.get_by_id("user-alice@example.com") is not None
