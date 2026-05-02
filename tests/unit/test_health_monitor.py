"""Tests for health monitor and health API.

Plan 11-02, Task 3: HealthMonitor.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.health_monitor import (
    HealthStatus,
    HealthThresholds,
    ConnectorHealth,
    HealthEvent,
    HealthMonitor,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_status_has_healthy(self):
        """Test HealthStatus has HEALTHY."""
        assert HealthStatus.HEALTHY.value == "healthy"

    def test_status_has_degraded(self):
        """Test HealthStatus has DEGRADED."""
        assert HealthStatus.DEGRADED.value == "degraded"

    def test_status_has_unhealthy(self):
        """Test HealthStatus has UNHEALTHY."""
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestHealthThresholds:
    """Tests for HealthThresholds."""

    def test_thresholds_defaults(self):
        """Test default threshold values."""
        thresholds = HealthThresholds()
        assert thresholds.degraded_after_failures == 2
        assert thresholds.unhealthy_after_failures == 5
        assert thresholds.healthy_after_successes == 3


class TestConnectorHealth:
    """Tests for ConnectorHealth."""

    def test_health_creation(self):
        """Test creating ConnectorHealth."""
        health = ConnectorHealth(
            connector_id="conn-123",
            platform="slack",
            status=HealthStatus.HEALTHY,
        )
        assert health.connector_id == "conn-123"
        assert health.platform == "slack"
        assert health.status == HealthStatus.HEALTHY
        assert health.consecutive_failures == 0

    def test_health_to_dict(self):
        """Test ConnectorHealth serialization."""
        now = utcnow()
        health = ConnectorHealth(
            connector_id="conn-456",
            platform="github",
            status=HealthStatus.DEGRADED,
            last_success_at=now,
            consecutive_failures=2,
            total_syncs=10,
            total_failures=2,
        )
        d = health.to_dict()
        assert d["connector_id"] == "conn-456"
        assert d["status"] == "degraded"
        assert d["consecutive_failures"] == 2


class TestHealthMonitor:
    """Tests for HealthMonitor."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def monitor(self, mock_session):
        """Create HealthMonitor instance."""
        return HealthMonitor(mock_session, HealthThresholds())

    @pytest.mark.asyncio
    async def test_records_healthy_status(self, monitor, mock_session):
        """Test 1: HealthMonitor tracks healthy status for successful syncs."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        health = await monitor.record_success("conn-1", "slack")

        assert health.status == HealthStatus.HEALTHY
        assert health.consecutive_successes == 1
        assert health.last_success_at is not None

    @pytest.mark.asyncio
    async def test_transitions_to_degraded_after_failures(self, monitor, mock_session):
        """Test 2: HealthMonitor transitions to degraded after transient failures."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Record failures up to degraded threshold
        for i in range(2):
            health = await monitor.record_failure("conn-2", "github", f"Error {i}")

        assert health.status == HealthStatus.DEGRADED
        assert health.consecutive_failures == 2

    @pytest.mark.asyncio
    async def test_transitions_to_unhealthy_after_persistent_failures(self, monitor, mock_session):
        """Test 3: HealthMonitor transitions to unhealthy after persistent failures."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Record failures up to unhealthy threshold
        for i in range(5):
            health = await monitor.record_failure("conn-3", "notion", f"Error {i}")

        assert health.status == HealthStatus.UNHEALTHY
        assert health.consecutive_failures == 5

    @pytest.mark.asyncio
    async def test_emits_connector_unhealthy_event(self, monitor, mock_session):
        """Test 4: HealthMonitor emits connector_unhealthy event."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Track emitted events
        events = []
        original_emit = monitor._emit_event

        def capture_event(event):
            events.append(event)
            original_emit(event)

        monitor._emit_event = capture_event

        # Record failures to trigger unhealthy
        for i in range(5):
            await monitor.record_failure("conn-4", "discord", f"Error {i}")

        # Check that unhealthy event was emitted
        assert any(e.new_status == HealthStatus.UNHEALTHY for e in events)

    @pytest.mark.asyncio
    async def test_health_api_returns_per_connector_health(self, monitor, mock_session):
        """Test 5: Health API endpoint returns per-connector health."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Record some data
        await monitor.record_success("conn-5", "slack")
        health = await monitor.get_health("conn-5")

        assert health.connector_id == "conn-5"
        assert health.platform == "slack"

    @pytest.mark.asyncio
    async def test_system_health_aggregates_all(self, monitor, mock_session):
        """Test 6: Health API endpoint returns overall system health."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Record multiple connectors
        await monitor.record_success("conn-a", "slack")
        await monitor.record_success("conn-b", "github")
        await monitor.record_failure("conn-c", "notion", "Error")

        system_health = await monitor.get_system_health()

        assert "status" in system_health
        assert "healthy_count" in system_health
        assert "degraded_count" in system_health
        assert "unhealthy_count" in system_health

    @pytest.mark.asyncio
    async def test_recovery_to_healthy(self, monitor, mock_session):
        """Test recovery from degraded to healthy after successes."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Degrade to unhealthy
        for i in range(5):
            await monitor.record_failure("conn-6", "slack", f"Error {i}")

        health = await monitor.get_health("conn-6")
        assert health.status == HealthStatus.UNHEALTHY

        # Recover with consecutive successes
        for i in range(3):
            await monitor.record_success("conn-6", "slack")

        health = await monitor.get_health("conn-6")
        assert health.status == HealthStatus.HEALTHY
        assert health.consecutive_failures == 0


class TestHealthEvent:
    """Tests for HealthEvent."""

    def test_event_creation(self):
        """Test creating HealthEvent."""
        event = HealthEvent(
            connector_id="conn-123",
            event_type="status_change",
            old_status=HealthStatus.HEALTHY,
            new_status=HealthStatus.DEGRADED,
            details={"error": "timeout"},
        )
        assert event.connector_id == "conn-123"
        assert event.event_type == "status_change"
        assert event.old_status == HealthStatus.HEALTHY
        assert event.new_status == HealthStatus.DEGRADED
