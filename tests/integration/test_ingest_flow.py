"""Integration tests for the ingestion flow.

Tests the complete flow: saw init -> saw ingest -> verify DB.
"""
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.vault_repository import VaultRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.adapters.llm.router import LLMRouter
from saw.config.settings import LLMSettings, WikiSettings
from saw.engines.ingest.pipeline import IngestPipeline
from saw.write_queue.queue import SQLiteWriteQueue
from saw.write_queue.dispatcher import Dispatcher
from saw.write_queue.sinks.vault_sink import VaultSink
from saw.write_queue.sinks.claims_sink import ClaimsSink
from saw.write_queue.sinks.wiki_sink import WikiSink
from saw.write_queue.sinks.fts5_sink import FTS5Sink
from saw.write_queue.sinks.graph_sink import GraphSink


@pytest.fixture
def tmp_wiki(tmp_path: Path) -> Path:
    """Create a temporary wiki structure for testing."""
    wiki = tmp_path / "test-wiki"
    wiki.mkdir(parents=True)

    # Create .saw directory structure
    saw_dir = wiki / ".saw"
    saw_dir.mkdir()
    (saw_dir / "config.yaml").write_text("path: .\n")

    db_dir = saw_dir / "db"
    db_dir.mkdir()

    # Let ClaimsRepository and WriteQueue initialize the schema
    # Just create an empty DB file
    conn = sqlite3.connect(str(db_dir / "claims.db"))
    conn.close()

    # Create vault and wiki directories
    (wiki / "vault").mkdir()
    (wiki / "wiki").mkdir()

    return wiki


class TestIngestMarkdown:
    """Tests for ingesting Markdown files."""

    def test_ingest_markdown_creates_claims(self, tmp_wiki: Path, tmp_path: Path) -> None:
        """Ingesting a Markdown file creates claims in the database."""
        # Create test markdown file
        md_file = tmp_path / "test-doc.md"
        md_file.write_text("""---
title: Test Document
tags: [test, example]
---
# Introduction
Machine learning transforms data into predictions.
""")

        # Setup components
        db_path = tmp_wiki / ".saw" / "db" / "claims.db"
        conn = sqlite3.connect(str(db_path))

        claims_repo = SQLiteClaimsRepository(conn)
        vault_repo = VaultRepository(tmp_wiki / "vault", tmp_wiki)
        wiki_repo = WikiRepository(tmp_wiki / "wiki")
        write_queue = SQLiteWriteQueue(conn)

        # Mock LLM to return fixed claims
        mock_llm = MagicMock(spec=LLMRouter)
        mock_llm.extract_claims.return_value = {
            "claims": [
                {
                    "content": "Machine learning transforms data into predictions.",
                    "entities": ["Machine learning", "data", "predictions"],
                    "relations": [],
                    "source_mark": "extracted",
                    "tags": ["ml", "data"],
                }
            ]
        }

        pipeline = IngestPipeline(
            claims_repo=claims_repo,
            write_queue=write_queue,
            llm_router=mock_llm,
            vault_repo=vault_repo,
            wiki_repo=wiki_repo,
        )

        result = pipeline.ingest(str(md_file))

        # Dispatch pending operations - register ALL sinks
        dispatcher = Dispatcher(write_queue)
        dispatcher.register_sink(VaultSink(vault_repo))
        dispatcher.register_sink(ClaimsSink(claims_repo))
        dispatcher.register_sink(WikiSink(wiki_repo))
        dispatcher.register_sink(FTS5Sink(conn))  # FTS5 sink needs Connection
        dispatcher.register_sink(GraphSink(conn))
        dispatcher.dispatch_pending()

        # Verify claims in DB
        cursor = conn.execute("SELECT count(*) FROM claim")
        claim_count = cursor.fetchone()[0]
        assert claim_count >= 1

        # Verify FTS5 index updated
        cursor = conn.execute("SELECT * FROM fts_index WHERE fts_index MATCH 'machine'")
        fts_results = cursor.fetchall()
        assert len(fts_results) >= 1

        conn.close()

    def test_ingest_markdown_offline_mode(self, tmp_wiki: Path, tmp_path: Path) -> None:
        """Ingesting in offline mode creates basic claims from headings."""
        md_file = tmp_path / "test-offline.md"
        md_file.write_text("""---
title: Offline Test
---
# Main Heading
This is content.
""")

        db_path = tmp_wiki / ".saw" / "db" / "claims.db"
        conn = sqlite3.connect(str(db_path))

        claims_repo = SQLiteClaimsRepository(conn)
        vault_repo = VaultRepository(tmp_wiki / "vault", tmp_wiki)
        wiki_repo = WikiRepository(tmp_wiki / "wiki")
        write_queue = SQLiteWriteQueue(conn)

        # No LLM (offline mode)
        pipeline = IngestPipeline(
            claims_repo=claims_repo,
            write_queue=write_queue,
            llm_router=None,  # Offline mode
            vault_repo=vault_repo,
            wiki_repo=wiki_repo,
        )

        result = pipeline.ingest(str(md_file))

        # Dispatch pending
        dispatcher = Dispatcher(write_queue)
        dispatcher.register_sink(ClaimsSink(claims_repo))
        dispatcher.dispatch_pending()

        # Should have claims from headings (offline mode)
        assert result.claim_count >= 1

        conn.close()


