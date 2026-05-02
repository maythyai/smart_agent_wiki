"""Tests for sync logger and sync models.

Plan 11-01, Task 1: Sync models and SyncLogger.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.sync_logger import SyncLogger, SyncLogEntry


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestSyncLogEntry:
    """Tests for SyncLogEntry dataclass."""

    def test_sync_log_entry_creation(self):
        """Test creating a SyncLogEntry."""
        entry = SyncLogEntry(
            connector_id="conn-123",
            platform="slack",
            direction="pull",
            status="success",
            items={"pulled": 10, "pushed": 0, "skipped": 2},
        )
        assert entry.connector_id == "conn-123"
        assert entry.platform == "slack"
        assert entry.direction == "pull"
        assert entry.status == "success"
        assert entry.items["pulled"] == 10

    def test_sync_log_entry_defaults(self):
        """Test SyncLogEntry default values."""
        entry = SyncLogEntry(
            connector_id="conn-123",
            platform="notion",
            direction="push",
            status="success",
        )
        assert entry.items == {}
        assert entry.metadata == {}
        assert entry.error_message is None


class TestSyncLogger:
    """Tests for SyncLogger."""

    @pytest.mark.asyncio
    async def test_log_sync_creates_sync_log_model(self):
        """Test 1: SyncLogger.log_sync() creates SyncLogModel with timestamp, direction, platform."""
        session = AsyncMock()
        session.flush = AsyncMock()
        logger = SyncLogger(session)

        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.connector_id = "conn-123"
        mock_log.platform = "slack"
        mock_log.direction = "pull"
        mock_log.status = "success"

        with patch("saw.connectors.sync_logger.SyncLogModel", return_value=mock_log):
            result = await logger.log_sync(
                connector_id="conn-123",
                platform="slack",
                direction="pull",
                status="success",
                items={"pulled": 5, "pushed": 0, "skipped": 1},
            )

        assert session.add.called
        assert session.flush.called

    @pytest.mark.asyncio
    async def test_log_sync_records_item_counts(self):
        """Test 2: SyncLogger.log_sync() records items_pulled, items_pushed, items_skipped counts."""
        session = AsyncMock()
        session.flush = AsyncMock()
        logger = SyncLogger(session)

        mock_log = MagicMock()

        with patch("saw.connectors.sync_logger.SyncLogModel", return_value=mock_log) as MockLogModel:
            await logger.log_sync(
                connector_id="conn-456",
                platform="github",
                direction="bidirectional",
                status="success",
                items={"pulled": 20, "pushed": 15, "skipped": 3},
            )

        # Check that SyncLogModel was called with correct counts
        call_kwargs = MockLogModel.call_args[1]
        assert call_kwargs["items_pulled"] == 20
        assert call_kwargs["items_pushed"] == 15
        assert call_kwargs["items_skipped"] == 3

    @pytest.mark.asyncio
    async def test_log_error_records_error_details(self):
        """Test 3: SyncLogger.log_error() records error details with ERROR level."""
        session = AsyncMock()
        session.flush = AsyncMock()
        logger = SyncLogger(session)

        mock_log = MagicMock()

        with patch("saw.connectors.sync_logger.SyncLogModel", return_value=mock_log) as MockLogModel:
            result = await logger.log_error(
                connector_id="conn-789",
                platform="notion",
                error="Connection timeout after 30s",
                metadata={"retry_count": 3, "error_code": "ETIMEDOUT"},
            )

        call_kwargs = MockLogModel.call_args[1]
        assert call_kwargs["status"] == "failed"
        assert call_kwargs["error_message"] == "Connection timeout after 30s"
        assert call_kwargs["extra_data"]["retry_count"] == 3
        assert call_kwargs["extra_data"]["error_code"] == "ETIMEDOUT"

    @pytest.mark.asyncio
    async def test_get_recent_logs_filtered_by_platform(self):
        """Test 4: SyncLogger.get_recent_logs() returns logs filtered by platform."""
        session = AsyncMock()

        # Mock the execute return value chain
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        session.execute = AsyncMock(return_value=mock_result)

        logger = SyncLogger(session)

        logs = await logger.get_recent_logs(platform="slack", limit=10)

        # Verify the query was executed
        assert session.execute.called

    @pytest.mark.asyncio
    async def test_get_sync_summary(self):
        """Test 5: get_sync_summary returns aggregated metrics."""
        session = AsyncMock()

        # Create mock logs
        mock_log1 = MagicMock()
        mock_log1.items_pulled = 10
        mock_log1.items_pushed = 5
        mock_log1.status = "success"
        mock_log1.completed_at = utcnow()

        mock_log2 = MagicMock()
        mock_log2.items_pulled = 0
        mock_log2.items_pushed = 3
        mock_log2.status = "success"
        mock_log2.completed_at = utcnow()

        mock_log3 = MagicMock()
        mock_log3.items_pulled = 0
        mock_log3.items_pushed = 0
        mock_log3.status = "failed"
        mock_log3.completed_at = None

        # Mock the execute return value chain
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_log1, mock_log2, mock_log3]
        mock_result.scalars.return_value = mock_scalars
        session.execute = AsyncMock(return_value=mock_result)

        logger = SyncLogger(session)

        summary = await logger.get_sync_summary("conn-xyz", hours=24)

        assert summary["connector_id"] == "conn-xyz"
        assert summary["items_pulled"] == 10
        assert summary["items_pushed"] == 8
        assert summary["error_count"] == 1
        assert summary["total_operations"] == 3


class TestSyncLogModel:
    """Tests for SyncLogModel SQLAlchemy model."""

    def test_sync_log_model_schema(self):
        """Test 6: SyncLogModel persists to SQLite with correct schema."""
        # Verify model has correct columns
        from saw.db.sync_models import SyncLogModel
        columns = {c.name: c.type for c in SyncLogModel.__table__.columns}

        assert "id" in columns
        assert "connector_id" in columns
        assert "platform" in columns
        assert "direction" in columns
        assert "started_at" in columns
        assert "completed_at" in columns
        assert "status" in columns
        assert "items_pulled" in columns
        assert "items_pushed" in columns
        assert "items_skipped" in columns
        assert "error_message" in columns
        assert "extra_data" in columns

        # verify defaults
        assert SyncLogModel.items_pulled.default.arg == 0
        assert SyncLogModel.items_pushed.default.arg == 0
        assert SyncLogModel.items_skipped.default.arg == 0


class TestSyncStateModel:
    """Tests for SyncStateModel SQLAlchemy model."""

    def test_sync_state_model_schema(self):
        """Test SyncStateModel has correct schema."""
        from saw.db.sync_models import SyncStateModel
        columns = {c.name: c.type for c in SyncStateModel.__table__.columns}

        assert "id" in columns
        assert "connector_id" in columns
        assert "platform" in columns
        assert "last_sync_at" in columns
        assert "last_sync_cursor" in columns
        assert "last_error" in columns
        assert "last_error_at" in columns
        assert "items_synced_total" in columns
        assert "sync_in_progress" in columns


class TestConflictRecordModel:
    """Tests for ConflictRecordModel SQLAlchemy model."""

    def test_conflict_record_model_schema(self):
        """Test ConflictRecordModel has correct schema."""
        from saw.db.sync_models import ConflictRecordModel
        columns = {c.name: c.type for c in ConflictRecordModel.__table__.columns}

        assert "id" in columns
        assert "connector_id" in columns
        assert "platform_item_id" in columns
        assert "saw_claim_id" in columns
        assert "platform_modified_at" in columns
        assert "saw_modified_at" in columns
        assert "resolution" in columns
        assert "resolved_at" in columns
        assert "created_at" in columns
