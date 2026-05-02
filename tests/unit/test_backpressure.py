"""Tests for backpressure manager.

Plan 11-02, Task 1: BackpressureManager.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.backpressure import (
    BackpressureConfig,
    BackpressureState,
    BackpressureStats,
    BackpressureManager,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestBackpressureConfig:
    """Tests for BackpressureConfig."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = BackpressureConfig()
        assert config.pause_threshold == 1000
        assert config.resume_threshold == 500
        assert config.check_interval_seconds == 1.0
        assert config.max_pause_duration_seconds == 300.0

    def test_config_custom(self):
        """Test custom configuration values."""
        config = BackpressureConfig(
            pause_threshold=500,
            resume_threshold=200,
            check_interval_seconds=0.5,
            max_pause_duration_seconds=60.0,
        )
        assert config.pause_threshold == 500
        assert config.resume_threshold == 200


class TestBackpressureState:
    """Tests for BackpressureState enum."""

    def test_state_has_active(self):
        """Test BackpressureState has ACTIVE."""
        assert BackpressureState.ACTIVE.value == "active"

    def test_state_has_paused(self):
        """Test BackpressureState has PAUSED."""
        assert BackpressureState.PAUSED.value == "paused"

    def test_state_has_throttled(self):
        """Test BackpressureState has THROTTLED."""
        assert BackpressureState.THROTTLED.value == "throttled"


class TestBackpressureStats:
    """Tests for BackpressureStats."""

    def test_stats_creation(self):
        """Test creating BackpressureStats."""
        stats = BackpressureStats(
            state=BackpressureState.ACTIVE,
            current_depth=100,
        )
        assert stats.state == BackpressureState.ACTIVE
        assert stats.current_depth == 100
        assert stats.total_pause_events == 0

    def test_stats_to_dict(self):
        """Test BackpressureStats serialization."""
        now = utcnow()
        stats = BackpressureStats(
            state=BackpressureState.PAUSED,
            current_depth=1200,
            paused_at=now,
            total_pause_events=5,
            total_pause_duration_seconds=30.5,
        )
        d = stats.to_dict()
        assert d["state"] == "paused"
        assert d["current_depth"] == 1200
        assert d["total_pause_events"] == 5


class TestBackpressureManager:
    """Tests for BackpressureManager."""

    @pytest.fixture
    def mock_write_queue(self):
        """Create mock write queue."""
        queue = MagicMock()
        queue.get_pending = MagicMock(return_value=[])
        return queue

    @pytest.fixture
    def manager(self, mock_write_queue):
        """Create BackpressureManager instance."""
        return BackpressureManager(mock_write_queue, BackpressureConfig())

    @pytest.mark.asyncio
    async def test_is_paused_returns_false_below_threshold(self, manager, mock_write_queue):
        """Test 1: BackpressureManager.is_paused() returns False when depth < 1000."""
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 500)
        is_paused = await manager.is_paused()
        assert is_paused is False

    @pytest.mark.asyncio
    async def test_is_paused_returns_true_at_threshold(self, manager, mock_write_queue):
        """Test 2: BackpressureManager.is_paused() returns True when depth >= 1000."""
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 1000)
        is_paused = await manager.is_paused()
        assert is_paused is True

    @pytest.mark.asyncio
    async def test_transitions_from_paused_to_resumed(self, manager, mock_write_queue):
        """Test 3: BackpressureManager transitions from paused to resumed when depth < 500."""
        # First, trigger pause
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 1000)
        await manager.check()
        assert manager._state == BackpressureState.PAUSED

        # Then drop below resume threshold
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 400)
        await manager.check()
        assert manager._state == BackpressureState.ACTIVE

    @pytest.mark.asyncio
    async def test_records_pause_events(self, manager, mock_write_queue):
        """Test 4: BackpressureManager records pause/resume events."""
        # Trigger pause
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 1000)
        await manager.check()
        assert manager._total_pause_events == 1
        assert manager._paused_at is not None

        # Resume
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 400)
        await manager.check()
        assert manager._total_pause_duration > 0

    def test_get_stats_returns_state_and_thresholds(self, manager, mock_write_queue):
        """Test 5: BackpressureManager.get_stats() returns current state and thresholds."""
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 200)
        stats = manager.get_stats()

        assert stats.state == BackpressureState.ACTIVE
        assert stats.current_depth == 200
        assert stats.pause_threshold == 1000
        assert stats.resume_threshold == 500

    @pytest.mark.asyncio
    async def test_force_resume(self, manager, mock_write_queue):
        """Test force_resume allows admin override."""
        # Trigger pause
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 1500)
        await manager.check()
        assert manager._state == BackpressureState.PAUSED

        # Force resume without dropping queue
        await manager.force_resume()
        assert manager._state == BackpressureState.ACTIVE

    @pytest.mark.asyncio
    async def test_hysteresis_prevents_oscillation(self, manager, mock_write_queue):
        """Test hysteresis prevents rapid state changes."""
        # Pause at 1000
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 1000)
        await manager.check()
        assert manager._state == BackpressureState.PAUSED

        # Depth drops to 600 (between thresholds) - should stay paused
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 600)
        await manager.check()
        assert manager._state == BackpressureState.PAUSED

        # Only resume when below 500
        mock_write_queue.get_pending = MagicMock(return_value=[MagicMock()] * 400)
        await manager.check()
        assert manager._state == BackpressureState.ACTIVE