"""Tests for sync status and conflict resolver.

Plan 11-01, Task 2: SyncStatus and ConflictResolver.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.sync_status import SyncState, SyncStatus, SyncStatusTracker
from saw.connectors.conflict_resolver import (
    ConflictStrategy,
    ConflictInfo,
    ConflictResult,
    ConflictResolver,
)
from saw.connectors.protocol import ConnectorItem
from saw.connectors.models import SyncResult, SyncDirection


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestSyncState:
    """Tests for SyncState enum."""

    def test_sync_state_has_idle(self):
        """Test SyncState has IDLE value."""
        assert SyncState.IDLE.value == "idle"

    def test_sync_state_has_syncing(self):
        """Test SyncState has SYNCING value."""
        assert SyncState.SYNCING.value == "syncing"

    def test_sync_state_has_paused(self):
        """Test SyncState has PAUSED value."""
        assert SyncState.PAUSED.value == "paused"

    def test_sync_state_has_error(self):
        """Test SyncState has ERROR value."""
        assert SyncState.ERROR.value == "error"


class TestSyncStatus:
    """Tests for SyncStatus dataclass."""

    def test_sync_status_creation(self):
        """Test 1: SyncStatus can be created with all fields."""
        status = SyncStatus(
            connector_id="conn-123",
            platform="slack",
            state=SyncState.IDLE,
            last_sync_at=utcnow(),
            items_pending=5,
        )
        assert status.connector_id == "conn-123"
        assert status.platform == "slack"
        assert status.state == SyncState.IDLE
        assert status.items_pending == 5

    def test_sync_status_to_dict(self):
        """Test SyncStatus serialization."""
        now = utcnow()
        status = SyncStatus(
            connector_id="conn-456",
            platform="github",
            state=SyncState.SYNCING,
            last_sync_at=now,
            sync_cursor="cursor-abc",
        )
        d = status.to_dict()
        assert d["connector_id"] == "conn-456"
        assert d["platform"] == "github"
        assert d["state"] == "syncing"
        assert d["sync_cursor"] == "cursor-abc"


class TestSyncStatusTracker:
    """Tests for SyncStatusTracker."""

    @pytest.mark.asyncio
    async def test_get_status_returns_status_for_connector(self):
        """Test 1: SyncStatusTracker.get_status() returns status for connector."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        session.flush = AsyncMock()

        tracker = SyncStatusTracker(session)
        status = await tracker.get_status("conn-123")

        assert status.connector_id == "conn-123"
        assert status.state == SyncState.IDLE

    @pytest.mark.asyncio
    async def test_mark_sync_started_updates_status(self):
        """Test 2: SyncStatusTracker.mark_sync_started() updates status to syncing."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()
        session.flush = AsyncMock()

        tracker = SyncStatusTracker(session)
        await tracker.mark_sync_started("conn-123", "slack")

        # Check in-memory status updated
        status = tracker._in_memory_status["conn-123"]
        assert status.state == SyncState.SYNCING
        assert status.platform == "slack"

    @pytest.mark.asyncio
    async def test_mark_sync_completed_updates_last_sync_at(self):
        """Test 3: SyncStatusTracker.mark_sync_completed() updates last_sync_at."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.connector_id = "conn-123"
        mock_model.platform = "github"
        mock_result.scalar_one_or_none.return_value = mock_model
        session.execute = AsyncMock(return_value=mock_result)
        session.flush = AsyncMock()

        tracker = SyncStatusTracker(session)

        # Set up initial status
        tracker._in_memory_status["conn-123"] = SyncStatus(
            connector_id="conn-123",
            platform="github",
            state=SyncState.SYNCING,
        )

        result = SyncResult(
            connector_id="conn-123",
            direction=SyncDirection.PULL,
            pulled_count=10,
            pushed_count=0,
        )

        await tracker.mark_sync_completed("conn-123", result, cursor="next-page")

        status = tracker._in_memory_status["conn-123"]
        assert status.state == SyncState.IDLE
        assert status.last_sync_at is not None
        assert status.sync_cursor == "next-page"

    @pytest.mark.asyncio
    async def test_mark_error_updates_status(self):
        """Test SyncStatusTracker.mark_error() updates error status."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        session.execute = AsyncMock(return_value=mock_result)
        session.flush = AsyncMock()

        tracker = SyncStatusTracker(session)
        tracker._in_memory_status["conn-123"] = SyncStatus(
            connector_id="conn-123",
            platform="notion",
            state=SyncState.SYNCING,
        )

        await tracker.mark_error("conn-123", "API rate limit exceeded")

        status = tracker._in_memory_status["conn-123"]
        assert status.state == SyncState.ERROR
        assert status.last_error == "API rate limit exceeded"


class TestConflictStrategy:
    """Tests for ConflictStrategy enum."""

    def test_conflict_strategy_has_last_modified_wins(self):
        """Test ConflictStrategy has LAST_MODIFIED_WINS."""
        assert ConflictStrategy.LAST_MODIFIED_WINS.value == "last_modified_wins"

    def test_conflict_strategy_has_platform_wins(self):
        """Test ConflictStrategy has PLATFORM_WINS."""
        assert ConflictStrategy.PLATFORM_WINS.value == "platform_wins"

    def test_conflict_strategy_has_saw_wins(self):
        """Test ConflictStrategy has SAW_WINS."""
        assert ConflictStrategy.SAW_WINS.value == "saw_wins"

    def test_conflict_strategy_has_manual(self):
        """Test ConflictStrategy has MANUAL."""
        assert ConflictStrategy.MANUAL.value == "manual"


class TestConflictResolver:
    """Tests for ConflictResolver."""

    @pytest.fixture
    def resolver(self):
        """Create ConflictResolver instance."""
        session = AsyncMock()
        session.flush = AsyncMock()
        return ConflictResolver(session, ConflictStrategy.LAST_MODIFIED_WINS)

    def test_detect_conflict_returns_no_conflict_first_sync(self, resolver):
        """Test no conflict when first sync (no last_sync_at)."""
        item = ConnectorItem(
            id="msg-1",
            title="Test",
            content="Content",
            updated_at=utcnow(),
        )
        claim = {"id": "claim-1", "updated_at": utcnow()}

        result = resolver.detect_conflict(item, claim, last_sync_at=None)
        assert result.has_conflict is False
        assert result.winner == "platform"

    def test_detect_conflict_returns_conflict_when_both_modified(self, resolver):
        """Test 4: ConflictResolver.detect_conflict() returns ConflictResult when both modified."""
        now = utcnow()
        earlier = now - timedelta(hours=2)
        later_platform = now - timedelta(minutes=30)
        later_saw = now - timedelta(minutes=15)

        item = ConnectorItem(
            id="msg-2",
            title="Test",
            content="Platform content",
            updated_at=later_platform,
        )
        claim = {"id": "claim-2", "updated_at": later_saw}

        result = resolver.detect_conflict(item, claim, last_sync_at=earlier)

        assert result.has_conflict is True
        assert result.conflict_info is not None
        assert result.conflict_info.platform_item_id == "msg-2"

    def test_resolve_last_modified_wins(self, resolver):
        """Test 5: ConflictResolver.resolve() applies last_modified_wins strategy."""
        now = utcnow()
        earlier = now - timedelta(hours=1)

        conflict = ConflictInfo(
            platform_item_id="msg-3",
            saw_claim_id="claim-3",
            platform_modified_at=earlier,  # Platform is older
            saw_modified_at=now,  # SAW is newer
        )

        winner = resolver.resolve(conflict)
        assert winner == "saw"  # SAW is newer

    def test_resolve_platform_wins(self):
        """Test resolution with PLATFORM_WINS strategy."""
        session = AsyncMock()
        resolver = ConflictResolver(session, ConflictStrategy.PLATFORM_WINS)

        now = utcnow()
        conflict = ConflictInfo(
            platform_item_id="msg-4",
            saw_claim_id="claim-4",
            platform_modified_at=now - timedelta(hours=1),  # Older
            saw_modified_at=now,  # Newer
        )

        winner = resolver.resolve(conflict)
        assert winner == "platform"  # Platform wins regardless

    @pytest.mark.asyncio
    async def test_record_conflict(self, resolver):
        """Test 6: ConflictResolver logs conflicts to ConflictRecordModel."""
        resolver._session.add = MagicMock()
        resolver._session.flush = AsyncMock()

        conflict = ConflictInfo(
            platform_item_id="msg-5",
            saw_claim_id="claim-5",
            platform_modified_at=utcnow(),
            saw_modified_at=utcnow(),
        )

        with patch("saw.connectors.conflict_resolver.ConflictRecordModel") as MockRecord:
            mock_record = MagicMock()
            MockRecord.return_value = mock_record
            result = await resolver.record_conflict(conflict, "platform_wins", "conn-123")

        assert resolver._session.add.called
        assert resolver._session.flush.called


class TestConflictInfo:
    """Tests for ConflictInfo dataclass."""

    def test_conflict_info_creation(self):
        """Test creating ConflictInfo."""
        now = utcnow()
        info = ConflictInfo(
            platform_item_id="msg-123",
            saw_claim_id="claim-456",
            platform_modified_at=now,
            saw_modified_at=now,
        )
        assert info.platform_item_id == "msg-123"
        assert info.saw_claim_id == "claim-456"
        assert info.resolution is None


class TestConflictResult:
    """Tests for ConflictResult dataclass."""

    def test_conflict_result_no_conflict(self):
        """Test ConflictResult for no conflict."""
        result = ConflictResult(has_conflict=False, winner="platform")
        assert result.has_conflict is False
        assert result.winner == "platform"
        assert result.conflict_info is None

    def test_conflict_result_with_conflict(self):
        """Test ConflictResult with conflict."""
        info = ConflictInfo(
            platform_item_id="msg-1",
            saw_claim_id="claim-1",
            platform_modified_at=utcnow(),
            saw_modified_at=utcnow(),
        )
        result = ConflictResult(has_conflict=True, conflict_info=info)
        assert result.has_conflict is True
        assert result.conflict_info == info
