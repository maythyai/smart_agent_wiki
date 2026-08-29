"""Claim fuser for deduplication and contradiction detection.

Per D-04: Dedup claims by content_hash.
Per D-12: Fuser compares new claims against existing.
"""
from __future__ import annotations

from dataclasses import dataclass

from saw.domain.claims import Claim

# F-INGEST-07: negation prefixes that indicate a claim contradicts another
# from the same source (e.g. "X is blue" vs "X is not blue").
_NEGATION_PREFIXES = (
    "not ", "no ", "never ", "isn't ", "doesn't ", "don't ",
    "is not ", "does not ", "do not ", "are not ", "aren't ",
)


def _is_contradiction(a: str, b: str) -> bool:
    """Return True if one claim negates the other (same subject, opposite polarity)."""
    a = a.strip().lower().rstrip(".")
    b = b.strip().lower().rstrip(".")
    if not a or not b or a == b:
        return False
    for prefix in _NEGATION_PREFIXES:
        if a == prefix + b or b == prefix + a:
            return True
    return False


@dataclass
class FusedResult:
    """Result of fusing new and existing claims."""
    to_insert: list[Claim]
    to_skip: list[Claim]
    contradictions: list[tuple[Claim, Claim]]


class Fuser:
    """Fuse new claims with existing claims."""

    def fuse(self, new_claims: list[Claim], existing_claims: list[Claim]) -> FusedResult:
        """Compare new claims against existing for dedup and contradictions.

        Args:
            new_claims: Claims extracted from the current ingestion.
            existing_claims: Claims already in the database.

        Returns:
            FusedResult with claims to insert, skip, and contradictions.
        """
        to_insert: list[Claim] = []
        to_skip: list[Claim] = []
        contradictions: list[tuple[Claim, Claim]] = []

        # Build hash map of existing claims
        existing_by_hash: dict[str, Claim] = {
            c.content_hash: c for c in existing_claims
        }

        for new_claim in new_claims:
            existing = existing_by_hash.get(new_claim.content_hash)

            if existing:
                # Exact duplicate by content_hash -> skip
                to_skip.append(new_claim)
            else:
                # Check for contradiction (same source_uuid, different content)
                same_source_claims = [
                    c for c in existing_claims
                    if c.source_uuid == new_claim.source_uuid
                ]

                # F-INGEST-07: detect negation contradictions against
                # same-source existing claims (was always empty).
                for c in same_source_claims:
                    if _is_contradiction(new_claim.content, c.content):
                        contradictions.append((new_claim, c))

                to_insert.append(new_claim)

        return FusedResult(
            to_insert=to_insert,
            to_skip=to_skip,
            contradictions=contradictions,
        )