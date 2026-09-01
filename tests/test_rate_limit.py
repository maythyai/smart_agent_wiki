"""T-F-C-3-1: rate-limit dual-track (api-key + anonymous IP) regression tests.

Verifies AC-SEC-3: exceeding the hourly limit returns 429 + Retry-After,
and that env overrides (RATE_LIMIT_HOUR/DAY/ENABLED) take effect.
Ground: src/saw/api/rate_limit.py (memory fallback when Redis absent).
"""
from __future__ import annotations

import importlib
import os

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from saw.api.rate_limit import (
    RateLimitConfig,
    RateLimitMiddleware,
    RedisRateLimiter,
)


# --- config / env override ---

def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_HOUR", "7")
    monkeypatch.setenv("RATE_LIMIT_DAY", "99")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    cfg = RateLimitConfig.from_env()
    assert cfg.default_hour_limit == 7
    assert cfg.default_day_limit == 99
    assert cfg.enabled is False


def test_defaults() -> None:
    cfg = RateLimitConfig()
    assert cfg.default_hour_limit == 100
    assert cfg.default_day_limit == 1000
    assert cfg.enabled is True


# --- limiter memory mode (no Redis) ---

def _memory_limiter(hour_limit: int = 2) -> RedisRateLimiter:
    cfg = RateLimitConfig(default_hour_limit=hour_limit, default_day_limit=1000)
    lim = RedisRateLimiter(cfg)
    lim._redis = None  # force memory fallback
    return lim


def test_limiter_allows_under_limit() -> None:
    lim = _memory_limiter(hour_limit=3)
    for _ in range(3):
        st = lim.check_rate_limit("ip:test")
        assert not lim.is_rate_limited(st)


def test_limiter_blocks_over_limit() -> None:
    lim = _memory_limiter(hour_limit=2)
    lim.check_rate_limit("ip:t")
    lim.check_rate_limit("ip:t")
    over = lim.check_rate_limit("ip:t")
    assert lim.is_rate_limited(over)
    assert over.hour_count == 3
    assert over.hour_remaining == 0


# --- middleware 429 + Retry-After (AC-SEC-3) ---

def _app(hour_limit: int = 2) -> FastAPI:
    app = FastAPI()

    @app.get("/api/test")
    def _read() -> dict:  # noqa: D401
        return {"ok": True}

    cfg = RateLimitConfig(default_hour_limit=hour_limit, default_day_limit=1000)
    app.add_middleware(RateLimitMiddleware, config=cfg)
    return app


def test_middleware_returns_429_with_retry_after() -> None:
    app = _app(hour_limit=2)
    client = TestClient(app)
    r1 = client.get("/api/test")
    r2 = client.get("/api/test")
    r3 = client.get("/api/test")  # 3rd exceeds
    assert r1.status_code == 200 and r2.status_code == 200
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers
    assert int(r3.headers["Retry-After"]) >= 1
    assert "X-RateLimit-Limit-Hour" in r3.headers


def test_middleware_skips_health_paths() -> None:
    app = _app(hour_limit=1)

    @app.get("/health")
    def _h() -> dict:
        return {"ok": True}

    client = TestClient(app)
    # health is in skip_paths → never rate limited even with limit=1
    for _ in range(5):
        r = client.get("/health")
        assert r.status_code == 200
