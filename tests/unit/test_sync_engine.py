"""Tests for sync engine.

Plan 11-01, Task 3: SyncEngine with loop detection and backpressure.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.sync_engine import (
    SyncEngine,
    SyncMode,
    SyncOptions,
    ClaimCreate,
)
from saw.connectors.protocol import SyncDirection, ConnectorItem
from saw.connectors.models import SyncResult


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestSyncMode:
    """Tests for SyncMode enum."""

    def test_sync_mode_has_full(self):
        """Test SyncMode has FULL value."""
        assert SyncMode.FULL.value == "full"

    def test_sync_mode_has_incremental(self):
        """Test SyncMode has INCREMENTAL value."""
        assert SyncMode.INCREMENTAL.value == "incremental"


class TestSyncOptions:
    """Tests for SyncOptions dataclass."""

    def test_sync_options_defaults(self):
        """Test SyncOptions default values."""
        options = SyncOptions()
        assert options.direction == SyncDirection.BIDIRECTIONAL
        assert options.mode == SyncMode.INCREMENTAL
        assert options.force is False

    def test_sync_options_custom(self):
        """Test SyncOptions with custom values."""
        options = SyncOptions(
            direction=SyncDirection.PULL,
            mode=SyncMode.FULL,
            force=True,
        )
        assert options.direction == SyncDirection.PULL
        assert options.mode == SyncMode.FULL
        assert options.force is True


class TestClaimCreate:
    """Tests for ClaimCreate dataclass."""

    def test_claim_create_basic(self):
        """Test creating ClaimCreate."""
        claim = ClaimCreate(
            content="Test content",
            source_platform="slack",
            source_id="msg-123",
        )
        assert claim.content == "Test content"
        assert claim.source_platform == "slack"
        assert claim.source_id == "msg-123"
        assert claim.source_url is None
        assert claim.metadata == {}

    def test_claim_create_with_metadata(self):
        """Test ClaimCreate with metadata."""
        claim = ClaimCreate(
            content="Test",
            source_platform="github",
            source_id="issue-456",
            source_url="https://github.com/repo/issues/456",
            metadata={"author": "user1", "labels": ["bug"]},
        )
        assert claim.source_url == "https://github.com/repo/issues/456"
        assert claim.metadata["author"] == "user1"


class TestSyncEngine:
    """Tests for SyncEngine."""

    @pytest.fixture
    def mock_registry(self):
        """Create mock connector registry."""
        registry = MagicMock()
        registry.get = MagicMock(return_value=None)
        return registry

    @pytest.fixture
    def mock_write_queue(self):
        """Create mock write queue."""
        queue = MagicMock()
        queue.enqueue = MagicMock()
        queue.get_pending = MagicMock(return_value=[])
        return queue

    @pytest.fixture
    def mock_session(self):
        """Create mock async session.

        ``AsyncSession.execute()`` returns a sync ``Result``; its
        ``scalar_one_or_none()`` is a sync call. A bare ``AsyncMock()`` for
        ``execute`` makes ``result.scalar_one_or_none()`` return an
        un-awaited coroutine → ``AttributeError: 'coroutine' object has no
        attribute 'connector_id'``. Return a sync Result mock whose
        ``scalar_one_or_none`` returns None (→ SyncStatusTracker default
        status).
        """
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def sync_engine(self, mock_registry, mock_write_queue, mock_session):
        """Create SyncEngine instance."""
        return SyncEngine(mock_registry, mock_write_queue, mock_session)

    @pytest.fixture
    def mock_connector(self):
        """Create mock connector."""
        connector = AsyncMock()
        connector.platform_name = "slack"
        connector.supports_push = True
        connector.get_items = AsyncMock(return_value=[])
        connector.put_item = AsyncMock(return_value="item-id")
        return connector

    @pytest.mark.asyncio
    async def test_sync_pull_fetches_items(self, sync_engine, mock_connector, mock_session):
        """Test 1: SyncEngine.sync_pull() fetches items from connector."""
        # Mock status tracker
        mock_status = MagicMock()
        mock_status.last_sync_at = None
        sync_engine._status_tracker.get_status = AsyncMock(return_value=mock_status)

        # Create test items
        items = [
            ConnectorItem(
                id="msg-1",
                title="Test",
                content="Content 1",
                updated_at=utcnow(),
            ),
            ConnectorItem(
                id="msg-2",
                title="Test 2",
                content="Content 2",
                updated_at=utcnow(),
            ),
        ]
        mock_connector.get_items = AsyncMock(return_value=items)

        options = SyncOptions(direction=SyncDirection.PULL)
        result = await sync_engine.sync_pull(mock_connector, options)

        assert result.pulled_count == 2
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_sync_push_sends_items(self, sync_engine, mock_connector, mock_session):
        """Test 2: SyncEngine.sync_push() sends items to connector."""
        options = SyncOptions(direction=SyncDirection.PUSH)
        result = await sync_engine.sync_push(mock_connector, options)

        # Push returns 0 for now (TODO: requires ClaimRepository)
        assert result.pushed_count == 0

    @pytest.mark.asyncio
    async def test_sync_push_counts_success_with_empty_id(
        self, sync_engine, mock_connector, mock_session, tmp_path, monkeypatch
    ):
        """A connector whose put_item returns "" on success (e.g. WeCom bot
        webhooks, which reply with no msgid) must still count as pushed,
        not be reported as a sync error."""
        from types import SimpleNamespace

        mock_connector.put_item = AsyncMock(return_value="")
        mock_connector.platform_name = "wecom"

        # Point sync_push at a claims DB that exists + exposes one claim.
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".saw" / "db").mkdir(parents=True)
        (tmp_path / ".saw" / "db" / "claims.db").write_bytes(b"")

        with patch("saw.adapters.storage.claims_repository.SQLiteClaimsRepository") as MockRepo:
            claim = SimpleNamespace(
                uuid="u-1", content="hello", title="t",
                source_url=None, author=None,
                created_at=None, updated_at=None, metadata={},
            )
            mock_repo = MockRepo.return_value
            mock_repo.list_modified_since.return_value = [claim]

            status = MagicMock()
            status.last_sync_at = None
            sync_engine._status_tracker.get_status = AsyncMock(return_value=status)

            options = SyncOptions(direction=SyncDirection.PUSH, force=True)
            result = await sync_engine.sync_push(mock_connector, options)

        assert result.pushed_count == 1
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_sync_loop_detection(self, sync_engine, mock_connector):
        """Test 3: SyncEngine detects sync loop (skips items with source_platform matching target)."""
        # Item that originated from slack (same as target platform)
        loop_item = ConnectorItem(
            id="msg-loop",
            title="Loop",
            content="Content",
            updated_at=utcnow(),
            metadata={"source_platform": "slack"},  # Same as connector!
        )

        is_loop = sync_engine._is_sync_loop(loop_item, "slack")
        assert is_loop is True

        # Item from different platform
        normal_item = ConnectorItem(
            id="msg-normal",
            title="Normal",
            content="Content",
            updated_at=utcnow(),
            metadata={"source_platform": "notion"},  # Different platform
        )

        is_loop = sync_engine._is_sync_loop(normal_item, "slack")
        assert is_loop is False

    @pytest.mark.asyncio
    async def test_backpressure_pauses_at_threshold(self, sync_engine, mock_write_queue):
        """Test 4: SyncEngine pauses pull when queue depth > 1000."""
        # Mock queue with 1500 pending items
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 1500)

        should_pause, depth = await sync_engine.check_backpressure()

        assert should_pause is True
        assert depth == 1500

    @pytest.mark.asyncio
    async def test_backpressure_resumes_below_threshold(self, sync_engine, mock_write_queue):
        """Test 5: SyncEngine resumes pull when queue depth < 500."""
        # First trigger pause
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 1500)
        await sync_engine.check_backpressure()
        assert sync_engine._is_paused is True

        # Then drop below resume threshold
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 400)
        should_pause, depth = await sync_engine.check_backpressure()

        assert should_pause is False
        assert depth == 400

    @pytest.mark.asyncio
    async def test_create_claim_with_source_metadata(self, sync_engine):
        """Test 6: SyncEngine creates Claims with source_platform and source_id metadata."""
        item = ConnectorItem(
            id="msg-metadata",
            title="Test",
            content="Content with metadata",
            url="https://slack.com/msg/123",
            author="user1",
            created_at=utcnow(),
            updated_at=utcnow(),
            metadata={"channel_id": "ch-1", "thread_parent_id": "thread-1"},
        )

        claim = sync_engine._create_claim_from_item(item, "slack")

        assert claim.source_platform == "slack"
        assert claim.source_id == "msg-metadata"
        assert claim.source_url == "https://slack.com/msg/123"
        assert claim.metadata["source_platform"] == "slack"
        assert claim.metadata["source_id"] == "msg-metadata"
        assert claim.metadata["channel_id"] == "ch-1"
        assert claim.metadata["thread_parent_id"] == "thread-1"

    @pytest.mark.asyncio
    async def test_sync_logs_operations(self, sync_engine, mock_connector, mock_session):
        """Test 7: SyncEngine logs all operations via SyncLogger."""
        # Mock status tracker
        sync_engine._status_tracker.get_status = AsyncMock(
            return_value=MagicMock(last_sync_at=None)
        )
        sync_engine._status_tracker.mark_sync_started = AsyncMock()
        sync_engine._status_tracker.mark_sync_completed = AsyncMock()

        # Mock logger
        sync_engine._logger.log_sync = AsyncMock()

        mock_connector.get_items = AsyncMock(return_value=[])

        result = await sync_engine.sync(
            connector_id="conn-123",
            connector=mock_connector,
            options=SyncOptions(direction=SyncDirection.PULL),
        )

        # Verify logging was called
        assert sync_engine._logger.log_sync.called