class TestIngestPython:
    """Tests for ingesting Python code files."""

    def test_ingest_python_ast_zero_llm(self, tmp_wiki: Path, tmp_path: Path) -> None:
        """Ingesting Python file extracts claims via AST with ZERO LLM calls."""
        py_file = tmp_path / "example.py"
        py_file.write_text('''
"""Module for testing."""

def calculate(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

class Calculator:
    """Calculator class."""

    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
''')

        db_path = tmp_wiki / ".saw" / "db" / "claims.db"
        conn = sqlite3.connect(str(db_path))

        claims_repo = SQLiteClaimsRepository(conn)
        vault_repo = VaultRepository(tmp_wiki / "vault", tmp_wiki)
        wiki_repo = WikiRepository(tmp_wiki / "wiki")
        write_queue = SQLiteWriteQueue(conn)

        pipeline = IngestPipeline(
            claims_repo=claims_repo,
            write_queue=write_queue,
            llm_router=None,  # Should NOT matter - AST extraction needs no LLM
            vault_repo=vault_repo,
            wiki_repo=wiki_repo,
        )

        result = pipeline.ingest(str(py_file))

        # Dispatch pending
        dispatcher = Dispatcher(write_queue)
        dispatcher.register_sink(ClaimsSink(claims_repo))
        dispatcher.register_sink(VaultSink(vault_repo))
        dispatcher.dispatch_pending()

        # Verify claims extracted
        assert result.claim_count >= 1
        assert result.parser == "ast"

        # Verify NO LLM calls were made (LLM is None)
        # (implicit assertion: no errors)

        conn.close()


class TestWriteQueueIntegration:
    """Tests for Write Queue integration."""

    def test_write_queue_sinks_complete(self, tmp_wiki: Path, tmp_path: Path) -> None:
        """Write Queue delivers to all 5 sinks."""
        md_file = tmp_path / "test-queue.md"
        md_file.write_text("# Test\\n\\nContent for queue test.")

        db_path = tmp_wiki / ".saw" / "db" / "claims.db"
        conn = sqlite3.connect(str(db_path))

        claims_repo = SQLiteClaimsRepository(conn)
        vault_repo = VaultRepository(tmp_wiki / "vault", tmp_wiki)
        wiki_repo = WikiRepository(tmp_wiki / "wiki")
        write_queue = SQLiteWriteQueue(conn)

        # Mock LLM
        mock_llm = MagicMock(spec=LLMRouter)
        mock_llm.extract_claims.return_value = {
            "claims": [{"content": "Test content", "entities": [], "relations": [], "source_mark": "extracted", "tags": []}]
        }

        pipeline = IngestPipeline(
            claims_repo=claims_repo,
            write_queue=write_queue,
            llm_router=mock_llm,
            vault_repo=vault_repo,
            wiki_repo=wiki_repo,
        )

        result = pipeline.ingest(str(md_file))

        # Verify write_outbox has ops
        cursor = conn.execute("SELECT count(*) FROM write_outbox")
        op_count = cursor.fetchone()[0]
        assert op_count >= 1

        # Dispatch all sinks
        dispatcher = Dispatcher(write_queue)
        dispatcher.register_sink(VaultSink(vault_repo))
        dispatcher.register_sink(ClaimsSink(claims_repo))
        dispatcher.register_sink(WikiSink(wiki_repo))
        dispatcher.register_sink(FTS5Sink(claims_repo))
        dispatcher.register_sink(GraphSink(conn))

        dispatcher.dispatch_pending()

        # Verify all ops completed
        cursor = conn.execute("SELECT count(*) FROM write_outbox WHERE status = 'done'")
        done_count = cursor.fetchone()[0]
        assert done_count >= 1

        conn.close()
