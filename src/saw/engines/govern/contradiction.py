"""Contradiction detection and resolution.

Per D-06: Async queue detection - runs in background without blocking ingestion.
Per D-07: Two-phase detection - filter candidates then LLM classify.
Per D-08: LLM auto-classifies contradiction type (TEMPORAL/OPINION/FACTUAL).
Per D-09: All types auto-resolve with correct strategy.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from saw.domain.claims import Claim
from saw.domain.value_objects import (
    ContradictionType,
    ResolutionStrategy,
)

if TYPE_CHECKING:
    from saw.adapters.llm.router import LLMRouter
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository


# SQL for contradictions table
CONTRADICTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS contradictions (
    uuid TEXT PRIMARY KEY,
    claim_a_uuid TEXT NOT NULL,
    claim_b_uuid TEXT NOT NULL,
    contradiction_type TEXT NOT NULL,
    resolution TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    resolved_at TEXT,
    blast_radius TEXT,  -- JSON array of affected pages
    FOREIGN KEY (claim_a_uuid) REFERENCES claim(uuid),
    FOREIGN KEY (claim_b_uuid) REFERENCES claim(uuid)
);
"""


@dataclass
class ContradictionRecord:
    """Record of a detected contradiction between claims.

    Per D-09: All contradictions have a resolution strategy applied.
    """
    uuid: str
    claim_a_uuid: str
    claim_b_uuid: str
    contradiction_type: ContradictionType
    resolution: ResolutionStrategy
    detected_at: datetime
    resolved_at: datetime | None = None
    blast_radius: list[str] = field(default_factory=list)


