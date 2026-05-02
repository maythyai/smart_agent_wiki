"""Tests for Notion database models.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-10: Sync cursor persists after each sync for resume capability.
Per NOTI-02: Database selection persistence.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from saw.db.notion_models import (
    NotionSyncCursorModel,
    NotionDatabaseConfigModel,
    SyncDirection,
)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestNotionSyncCursorModel:
    """Tests for NotionSyncCursorModel."""

    def test_model_creation(self) -> None:
        """Test 4: NotionSyncCursorModel persists cursor_token, database_id, last_sync_at."""
        now = utcnow()
        cursor = NotionSyncCursorModel(
            id="cursor-123",
            connector_id="connector-456",
            database_id="db-789",
            cursor_token="next-cursor-token",
            last_sync_at=now,
            last_page_edited_at=now,
            items_synced=100,
        )
        assert cursor.id == "cursor-123"
        assert cursor.connector_id == "connector-456"
        assert cursor.database_id == "db-789"
        assert cursor.cursor_token == "next-cursor-token"
        assert cursor.items_synced == 100

    def test_model_defaults(self) -> None:
        """Test model with minimal required fields."""
        cursor = NotionSyncCursorModel(
            connector_id="connector-123",
            database_id="db-456",
            items_synced=0,  # Explicit default since SQLAlchemy defaults apply on flush
        )
        assert cursor.items_synced == 0
        assert cursor.cursor_token is None
        assert cursor.last_sync_at is None

    def test_model_nullable_cursor(self) -> None:
        """Test model with null cursor (initial sync)."""
        cursor = NotionSyncCursorModel(
            connector_id="connector-123",
            database_id="db-456",
            cursor_token=None,
            last_sync_at=utcnow(),
        )
        assert cursor.cursor_token is None


class TestNotionDatabaseConfigModel:
    """Tests for NotionDatabaseConfigModel."""

    def test_model_creation(self) -> None:
        """Test 5: NotionDatabaseConfigModel persists selected databases with sync preferences."""
        config = NotionDatabaseConfigModel(
            id="config-123",
            connector_id="connector-456",
            database_id="db-789",
            database_name="My Tasks",
            is_selected=True,
            sync_direction=SyncDirection.BIDIRECTIONAL,
            property_mapping={"Title": "title", "Status": "confidence"},
        )
        assert config.database_name == "My Tasks"
        assert config.is_selected is True
        assert config.sync_direction == SyncDirection.BIDIRECTIONAL
        assert config.property_mapping["Status"] == "confidence"

    def test_sync_direction_enum(self) -> None:
        """Test sync direction enum values."""
        assert SyncDirection.PULL.value == "pull"
        assert SyncDirection.PUSH.value == "push"
        assert SyncDirection.BIDIRECTIONAL.value == "bidirectional"

    def test_model_defaults(self) -> None:
        """Test model with minimal fields."""
        config = NotionDatabaseConfigModel(
            connector_id="connector-123",
            database_id="db-456",
            database_name="Test DB",
            is_selected=True,  # Explicit default since SQLAlchemy defaults apply on flush
            sync_direction=SyncDirection.BIDIRECTIONAL,
            property_mapping={},  # Explicit default since SQLAlchemy defaults apply on flush
        )
        assert config.is_selected is True
        assert config.sync_direction == SyncDirection.BIDIRECTIONAL
        assert config.property_mapping == {}

    def test_property_mapping(self) -> None:
        """Test custom property mapping storage."""
        mapping = {
            "Title": "title",
            "Confidence": "confidence",
            "Freshness": "freshness",
            "Tags": "tags",
        }
        config = NotionDatabaseConfigModel(
            connector_id="connector-123",
            database_id="db-456",
            database_name="Test DB",
            property_mapping=mapping,
        )
        assert config.property_mapping == mapping
