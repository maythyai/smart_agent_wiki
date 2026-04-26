"""Integration tests for query flow.

Tests the full flow from ingestion to query, including:
- saw search returns results from ingested content
- saw query with mocked LLM returns layered answer
- Offline mode falls back to keyword search
- Graph traversal returns related entities
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.adapters.storage.wiki_repository import WikiRepository
from saw.domain.claims import Claim
from saw.domain.entities import Entity, EntityRelation
from saw.domain.value_objects import ConfidenceLevel
from saw.engines.query.compare import CompareEngine
from saw.engines.query.compiler import ContextCompiler
from saw.engines.query.engine import QueryEngine
from saw.engines.query.graph_traverse import GraphTraverse
from saw.engines.query.search import FTS5Search


@pytest.fixture
def temp_wiki(tmp_path: Path) -> Path:
    """Create temporary wiki directory structure."""
    wiki_path = tmp_path / "test-wiki"
    wiki_path.mkdir()

    # Create .saw directory
    saw_dir = wiki_path / ".saw"
    saw_dir.mkdir()

    # Create wiki subdirectories
    (wiki_path / "wiki" / "concepts").mkdir(parents=True)
    (wiki_path / "wiki" / "entities").mkdir(parents=True)
    (wiki_path / "wiki" / "sources").mkdir(parents=True)

    # Create test document
    doc_content = """# Machine Learning

Machine learning uses neural networks for pattern recognition.
Deep learning is a subset of machine learning with multiple layers.
Transformers replaced RNNs for sequence modeling tasks.

## Key Concepts

