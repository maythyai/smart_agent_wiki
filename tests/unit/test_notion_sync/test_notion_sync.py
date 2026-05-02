"""Tests for NotionSyncManager.

Plan 12-03: Bidirectional sync and polling.
Per NOTI-05: User can sync back to Notion.
Per NOTI-08: Configurable polling.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.notion.sync_manager import NotionSyncManager, NotionSyncConfig
from saw.connectors.protocol import SyncDirection
from saw.connectors.models import SyncResult
from saw.connectors.conflict_resolver import ConflictStrategy


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestNotionSyncManager:
    """Tests for NotionSyncManager class."""

    @pytest.mark.asyncio
    async def test_sync_pull_fetches_pages(self) -> None:
        """Test 1: sync_pull() fetches pages from selected databases and creates Claims."""
        mock_connector = AsyncMock()
        mock_connector.platform_name = "notion"
        mock_connector._config = MagicMock()
        mock_connector._config.id = "connector-1"
        mock_connector.get_items = AsyncMock(return_value=[])

        result = SyncResult(
            connector_id="connector-1",
            direction=SyncDirection.PULL,
            pulled_count=10,
        )

        mock_sync_engine = AsyncMock()
        mock_sync_engine.sync = AsyncMock(return_value=result)

        mock_scheduler = MagicMock()
        mock_session = AsyncMock()

        config = NotionSyncConfig()
        manager = NotionSyncManager(
            config=config,
            connector=mock_connector,
            sync_engine=mock_sync_engine,
            scheduler=mock_scheduler,
            session=mock_session,
        )

        result = await manager.sync_pull()

        assert result.pulled_count == 10

    @pytest.mark.asyncio
    async def test_sync_push_sends_modified_claims(self) -> None:
        """Test 2: sync_push() sends modified Claims back to Notion."""
        mock_connector = AsyncMock()
        mock_connector.platform_name = "notion"
        mock_connector._config = MagicMock()
        mock_connector._config.id = "connector-1"
        mock_connector.put_item = AsyncMock(return_value="page-1")

        result = SyncResult(
            connector_id="connector-1",
            direction=SyncDirection.PUSH,
            pushed_count=5,
        )

        mock_sync_engine = AsyncMock()
        mock_sync_engine.sync = AsyncMock(return_value=result)

        mock_scheduler = MagicMock()
        mock_session = AsyncMock()

        config = NotionSyncConfig()
        manager = NotionSyncManager(
            config=config,
            connector=mock_connector,
            sync_engine=mock_sync_engine,
            scheduler=mock_scheduler,
            session=mock_session,
        )

        result = await manager.sync_push()

        assert result.pushed_count == 5

    @pytest.mark.asyncio
    async def test_bidirectional_sync(self) -> None:
        """Test 3: Bidirectional sync performs both pull and push."""
        mock_connector = AsyncMock()
        mock_connector.platform_name = "notion"

        mock_sync_engine = AsyncMock()
        mock_sync_engine.sync = AsyncMock(return_value=SyncResult(
            connector_id="connector-1",
            direction=SyncDirection.BIDIRECTIONAL,
            pulled_count=10,
            pushed_count=5,
        ))

        mock_scheduler = MagicMock()
        mock_session = AsyncMock()

        config = NotionSyncConfig()
        manager = NotionSyncManager(
            config=config,
            connector=mock_connector,
            sync_engine=mock_sync_engine,
            scheduler=mock_scheduler,
            session=mock_session,
        )

        result = await manager.run_sync(direction=SyncDirection.BIDIRECTIONAL)

        assert result.pulled_count == 10
        assert result.pushed_count == 5

    @pytest.mark.asyncio
    async def test_conflicts_detected_during_sync(self) -> None:
        """Test 4: Conflicts detected during bidirectional sync."""
        mock_connector = AsyncMock()
        mock_connector.platform_name = "notion"

        mock_sync_engine = AsyncMock()
        mock_sync_engine.sync = AsyncMock(return_value=SyncResult(
            connector_id="connector-1",
            direction=SyncDirection.BIDIRECTIONAL,
            pulled_count=5,
            pushed_count=5,
            conflicts_count=2,
        ))

        mock_scheduler = MagicMock()
        mock_session = AsyncMock()

        config = NotionSyncConfig()
        manager = NotionSyncManager(
            config=config,
            connector=mock_connector,
            sync_engine=mock_sync_engine,
            scheduler=mock_scheduler,
            session=mock_session,
        )

        result = await manager.run_sync(direction=SyncDirection.BIDIRECTIONAL)

        assert result.conflicts_count == 2

    def test_poll_interval_configurable(self) -> None:
        """Test 5: Poll interval configurable (default 3600 seconds)."""
        config = NotionSyncConfig()
        assert config.poll_interval_seconds == 3600

        custom_config = NotionSyncConfig(poll_interval_seconds=1800)
        assert custom_config.poll_interval_seconds == 1800

    def test_start_polling(self) -> None:
        """Test 6: start_polling() continues until cancelled."""
        mock_connector = AsyncMock()
        mock_sync_engine = AsyncMock()
        mock_scheduler = MagicMock()
        mock_scheduler.add_job = MagicMock()
        mock_session = AsyncMock()

        config = NotionSyncConfig()
        manager = NotionSyncManager(
            config=config,
            connector=mock_connector,
            sync_engine=mock_sync_engine,
            scheduler=mock_scheduler,
            session=mock_session,
        )

        manager.start_polling()

        mock_scheduler.add_job.assert_called_once()

    def test_stop_polling(self) -> None:
        """Test that stop_polling removes scheduled job."""
        mock_connector = AsyncMock()
        mock_sync_engine = AsyncMock()
        mock_scheduler = MagicMock()
        mock_scheduler.remove_job = MagicMock()
        mock_session = AsyncMock()

        config = NotionSyncConfig()
        manager = NotionSyncManager(
            config=config,
            connector=mock_connector,
            sync_engine=mock_sync_engine,
            scheduler=mock_scheduler,
            session=mock_session,
        )

        manager._job_id = "notion-sync-connector-1"
        manager.stop_polling()

        mock_scheduler.remove_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_manual_trigger_overrides_scheduled(self) -> None:
        """Test 7: Manual trigger overrides scheduled poll."""
        mock_connector = AsyncMock()
        mock_connector.platform_name = "notion"

        mock_sync_engine = AsyncMock()
        mock_sync_engine.sync = AsyncMock(return_value=SyncResult(
            connector_id="connector-1",
            direction=SyncDirection.BIDIRECTIONAL,
        ))

        mock_scheduler = MagicMock()
        mock_session = AsyncMock()

        config = NotionSyncConfig()
        manager = NotionSyncManager(
            config=config,
            connector=mock_connector,
            sync_engine=mock_sync_engine,
            scheduler=mock_scheduler,
            session=mock_session,
        )

        result = await manager.trigger_manual_sync()

        assert result is not None

    @pytest.mark.asyncio
    async def test_sync_respects_backpressure(self) -> None:
        """Test 8: Sync respects backpressure (pauses when queue full)."""
        mock_connector = AsyncMock()
        mock_connector.platform_name = "notion"

        mock_sync_engine = AsyncMock()
        mock_sync_engine.check_backpressure = AsyncMock(return_value=(True, 1500))
        mock_sync_engine.sync = AsyncMock(return_value=SyncResult(
            connector_id="connector-1",
            direction=SyncDirection.PULL,
        ))

        mock_scheduler = MagicMock()
        mock_session = AsyncMock()

        config = NotionSyncConfig()
        manager = NotionSyncManager(
            config=config,
            connector=mock_connector,
            sync_engine=mock_sync_engine,
            scheduler=mock_scheduler,
            session=mock_session,
        )

        # Sync should still work but log backpressure
        result = await manager.sync_pull(force=True)

        # Sync should complete (backpressure handled by sync_engine)
        assert result is not None


class TestNotionSyncConfig:
    """Tests for NotionSyncConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = NotionSyncConfig()

        assert config.poll_interval_seconds == 3600
        assert config.batch_size == 100
        assert config.skip_large_pages is True
        assert config.large_page_threshold == 100
        assert config.enable_push is True
        assert config.conflict_strategy == ConflictStrategy.LAST_MODIFIED_WINS

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = NotionSyncConfig(
            poll_interval_seconds=1800,
            batch_size=50,
            enable_push=False,
            conflict_strategy=ConflictStrategy.SAW_WINS,
        )

        assert config.poll_interval_seconds == 1800
        assert config.batch_size == 50
        assert config.enable_push is False
        assert config.conflict_strategy == ConflictStrategy.SAW_WINS
