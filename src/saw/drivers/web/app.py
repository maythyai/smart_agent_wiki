"""FastAPI Application Factory.

Per D-01: FastAPI server with RESTful API and WebSocket support.
Per D-02: Default port 8000.
Per D-03: CORS configuration for frontend development.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    from saw.engines.collaborate.orchestrator import CollaborateEngine
    from saw.engines.query.engine import QueryEngine
    from saw.write_queue.queue import SQLiteWriteQueue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle: startup/shutdown.

    Per D-04: Start WebSocket broadcaster on startup.
    """
    from saw.drivers.web.websocket import manager

    # Startup: start WebSocket broadcast task
    if hasattr(app.state, "event_bus") and app.state.event_bus is not None:
        manager.set_event_bus(app.state.event_bus)
        await manager.start_broadcaster()

    yield

    # Shutdown: cleanup resources
    await manager.stop_broadcaster()


def create_app(
    query: QueryEngine,
    collaborate: CollaborateEngine,
    write_queue: SQLiteWriteQueue,
    event_bus: Any = None,
    cors_origins: list[str] | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> FastAPI:
    """Create FastAPI application with injected dependencies.

    Per D-01: Application factory pattern for testability.
    Per D-02: Default port 8000.
    Per D-03: CORS configuration for frontend development.

    Args:
        query: Query engine for search/graph operations.
        collaborate: Collaboration engine for agent workflows.
        write_queue: Write queue for durable mutations.
        event_bus: Event bus for cross-engine communication (optional).
        cors_origins: Allowed CORS origins (default: localhost:3000 for dev).
        host: Server host address.
        port: Server port (default: 8000 per D-02).

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Smart Agent Wiki",
        version="1.1.0",
        description="Web API for knowledge management",
        lifespan=lifespan,
    )

    # Store engines in app.state for dependency injection
    app.state.query = query
    app.state.collaborate = collaborate
    app.state.write_queue = write_queue
    app.state.event_bus = event_bus
    app.state.host = host
    app.state.port = port

    # CORS configuration (per D-03)
    origins = cors_origins or ["http://localhost:3000", "http://127.0.0.1:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register error handlers (per RESEARCH.md Pattern 5)
    from saw.drivers.web.middleware.errors import register_exception_handlers

    register_exception_handlers(app)

    # SEC-08: Security headers middleware
    from saw.drivers.web.middleware.security import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware)

    # SEC-07: Audit logging middleware
    from saw.drivers.web.middleware.security import AuditLogMiddleware

    app.add_middleware(AuditLogMiddleware)

    # SEC-04: Input sanitization middleware
    from saw.drivers.web.middleware.security import InputSanitizerMiddleware

    app.add_middleware(InputSanitizerMiddleware)

    # SEC-03: Rate limiting middleware
    from saw.api.rate_limit import RateLimitMiddleware, RateLimitConfig

    rate_config = RateLimitConfig.from_env()
    if rate_config.enabled:
        app.add_middleware(RateLimitMiddleware, config=rate_config)

    # Register WebSocket route (per D-04)
    from saw.drivers.web.routes.websocket import router as ws_router

    app.include_router(ws_router, tags=["websocket"])

    # Register integration WebSocket route (per DASH-01, DASH-02)
    from saw.api.integrations_ws import router as integrations_ws_router

    app.include_router(integrations_ws_router, prefix="/ws", tags=["websocket"])

    # Register REST API routes
    from saw.drivers.web.routes.graph import router as graph_router
    from saw.drivers.web.routes.pages import router as pages_router
    from saw.drivers.web.routes.search import router as search_router
    from saw.drivers.web.routes.import_md import router as import_router
    from saw.drivers.web.routes.capture import router as capture_router
    from saw.drivers.web.routes.templates import router as templates_router
    from saw.drivers.web.routes.entity_types import router as entity_types_router

    app.include_router(graph_router, prefix="/api", tags=["graph"])
    app.include_router(pages_router, prefix="/api", tags=["pages"])
    app.include_router(search_router, prefix="/api", tags=["search"])
    app.include_router(import_router, prefix="/api", tags=["import"])
    app.include_router(capture_router, prefix="/api", tags=["capture"])
    app.include_router(templates_router, prefix="/api", tags=["templates"])
    app.include_router(entity_types_router, prefix="/api", tags=["entity-types"])

    # Register onboarding routes (Phase 55)
    from saw.drivers.web.routes.onboarding import router as onboarding_router
    app.include_router(onboarding_router)

    # Register timeline routes (Phase 56)
    from saw.drivers.web.routes.timeline import router as timeline_router
    app.include_router(timeline_router)

    # Register connector settings routes (Phase 18)
    from saw.api.connector_settings import router as connector_settings_router

    app.include_router(connector_settings_router, tags=["connector-settings"])

    # Register dashboard statistics routes (Phase 36)
    from saw.api.dashboard_stats import router as dashboard_stats_router

    app.include_router(dashboard_stats_router, tags=["dashboard"])

    # SEC-01: Authentication routes (Phase 39)
    from saw.drivers.web.routes.auth import router as auth_router

    app.include_router(auth_router)

    return app


def create_app_from_config(
    cors_origins: list[str] | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> FastAPI:
    """Factory for uvicorn --reload mode.

    Per D-02: Default port 8000.
    Loads configuration and creates app instance for development.
    """
    import sqlite3
    from pathlib import Path

    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch
    from saw.write_queue.queue import SQLiteWriteQueue

    # Try to load config from .saw/config.yaml
    try:
        import yaml

        config_path = Path(".saw/config.yaml")
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            db_path = Path(config.get("path", ".")) / ".saw" / "db" / "claims.db"
        else:
            db_path = Path(".saw/db/claims.db")
    except Exception:
        # Fallback to default path
        db_path = Path(".saw/db/claims.db")

    # Create write queue
    try:
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            write_queue = SQLiteWriteQueue(conn)
        else:
            # Use in-memory for non-existent DB
            conn = sqlite3.connect(":memory:")
            write_queue = SQLiteWriteQueue(conn)
    except Exception:
        conn = sqlite3.connect(":memory:")
        write_queue = SQLiteWriteQueue(conn)

    # Initialize QueryEngine with real repositories
    wiki_path = Path(".")
    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(wiki_path)

    search = FTS5Search(conn)
    compiler = ContextCompiler(claims_repo, wiki_repo, None)
    graph = GraphTraverse(claims_repo)
    compare_engine = CompareEngine(claims_repo, wiki_repo)
    tree_mode = TreeModeSearch(claims_repo)

    query_engine = QueryEngine(
        search=search,
        compiler=compiler,
        graph=graph,
        compare_engine=compare_engine,
        tree_mode=tree_mode,
        llm=None,  # Offline mode
        claims_repo=claims_repo,
        wiki_repo=wiki_repo,
        conn=conn,
    )

    # Startup: index wiki pages into FTS5 for search
    from saw.engines.query.wiki_indexer import WikiIndexer

    wiki_indexer = WikiIndexer(conn, wiki_repo)
    try:
        indexed = wiki_indexer.index_all()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Indexed {indexed} wiki pages into FTS5")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Wiki indexing failed: {e}")

    return create_app(
        query=query_engine,
        collaborate=None,
        write_queue=write_queue,
        cors_origins=cors_origins,
        host=host,
        port=port,
    )