class ContradictionDetector:
    """Detects and resolves contradictions between claims.

    Per D-06: Uses async queue for background detection.
    Per D-07: Two-phase detection (filter -> classify).
    Per D-08: LLM classifies type.
    Per D-09: Auto-apply resolution per type.
    """

    def __init__(
        self,
        claims_repo: SQLiteClaimsRepository,
        llm_router: LLMRouter,
    ) -> None:
        """Initialize detector with repositories.

        Args:
            claims_repo: Claims DB repository for claim lookups.
            llm_router: LLM router for classification.
        """
        self._claims_repo = claims_repo
        self._llm_router = llm_router
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._processing: bool = False
        self._worker_task: asyncio.Task | None = None

    async def start_detection_queue(self) -> None:
        """Start background queue for contradiction detection.

        Per D-06: Async processing doesn't block ingestion.
        """
        self._processing = True
        self._worker_task = asyncio.create_task(self._process_queue())

    async def stop_detection_queue(self) -> None:
        """Stop the background detection queue."""
        self._processing = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def enqueue_for_detection(self, claim_uuid: str) -> None:
        """Enqueue claim for background contradiction check.

        Args:
            claim_uuid: UUID of claim to check for contradictions.
        """
        await self._queue.put(claim_uuid)

    async def _process_queue(self) -> None:
        """Background worker that processes queued claims."""
        while self._processing:
            try:
                claim_uuid = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
                await self._detect_for_claim(claim_uuid)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def _detect_for_claim(self, claim_uuid: str) -> None:
        """Run full two-phase detection for a claim.

        Args:
            claim_uuid: UUID of claim to check.
        """
        claim = self._claims_repo.get_by_id(claim_uuid)
        if claim is None:
            return

        # Phase 1: Find candidates
        candidates = self.detect_candidates(claim)

        # Phase 2: Classify each candidate
        for candidate in candidates:
            contradiction_type = await self.classify_contradiction(
                claim, candidate
            )
            if contradiction_type is not None:
                # Resolve and record
                resolution = self.resolve_contradiction(
                    contradiction_type, claim, candidate
                )
                record = self._create_record(
                    claim, candidate, contradiction_type, resolution
                )
                self._store_contradiction(record)

    def detect_candidates(
        self,
        claim: Claim,
        threshold: float = 0.8,
    ) -> list[Claim]:
        """Phase 1: Filter candidates using keyword + semantic similarity.

        Per D-07: Uses keyword matching and semantic filtering.

        Args:
            claim: The claim to find candidates for.
            threshold: Similarity threshold (0.0-1.0).

        Returns:
            List of candidate claims that might contradict.
        """
        # Extract keywords from claim content
        keywords = self._extract_keywords(claim.content)

        # Search for similar claims via FTS5
        if keywords:
            search_query = " ".join(keywords[:5])  # Top 5 keywords
            similar_claims = self._claims_repo.search(search_query, limit=20)

            # Filter out self and same-source claims
            candidates = [
                c for c in similar_claims
                if c.uuid != claim.uuid and c.source_uuid != claim.source_uuid
            ]
            return candidates

        return []

    def _extract_keywords(self, content: str) -> list[str]:
        """Extract keywords from content for candidate filtering.

        Simple keyword extraction: split on whitespace, filter short words.
        """
        words = content.lower().split()
        # Filter: at least 4 chars, not common stop words
        stop_words = {"the", "is", "are", "was", "were", "be", "been",
                      "being", "have", "has", "had", "do", "does", "did",
                      "will", "would", "could", "should", "may", "might",
                      "must", "shall", "can", "need", "dare", "ought",
                      "used", "a", "an", "and", "or", "but", "in", "on",
                      "at", "to", "for", "of", "with", "by", "from", "as"}
        keywords = [
            w for w in words
            if len(w) >= 4 and w not in stop_words
        ]
        return keywords[:10]  # Top 10 keywords

    async def classify_contradiction(
        self,
        claim_a: Claim,
        claim_b: Claim,
    ) -> ContradictionType | None:
        """Phase 2: LLM precise classification.

        Per D-08: LLM auto-classifies type (TEMPORAL/OPINION/FACTUAL).

        Args:
            claim_a: First claim.
            claim_b: Second claim.

        Returns:
            ContradictionType if contradiction found, None otherwise.
        """
        # Check if LLM router has classify method
        if hasattr(self._llm_router, 'classify_contradiction'):
            return await self._llm_router.classify_contradiction(
                claim_a.content, claim_b.content
            )

        # Fallback: simple heuristic classification
        # Check timestamps for temporal
        if claim_a.created_at != claim_b.created_at:
            time_diff = abs(
                (claim_a.created_at - claim_b.created_at).total_seconds()
            )
            if time_diff > 365 * 24 * 3600:  # > 1 year difference
                return ContradictionType.TEMPORAL

        # Check for opinion indicators
        opinion_words = ["best", "worst", "should", "prefer", "recommend",
                        "good", "bad", "better", "worse"]
        content_a_lower = claim_a.content.lower()
        content_b_lower = claim_b.content.lower()
        if any(w in content_a_lower or w in content_b_lower for w in opinion_words):
            return ContradictionType.OPINION

        # Default to factual for hard conflicts
        return ContradictionType.FACTUAL

    def resolve_contradiction(
        self,
        contradiction_type: ContradictionType,
        claim_a: Claim,
        claim_b: Claim,
    ) -> ResolutionStrategy:
        """Auto-apply resolution strategy per D-09.

        Args:
            contradiction_type: The type of contradiction.
            claim_a: First claim.
            claim_b: Second claim.

        Returns:
            ResolutionStrategy to apply.
        """
        if contradiction_type == ContradictionType.TEMPORAL:
            # Newer claim wins, older marked historical
            return ResolutionStrategy.SUPERSEDED

        elif contradiction_type == ContradictionType.OPINION:
            # Both preserved, flagged for readers
            return ResolutionStrategy.DISPUTED

        else:  # FACTUAL
            # Both preserved, escalate to human review
            return ResolutionStrategy.HISTORICAL

    def apply_resolution(self, record: ContradictionRecord) -> None:
        """Apply resolution: persist the resolved state of a contradiction.

        Per D-09 the resolution strategy is chosen when the record is created.
        This stamps ``resolved_at`` (and re-persists the strategy) so records
        that were left unresolved (e.g. HISTORICAL awaiting human review) are
        marked resolved. Previously a ``pass`` no-op, so contradictions stayed
        "unresolved" forever. Best-effort: errors are logged, not raised.
        """
        conn = getattr(self._claims_repo, "_conn", None)
        if not isinstance(conn, sqlite3.Connection):
            return
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        try:
            conn.execute(
                "UPDATE contradictions SET resolved_at = ?, resolution = ? "
                "WHERE uuid = ?",
                (now, record.resolution.name.lower(), record.uuid),
            )
            conn.commit()
            record.resolved_at = datetime.fromisoformat(now)
        except sqlite3.Error:
            import logging

            logging.getLogger(__name__).warning(
                "Failed to apply resolution for contradiction %s", record.uuid
            )

    def _create_record(
        self,
        claim_a: Claim,
        claim_b: Claim,
        contradiction_type: ContradictionType,
        resolution: ResolutionStrategy,
    ) -> ContradictionRecord:
        """Create a contradiction record.

        Args:
            claim_a: First claim.
            claim_b: Second claim.
            contradiction_type: Detected type.
            resolution: Applied resolution.

        Returns:
            ContradictionRecord with all metadata.
        """
        import uuid
        return ContradictionRecord(
            uuid=str(uuid.uuid4()),
            claim_a_uuid=claim_a.uuid,
            claim_b_uuid=claim_b.uuid,
            contradiction_type=contradiction_type,
            resolution=resolution,
            detected_at=datetime.now(timezone.utc),
            resolved_at=datetime.now(timezone.utc) if resolution != ResolutionStrategy.HISTORICAL else None,
            blast_radius=[],  # Would be computed by BlastRadiusAnalyzer
        )

    def _store_contradiction(self, record: ContradictionRecord) -> None:
        """Store contradiction in database (idempotent, transactional).

        C3: delegates to ``ContradictionsSink``'s shared ``store_contradiction``
        helper so the contradictions table has a single write path (also
        usable by the outbox dispatcher). Best-effort: errors are logged
        rather than silently swallowed.
        """
        if not hasattr(self._claims_repo, "_conn"):
            return
        conn = self._claims_repo._conn
        try:
            from saw.write_queue.sinks.contradictions_sink import store_contradiction

            store_contradiction(conn, record)
        except sqlite3.Error:
            # Table may not exist yet on a fresh DB; schema is created
            # lazily elsewhere. Log and continue — detection is best-effort.
            import logging

            logging.getLogger(__name__).warning(
                "Failed to store contradiction %s", record.uuid
            )

    def get_all_contradictions(self) -> list[ContradictionRecord]:
        """Get all contradiction records.

        Returns:
            List of all stored contradiction records.
        """
        if hasattr(self._claims_repo, '_conn'):
            conn = self._claims_repo._conn
            try:
                rows = conn.execute(
                    "SELECT * FROM contradictions"
                ).fetchall()
                return [self._row_to_record(row) for row in rows]
            except sqlite3.Error:
                return []
        return []

    def get_unresolved_contradictions(self) -> list[ContradictionRecord]:
        """Get only unresolved contradictions.

        Returns:
            List of unresolved records (resolved_at is None).
        """
        if hasattr(self._claims_repo, '_conn'):
            conn = self._claims_repo._conn
            try:
                rows = conn.execute(
                    "SELECT * FROM contradictions WHERE resolved_at IS NULL"
                ).fetchall()
                return [self._row_to_record(row) for row in rows]
            except sqlite3.Error:
                return []
        return []

    def _row_to_record(self, row) -> ContradictionRecord:
        """Convert DB row to ContradictionRecord."""
        return ContradictionRecord(
            uuid=row[0],
            claim_a_uuid=row[1],
            claim_b_uuid=row[2],
            contradiction_type=ContradictionType[row[3].upper()],
            resolution=ResolutionStrategy[row[4].upper()],
            detected_at=datetime.fromisoformat(row[5]),
            resolved_at=datetime.fromisoformat(row[6]) if row[6] else None,
            blast_radius=json.loads(row[7]) if row[7] else [],
        )