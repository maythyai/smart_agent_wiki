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

# M-18: single source of truth for the version (pyproject.toml). Previously
# the app advertised 1.1.0, /health 2.0.0, the Dockerfile 3.4.0, and pyproject
# 1.0.1 — four different numbers.
try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("smart-agent-wiki")
except Exception:  # pragma: no cover — not installed
    __version__ = "0.0.0"

if TYPE_CHECKING:
    from saw.engines.collaborate.orchestrator import CollaborateEngine
    from saw.engines.query.engine import QueryEngine
    from saw.write_queue.queue import SQLiteWriteQueue


def _recover_stranded_workflows(conn) -> int:
    """HI-9: mark workflow executions left 'running' by a crash as 'interrupted'.

    Returns the count of recovered rows. Safe to call on a fresh DB (the
    workflow_executions table is created by migration v4).
    """
    try:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        with conn:
            cur = conn.execute(
                "UPDATE workflow_executions SET status='interrupted', "
                "updated_at=?, finished_at=? WHERE status='running'",
                (now, now),
            )
            return cur.rowcount
    except sqlite3.Error:
        return 0


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

    # CR-3 / HI-7: recover stranded 'processing' ops and drain pending so
    # writes are not lost across restarts. HI-7: a recurring background task
    # also re-runs recover() every 60s to reset ops stranded by a mid-flight
    # crash (process killed between mark_processing and mark_done).
    _wq = getattr(app.state, "write_queue", None)
    _disp = getattr(_wq, "_dispatcher", None) if _wq else None
    if _disp is not None:
        import asyncio as _asyncio
        await _asyncio.to_thread(_disp.recover)
        await _asyncio.to_thread(_disp.dispatch_pending)

        async def _recover_loop():
            while True:
                try:
                    await _asyncio.sleep(60)
                    await _asyncio.to_thread(_disp.recover)
                except _asyncio.CancelledError:
                    break
                except Exception:
                    pass

        app.state._recover_task = _asyncio.create_task(_recover_loop())

        # HI-9: mark workflow executions stranded in 'running' (from a previous
        # crash) as 'interrupted' so they are visible, not silently lost.
        _db_conn = getattr(_wq, "_conn", None) if _wq else None
        if _db_conn is not None:
            await _asyncio.to_thread(_recover_stranded_workflows, _db_conn)

        # HI-5: register default connectors so the connector API endpoints no
        # longer 404 (ConnectorRegistry singleton is populated at startup).
        try:
            from saw.connectors.bootstrap import register_default_connectors
            from saw.connectors.registry import ConnectorRegistry
            await _asyncio.to_thread(
                register_default_connectors, ConnectorRegistry()
            )
        except Exception as _e:  # pragma: no cover — never block `saw web`
            _logging = __import__("logging")
            _logging.getLogger(__name__).warning(
                "Connector bootstrap failed: %s", _e
            )

    yield

    # Shutdown: cleanup resources
    _recover_task = getattr(app.state, "_recover_task", None)
    if _recover_task is not None:
        _recover_task.cancel()
        try:
            await _recover_task
        except Exception:
            pass
    await manager.stop_broadcaster()


