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

    # Register routes
    # Note: Routes will be added in subsequent tasks
    # from saw.drivers.web.routes import search, graph, pages, websocket
    # app.include_router(search.router, prefix="/api", tags=["search"])
    # app.include_router(graph.router, prefix="/api", tags=["graph"])
    # app.include_router(pages.router, prefix="/api", tags=["pages"])
    # app.include_router(websocket.router, tags=["websocket"])

    return app
