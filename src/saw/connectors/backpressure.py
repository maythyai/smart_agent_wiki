"""Backpressure management for Write Queue integration.

Plan 11-02: Backpressure, retry, and health status.
Per SYNC-05: Backpressure handling via Write Queue with pause/resume thresholds.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from saw.domain.utils import utcnow  # noqa: F401


class BackpressureConfig:
    """Configuration for backpressure handling.

    Attributes:
        pause_threshold: Queue depth to pause sync_pull.
        resume_threshold: Queue depth to resume (hysteresis).
        check_interval_seconds: Interval between backpressure checks.
        max_pause_duration_seconds: Maximum time to remain paused.
    """

    def __init__(
        self,
        pause_threshold: int = 1000,
        resume_threshold: int = 500,
        check_interval_seconds: float = 1.0,
        max_pause_duration_seconds: float = 300.0,
    ) -> None:
        self.pause_threshold = pause_threshold
        self.resume_threshold = resume_threshold
        self.check_interval_seconds = check_interval_seconds
        self.max_pause_duration_seconds = max_pause_duration_seconds


class BackpressureState(enum.Enum):
    """State of backpressure management."""
    ACTIVE = "active"  # Sync pulling normally
    PAUSED = "paused"  # Sync_pull paused, queue full
    THROTTLED = "throttled"  # Reduced pull rate


@dataclass
class BackpressureStats:
    """Statistics for backpressure state.

    Attributes:
        state: Current backpressure state.
        current_depth: Current queue depth.
        pause_threshold: Threshold to pause.
        resume_threshold: Threshold to resume.
        paused_at: When pause started.
        total_pause_events: Total number of pause events.
        total_pause_duration_seconds: Total time spent paused.
    """

    state: BackpressureState = BackpressureState.ACTIVE
    current_depth: int = 0
    pause_threshold: int = 1000
    resume_threshold: int = 500
    paused_at: Optional[datetime] = None
    total_pause_events: int = 0
    total_pause_duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "state": self.state.value,
            "current_depth": self.current_depth,
            "pause_threshold": self.pause_threshold,
            "resume_threshold": self.resume_threshold,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "total_pause_events": self.total_pause_events,
            "total_pause_duration_seconds": self.total_pause_duration_seconds,
        }


class BackpressureManager:
    """Manages backpressure for Write Queue integration.

    Per SYNC-05: Backpressure handling via Write Queue with pause/resume thresholds.

    Uses hysteresis to prevent oscillation:
    - Pause when depth >= pause_threshold
    - Resume when depth < resume_threshold
    """

    def __init__(
        self,
        write_queue: Any,  # WriteQueue type hint avoided
        config: Optional[BackpressureConfig] = None,
    ) -> None:
        """Initialize backpressure manager.

        Args:
            write_queue: Write queue to monitor.
            config: Backpressure configuration.
        """
        self._write_queue = write_queue
        self._config = config or BackpressureConfig()

        # State tracking
        self._state: BackpressureState = BackpressureState.ACTIVE
        self._paused_at: Optional[datetime] = None
        self._total_pause_events: int = 0
        self._total_pause_duration: float = 0.0
        self._last_pause_duration: float = 0.0

    async def check(self) -> BackpressureState:
        """Check current backpressure state.

        Updates state based on queue depth with hysteresis.

        Returns:
            Current BackpressureState.
        """
        depth = await self._get_queue_depth()

        # Hysteresis logic
        if self._state == BackpressureState.PAUSED:
            # Check if we can resume
            if depth < self._config.resume_threshold:
                await self._record_resume()
                self._state = BackpressureState.ACTIVE
            # Check for max pause duration
            elif self._paused_at:
                pause_duration = (utcnow() - self._paused_at).total_seconds()
                if pause_duration >= self._config.max_pause_duration_seconds:
                    await self._record_resume()
                    self._state = BackpressureState.ACTIVE
        else:
            # Check if we need to pause
            if depth >= self._config.pause_threshold:
                await self._record_pause()
                self._state = BackpressureState.PAUSED

        return self._state

    async def is_paused(self) -> bool:
        """Check if sync should be paused.

        Returns:
            True if paused, False otherwise.
        """
        state = await self.check()
        return state == BackpressureState.PAUSED

    async def wait_if_paused(
        self,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until resumed or timeout.

        Async wait until queue depth drops below resume threshold.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if resumed, False if timeout.
        """
        import asyncio

        start_time = utcnow()
        check_interval = self._config.check_interval_seconds

        while await self.is_paused():
            # Check timeout
            if timeout:
                elapsed = (utcnow() - start_time).total_seconds()
                if elapsed >= timeout:
                    return False

            # Wait before next check
            await asyncio.sleep(check_interval)

        return True

    def get_stats(self) -> BackpressureStats:
        """Get current backpressure statistics.

        Returns:
            BackpressureStats dataclass.
        """
        return BackpressureStats(
            state=self._state,
            current_depth=self._get_depth_sync(),
            pause_threshold=self._config.pause_threshold,
            resume_threshold=self._config.resume_threshold,
            paused_at=self._paused_at,
            total_pause_events=self._total_pause_events,
            total_pause_duration_seconds=self._total_pause_duration,
        )

    async def force_resume(self) -> None:
        """Force resume (admin override).

        Ignores queue depth and resumes sync.
        """
        if self._state == BackpressureState.PAUSED:
            await self._record_resume()
            self._state = BackpressureState.ACTIVE

    async def _get_queue_depth(self) -> int:
        """Get current queue depth.

        Returns:
            Number of pending items in queue.
        """
        if self._write_queue:
            pending = self._write_queue.get_pending()
            return len(pending) if pending else 0
        return 0

    def _get_depth_sync(self) -> int:
        """Get queue depth synchronously (for stats).

        Returns:
            Number of pending items in queue.
        """
        if self._write_queue:
            pending = self._write_queue.get_pending()
            return len(pending) if pending else 0
        return 0

    async def _record_pause(self) -> None:
        """Record a pause event."""
        self._paused_at = utcnow()
        self._total_pause_events += 1

    async def _record_resume(self) -> None:
        """Record a resume event."""
        if self._paused_at:
            duration = (utcnow() - self._paused_at).total_seconds()
            self._last_pause_duration = duration
            self._total_pause_duration += duration
            self._paused_at = None