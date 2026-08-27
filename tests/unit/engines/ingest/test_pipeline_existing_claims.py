"""DEF-8: ``IngestPipeline._get_existing_claims`` must really find overlapping
claims by content_hash so the fuser can dedup, instead of returning ``[]``.
"""
from __future__ import annotations

import sqlite3

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.domain.claims import Claim
from saw.domain.value_objects import ConfidenceLevel
from saw.engines.ingest.pipeline import IngestPipeline


def _claim(uuid: str, content: str, source_uuid: str, content_hash: str) -> Claim:
    return Claim(
        uuid=uuid,
        content=content,
        source_uuid=source_uuid,
        content_hash=content_hash,
        confidence=ConfidenceLevel.SINGLE_SOURCE,
    )


def test_get_existing_claims_finds_by_content_hash(tmp_path) -> None:
    conn = sqlite3.connect(str(tmp_path / "ingest.db"))
    repo = SQLiteClaimsRepository(conn)
    repo.insert(_claim("e1", "hello", "s1", "HASHX"))

    pipe = IngestPipeline.__new__(IngestPipeline)
    pipe._claims_repo = repo

    new = _claim("n1", "hello again", "s2", "HASHX")
    found = pipe._get_existing_claims([new])
    assert len(found) == 1
    assert found[0].uuid == "e1"


def test_get_existing_claims_empty_for_new_hash(tmp_path) -> None:
    conn = sqlite3.connect(str(tmp_path / "ingest.db"))
    repo = SQLiteClaimsRepository(conn)
    repo.insert(_claim("e1", "hello", "s1", "HASHX"))

    pipe = IngestPipeline.__new__(IngestPipeline)
    pipe._claims_repo = repo

    new = _claim("n1", "different", "s2", "NEWHASH")
    assert pipe._get_existing_claims([new]) == []
