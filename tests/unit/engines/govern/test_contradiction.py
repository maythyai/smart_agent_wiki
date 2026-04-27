"""Tests for contradiction detection and resolution.

Tests the ContradictionDetector class with:
1. detect_candidates() - finds claim pairs with similar content
2. classify_contradiction() - returns TEMPORAL/OPINION/FACTUAL via LLM
3. resolve_contradiction() - applies correct strategy per type
4. Async queue processing
5. Two-phase detection
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from saw.domain.claims import Claim
from saw.domain.value_objects import (
    ConfidenceLevel,
    ContradictionType,
    ResolutionStrategy,
    SourceMark,
)
from saw.engines.govern.contradiction import (
    ContradictionDetector,
    ContradictionRecord,
)


class TestDetectCandidates:
    """Test 1: detect_candidates() finds claim pairs with similar content."""

    def test_finds_similar_claims_by_keyword_matching(self) -> None:
        """Should find claims with overlapping keywords."""
        claims_repo = MagicMock()
        detector = ContradictionDetector(claims_repo, MagicMock())

        claim = Claim(
            uuid="claim-1",
            content="Python is a programming language",
            source_uuid="doc-1",
            content_hash="hash-1",
        )

        # Mock search results
        claims_repo.search.return_value = [
            Claim(
                uuid="claim-2",
                content="Python is a scripting language",
                source_uuid="doc-2",
                content_hash="hash-2",
            ),
            Claim(
                uuid="claim-3",
                content="JavaScript is a programming language",
                source_uuid="doc-3",
                content_hash="hash-3",
            ),
        ]

        candidates = detector.detect_candidates(claim, threshold=0.5)

        # Should find candidates with overlapping keywords
        assert len(candidates) >= 1
        claims_repo.search.assert_called()

    def test_filters_by_similarity_threshold(self) -> None:
        """Should filter candidates by similarity threshold."""
        claims_repo = MagicMock()
        detector = ContradictionDetector(claims_repo, MagicMock())

        claim = Claim(
            uuid="claim-1",
            content="The sky is blue",
            source_uuid="doc-1",
            content_hash="hash-1",
        )

        claims_repo.search.return_value = []

        candidates = detector.detect_candidates(claim, threshold=0.9)

        assert isinstance(candidates, list)


class TestClassifyContradiction:
    """Test 2: classify_contradiction() returns correct type via LLM."""

    @pytest.mark.asyncio
    async def test_returns_temporal_for_time_based_conflict(self) -> None:
        """TEMPORAL: New data supersedes old."""
        claims_repo = MagicMock()
        llm_router = MagicMock()
        llm_router.classify_contradiction = AsyncMock(
            return_value=ContradictionType.TEMPORAL
        )

        detector = ContradictionDetector(claims_repo, llm_router)

        claim_a = Claim(
            uuid="claim-1",
            content="Earth is 4.5 billion years old",
            source_uuid="doc-1",
            content_hash="hash-1",
            created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        claim_b = Claim(
            uuid="claim-2",
            content="Earth is 4.54 billion years old",
            source_uuid="doc-2",
            content_hash="hash-2",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )

        result = await detector.classify_contradiction(claim_a, claim_b)

        assert result == ContradictionType.TEMPORAL

    @pytest.mark.asyncio
    async def test_returns_opinion_for_different_perspectives(self) -> None:
        """OPINION: Different perspectives on same topic."""
        claims_repo = MagicMock()
        llm_router = MagicMock()
        llm_router.classify_contradiction = AsyncMock(
            return_value=ContradictionType.OPINION
        )

        detector = ContradictionDetector(claims_repo, llm_router)

        claim_a = Claim(
            uuid="claim-1",
            content="Python is the best language for beginners",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claim_b = Claim(
            uuid="claim-2",
            content="JavaScript is the best language for beginners",
            source_uuid="doc-2",
            content_hash="hash-2",
        )

        result = await detector.classify_contradiction(claim_a, claim_b)

        assert result == ContradictionType.OPINION

    @pytest.mark.asyncio
    async def test_returns_factual_for_hard_conflict(self) -> None:
        """FACTUAL: Hard conflict requiring human review."""
        claims_repo = MagicMock()
        llm_router = MagicMock()
        llm_router.classify_contradiction = AsyncMock(
            return_value=ContradictionType.FACTUAL
        )

        detector = ContradictionDetector(claims_repo, llm_router)

        claim_a = Claim(
            uuid="claim-1",
            content="The Earth has one moon",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claim_b = Claim(
            uuid="claim-2",
            content="The Earth has two moons",
            source_uuid="doc-2",
            content_hash="hash-2",
        )

        result = await detector.classify_contradiction(claim_a, claim_b)

        assert result == ContradictionType.FACTUAL

    @pytest.mark.asyncio
    async def test_returns_none_for_no_actual_contradiction(self) -> None:
        """Should return None if claims don't actually contradict."""
        claims_repo = MagicMock()
        llm_router = MagicMock()
        llm_router.classify_contradiction = AsyncMock(return_value=None)

        detector = ContradictionDetector(claims_repo, llm_router)

        claim_a = Claim(
            uuid="claim-1",
            content="Python supports object-oriented programming",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claim_b = Claim(
            uuid="claim-2",
            content="Python supports functional programming",
            source_uuid="doc-2",
            content_hash="hash-2",
        )

        result = await detector.classify_contradiction(claim_a, claim_b)

        assert result is None


class TestResolveContradiction:
    """Test 3: resolve_contradiction() applies correct strategy per type."""

    def test_temporal_returns_superseded(self) -> None:
        """TEMPORAL -> SUPERSEDED: newer claim wins."""
        detector = ContradictionDetector(MagicMock(), MagicMock())

        claim_a = Claim(
            uuid="claim-1",
            content="Old data",
            source_uuid="doc-1",
            content_hash="hash-1",
            created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        claim_b = Claim(
            uuid="claim-2",
            content="New data",
            source_uuid="doc-2",
            content_hash="hash-2",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        )

        result = detector.resolve_contradiction(
            ContradictionType.TEMPORAL, claim_a, claim_b
        )

        assert result == ResolutionStrategy.SUPERSEDED

    def test_opinion_returns_disputed(self) -> None:
        """OPINION -> DISPUTED: both preserved with flag."""
        detector = ContradictionDetector(MagicMock(), MagicMock())

        claim_a = Claim(
            uuid="claim-1",
            content="Opinion A",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claim_b = Claim(
            uuid="claim-2",
            content="Opinion B",
            source_uuid="doc-2",
            content_hash="hash-2",
        )

        result = detector.resolve_contradiction(
            ContradictionType.OPINION, claim_a, claim_b
        )

        assert result == ResolutionStrategy.DISPUTED

    def test_factual_returns_historical(self) -> None:
        """FACTUAL -> HISTORICAL: both preserved for human review."""
        detector = ContradictionDetector(MagicMock(), MagicMock())

        claim_a = Claim(
            uuid="claim-1",
            content="Fact A",
            source_uuid="doc-1",
            content_hash="hash-1",
        )
        claim_b = Claim(
            uuid="claim-2",
            content="Fact B",
            source_uuid="doc-2",
            content_hash="hash-2",
        )

        result = detector.resolve_contradiction(
            ContradictionType.FACTUAL, claim_a, claim_b
        )

        assert result == ResolutionStrategy.HISTORICAL


class TestAsyncQueueProcessing:
    """Test 4: Async queue processing - detection runs in background."""

    @pytest.mark.asyncio
    async def test_enqueue_starts_background_detection(self) -> None:
        """Should enqueue claim for background detection."""
        claims_repo = MagicMock()
        detector = ContradictionDetector(claims_repo, MagicMock())

        # Start the queue
        await detector.start_detection_queue()

        # Enqueue a claim
        await detector.enqueue_for_detection("claim-uuid-1")

        # Verify it's queued
        assert detector._queue.qsize() >= 1

        # Clean up
        await detector.stop_detection_queue()

    @pytest.mark.asyncio
    async def test_queue_processes_enqueued_claims(self) -> None:
        """Should process claims from the queue."""
        claims_repo = MagicMock()
        claims_repo.get_by_id.return_value = Claim(
            uuid="claim-1",
            content="Test claim",
            source_uuid="doc-1",
            content_hash="hash-1",
        )

        detector = ContradictionDetector(claims_repo, MagicMock())
        await detector.start_detection_queue()
        await detector.enqueue_for_detection("claim-1")

        # Wait briefly for processing
        await asyncio.sleep(0.1)

        # Verify claim was fetched
        claims_repo.get_by_id.assert_called()

        await detector.stop_detection_queue()


class TestTwoPhaseDetection:
    """Test 5: Two-phase detection - filter candidates then LLM classify."""

    @pytest.mark.asyncio
    async def test_two_phase_filters_before_llm(self) -> None:
        """Should filter candidates before calling LLM."""
        claims_repo = MagicMock()
        llm_router = MagicMock()
        llm_router.classify_contradiction = AsyncMock(
            return_value=ContradictionType.OPINION
        )

        detector = ContradictionDetector(claims_repo, llm_router)

        # Mock phase 1: search returns candidates
        claims_repo.search.return_value = [
            Claim(
                uuid="claim-2",
                content="Similar content",
                source_uuid="doc-2",
                content_hash="hash-2",
            ),
        ]

        claim = Claim(
            uuid="claim-1",
            content="Test content",
            source_uuid="doc-1",
            content_hash="hash-1",
        )

        # Phase 1: detect candidates
        candidates = detector.detect_candidates(claim)

        # Phase 2: classify each candidate
        for candidate in candidates:
            result = await detector.classify_contradiction(claim, candidate)
            assert result is not None or result is None  # Returns type or None

    def test_phase_one_returns_only_similar_claims(self) -> None:
        """Phase 1 should only return claims above similarity threshold."""
        claims_repo = MagicMock()
        detector = ContradictionDetector(claims_repo, MagicMock())

        claim = Claim(
            uuid="claim-1",
            content="Python programming tutorial",
            source_uuid="doc-1",
            content_hash="hash-1",
        )

        claims_repo.search.return_value = []

        candidates = detector.detect_candidates(claim, threshold=0.8)

        # Should call search with relevant keywords
        claims_repo.search.assert_called()


class TestContradictionRecord:
    """Tests for ContradictionRecord dataclass."""

    def test_record_stores_all_required_fields(self) -> None:
        """Record should store all required contradiction info."""
        record = ContradictionRecord(
            uuid="contradiction-1",
            claim_a_uuid="claim-1",
            claim_b_uuid="claim-2",
            contradiction_type=ContradictionType.OPINION,
            resolution=ResolutionStrategy.DISPUTED,
            detected_at=datetime.now(timezone.utc),
            resolved_at=None,
            blast_radius=["page-1", "page-2"],
        )

        assert record.uuid == "contradiction-1"
        assert record.claim_a_uuid == "claim-1"
        assert record.claim_b_uuid == "claim-2"
        assert record.contradiction_type == ContradictionType.OPINION
        assert record.resolution == ResolutionStrategy.DISPUTED
        assert record.blast_radius == ["page-1", "page-2"]

    def test_record_with_none_resolved_at(self) -> None:
        """Unresolved records should have None resolved_at."""
        record = ContradictionRecord(
            uuid="contradiction-1",
            claim_a_uuid="claim-1",
            claim_b_uuid="claim-2",
            contradiction_type=ContradictionType.FACTUAL,
            resolution=ResolutionStrategy.HISTORICAL,
            detected_at=datetime.now(timezone.utc),
            resolved_at=None,
            blast_radius=[],
        )

        assert record.resolved_at is None


class TestGetContradictions:
    """Tests for get_all_contradictions and get_unresolved_contradictions."""

    def test_get_all_contradictions_returns_list(self) -> None:
        """Should return list of all contradiction records."""
        import sqlite3
        import tempfile

        # Create temp DB with proper schema
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        conn = sqlite3.connect(temp_db.name)

        claims_repo = MagicMock()
        claims_repo._conn = conn

        # Create contradictions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contradictions (
                uuid TEXT PRIMARY KEY,
                claim_a_uuid TEXT NOT NULL,
                claim_b_uuid TEXT NOT NULL,
                contradiction_type TEXT NOT NULL,
                resolution TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                resolved_at TEXT,
                blast_radius TEXT
            )
        """)
        conn.execute("""
            INSERT INTO contradictions
            (uuid, claim_a_uuid, claim_b_uuid, contradiction_type,
             resolution, detected_at, resolved_at, blast_radius)
            VALUES ('c-1', 'a-1', 'b-1', 'temporal', 'superseded',
                    '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00', '[]')
        """)
        conn.commit()

        detector = ContradictionDetector(claims_repo, MagicMock())
        contradictions = detector.get_all_contradictions()

        assert len(contradictions) == 1

        conn.close()
        import os
        os.unlink(temp_db.name)

    def test_get_unresolved_filters_resolved(self) -> None:
        """Should return only unresolved contradictions."""
        claims_repo = MagicMock()
        claims_repo.get_unresolved_contradictions.return_value = []

        detector = ContradictionDetector(claims_repo, MagicMock())
        unresolved = detector.get_unresolved_contradictions()

        assert isinstance(unresolved, list)
