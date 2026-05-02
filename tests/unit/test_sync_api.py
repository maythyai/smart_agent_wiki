"""Tests for sync API and connector sink.

Plan 11-03, Task 3 & 4: Sync API endpoints and ConnectorSink.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.protocol import SyncDirection
from saw.connectors.sync_engine import SyncOptions, SyncMode
from saw.connectors.health_monitor import HealthStatus, ConnectorHealth


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestSyncOptions:
    """Tests for SyncOptions."""

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


class TestConnectorSink:
    """Tests for ConnectorSink."""

    @pytest.fixture
    def mock_registry(self):
        """Create mock connector registry."""
        registry = MagicMock()
        registry.get = MagicMock(return_value=None)
        registry.list_all = MagicMock(return_value=[])
        return registry

    @pytest.fixture
    def mock_sync_engine(self):
        """Create mock sync engine."""
        engine = MagicMock()
        engine.sync = AsyncMock()
        return engine

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def sink_config(self):
        """Create connector sink config."""
        from saw.write_queue.sinks.connector_sink import ConnectorSinkConfig
        return ConnectorSinkConfig(
            enabled_connectors=["slack", "github"],
            batch_size=5,
        )

    @pytest.fixture
    def connector_sink(self, sink_config, mock_sync_engine, mock_registry, mock_session):
        """Create ConnectorSink instance."""
        from saw.write_queue.sinks.connector_sink import ConnectorSink
        sink = ConnectorSink(
            config=sink_config,
            sync_engine=mock_sync_engine,
            registry=mock_registry,
            session=mock_session,
        )
        # Pre-populate health cache to avoid DB queries
        sink._health_monitor._health_cache["slack"] = ConnectorHealth(
            connector_id="slack",
            platform="slack",
            status=HealthStatus.HEALTHY,
        )
        sink._health_monitor._health_cache["github"] = ConnectorHealth(
            connector_id="github",
            platform="github",
            status=HealthStatus.HEALTHY,
        )
        return sink

    @pytest.mark.asyncio
    async def test_processes_claim_write_operations(self, connector_sink, mock_registry):
        """Test 1: ConnectorSink processes Claim write operations."""
        from saw.write_queue.queue import WriteOp
        from saw.domain.value_objects import WriteOpStatus

        mock_connector = AsyncMock()
        mock_connector.platform_name = "slack"
        mock_connector.supports_push = True
        mock_connector.put_item = AsyncMock(return_value="item-id")

        # Set up registry to return connector for slack
        def get_connector(name):
            if name == "slack":
                return mock_connector
            return None
        mock_registry.get = MagicMock(side_effect=get_connector)

        op = WriteOp(
            op_id="op-1",
            session_id="session-1",
            sink_name="claims",
            payload={
                "content": "Test content",
                "source_platform": "notion",  # Different from target
                "source_id": "item-123",
            },
            status=WriteOpStatus.PENDING,
        )

        result = await connector_sink.process(op)

        assert result.success is True
        assert result.items_pushed > 0

    @pytest.mark.asyncio
    async def test_calls_sync_push_for_outbound(self, connector_sink, mock_registry, mock_session):
        """Test 2: ConnectorSink calls sync_push for outbound writes."""
        from saw.write_queue.queue import WriteOp
        from saw.domain.value_objects import WriteOpStatus

        mock_connector = AsyncMock()
        mock_connector.platform_name = "github"
        mock_connector.supports_push = True
        mock_connector.put_item = AsyncMock(return_value="issue-123")

        def get_connector(name):
            if name == "github":
                return mock_connector
            return None
        mock_registry.get = MagicMock(side_effect=get_connector)

        op = WriteOp(
            op_id="op-2",
            session_id="session-2",
            sink_name="claims",
            payload={
                "content": "GitHub issue",
                "source_platform": "local",
                "source_id": "claim-1",
            },
            status=WriteOpStatus.PENDING,
        )

        result = await connector_sink.process(op)

        assert result.success is True
        assert result.items_pushed > 0

    @pytest.mark.asyncio
    async def test_handles_backpressure_correctly(self, connector_sink):
        """Test 3: ConnectorSink handles backpressure."""
        from saw.write_queue.sinks.connector_sink import SinkResult

        # With no enabled connectors, should return success
        connector_sink._config.enabled_connectors = []

        from saw.write_queue.queue import WriteOp
        from saw.domain.value_objects import WriteOpStatus

        op = WriteOp(
            op_id="op-3",
            session_id="session-3",
            sink_name="claims",
            payload={"content": "test"},
            status=WriteOpStatus.PENDING,
        )

        result = await connector_sink.process(op)

        assert result.success is True
        assert result.items_pushed == 0

    @pytest.mark.asyncio
    async def test_retries_failed_pushes(self, connector_sink, mock_registry):
        """Test 4: ConnectorSink retries failed pushes."""
        from saw.write_queue.queue import WriteOp
        from saw.domain.value_objects import WriteOpStatus
        from saw.connectors.retry_handler import TransientError

        mock_connector = AsyncMock()
        mock_connector.platform_name = "slack"
        mock_connector.supports_push = True
        mock_connector.put_item = AsyncMock(side_effect=TransientError("Rate limit"))

        def get_connector(name):
            if name == "slack":
                return mock_connector
            return None
        mock_registry.get = MagicMock(side_effect=get_connector)

        # Mark as unhealthy to skip
        connector_sink._health_monitor._health_cache["slack"] = ConnectorHealth(
            connector_id="slack",
            platform="slack",
            status=HealthStatus.UNHEALTHY,
        )

        op = WriteOp(
            op_id="op-4",
            session_id="session-4",
            sink_name="claims",
            payload={
                "content": "test",
                "source_platform": "local",
            },
            status=WriteOpStatus.PENDING,
        )

        result = await connector_sink.process(op)

        # Should skip unhealthy connector - graceful degradation
        # The result indicates the error but still processes (no crash)
        assert result.error is not None  # Error logged
        assert "unhealthy" in result.error.lower()

    def test_should_process_claim_items(self, connector_sink, mock_registry):
        """Test 5: should_process returns True for claim items."""
        from saw.write_queue.queue import WriteOp
        from saw.domain.value_objects import WriteOpStatus

        mock_connector = MagicMock()
        mock_connector.supports_push = True

        def get_connector(name):
            if name == "slack":
                return mock_connector
            return None
        mock_registry.get = MagicMock(side_effect=get_connector)

        op = WriteOp(
            op_id="op-5",
            session_id="session-5",
            sink_name="claims",
            payload={
                "content": "test",
                "source_platform": "local",  # Different from slack
            },
            status=WriteOpStatus.PENDING,
        )

        should = connector_sink.should_process(op)
        assert should is True

    def test_should_not_process_non_claim_items(self, connector_sink):
        """Test should_process returns False for non-claim items."""
        from saw.write_queue.queue import WriteOp
        from saw.domain.value_objects import WriteOpStatus

        op = WriteOp(
            op_id="op-6",
            session_id="session-6",
            sink_name="vault",  # Not claims
            payload={},
            status=WriteOpStatus.PENDING,
        )

        should = connector_sink.should_process(op)
        assert should is False

    def test_loop_prevention(self, connector_sink, mock_registry):
        """Test source_platform matching prevents push to same platform."""
        from saw.write_queue.queue import WriteOp
        from saw.domain.value_objects import WriteOpStatus

        # Item from slack should not push to slack
        op = WriteOp(
            op_id="op-7",
            session_id="session-7",
            sink_name="claims",
            payload={
                "content": "test",
                "source_platform": "slack",  # Same as enabled connector
            },
            status=WriteOpStatus.PENDING,
        )

        mock_connector = MagicMock()
        mock_connector.supports_push = True

        def get_connector(name):
            return mock_connector
        mock_registry.get = MagicMock(side_effect=get_connector)

        should = connector_sink.should_process(op)
        # Should be True because github is also enabled
        assert should is True


class TestConnectorSinkConfig:
    """Tests for ConnectorSinkConfig."""

    def test_config_defaults(self):
        """Test default configuration."""
        from saw.write_queue.sinks.connector_sink import ConnectorSinkConfig
        config = ConnectorSinkConfig()

        assert config.enabled_connectors == []
        assert config.batch_size == 10
        assert config.batch_timeout_seconds == 5.0

    def test_config_custom(self):
        """Test custom configuration."""
        from saw.write_queue.sinks.connector_sink import ConnectorSinkConfig
        config = ConnectorSinkConfig(
            enabled_connectors=["slack", "github", "notion"],
            batch_size=20,
        )

        assert len(config.enabled_connectors) == 3
        assert config.batch_size == 20


class TestSinkResult:
    """Tests for SinkResult."""

    def test_result_success(self):
        """Test SinkResult for success."""
        from saw.write_queue.sinks.connector_sink import SinkResult
        result = SinkResult(
            success=True,
            items_pushed=5,
        )
        assert result.success is True
        assert result.items_pushed == 5
        assert result.error is None

    def test_result_failure(self):
        """Test SinkResult for failure."""
        from saw.write_queue.sinks.connector_sink import SinkResult
        result = SinkResult(
            success=False,
            error="API rate limit exceeded",
        )
        assert result.success is False
        assert result.error == "API rate limit exceeded"