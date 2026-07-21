"""MCP server using FastMCP.

Per STACK.md: FastMCP==3.2.4
Per PITFALLS.md: Use async LiteLLM calls with timeouts.
"""
from __future__ import annotations

import logging
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


def create_server(wiki_path: Path, db_path: Path | None = None) -> FastMCP:
    """Create and configure MCP server with all tools registered.

    Initializes engines from the wiki path and registers all MCP tools.

    Args:
        wiki_path: Path to the wiki directory.
        db_path: Path to claims.db (default: wiki_path/.saw/db/claims.db).

    Returns:
        Configured FastMCP instance with all tools registered.
    """
    global _query_engine, _governor, _detector, _pipeline, _learn_engine, _wiki_repo, _write_queue

    # Resolve DB path
    if db_path is None:
        db_path = wiki_path / ".saw" / "db" / "claims.db"

    # Initialize engines
    try:
        from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
        from saw.adapters.storage.wiki_repository import WikiRepository
        from saw.write_queue.queue import SQLiteWriteQueue
        from saw.engines.query.engine import QueryEngine
        from saw.engines.query.search import FTS5Search
        from saw.engines.query.compiler import ContextCompiler
        from saw.engines.query.graph_traverse import GraphTraverse
        from saw.engines.query.compare import CompareEngine
        from saw.engines.query.tree_mode import TreeModeSearch
        from saw.engines.govern.governor import Governor
        from saw.engines.govern.contradiction import ContradictionDetector
        from saw.engines.govern.linter import Linter
        from saw.engines.ingest.pipeline import IngestPipeline

        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            claims_repo = SQLiteClaimsRepository(conn)
            wiki_repo = WikiRepository(wiki_path)

            search = FTS5Search(conn)
            compiler = ContextCompiler(claims_repo, wiki_repo, None)
            graph = GraphTraverse(claims_repo)
            compare_engine = CompareEngine(claims_repo, wiki_repo)
            tree_mode = TreeModeSearch(claims_repo)

            _query_engine = QueryEngine(
                search=search,
                compiler=compiler,
                graph=graph,
                compare_engine=compare_engine,
                tree_mode=tree_mode,
                llm=None,
                claims_repo=claims_repo,
                wiki_repo=wiki_repo,
                conn=conn,
            )

            _governor = Governor(claims_repo, wiki_repo)
            _detector = ContradictionDetector(claims_repo, None)
            _pipeline = IngestPipeline(claims_repo, wiki_repo)
            _wiki_repo = wiki_repo

            # Initialize write queue for MCP page mutations
            _write_queue = SQLiteWriteQueue(conn)
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