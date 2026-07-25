"""Rate limiting middleware for API protection.

Phase 6: API Platform — Rate limiting.
Per APIP-03: Rate limiting per API key.

Uses Redis sliding window algorithm.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    default_hour_limit: int = 100
    default_day_limit: int = 1000
    redis_url: str = "redis://localhost:6379/0"
    enabled: bool = True

    @classmethod
    def from_env(cls) -> RateLimitConfig:
        return cls(
            default_hour_limit=int(os.environ.get("RATE_LIMIT_HOUR", "100")),
            default_day_limit=int(os.environ.get("RATE_LIMIT_DAY", "1000")),
            redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            enabled=os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true",
        )


@dataclass
class RateLimitStatus:
    """Current rate limit status."""
    hour_count: int
    hour_limit: int
    hour_remaining: int
    hour_reset: int
    day_count: int
    day_limit: int
    day_remaining: int
    day_reset: int

    def to_headers(self) -> dict:
        """Convert to response headers."""
        return {
            "X-RateLimit-Limit-Hour": str(self.hour_limit),
            "X-RateLimit-Remaining-Hour": str(self.hour_remaining),
            "X-RateLimit-Limit-Day": str(self.day_limit),
            "X-RateLimit-Remaining-Day": str(self.day_remaining),
            "X-RateLimit-Reset-Hour": str(self.hour_reset),
            "X-RateLimit-Reset-Day": str(self.day_reset),
        }


class RedisRateLimiter:
    """Redis-based rate limiter using sliding window."""

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig.from_env()
        self._redis = None
        # In-memory fallback counters for when Redis is unavailable
        # (local/single-node deployments). Keyed by key_id.
        self._memory_counters: dict[str, dict] = {}

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self.config.redis_url)
            except ImportError:
                self._redis = None
        return self._redis

    def _get_hour_timestamp(self) -> int:
        """Get current hour timestamp (for Redis key)."""
        now = time.time()
        return int(now // 3600) * 3600

    def _get_day_timestamp(self) -> int:
        """Get current day timestamp (for Redis key)."""
        now = time.time()
        return int(now // 86400) * 86400

    def _check_rate_limit_memory(
        self, key_id: str, hour_limit: int, day_limit: int
    ) -> RateLimitStatus:
        """In-memory fixed-window rate limiting (Redis fallback).

        Suitable for local/single-node deployments where Redis is unavailable.
        Counters reset when the hour/day window rolls over.
        """
        now = int(time.time())
        hour_ts = self._get_hour_timestamp()
        day_ts = self._get_day_timestamp()

        entry = self._memory_counters.get(key_id)
        if entry is None:
            entry = {"hour_ts": hour_ts, "day_ts": day_ts, "hour": 0, "day": 0}
            self._memory_counters[key_id] = entry

        # Reset counters when the window rolls over
        if entry["hour_ts"] != hour_ts:
            entry["hour_ts"] = hour_ts
            entry["hour"] = 0
        if entry["day_ts"] != day_ts:
            entry["day_ts"] = day_ts
            entry["day"] = 0

        entry["hour"] += 1
        entry["day"] += 1

        return RateLimitStatus(
            hour_count=entry["hour"],
            hour_limit=hour_limit,
            hour_remaining=max(0, hour_limit - entry["hour"]),
            hour_reset=hour_ts + 3600,
            day_count=entry["day"],
            day_limit=day_limit,
            day_remaining=max(0, day_limit - entry["day"]),
            day_reset=day_ts + 86400,
        )

    def check_rate_limit(
        self,
        key_id: str,
        hour_limit: int | None = None,
        day_limit: int | None = None,
    ) -> RateLimitStatus:
        """Check rate limit and increment counters.

        Returns current status after incrementing.
        """
        hour_limit = hour_limit or self.config.default_hour_limit
        day_limit = day_limit or self.config.default_day_limit

        redis_client = self._get_redis()

        if redis_client is None:
            # Redis not available — fall back to in-memory counters so
            # local/single-node deployments work without a Redis server.
            return self._check_rate_limit_memory(key_id, hour_limit, day_limit)

        # Get timestamps
        hour_ts = self._get_hour_timestamp()
        day_ts = self._get_day_timestamp()

        # Redis keys
        hour_key = f"ratelimit:{key_id}:hour:{hour_ts}"
        day_key = f"ratelimit:{key_id}:day:{day_ts}"

        # Increment counters
        hour_count = redis_client.incr(hour_key)
        day_count = redis_client.incr(day_key)

        # Set expiry on first use
        if hour_count == 1:
            redis_client.expire(hour_key, 3600)
        if day_count == 1:
            redis_client.expire(day_key, 86400)

        return RateLimitStatus(
            hour_count=hour_count,
            hour_limit=hour_limit,
            hour_remaining=max(0, hour_limit - hour_count),
            hour_reset=hour_ts + 3600,
            day_count=day_count,
            day_limit=day_limit,
            day_remaining=max(0, day_limit - day_count),
            day_reset=day_ts + 86400,
        )

    def is_rate_limited(self, status: RateLimitStatus) -> bool:
        """Check if rate limit is exceeded."""
        return status.hour_count > status.hour_limit or status.day_count > status.day_limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        config: RateLimitConfig | None = None,
        get_api_key_func: Callable | None = None,
    ):
        super().__init__(app)
        self.config = config or RateLimitConfig.from_env()
        self.limiter = RedisRateLimiter(self.config)
        self.get_api_key_func = get_api_key_func

        # Paths to skip rate limiting
        self.skip_paths = {
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Skip if disabled
        if not self.config.enabled:
            return await call_next(request)

        # Get API key info
        api_key_id = None
        hour_limit = self.config.default_hour_limit
        day_limit = self.config.default_day_limit

        # Try to extract API key from request
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("ApiKey "):
            # Extract key and verify
            key_str = auth_header[7:].strip()
            if self.get_api_key_func:
                api_key = await self.get_api_key_func(key_str)
                if api_key:
                    api_key_id = api_key.id
                    hour_limit = api_key.rate_limit_hour
                    day_limit = api_key.rate_limit_day

        # Use IP-based rate limiting if no API key
        if not api_key_id:
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.headers.get(
                    "X-Real-IP",
                    request.client.host if request.client else "unknown",
                )
            api_key_id = f"ip:{client_ip}"

        # Check rate limit
        status = self.limiter.check_rate_limit(
            api_key_id,
            hour_limit,
            day_limit,
        )

        # Rate limited?
        if self.limiter.is_rate_limited(status):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": min(
                        status.hour_reset - int(time.time()),
                        status.day_reset - int(time.time())
                    ),
                },
                headers=status.to_headers(),
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        for key, value in status.to_headers().items():
            response.headers[key] = value

        return response


def create_rate_limit_middleware(
    app,
    config: RateLimitConfig | None = None,
    get_api_key_func: Callable | None = None,
):
    """Create and configure rate limit middleware."""
    return RateLimitMiddleware(app, config, get_api_key_func)
