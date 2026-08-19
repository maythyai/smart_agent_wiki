"""Knowledge Expiry - tactical vs strategic classification.

Per D-18: Knowledge NEVER auto-expires, only user can delete.
This module classifies knowledge and identifies expiry candidates for user review.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from saw.domain.value_objects import FreshnessLevel

if TYPE_CHECKING:
    from saw.domain.claims import Claim
    from saw.domain.protocols import ClaimsRepository


@dataclass
class ExpiryCandidate:
    """A claim that may need expiry review.

    Attributes:
        claim_uuid: UUID of the claim
        content: Claim content snippet
        classification: "tactical" or "strategic"
        age_days: How old the claim is
        reason: Why it's an expiry candidate
    """
    claim_uuid: str
    content: str
    classification: str
    age_days: int
    reason: str


class KnowledgeExpiry:
    """Manages knowledge classification and expiry identification.

    Per D-18: Knowledge NEVER auto-expires.
    This class identifies candidates for user review only.
    """

    # Age threshold for tactical knowledge review
    TACTICAL_REVIEW_THRESHOLD = 90  # days

    def __init__(self, claims_repo: ClaimsRepository) -> None:
        self._claims = claims_repo

    def classify_knowledge(self, claim: Claim) -> str:
        """Classify knowledge as tactical or strategic (per D-18).

        Tactical: Time-sensitive, specific to context.
        Strategic: Timeless principles, generally applicable.

        Args:
            claim: The claim to classify.

        Returns:
            "tactical" or "strategic".
        """
        content = claim.content.lower()

        # Tactical indicators
        tactical_patterns = [
            "current", "currently", "now", "today", "this year",
            "latest", "recent", "as of", "version",
            "rate", "limit", "quota", "price", "cost",
            "temporary", "interim", "beta", "experimental",
        ]

        # Strategic indicators
        strategic_patterns = [
            "always", "never", "principle", "fundamental",
            "rule", "law", "theory", "concept", "definition",
            "architecture", "design", "pattern", "best practice",
        ]

        # Count indicators
        tactical_score = sum(1 for p in tactical_patterns if p in content)
        strategic_score = sum(1 for p in strategic_patterns if p in content)

        # Tags can also indicate classification
        if "tactical" in claim.tags:
            tactical_score += 2
        if "strategic" in claim.tags:
            strategic_score += 2

        if tactical_score > strategic_score:
            return "tactical"
        else:
            return "strategic"

    def get_expiry_candidates(self) -> list[ExpiryCandidate]:
        """Get tactical knowledge older than threshold for review.

        Per D-18: Returns candidates only, does NOT auto-delete.

        Enumerates non-deleted claims via the repository's backing sqlite
        connection (the same pattern the Govern Linter uses), classifies each
        as tactical/strategic, and returns tactical claims older than
        ``TACTICAL_REVIEW_THRESHOLD``. Timestamps are normalized to aware UTC
        so SQLite's naive ``datetime('now')`` default is handled correctly.
        """
        import json
        import sqlite3
        from types import SimpleNamespace

        candidates: list[ExpiryCandidate] = []

        conn = getattr(self._claims, "_conn", None)
        # Only proceed with a real sqlite3 connection; degrade to [] otherwise
        # (e.g. when the repository is a unittest Mock without a backing conn).
        if not isinstance(conn, sqlite3.Connection):
            return candidates

        try:
            rows = conn.execute(
                "SELECT uuid, content, tags, created_at FROM claim WHERE deleted_at IS NULL"
            ).fetchall()
        except Exception:
            return candidates

        now = datetime.now(timezone.utc)
        for uuid, content, tags_json, created_at in rows:
            try:
                tags = json.loads(tags_json) if tags_json else []
                if not isinstance(tags, list):
                    tags = []
            except Exception:
                tags = []

            claim_like = SimpleNamespace(content=content or "", tags=tags)
            try:
                if self.classify_knowledge(claim_like) != "tactical":
                    continue
                ca = created_at
                if isinstance(ca, str):
                    ca = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                if ca is None:
                    continue
                if ca.tzinfo is None:
                    ca = ca.replace(tzinfo=timezone.utc)
                age_days = (now - ca).days
            except Exception:
                continue

            if age_days > self.TACTICAL_REVIEW_THRESHOLD:
                candidates.append(ExpiryCandidate(
                    claim_uuid=uuid,
                    content=(content or "")[:100],
                    classification="tactical",
                    age_days=age_days,
                    reason=f"Tactical knowledge older than {self.TACTICAL_REVIEW_THRESHOLD} days",
                ))

        return candidates

    def mark_reviewed(self, claim_uuid: str, action: str) -> None:
        """Record user's expiry decision for a claim.

        Args:
            claim_uuid: UUID of the reviewed claim.
            action: User action ("keep", "delete", "update").
        """
        # Would record the decision in the claims DB
        # For now, just a placeholder
        pass