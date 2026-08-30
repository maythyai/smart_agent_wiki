"""Claims sink - writes structured claims to the Claims DB.

Per Pitfall 7: idempotent via INSERT OR IGNORE with UUID PK.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.domain.claims import Claim
from saw.domain.exceptions import ClaimsDBError
from saw.domain.value_objects import ConfidenceLevel, SourceMark


class ClaimsSink:
    """Write Queue sink for Claims DB."""

    def __init__(self, claims_repo: SQLiteClaimsRepository) -> None:
        self._repo = claims_repo

    @property
    def name(self) -> str:
        return "claims"

    def write(self, op) -> None:
        """Write a claim from a WriteOp.

        Idempotent: INSERT OR IGNORE on duplicate UUID.
        """
        payload = op.payload
        claim = Claim(
            uuid=payload.get("uuid", op.op_id),
            content=payload.get("content", ""),
            source_uuid=payload.get("source_uuid", ""),
            content_hash=payload.get("content_hash", Claim.compute_hash(payload.get("content", ""))),
            page_number=payload.get("page_number"),
            line_number=payload.get("line_number"),
            timestamp=payload.get("timestamp"),
            tags=payload.get("tags", []),
            entities=payload.get("entities", []),
            # F-CONN-04: persist connector provenance for conflict detection.
            source_platform=payload.get("source_platform"),
            source_id=payload.get("source_id"),
        )

        # Parse confidence level
        conf_str = payload.get("confidence", "unverified").upper()
        try:
            claim.confidence = ConfidenceLevel[conf_str]
        except KeyError:
            claim.confidence = ConfidenceLevel.UNVERIFIED

        # Parse source mark
        mark_str = payload.get("source_mark", "extracted").upper()
        try:
            claim.source_mark = SourceMark[mark_str]
        except KeyError:
            claim.source_mark = SourceMark.EXTRACTED

        # F-CONN-04 resolution: upsert so a platform-wins conflict overwrites
        # the stale claim content (was INSERT OR IGNORE → no update).
        self._repo.upsert(claim)

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "claims"
