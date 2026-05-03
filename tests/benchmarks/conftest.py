"""Benchmark fixtures and configuration."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pytest


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def benchmark_dir() -> Path:
    """Directory for benchmark output files."""
    path = Path(".planning/benchmarks")
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def rate_limiter_benchmark_dir(benchmark_dir: Path) -> Path:
    """Directory for rate limiter benchmark output."""
    path = benchmark_dir / "rate_limiter"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def sync_engine_benchmark_dir(benchmark_dir: Path) -> Path:
    """Directory for sync engine benchmark output."""
    path = benchmark_dir / "sync_engine"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def backpressure_benchmark_dir(benchmark_dir: Path) -> Path:
    """Directory for backpressure benchmark output."""
    path = benchmark_dir / "backpressure"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_benchmark_report(path: Path, report: dict[str, Any]) -> None:
    """Save benchmark report to JSON file."""
    report["date"] = utcnow().isoformat()
    report["version"] = "1.0"

    with open(path, "w") as f:
        json.dump(report, f, indent=2)


# Mock connector for sync engine benchmarks


@dataclass
class MockConnectorItem:
    """Mock connector item for benchmarking."""
    id: str
    content: str
    url: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class MockConnector:
    """Mock connector for benchmark testing."""

    def __init__(self, item_count: int = 1000):
        self._items = [
            MockConnectorItem(
                id=f"item-{i}",
                content=f"Test content {i}. " * 10,  # ~200 chars
                url=f"https://example.com/item/{i}",
                author=f"author-{i % 10}",
                created_at=utcnow(),
                updated_at=utcnow(),
                metadata={"source_platform": "external", "index": i}
            )
            for i in range(item_count)
        ]
        self._platform_name = "mock"
        self._supports_push = True

    async def get_items(self, since=None):
        """Get items from connector."""
        if since:
            return [item for item in self._items if item.updated_at and item.updated_at > since]
        return self._items

    async def push_items(self, items):
        """Push items to connector."""
        return len(items)

    @property
    def platform_name(self):
        return self._platform_name

    @property
    def supports_push(self):
        return self._supports_push


class MockWriteQueue:
    """Mock write queue for backpressure testing."""

    def __init__(self, initial_depth: int = 0):
        self._depth = initial_depth
        self._pending = []

    def get_pending(self):
        return self._pending

    def fill_to(self, depth: int):
        """Fill queue to specified depth."""
        self._pending = [f"item-{i}" for i in range(depth)]
        self._depth = depth

    def drain_to(self, depth: int):
        """Drain queue to specified depth."""
        self._pending = self._pending[:depth]
        self._depth = depth

    def enqueue(self, items):
        """Enqueue items."""
        self._pending.extend(items)
        self._depth = len(self._pending)