def create_app(
    query: QueryEngine,
    collaborate: CollaborateEngine,
    write_queue: SQLiteWriteQueue,
    event_bus: Any = None,
    wiki_repo: Any = None,
    cors_origins: list[str] | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    auth_mode: str = "local",
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
        auth_mode: ``"local"`` (default; trust local requests, honour JWT if
            supplied) or ``"team"`` (require a valid JWT on protected
            routes). SEC-01/SEC-02 wiring (C1).

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Smart Agent Wiki",
        version=__version__,
        description="Web API for knowledge management",
        lifespan=lifespan,
    )

    # Store engines in app.state for dependency injection
    app.state.query = query
    app.state.collaborate = collaborate
    app.state.write_queue = write_queue
    app.state.event_bus = event_bus
    # wiki_repo is consumed by onboarding/timeline routes (get_wiki_repo);
    # previously it was constructed in create_app_from_config but never
    # mounted, so those endpoints raised 500. Fall back to the query
    # engine's wiki repo if the caller did not pass one explicitly.
    app.state.wiki_repo = wiki_repo if wiki_repo is not None else getattr(query, "_wiki_repo", None)
    app.state.host = host
    app.state.port = port
    # C1: auth mode consumed by get_current_user() on protected routes.
    app.state.auth_mode = auth_mode

    # DEF-4: local mode trusts all requests as admin by design (single-user,
    # local-first). Surface this loudly at startup so it is never mistaken
    # for a hardened deployment. Team mode (require JWT) is the production
    # setting.
    if auth_mode == "local":
        import logging as _auth_logging

        _auth_logging.getLogger(__name__).warning(
            "SAW is running in auth_mode='local': unauthenticated requests "
            "are trusted as admin. This is fine for single-user local use "
            "but NOT for any networked deployment — set auth_mode='team'."
        )

    # P1: Cedar policy engine (optional — if a .cedar policy file exists,
    # resource-level Cedar policy checks are available alongside RBAC).
    from pathlib import Path as _Path
    _cedar_path = _Path(".saw/policies/saw.cedar")
    if _cedar_path.exists():
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine
        app.state.cedar = CedarPolicyEngine(_cedar_path)
    else:
        app.state.cedar = None

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

    # HI-16: request-id propagation (must run before audit/log middleware so
    # every log line carries the correlation ID). init_observability also
    # configures JSON logging (team mode) and optional Sentry.
    from saw.drivers.web.middleware.observability import (
        RequestContextMiddleware,
        init_observability,
    )
    init_observability(auth_mode)
    app.add_middleware(RequestContextMiddleware)

    # SEC-07: Audit logging middleware
    from saw.drivers.web.middleware.security import AuditLogMiddleware

    app.add_middleware(AuditLogMiddleware)

    # SEC-04: Input sanitization middleware
    from saw.drivers.web.middleware.security import InputSanitizerMiddleware

    app.add_middleware(InputSanitizerMiddleware)

    # SEC-03: Rate limiting middleware
    from saw.api.rate_limit import RateLimitMiddleware, RateLimitConfig

    rate_config = RateLimitConfig.from_env()
    # P2: wire API key verification into rate limiting (so that
    # valid ApiKey headers count against the key's rate limit, not
    # the global/default limit).
    api_key_func = None
    try:
        from saw.api.keys import verify_api_key_for_rate_limit
        api_key_func = verify_api_key_for_rate_limit
    except ImportError:
        pass

    if rate_config.enabled:
        app.add_middleware(RateLimitMiddleware, config=rate_config, get_api_key_func=api_key_func)

    # SEC-01/02: auth dependency attached to protected routers (C1).
    from fastapi import Depends
    from saw.drivers.web.middleware.security import (
        get_current_user,
        require_role,
    )

    # Common "authenticated" dependency for all protected routes.
    auth_dep = [Depends(get_current_user)]
    # Connector settings also require an editor/admin role (writes infra).
    connector_auth_dep = [Depends(get_current_user), Depends(require_role("admin", "editor"))]

    # Register WebSocket route (per D-04)
    from saw.drivers.web.routes.websocket import router as ws_router

    app.include_router(ws_router, tags=["websocket"])

    # Register integration WebSocket route (per DASH-01, DASH-02)
    from saw.api.integrations_ws import router as integrations_ws_router

    app.include_router(integrations_ws_router, prefix="/ws", tags=["websocket"])

    # Register REST API routes (C1: protected with get_current_user)
    from saw.drivers.web.routes.graph import router as graph_router
    from saw.drivers.web.routes.pages import router as pages_router
    from saw.drivers.web.routes.search import router as search_router
    from saw.drivers.web.routes.import_md import router as import_router
    from saw.drivers.web.routes.capture import router as capture_router
    from saw.drivers.web.routes.templates import router as templates_router
    from saw.drivers.web.routes.entity_types import router as entity_types_router

    app.include_router(graph_router, prefix="/api", tags=["graph"], dependencies=auth_dep)
    app.include_router(pages_router, prefix="/api", tags=["pages"], dependencies=auth_dep)
    app.include_router(search_router, prefix="/api", tags=["search"], dependencies=auth_dep)
    app.include_router(import_router, prefix="/api", tags=["import"], dependencies=auth_dep)
    app.include_router(capture_router, prefix="/api", tags=["capture"], dependencies=auth_dep)
    app.include_router(templates_router, prefix="/api", tags=["templates"], dependencies=auth_dep)
    app.include_router(entity_types_router, prefix="/api", tags=["entity-types"], dependencies=auth_dep)

    # Register onboarding routes (Phase 55)
    from saw.drivers.web.routes.onboarding import router as onboarding_router
    app.include_router(onboarding_router, dependencies=auth_dep)

    # Register timeline routes (Phase 56)
    from saw.drivers.web.routes.timeline import router as timeline_router
    app.include_router(timeline_router, dependencies=auth_dep)

    # Register connector settings routes (Phase 18) — editor+ only
    from saw.api.connector_settings import router as connector_settings_router

    app.include_router(connector_settings_router, tags=["connector-settings"], dependencies=connector_auth_dep)

    # Register dashboard statistics routes (Phase 36) — authenticated
    from saw.api.dashboard_stats import router as dashboard_stats_router

    app.include_router(dashboard_stats_router, tags=["dashboard"], dependencies=auth_dep)

    # H1-1: register previously-unwired api/ routers (all already have
    # their own /api/v1/... prefix). Public read endpoints get auth_dep;
    # webhook/inbound endpoints are exempt (they use HMAC verification).
    from saw.api.feeds import router as feeds_router
    from saw.api.health import router as health_router
    from saw.api.oauth_callback import router as oauth_router
    from saw.api.webhook_inbound import router as webhook_inbound_router
    from saw.api.sync import router as sync_router
    from saw.api.integrations import router as integrations_router

    app.include_router(health_router)  # public health check

    # Public Kubernetes-style probes + /metrics (Prometheus). These live on
    # root paths (/health, /health/live, /health/ready, /metrics) and were
    # previously defined but never mounted.
    from saw.drivers.web.health import router as web_health_router

    app.include_router(web_health_router)
    app.include_router(feeds_router, dependencies=auth_dep)
    # OAuth authorize/callback are third-party redirect entry points: the
    # user is NOT yet authenticated when they hit them (that is the whole
    # point of OAuth), so they must be public. (GET /platforms is also fine
    # to leave public.) Previously gated behind auth_dep, which made every
    # OAuth callback return 401.
    app.include_router(oauth_router)
    app.include_router(webhook_inbound_router)  # HMAC-verified, no JWT required
    app.include_router(sync_router, dependencies=auth_dep)
    app.include_router(integrations_router, dependencies=auth_dep)

    # Register connector-specific routers (notion, notion_sync, github,
    # github_webhook, logseq). These define their own prefixes. notion and
    # notion_sync import cleanly; github was fixed to use the shared
    # session dependency. logseq requires the optional ``watchdog`` package,
    # so its registration is guarded — a missing optional dependency must not
    # prevent the rest of the app from starting.
    from saw.api.notion import get_notion_router
    from saw.api.notion_sync import get_notion_sync_router

    app.include_router(get_notion_router(), dependencies=auth_dep)
    app.include_router(get_notion_sync_router(), dependencies=auth_dep)

    import logging as _logging
    _app_logger = _logging.getLogger(__name__)

    try:
        from saw.api.github import router as github_router
        app.include_router(github_router, dependencies=auth_dep)
    except ImportError as _e:  # pragma: no cover — optional connector deps
        _app_logger.warning("GitHub connector router not registered: %s", _e)

    try:
        from saw.api.github_webhook import router as github_webhook_router
        app.include_router(github_webhook_router)  # HMAC-verified, no JWT
    except ImportError as _e:  # pragma: no cover
        _app_logger.warning("GitHub webhook router not registered: %s", _e)

    try:
        from saw.api.logseq import router as logseq_router
        app.include_router(logseq_router, dependencies=auth_dep)
    except ImportError as _e:  # pragma: no cover — requires watchdog
        _app_logger.warning("Logseq connector router not registered: %s", _e)


    # H1-2: govern API routes (claims, contradictions, verify, lint,
    # blast-radius, status) — authenticated
    from saw.api.routes.govern import router as govern_router
    app.include_router(govern_router, dependencies=auth_dep)

    # H1-2: impact analysis routes (pre-existing, previously unregistered)
    from saw.api.routes.impact import router as impact_router
    app.include_router(impact_router, dependencies=auth_dep)

    # H1-3: query / ingest / learn API routes
    from saw.api.routes.query_ingest_learn import router as qil_router
    app.include_router(qil_router, dependencies=auth_dep)

    # H1-4: collaborate / workflows API routes
    from saw.api.routes.collaborate import router as collaborate_api_router
    app.include_router(collaborate_api_router, dependencies=auth_dep)

    # SEC-01: Authentication routes (Phase 39) — public (login/register)
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

    # Create write queue. check_same_thread=False: the shared connection is
    # touched by the WriteQueue worker thread, by request-threadpool sync
    # endpoints, and by background workflow tasks that run QueryEngine calls
    # via a single-worker executor (see api/routes/collaborate.py). Serializing
    # query work in that executor is what keeps it safe; this flag removes the
    # hard ProgrammingError that previously aborted every local-mode workflow.
    # CR-4: fail fast if the claims DB cannot be opened. The previous
    # ``except Exception → :memory:`` fallback silently lost every write on
    # restart. sqlite3.connect creates the file on disk when missing, so the
    # in-memory branch was both unnecessary and dangerous.
    # Test isolation (infra): under pytest, use an in-memory DB so concurrent
    # tests don't contend on the on-disk claims.db (which caused fcntl "database
    # is locked" hangs when leaked connections stacked up). Each call gets its
    # own isolated in-memory DB via the single shared conn.
    import sys as _sys
    _test_mode = "pytest" in _sys.modules

    if _test_mode:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        # PRAGMAs: WAL for concurrent readers + busy_timeout so concurrent
        # access (e.g. a test run holding the DB) waits instead of raising
        # "database is locked" immediately.
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA foreign_keys=ON")
        except sqlite3.Error:
            pass
    write_queue = SQLiteWriteQueue(conn)

    # Initialize QueryEngine with real repositories
    wiki_path = Path(".")
    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(wiki_path)

    search = FTS5Search(conn)
    compiler = ContextCompiler(claims_repo, wiki_repo, search, conn)
    graph = GraphTraverse(conn)
    compare_engine = CompareEngine(claims_repo, wiki_repo)
    tree_mode = TreeModeSearch(wiki_repo, claims_repo, conn)

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

    # Startup: index wiki pages into FTS5 for search. Skipped under pytest
    # (test mode uses an in-memory DB + scanning the cwd project root is slow
    # and irrelevant for app-factory tests).
    from saw.engines.query.wiki_indexer import WikiIndexer

    wiki_indexer = WikiIndexer(conn, wiki_repo)
    if not _test_mode:
        try:
            indexed = wiki_indexer.index_all()
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Indexed {indexed} wiki pages into FTS5")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Wiki indexing failed: {e}")

    # DEF-1: wire a real CollaborateEngine so the 6 agents are actually
    # registered and the collaborate/workflow API's execute_workflow branch
    # is reachable. Previously create_app_from_config passed collaborate=None,
    # which left app.state.collaborate None and every workflow request falling
    # back to the stub "_run_workflow" path (returning "(No source material
    # found; stub synthesis.)"). llm_router=None matches the QueryEngine's
    # offline mode; agents then use their heuristic fallbacks (no silent stub).
    # HI-2: instantiate the in-process event bus early so it is available to
    # the CollaborateEngine, the Write Queue dispatcher, and create_app — even
    # if any of those wirings fail. Previously event_bus was always None, so
    # workflow progress events were dropped, the WebSocket broadcaster never
    # started, and plugin events had no delivery mechanism.
    from saw.plugins.event_bus import InMemoryEventBus
    _event_bus = InMemoryEventBus()

    collaborate_engine = None
    try:
        from saw.engines.collaborate.agents import build_default_agents
        from saw.engines.collaborate.a2a_protocol import A2AAdapter
        from saw.engines.collaborate.dispatcher import AgentDispatcher
        from saw.engines.collaborate.orchestrator import CollaborateEngine
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor

        _collab_agents = build_default_agents(llm_router=None)
        _dispatcher = AgentDispatcher(llm_router=None, agents=_collab_agents)
        _a2a = A2AAdapter(
            agents=_collab_agents,
            audit_signer=None,
            dispatcher=_dispatcher,
        )
        _workflow_executor = WorkflowExecutor(
            dispatcher=_dispatcher,
            a2a_adapter=_a2a,
            governor=None,
            event_bus=_event_bus,
            conn=conn,
        )
        collaborate_engine = CollaborateEngine(
            dispatcher=_dispatcher,
            a2a_adapter=_a2a,
            workflow_executor=_workflow_executor,
            policy_engine=None,
        )
    except Exception as e:  # pragma: no cover — defensive: never block `saw web`
        import logging

        logging.getLogger(__name__).warning(
            "CollaborateEngine wiring failed (%s); collaborate features will "
            "be unavailable. Run `saw web` with a configured LLM for full "
            "agent support.", e,
        )

    # CR-3: wire the Write Queue dispatcher so web writes reach the sinks.
    # Previously enqueue_atomic enqueued but nothing dispatched — every web
    # write was silently lost. Recover any ops stranded in 'processing' from
    # a previous crash before serving.
    try:
        from saw.write_queue.dispatcher import Dispatcher
        from saw.write_queue.sinks.wiki_sink import WikiSink
        from saw.write_queue.sinks.fts5_sink import FTS5Sink
        from saw.write_queue.sinks.claims_sink import ClaimsSink
        from saw.write_queue.sinks.graph_sink import GraphSink
        from saw.write_queue.sinks.contradictions_sink import ContradictionsSink
        _dispatcher = Dispatcher(
            write_queue,
            sinks=[
                WikiSink(wiki_repo),
                FTS5Sink(conn),
                ClaimsSink(claims_repo),
                GraphSink(conn),
                ContradictionsSink(conn),
            ],
            event_bus=_event_bus,
        )
        write_queue.attach_dispatcher(_dispatcher)
        _dispatcher.recover()
    except Exception as _e:  # pragma: no cover — never block `saw web`
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "Write Queue dispatcher wiring failed: %s", _e
        )

    # CR-2: resolve auth_mode — never default to unauthenticated "local" for a
    # networked bind. SAW_AUTH_MODE env → .saw/config.yaml → "local" (loopback only).
    import os as _os
    _auth_mode = _os.environ.get("SAW_AUTH_MODE")
    if not _auth_mode:
        try:
            import yaml as _yaml
            _cfg_path = Path(".saw/config.yaml")
            if _cfg_path.exists():
                with open(_cfg_path, encoding="utf-8") as _f:
                    _auth_mode = (_yaml.safe_load(_f) or {}).get("auth_mode")
        except Exception:
            pass
    _auth_mode = _auth_mode or "local"
    _networked = host not in ("127.0.0.1", "localhost", "::1")
    if (
        _auth_mode == "local"
        and _networked
        and _os.environ.get("SAW_ALLOW_UNAUTH_NETWORK") != "1"
    ):
        raise RuntimeError(
            "Refusing to start in auth_mode='local' on non-loopback host "
            f"({host}): this would expose the full admin API unauthenticated. "
            "Set SAW_AUTH_MODE=team (and configure JWT) or bind to 127.0.0.1. "
            "Override with SAW_ALLOW_UNAUTH_NETWORK=1."
        )

    app = create_app(
        query=query_engine,
        collaborate=collaborate_engine,
        write_queue=write_queue,
        event_bus=_event_bus,
        wiki_repo=wiki_repo,
        cors_origins=cors_origins,
        host=host,
        port=port,
        auth_mode=_auth_mode,
    )

    # HI-3: wire the Govern engine so govern API routes don't return 503.
    # Previously app.state.govern was never set, so _contradiction_detector
    # raised 503 for every govern endpoint.
    try:
        from saw.engines.govern.governor import Governor
        app.state.govern = Governor(
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            llm_router=None,
        )
    except Exception as _e:  # pragma: no cover — never block `saw web`
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "Governor wiring failed: %s", _e
        )
        app.state.govern = None

    # HI-4: discover + enable user plugins, wiring their event hooks to the
    # in-process event bus. Previously PluginRegistry was only used by the
    # `saw plugin` CLI; the web runtime never loaded plugins, so the 6 plugin
    # event types (PageCreated/PageUpdated/...) had no delivery mechanism.
    try:
        from pathlib import Path as _Path
        from saw.plugins.registry import PluginRegistry
        from saw.plugins.base import PluginContext

        _plugin_reg = PluginRegistry()
        _plugin_reg.discover()
        _plugin_data_dir = _Path(".saw") / "plugin_data"
        _plugin_data_dir.mkdir(parents=True, exist_ok=True)

        def _subscribe_event(event_type, handler):
            _event_bus.add_subscriber(event_type, handler)

        def _publish_event(event_type, payload=None):
            evt = payload if payload is not None else {"type": event_type}
            if isinstance(evt, dict) and "type" not in evt:
                evt = {"type": event_type, **evt}
            _event_bus.publish_nowait(evt)

        _plugin_ctx = PluginContext(
            data_dir=_plugin_data_dir,
            wiki_read=lambda slug=None: (wiki_repo.read(slug) if wiki_repo else None),
            wiki_write=lambda *a, **k: False,
            claims_read=lambda *a, **k: [],
            graph_query=lambda *a, **k: [],
            subscribe_event=_subscribe_event,
            publish_event=_publish_event,
        )
        for _pname in list(_plugin_reg.metadata.keys()):
            _plugin_reg.enable(_pname, _plugin_ctx)
        app.state.plugins = _plugin_reg
    except Exception as _e:  # pragma: no cover — never block `saw web`
        import logging as _logging
        _logging.getLogger(__name__).warning("Plugin bootstrap failed: %s", _e)
        app.state.plugins = None

    return app
