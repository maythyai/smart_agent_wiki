"""Real-DB regression tests for the govern stubs fixed in DEF-8.

These verify the previously-placeholder methods actually mutate/query the DB
rather than silently returning empty/True:
- ``FreshnessTracker.get_freshness_distribution`` / ``get_stale_claims`` /
  ``refresh_on_access``
- ``ConfidenceAssessor.upgrade_confidence`` / ``get_confidence_distribution``
- ``ContradictionDetector.apply_resolution``
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.db.migrations import apply_migrations
from saw.domain.claims import Claim
from saw.domain.value_objects import (
    ConfidenceLevel,
    ContradictionType,
    FreshnessLevel,
    ResolutionStrategy,
)
from saw.engines.govern.confidence import ConfidenceAssessor
from saw.engines.govern.contradiction import ContradictionDetector, ContradictionRecord
from saw.engines.govern.freshness import FreshnessTracker
from saw.write_queue.sinks.contradictions_sink import store_contradiction


def _fresh_repo(tmp_path) -> tuple[sqlite3.Connection, SQLiteClaimsRepository]:
    conn = sqlite3.connect(str(tmp_path / "govern.db"))
    apply_migrations(conn)  # ensures claim.last_accessed (migration v3) exists
    return conn, SQLiteClaimsRepository(conn)


def _claim(uuid, content, source_uuid="s", hash_="h",
           confidence=ConfidenceLevel.SINGLE_SOURCE, age_days=0) -> Claim:
    created = datetime.now(timezone.utc) - timedelta(days=age_days)
    return Claim(
        uuid=uuid,
        content=content,
        source_uuid=source_uuid,
        content_hash=hash_,
        confidence=confidence,
        created_at=created,
    )


# ── FreshnessTracker ────────────────────────────────────────────────

def test_freshness_distribution_counts_claims(tmp_path) -> None:
    conn, repo = _fresh_repo(tmp_path)
    repo.insert(_claim("c-old", "x", hash_="h1", age_days=200))
    repo.insert(_claim("c-new", "y", hash_="h2", age_days=0))
    dist = FreshnessTracker().get_freshness_distribution(repo)
    assert sum(dist.values()) == 2
    assert dist[FreshnessLevel.LEVEL_8] == 1  # 200-day claim is stale/red


def test_get_stale_claims_returns_only_stale(tmp_path) -> None:
    conn, repo = _fresh_repo(tmp_path)
    repo.insert(_claim("c-old", "x", hash_="h1", age_days=200))
    repo.insert(_claim("c-new", "y", hash_="h2", age_days=0))
    stale = FreshnessTracker().get_stale_claims(repo)
    assert "c-old" in stale
    assert "c-new" not in stale


def test_refresh_on_access_persists_last_accessed(tmp_path) -> None:
    conn, repo = _fresh_repo(tmp_path)
    repo.insert(_claim("c1", "x", hash_="h1"))
    FreshnessTracker().refresh_on_access("c1", repo)
    la = conn.execute(
        "SELECT last_accessed FROM claim WHERE uuid='c1'"
    ).fetchone()[0]
    assert la is not None  # previously a no-op


# ── ConfidenceAssessor ──────────────────────────────────────────────

def test_upgrade_confidence_persists(tmp_path) -> None:
    conn, repo = _fresh_repo(tmp_path)
    repo.insert(_claim("c1", "x", hash_="h1", confidence=ConfidenceLevel.UNVERIFIED))
    ok = ConfidenceAssessor().upgrade_confidence(
        "c1", ConfidenceLevel.SINGLE_SOURCE, repo
    )
    assert ok is True
    row = conn.execute("SELECT confidence FROM claim WHERE uuid='c1'").fetchone()
    assert row[0] == "single_source"  # previously returned True with no DB change


def test_upgrade_confidence_refuses_downgrade(tmp_path) -> None:
    conn, repo = _fresh_repo(tmp_path)
    repo.insert(_claim("c1", "x", hash_="h1", confidence=ConfidenceLevel.SINGLE_SOURCE))
    ok = ConfidenceAssessor().upgrade_confidence(
        "c1", ConfidenceLevel.UNVERIFIED, repo
    )
    assert ok is False  # D-03 never auto-downgrade
    row = conn.execute("SELECT confidence FROM claim WHERE uuid='c1'").fetchone()
    assert row[0] == "single_source"


def test_confidence_distribution_counts(tmp_path) -> None:
    conn, repo = _fresh_repo(tmp_path)
    repo.insert(_claim("c1", "x", hash_="h1", confidence=ConfidenceLevel.UNVERIFIED))
    repo.insert(_claim("c2", "y", hash_="h2", confidence=ConfidenceLevel.UNVERIFIED))
    repo.insert(_claim("c3", "z", hash_="h3", confidence=ConfidenceLevel.SINGLE_SOURCE))
    dist = ConfidenceAssessor().get_confidence_distribution(repo)
    assert dist[ConfidenceLevel.UNVERIFIED] == 2
    assert dist[ConfidenceLevel.SINGLE_SOURCE] == 1


# ── ContradictionDetector.apply_resolution ──────────────────────────

def test_apply_resolution_marks_resolved(tmp_path) -> None:
    conn, repo = _fresh_repo(tmp_path)
    repo.insert(_claim("a1", "x", source_uuid="s1", hash_="h1"))
    repo.insert(_claim("b1", "y", source_uuid="s2", hash_="h2"))
    detector = ContradictionDetector.__new__(ContradictionDetector)
    detector._claims_repo = repo
    detector._llm_router = MagicMock()
    record = ContradictionRecord(
        uuid="con-1",
        claim_a_uuid="a1",
        claim_b_uuid="b1",
        contradiction_type=ContradictionType.FACTUAL,
        resolution=ResolutionStrategy.HISTORICAL,
        detected_at=datetime.now(timezone.utc),
        resolved_at=None,
    )
    store_contradiction(conn, record)
    detector.apply_resolution(record)
    row = conn.execute(
        "SELECT resolved_at FROM contradictions WHERE uuid='con-1'"
    ).fetchone()
    assert row[0] is not None  # previously a `pass` no-op
    assert record.resolved_at is not None
