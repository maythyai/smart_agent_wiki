"""Rate limiting for third-party platform API calls.

Plan 10-01: Per-platform rate limits with token bucket algorithm.
Plan 10-03: Webhook rate limiting.
Per IM-06: Per-platform rate limits.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass


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


# Plan 10-03: Webhook Rate Limiting


@dataclass
class WebhookRateLimit:
    """Rate limit configuration for inbound webhooks.

    Per IM-06: System respects per-platform rate limits.
    """
    requests_per_minute: int = 100
    burst: int = 50

    @classmethod
    def slack(cls) -> "WebhookRateLimit":
        """Slack webhook limits: 100 requests per minute."""
        return cls(requests_per_minute=100, burst=50)

    @classmethod
    def github(cls) -> "WebhookRateLimit":
        """GitHub webhook limits: 60 requests per minute."""
        return cls(requests_per_minute=60, burst=30)

    @classmethod
    def discord(cls) -> "WebhookRateLimit":
        """Discord webhook limits: 100 requests per minute."""
        return cls(requests_per_minute=100, burst=50)

    @classmethod
    def feishu(cls) -> "WebhookRateLimit":
        """Feishu webhook limits: 60 requests per minute."""
        return cls(requests_per_minute=60, burst=30)


class WebhookRateLimiter:
    """Rate limiter for inbound webhooks.

    Per IM-06: System respects per-platform rate limits.
    """

    WEBHOOK_LIMITS: dict[str, WebhookRateLimit] = {
        "slack": WebhookRateLimit.slack(),
        "github": WebhookRateLimit.github(),
        "discord": WebhookRateLimit.discord(),
        "feishu": WebhookRateLimit.feishu(),
    }

    def __init__(self, platform: str, connector_id: str | None = None):
        """Initialize webhook rate limiter.

        Args:
            platform: Platform identifier.
            connector_id: Optional connector ID for per-connector limiting.
        """
        self._platform = platform
        self._connector_id = connector_id
        self._limits = self.WEBHOOK_LIMITS.get(platform, WebhookRateLimit())
        self._requests: dict[str, list[float]] = {}  # connector_id -> timestamps
        self._lock = asyncio.Lock()

    async def acquire(self) -> tuple[bool, dict]:
        """Check if webhook is allowed under rate limit.

        Returns:
            Tuple of (allowed, headers_dict).
            headers_dict contains X-RateLimit-* headers.
        """
        async with self._lock:
            try:
                loop = asyncio.get_running_loop()
                now = loop.time()
            except RuntimeError:
                import time
                now = time.time()

            key = self._connector_id or "default"

            # Initialize if needed
            if key not in self._requests:
                self._requests[key] = []

            # Clean old requests (older than 1 minute)
            self._requests[key] = [
                ts for ts in self._requests[key]
                if now - ts < 60
            ]

            # Check rate limit
            current_count = len(self._requests[key])
            allowed = current_count < self._limits.requests_per_minute

            # Calculate headers
            remaining = max(0, self._limits.requests_per_minute - current_count)
            reset_in = 60  # seconds until reset

            headers = {
                "X-RateLimit-Limit": str(self._limits.requests_per_minute),
                "X-RateLimit-Remaining": str(remaining - 1 if allowed else 0),
                "X-RateLimit-Reset": str(int(now + reset_in)),
            }

            if allowed:
                self._requests[key].append(now)

            return allowed, headers

    def reset(self, connector_id: str | None = None) -> None:
        """Reset rate limit for connector (for testing).

        Args:
            connector_id: Optional specific connector to reset.
        """
        key = connector_id or self._connector_id or "default"
        if key in self._requests:
            del self._requests[key]