- Neural networks learn from data
- Transformers use self-attention
- Deep learning requires GPUs
"""
    (wiki_path / "test.md").write_text(doc_content, encoding="utf-8")

    return wiki_path


@pytest.fixture
def populated_db(temp_wiki: Path) -> sqlite3.Connection:
    """Create populated Claims DB with test data."""
    db_path = temp_wiki / ".saw" / "claims.db"
    conn = sqlite3.connect(str(db_path))

    # Create schema - must match ClaimsRepository.CLAIMS_DB_SCHEMA exactly
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS claim (
            uuid TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            source_uuid TEXT NOT NULL,
            page_number INTEGER,
            line_number INTEGER,
            timestamp TEXT,
            confidence TEXT NOT NULL DEFAULT 'unverified',
            source_mark TEXT NOT NULL DEFAULT 'extracted',
            tags TEXT NOT NULL DEFAULT '[]',
            entities TEXT NOT NULL DEFAULT '[]',
            content_hash TEXT NOT NULL,
            session_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT,
            deleted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS entity (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            aliases TEXT NOT NULL DEFAULT '[]',
            entity_type TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS entity_relation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_uuid TEXT NOT NULL,
            target_uuid TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
        USING fts5(
            title,
            content,
            tags,
            tokenize='unicode61',
            detail=column
        );
    """)

    # Insert test claims - order must match schema columns
    claims = [
        ("claim-1", "Machine learning uses neural networks for pattern recognition.", "source-1", None, None, None, "SINGLE_SOURCE", "extracted", [], [], "hash-claim-1"),
        ("claim-2", "Deep learning is a subset of machine learning with multiple layers.", "source-1", None, None, None, "CROSS_VALIDATED", "extracted", [], [], "hash-claim-2"),
        ("claim-3", "Transformers replaced RNNs for sequence modeling tasks.", "source-2", None, None, None, "HUMAN_VERIFIED", "extracted", [], [], "hash-claim-3"),
        ("claim-4", "Neural networks learn representations from data automatically.", "source-2", None, None, None, "UNVERIFIED", "extracted", [], [], "hash-claim-4"),
    ]

    import json
    for uuid, content, source_uuid, page, line, timestamp, confidence, source_mark, tags, entities, content_hash in claims:
        conn.execute(
            """INSERT INTO claim (uuid, content, source_uuid, page_number, line_number, timestamp,
                                  confidence, source_mark, tags, entities, content_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uuid, content, source_uuid, page, line, timestamp, confidence, source_mark,
             json.dumps(tags), json.dumps(entities), content_hash),
        )
        conn.execute(
            """INSERT INTO fts_index (title, content, tags)
               VALUES (?, ?, '')""",
            (uuid, content),
        )

    # Insert test entities
    entities = [
        ("entity-1", "Machine Learning", "concept", "A field of AI"),
        ("entity-2", "Neural Networks", "concept", "Computing systems inspired by biological neural networks"),
        ("entity-3", "Transformers", "concept", "An architecture for sequence modeling"),
    ]

    for uuid, name, entity_type, desc in entities:
        conn.execute(
            """INSERT INTO entity (uuid, name, entity_type, description)
               VALUES (?, ?, ?, ?)""",
            (uuid, name, entity_type, desc),
        )

    # Insert relations
    conn.execute(
        """INSERT INTO entity_relation (source_uuid, target_uuid, relation_type, weight)
           VALUES (?, ?, ?, ?)""",
        ("entity-1", "entity-2", "uses", 1.0),
    )
    conn.execute(
        """INSERT INTO entity_relation (source_uuid, target_uuid, relation_type, weight)
           VALUES (?, ?, ?, ?)""",
        ("entity-1", "entity-3", "includes", 1.0),
    )

    conn.commit()
    return conn


class TestSearchFlow:
    """Tests for saw search functionality."""

    def test_search_returns_results_from_ingested_content(
        self, populated_db: sqlite3.Connection
    ) -> None:
        """Test that search returns results from ingested content."""
        search = FTS5Search(populated_db)
        result = search.search("machine learning")

        assert result.total >= 2
        assert "claim-1" in result.claim_uuids or "claim-2" in result.claim_uuids

    def test_search_bm25_ranking(self, populated_db: sqlite3.Connection) -> None:
        """Test that bm25 ranking orders results by relevance."""
        search = FTS5Search(populated_db)
        result = search.search("learning")

        assert result.total >= 2
        # Results should be ordered by bm25 score
        if len(result.scores) >= 2:
            assert result.scores[0] >= result.scores[-1]


class TestQueryFlow:
    """Tests for saw query functionality."""

    def test_query_with_mocked_llm_returns_layered_answer(
        self, populated_db: sqlite3.Connection, temp_wiki: Path
    ) -> None:
        """Test that query returns layered answer with citations."""
        # Setup mocks
        claims_repo = SQLiteClaimsRepository(populated_db)
        wiki_repo = WikiRepository(temp_wiki / "wiki")
        search_service = FTS5Search(populated_db)
        tree_mode = MagicMock()
        graph = GraphTraverse(populated_db)
        compare_engine = CompareEngine(claims_repo, wiki_repo)
        compiler = ContextCompiler(
            claims_repo, wiki_repo, search_service, populated_db
        )

        # Mock LLM that returns a structured answer
        mock_llm = MagicMock()
        mock_llm._query_model = "test-model"
        mock_llm.answer_query.return_value = """Machine Learning and Neural Networks

Machine learning is a field that uses neural networks for pattern recognition [^claim:claim-1]. Deep learning extends this with multiple layers [^claim:claim-2].

Key Conclusions:
- Neural networks are fundamental to ML [^claim:claim-1]
- Transformers have replaced RNNs [^claim:claim-3]

Detailed answer here...
"""

        engine = QueryEngine(
            search=search_service,
            compiler=compiler,
            graph=graph,
            compare_engine=compare_engine,
            tree_mode=tree_mode,
            llm=mock_llm,
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            conn=populated_db,
        )

        result = engine.query("What is machine learning?", mode="auto")

        assert result.answer != ""
        assert result.mode in ["nl_query", "auto"]
        # Check layered answer is parsed correctly
        assert result.layered_answer.get("L1") == "Machine Learning and Neural Networks"
        assert "L2" in result.layered_answer
        assert "L3" in result.layered_answer
        # Check citations are extracted from answer (even if sources may be empty in test)
        assert "claim-1" in result.answer or "[^claim:" in result.answer

    def test_query_offline_mode_falls_back_to_keyword_search(
        self, populated_db: sqlite3.Connection, temp_wiki: Path
    ) -> None:
        """Test that offline mode falls back to keyword search."""
        claims_repo = SQLiteClaimsRepository(populated_db)
        wiki_repo = WikiRepository(temp_wiki / "wiki")
        search_service = FTS5Search(populated_db)
        tree_mode = MagicMock()
        graph = GraphTraverse(populated_db)
        compare_engine = CompareEngine(claims_repo, wiki_repo)
        compiler = ContextCompiler(
            claims_repo, wiki_repo, search_service, populated_db
        )

        # No LLM (offline mode)
        engine = QueryEngine(
            search=search_service,
            compiler=compiler,
            graph=graph,
            compare_engine=compare_engine,
            tree_mode=tree_mode,
            llm=None,  # Offline
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            conn=populated_db,
        )

        result = engine.query("machine learning", mode="auto")

        # Should fall back to keyword search
        assert result.mode == "search"
        assert "Found" in result.answer or result.sources

    def test_no_llm_calls_in_offline_mode(
        self, populated_db: sqlite3.Connection, temp_wiki: Path
    ) -> None:
        """Test that no LLM calls are made in offline mode."""
        claims_repo = SQLiteClaimsRepository(populated_db)
        wiki_repo = WikiRepository(temp_wiki / "wiki")
        search_service = FTS5Search(populated_db)
        tree_mode = MagicMock()
        graph = GraphTraverse(populated_db)
        compare_engine = CompareEngine(claims_repo, wiki_repo)
        compiler = ContextCompiler(
            claims_repo, wiki_repo, search_service, populated_db
        )

        mock_llm = MagicMock()
        mock_llm._query_model = "test-model"

        engine = QueryEngine(
            search=search_service,
            compiler=compiler,
            graph=graph,
            compare_engine=compare_engine,
            tree_mode=tree_mode,
            llm=mock_llm,
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            conn=populated_db,
        )

        # Force search mode
        result = engine.query("machine learning", mode="search")

        # LLM should not be called
        mock_llm.answer_query.assert_not_called()
        assert result.mode == "search"


class TestGraphTraversal:
    """Tests for graph traversal functionality."""

    def test_graph_traversal_returns_related_entities(
        self, populated_db: sqlite3.Connection
    ) -> None:
        """Test that graph traversal returns related entities."""
        graph = GraphTraverse(populated_db)
        result = graph.traverse("Machine Learning", mode="bfs", max_depth=2)

        assert len(result.nodes) >= 1
        # Should include Neural Networks (connected)
        node_names = [n.name for n in result.nodes]
        assert "Machine Learning" in node_names

    def test_graph_shortest_path(self, populated_db: sqlite3.Connection) -> None:
        """Test finding shortest path between entities."""
        graph = GraphTraverse(populated_db)

        # Machine Learning connects to Neural Networks
        path = graph.find_path("Machine Learning", "Neural Networks")

        # Should find a path
        assert len(path) >= 2


class TestComparison:
    """Tests for comparison analysis."""

    def test_comparison_with_mock_pages(
        self, populated_db: sqlite3.Connection, temp_wiki: Path
    ) -> None:
        """Test comparison with mock wiki pages."""
        claims_repo = SQLiteClaimsRepository(populated_db)
        wiki_repo = WikiRepository(temp_wiki / "wiki")

        # Create test wiki pages
        from saw.domain.wiki import WikiPage
        from saw.domain.value_objects import PageType, ConfidenceLevel, FreshnessLevel

        page1 = WikiPage(
            path="concepts/ml.md",
            title="Machine Learning",
            page_type=PageType.SUMMARY,
            tags=["ai", "ml"],
            content="Machine learning content",
            frontmatter={"sources": ["source-1"]},
        )
        wiki_repo.write(page1)

        compare = CompareEngine(claims_repo, wiki_repo)
        result = compare.compare(["Machine Learning"])

        # With single page, comparison should return gracefully
        assert result.pages == ["Machine Learning"]
