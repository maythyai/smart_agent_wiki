"""MCP server using FastMCP.

Per STACK.md: FastMCP==3.2.4
Per PITFALLS.md: Use async LiteLLM calls with timeouts.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from fastmcp import FastMCP

from saw.drivers.mcp.config import MCPConfig

if TYPE_CHECKING:
    from saw.engines.govern.governor import Governor
    from saw.engines.learn.engine import LearnEngine
    from saw.engines.query.engine import QueryEngine
    from saw.engines.ingest.pipeline import IngestPipeline

logger = logging.getLogger(__name__)

# Global MCP instance
mcp = FastMCP(
    name="smart-agent-wiki",
    version="1.0.0",
)

# Global engine references (initialized by create_server)
_query_engine = None
_governor = None
_detector = None
_pipeline = None
_learn_engine = None
_wiki_repo = None
_write_queue = None
_llm_router = None

# New compile-layer engines
_compile_engine = None
_archiver = None
_wiki_linter = None
_concept_graph = None
_feedback_engine = None
_code_wiki_engine = None


def _build_llm_router():
    """Build an LLMRouter if any provider API key is configured.

    Returns None when no LLM is available so engines fall back to offline
    heuristics rather than crashing.
    """
    try:
        from saw.adapters.llm.router import LLMRouter
        from saw.config.settings import LLMSettings

        # Only construct if at least one provider key is present
        provider_keys = (
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "DEEPSEEK_API_KEY", "MISTRAL_API_KEY", "DASHSCOPE_API_KEY",
        )
        if not any(os.environ.get(k) for k in provider_keys):
            logger.info("No LLM API key configured — running in offline mode")
            return None

        settings = LLMSettings()
        router = LLMRouter(settings)
        if router._check_available():
            logger.info("LLM router initialized")
            return router
        return None
    except Exception as e:
        logger.warning("Failed to initialize LLM router: %s", e)
        return None


def create_server(wiki_path: Path, db_path: Path | None = None) -> FastMCP:
    """Create and configure MCP server with all tools registered.

    Initializes engines from the wiki path and registers all MCP tools.

    Args:
        wiki_path: Path to the wiki directory.
        db_path: Path to claims.db (default: wiki_path/.saw/db/claims.db).

    Returns:
        Configured FastMCP instance with all tools registered.
    """
    global _query_engine, _governor, _detector, _pipeline, _learn_engine
    global _wiki_repo, _write_queue, _llm_router
    global _compile_engine, _archiver, _wiki_linter
    global _concept_graph, _feedback_engine, _code_wiki_engine

    # Resolve DB path
    if db_path is None:
        db_path = wiki_path / ".saw" / "db" / "claims.db"

    # Build LLM router (shared across engines)
    _llm_router = _build_llm_router()

    # Initialize engines
    try:
        from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
        from saw.adapters.storage.wiki_repository import WikiRepository
        from saw.adapters.storage.vault_repository import VaultRepository
        from saw.write_queue.queue import SQLiteWriteQueue
        from saw.engines.query.engine import QueryEngine
        from saw.engines.query.search import FTS5Search
        from saw.engines.query.compiler import ContextCompiler
        from saw.engines.query.graph_traverse import GraphTraverse
        from saw.engines.query.compare import CompareEngine
        from saw.engines.query.tree_mode import TreeModeSearch
        from saw.engines.govern.governor import Governor
        from saw.engines.govern.contradiction import ContradictionDetector
        from saw.engines.ingest.pipeline import IngestPipeline

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            claims_repo = SQLiteClaimsRepository(conn)
            wiki_repo = WikiRepository(wiki_path)
            vault_repo = VaultRepository(wiki_path)

            search = FTS5Search(conn)
            # FIX: ContextCompiler requires (claims_repo, wiki_repo, search, conn)
            compiler = ContextCompiler(claims_repo, wiki_repo, search, conn)
            graph = GraphTraverse(claims_repo)
            compare_engine = CompareEngine(claims_repo, wiki_repo)
            tree_mode = TreeModeSearch(claims_repo)

            _query_engine = QueryEngine(
                search=search,
                compiler=compiler,
                graph=graph,
                compare_engine=compare_engine,
                tree_mode=tree_mode,
                llm=_llm_router,  # FIX: inject real LLM router
                claims_repo=claims_repo,
                wiki_repo=wiki_repo,
                conn=conn,
            )

            _governor = Governor(claims_repo, wiki_repo)
            _detector = ContradictionDetector(claims_repo, _llm_router)
            _wiki_repo = wiki_repo

            # Initialize write queue for MCP page mutations
            _write_queue = SQLiteWriteQueue(conn)

            # FIX: IngestPipeline requires 5 args
            _pipeline = IngestPipeline(
                claims_repo=claims_repo,
                write_queue=_write_queue,
                llm_router=_llm_router,
                vault_repo=vault_repo,
                wiki_repo=wiki_repo,
            )
        else:
            logger.warning("Database not found at %s — tools will return empty results", db_path)
    except Exception as e:
        logger.warning("Failed to initialize engines: %s — tools will return empty results", e)

    # Initialize code graph engine (optional — only if DB exists)
    _code_graph_engine = None
    try:
        code_graph_db = wiki_path / ".saw" / "code_graph.db"
        if code_graph_db.exists():
            from saw.code_graph.engine import CodeGraphEngine
            _code_graph_engine = CodeGraphEngine(wiki_path, db_path=code_graph_db)
            logger.info("Code graph engine initialized from %s", code_graph_db)
    except Exception as e:
        logger.warning("Failed to initialize code graph engine: %s", e)

    # Initialize compile-layer engines (wiki compile, archive, lint, concept, feedback, code wiki)
    try:
        from saw.engines.compile import (
            WikiCompileEngine,
            QueryArchiver,
            WikiLinter,
            ConceptGraphEngine,
            FeedbackEngine,
            CodeWikiEngine,
        )

        _compile_engine = WikiCompileEngine(
            vault_root=wiki_path,
            claims_repo=None,
            wiki_repo=_wiki_repo,
            llm_router=_llm_router,
        )
        _archiver = QueryArchiver(wiki_root=_compile_engine.wiki_root)
        _wiki_linter = WikiLinter(
            wiki_root=_compile_engine.wiki_root,
            vault_root=wiki_path,
        )
        _concept_graph = ConceptGraphEngine(wiki_root=_compile_engine.wiki_root)
        # Wire concept graph into compiler for auto-inference after compile
        _compile_engine.attach_concept_graph(_concept_graph)
        _feedback_engine = FeedbackEngine(
            storage_path=wiki_path / ".saw" / "feedback.json"
        )
        _code_wiki_engine = CodeWikiEngine(
            wiki_root=_compile_engine.wiki_root,
            llm_router=_llm_router,
            code_graph_engine=_code_graph_engine,
        )
        logger.info("Compile-layer engines initialized")
    except Exception as e:
        logger.warning("Failed to initialize compile-layer engines: %s", e)

    # Register all tools via @mcp.tool decorators (import triggers registration)
    from saw.drivers.mcp.tools import register_all_tools, init_all_tools

    register_all_tools()
    init_all_tools(
        pipeline=_pipeline,
        query_engine=_query_engine,
        search=getattr(_query_engine, '_search', None),
        compiler=getattr(_query_engine, '_compiler', None),
        graph=getattr(_query_engine, '_graph', None),
        tree_mode=getattr(_query_engine, '_tree_mode', None),
        governor=_governor,
        detector=_detector,
        blast_radius=None,
        audit=None,
        learn_engine=_learn_engine,
        wiki_repo=_wiki_repo,
        write_queue=_write_queue,
        code_graph_engine=_code_graph_engine,
        compile_engine=_compile_engine,
        archiver=_archiver,
        wiki_linter=_wiki_linter,
        concept_graph=_concept_graph,
        feedback_engine=_feedback_engine,
        code_wiki_engine=_code_wiki_engine,
    )

    # Register resources and prompts
    from saw.drivers.mcp.resources import init_resources
    from saw.drivers.mcp.prompts import init_prompts

    init_resources(_wiki_repo, _query_engine)
    init_prompts(_wiki_repo)

    logger.info("MCP server initialized with %d tools", len(_list_registered_tools()))
    return mcp


def _list_registered_tools() -> list[str]:
    """List all registered MCP tool names."""
    try:
        # FastMCP exposes tools via _tool_manager
        if hasattr(mcp, '_tool_manager') and mcp._tool_manager:
            return list(mcp._tool_manager.tools.keys())
        if hasattr(mcp, 'tools'):
            return list(mcp.tools.keys()) if isinstance(mcp.tools, dict) else []
    except Exception:
        pass
    return []


def run_server(config: MCPConfig) -> None:
    """Run the MCP server.

    Args:
        config: MCP server configuration.
    """
    mcp.run(transport=config.transport)
