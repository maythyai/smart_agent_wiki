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

    # Register WebSocket route (per D-04)
    from saw.drivers.web.routes.websocket import router as ws_router

    app.include_router(ws_router, tags=["websocket"])

    # Register REST API routes
    from saw.drivers.web.routes.graph import router as graph_router
    from saw.drivers.web.routes.pages import router as pages_router
    from saw.drivers.web.routes.search import router as search_router

    app.include_router(graph_router, prefix="/api", tags=["graph"])
    app.include_router(pages_router, prefix="/api", tags=["pages"])
    app.include_router(search_router, prefix="/api", tags=["search"])

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

    from saw.write_queue.queue import SQLiteWriteQueue

    # Try to load config from .saw/config.yaml
    try:
        from pathlib import Path

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

    # Create minimal write queue (engines initialized in lifespan)
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

    return create_app(
        query=None,  # Lazy initialization in lifespan
        collaborate=None,
        write_queue=write_queue,
        cors_origins=cors_origins,
        host=host,
        port=port,
    )
