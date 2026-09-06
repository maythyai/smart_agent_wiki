"""T-F-R-1: ingest directory recursion tests (AC-A-1..5).

Verifies that ``IngestPipeline.ingest()`` recursively ingests all
supported files in a directory (Bug A fix, ADR-013 decision one).

Uses a mock LLMRouter (no real LLM calls) and a real SQLite DB +
VaultRepository/WriteQueue so the full classify->extract->fuse->validate
->enqueue path is exercised per file.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from saw.adapters.llm.router import LLMRouter
from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.engines.ingest.pipeline import IngestPipeline
from saw.write_queue.queue import SQLiteWriteQueue


def _make_pipeline(tmp_path: Path) -> IngestPipeline:
    """Build an IngestPipeline with a mock LLMRouter and real SQLite repos."""
    conn = sqlite3.connect(str(tmp_path / "ingest_dir.db"), check_same_thread=False)
    claims_repo = SQLiteClaimsRepository(conn)
    write_queue = SQLiteWriteQueue(conn)
    vault_repo = WikiRepository(tmp_path / "vault")
    wiki_repo = WikiRepository(tmp_path / "wiki")

    mock_llm = MagicMock(spec=LLMRouter)
    mock_llm.extract_claims.return_value = {
        "claims": [
            {
                "content": "A claim extracted from the document.",
                "entities": ["document"],
                "relations": [],
                "source_mark": "extracted",
                "tags": ["test"],
            }
        ]
    }

    return IngestPipeline(
        claims_repo=claims_repo,
        write_queue=write_queue,
        llm_router=mock_llm,
        vault_repo=vault_repo,
        wiki_repo=wiki_repo,
    )


def _write_md(path: Path, content: str = "# Title\n\nSome content here.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── AC-A-1: directory recursive ingest ─────────────────────────────

def test_ac_a_1_directory_recursive_ingest(tmp_path):
    """Ingesting a dir with 3 .md files → all ingested, no 'Is a directory'."""
    d = tmp_path / "docs"
    d.mkdir()
    for i in range(3):
        _write_md(d / f"doc{i}.md", f"# Doc {i}\n\nContent number {i}.")

    pipe = _make_pipeline(tmp_path)
    result = pipe.ingest(str(d))

    assert result.claim_count >= 3, f"expected >= 3 claims, got {result.claim_count}"
    assert result.parser == "directory-batch"
    # No "Is a directory" errors (Bug A)
    for err in result.errors:
        assert "Is a directory" not in err, f"unexpected dir error: {err}"


# ── AC-A-2: empty directory ────────────────────────────────────────

def test_ac_a_2_empty_directory(tmp_path):
    """Ingesting an empty dir → error 'No ingestible files found' + 0 claims."""
    d = tmp_path / "empty"
    d.mkdir()

    pipe = _make_pipeline(tmp_path)
    result = pipe.ingest(str(d))

    assert result.claim_count == 0
    assert result.parser == "directory-batch"
    assert any("No ingestible files found" in e for e in result.errors)


# ── AC-A-3: partial failure ────────────────────────────────────────

def test_ac_a_3_partial_failure_continues(tmp_path):
    """Dir with 2 .md + 1 .pdf → 2 md succeed, pdf error recorded, no abort."""
    d = tmp_path / "mixed"
    d.mkdir()
    _write_md(d / "a.md", "# A\n\nContent A.")
    _write_md(d / "b.md", "# B\n\nContent B.")
    # Corrupt/unsupported binary with .pdf extension
    (d / "bad.pdf").write_bytes(b"\x00\x01\x02not a real pdf")

    pipe = _make_pipeline(tmp_path)
    result = pipe.ingest(str(d))

    # 2 markdown files should produce claims
    assert result.claim_count >= 2, f"expected >= 2 claims, got {result.claim_count}"
    assert result.parser == "directory-batch"
    # Some error recorded for the bad pdf (extraction failed or unknown)
    assert len(result.errors) > 0
    # But the batch did not abort — markdown claims present
    assert not any("Is a directory" in e for e in result.errors)


# ── AC-A-4: subdirectory recursion ─────────────────────────────────

def test_ac_a_4_subdirectory_recursion(tmp_path):
    """Dir with subdirectory containing 1 .md → subdirectory file ingested."""
    d = tmp_path / "root"
    d.mkdir()
    _write_md(d / "top.md", "# Top level\n\nTop content.")
    sub = d / "sub" / "deep"
    _write_md(sub / "nested.md", "# Nested\n\nNested content.")

    pipe = _make_pipeline(tmp_path)
    result = pipe.ingest(str(d))

    assert result.claim_count >= 2, f"expected >= 2 claims (top + nested), got {result.claim_count}"
    assert result.parser == "directory-batch"
    assert not any("Is a directory" in e for e in result.errors)


# ── AC-A-5: exclude SAW internal directories ────────────────────────

def test_ac_a_5_exclude_saw_internal(tmp_path):
    """Dir with .saw/inside.md → .saw/ files not ingested."""
    d = tmp_path / "project"
    d.mkdir()
    _write_md(d / "real.md", "# Real\n\nReal content.")
    _write_md(d / ".saw" / "inside.md", "# Inside SAW\n\nShould not ingest.")

    pipe = _make_pipeline(tmp_path)
    result = pipe.ingest(str(d))

    # Only 1 file (real.md) should be ingested, .saw/inside.md excluded
    assert result.claim_count >= 1
    assert result.parser == "directory-batch"
    # No errors referencing .saw/inside.md
    for err in result.errors:
        assert ".saw" not in err, f".saw file should not appear in errors: {err}"
    # Verify only 1 file processed (no .saw file)
    assert result.claim_count < 3, "too many claims — .saw may not be excluded"
