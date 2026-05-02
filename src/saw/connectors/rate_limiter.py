"""Rate limiting for third-party platform API calls.

Plan 10-01: Per-platform rate limits with token bucket algorithm.
Per IM-06: Per-platform rate limits.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlatformRateLimit:
    """Rate limit configuration for a platform.

    Per IM-06: Per-platform rate limits.
    """
    requests_per_second: float | None = None
    requests_per_minute: int | None = None
    requests_per_hour: int | None = None
    burst: int = 10  # Allow temporary spikes

    @classmethod
    def notion(cls) -> "PlatformRateLimit":
        """Notion API limits: 3 requests per second."""
        return cls(requests_per_second=3, burst=10)

    @classmethod
    def github(cls) -> "PlatformRateLimit":
        """GitHub API limits: 5000 requests per hour (authenticated)."""
        return cls(requests_per_hour=5000, burst=100)

    @classmethod
    def slack(cls) -> "PlatformRateLimit":
        """Slack API limits: ~60 requests per minute (tier 2)."""
        return cls(requests_per_minute=60, burst=20)

    @classmethod
    def discord(cls) -> "PlatformRateLimit":
        """Discord API limits: 50 requests per second (global)."""
        return cls(requests_per_second=50, burst=50)


class RateLimitManager:
    """Per-platform rate limit tracking with token bucket algorithm.

    Per IM-06: Per-platform rate limits.

    Token bucket algorithm:
    - Tokens replenish at the rate limit rate
    - Each request consumes 1 token
    - If no tokens available, wait for replenishment
    - Burst capacity allows temporary spikes
    """

    PLATFORM_LIMITS: dict[str, PlatformRateLimit] = {
        "notion": PlatformRateLimit.notion(),
        "github": PlatformRateLimit.github(),
        "slack": PlatformRateLimit.slack(),
        "discord": PlatformRateLimit.discord(),
    }

    def __init__(self, platform: str):
        """Initialize rate limiter for a platform.

        Args:
            platform: Platform identifier (notion, github, slack, discord).
        """
        self._platform = platform
        self._limits = self.PLATFORM_LIMITS.get(platform, PlatformRateLimit())
        self._tokens = float(self._limits.burst)
        self._last_update: float | None = None
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until rate limit allows next request.

        Uses token bucket algorithm:
        - Tokens replenish at rate limit rate
        - Each request consumes 1 token
        - If no tokens, wait for replenishment
        """
        async with self._lock:
            try:
                loop = asyncio.get_running_loop()
                now = loop.time()
            except RuntimeError:
                # No running loop, use time.time as fallback
                import time
                now = time.time()

            if self._last_update is not None:
                elapsed = now - self._last_update

                # Replenish tokens based on elapsed time
                if self._limits.requests_per_second is not None:
                    self._tokens += elapsed * self._limits.requests_per_second
                elif self._limits.requests_per_minute is not None:
                    self._tokens += elapsed * (self._limits.requests_per_minute / 60.0)
                elif self._limits.requests_per_hour is not None:
                    self._tokens += elapsed * (self._limits.requests_per_hour / 3600.0)

            # Cap at burst
            self._tokens = min(self._tokens, float(self._limits.burst))
            self._last_update = now

            # If no tokens, wait
            if self._tokens < 1.0:
                wait_time = self._calculate_wait_time()
                await asyncio.sleep(wait_time)
                self._tokens = 0.0
                try:
                    loop = asyncio.get_running_loop()
                    self._last_update = loop.time()
                except RuntimeError:
                    import time
                    self._last_update = time.time()
            else:
                self._tokens -= 1.0

    def _calculate_wait_time(self) -> float:
        """Calculate time to wait for next token."""
        if self._limits.requests_per_second is not None:
            return 1.0 / self._limits.requests_per_second
        elif self._limits.requests_per_minute is not None:
            return 60.0 / self._limits.requests_per_minute
        elif self._limits.requests_per_hour is not None:
            return 3600.0 / self._limits.requests_per_hour
        return 0.0
