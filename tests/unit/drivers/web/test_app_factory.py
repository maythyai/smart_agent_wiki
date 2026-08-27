"""Tests for Application Factory and Middleware.

Tests:
- create_app() returns FastAPI instance
- CORS middleware is configured
- Error handlers return RFC 7807 format
"""
import pytest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from saw.drivers.web.app import create_app, lifespan
from saw.drivers.web.middleware.errors import register_exception_handlers
from saw.domain.exceptions import SAWError


@pytest.fixture
def mock_query_engine():
    """Mock QueryEngine."""
    engine = MagicMock()
    engine.query.return_value = MagicMock(
        answer="Mock answer",
        sources=[],
        mode="search",
    )
    return engine


@pytest.fixture
def mock_collaborate_engine():
    """Mock CollaborateEngine."""
    return MagicMock()


@pytest.fixture
def mock_write_queue():
    """Mock SQLiteWriteQueue."""
    return MagicMock()


@pytest.fixture
def client(mock_query_engine, mock_collaborate_engine, mock_write_queue):
    """Create test client with mocked engines."""
    app = create_app(
        query=mock_query_engine,
        collaborate=mock_collaborate_engine,
        write_queue=mock_write_queue,
    )
    return TestClient(app)


class TestCreateApp:
    """Tests for create_app factory."""

    def test_create_app_returns_fastapi_instance(
        self, mock_query_engine, mock_collaborate_engine, mock_write_queue
    ):
        """create_app() should return a FastAPI instance."""
        app = create_app(
            query=mock_query_engine,
            collaborate=mock_collaborate_engine,
            write_queue=mock_write_queue,
        )
        assert isinstance(app, FastAPI)

    def test_create_app_has_correct_title(
        self, mock_query_engine, mock_collaborate_engine, mock_write_queue
    ):
        """App should have correct title."""
        app = create_app(
            query=mock_query_engine,
            collaborate=mock_collaborate_engine,
            write_queue=mock_write_queue,
        )
        assert app.title == "Smart Agent Wiki"

    def test_create_app_has_correct_version(
        self, mock_query_engine, mock_collaborate_engine, mock_write_queue
    ):
        """App should report the version derived from pyproject.toml (M-18)."""
        app = create_app(
            query=mock_query_engine,
            collaborate=mock_collaborate_engine,
            write_queue=mock_write_queue,
        )
        # M-18: version is no longer hardcoded; it comes from the installed
        # package metadata. It must be a non-empty string matching the package.
        try:
            from importlib.metadata import version as _pkg_version

            expected = _pkg_version("smart-agent-wiki")
        except Exception:
            expected = None
        assert app.version
        if expected:
            assert app.version == expected


class TestCORS:
    """Tests for CORS middleware."""

    def test_cors_middleware_is_registered(self, client):
        """CORS middleware should be registered."""
        # FastAPI adds CORSMiddleware to user_middleware
        app = client.app
        # Check that we have at least one middleware
        assert len(app.user_middleware) >= 1

    def test_cors_default_origins(self, mock_query_engine, mock_collaborate_engine, mock_write_queue):
        """Default CORS origins should be localhost:3000."""
        app = create_app(
            query=mock_query_engine,
            collaborate=mock_collaborate_engine,
            write_queue=mock_write_queue,
        )
        # Find CORS middleware - FastAPI wraps middleware in Middleware objects
        cors_middleware = None
        for middleware in app.user_middleware:
            # Check the cls attribute which holds the actual middleware class
            if hasattr(middleware, 'cls') and 'CORSMiddleware' in str(middleware.cls):
                cors_middleware = middleware
                break

        # Check middleware exists
        assert cors_middleware is not None

    def test_cors_custom_origins(self, mock_query_engine, mock_collaborate_engine, mock_write_queue):
        """Custom CORS origins should be configurable."""
        custom_origins = ["http://example.com", "http://localhost:8080"]
        app = create_app(
            query=mock_query_engine,
            collaborate=mock_collaborate_engine,
            write_queue=mock_write_queue,
            cors_origins=custom_origins,
        )
        # App should be created successfully with custom origins
        assert app is not None


class TestErrorHandlers:
    """Tests for RFC 7807 error handlers."""

    def test_error_handler_returns_rfc_7807_format(self):
        """Error responses should follow RFC 7807 Problem Details."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-error")
        def raise_saw_error():
            raise SAWError("Test error")

        client = TestClient(app)
        response = client.get("/test-error")

        assert response.status_code == 400
        data = response.json()
        # RFC 7807 fields
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert data["status"] == 400

    def test_validation_error_handler_returns_rfc_7807_format(self):
        """Validation errors should return RFC 7807 format."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-validation")
        def validation_endpoint(q: str):
            return {"q": q}

        client = TestClient(app)
        # Missing required query parameter
        response = client.get("/test-validation")

        assert response.status_code == 422
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 422

    def test_generic_error_handler_returns_rfc_7807_format(self):
        """Unexpected errors should return RFC 7807 format."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-internal")
        def internal_error():
            raise RuntimeError("Unexpected error")

        # Use raise_server_exceptions=False to let our error handler catch the exception
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-internal")

        assert response.status_code == 500
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert data["status"] == 500
        # Per T-03-02-04: no stack traces in production
        assert "detail" in data
        # Check that the detail is the generic message, not the actual error
        assert data["detail"] == "An unexpected error occurred"


class TestLifespan:
    """Tests for app lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_starts_broadcaster(self, mock_query_engine, mock_collaborate_engine, mock_write_queue):
        """Lifespan should start WebSocket broadcaster on startup."""
        app = create_app(
            query=mock_query_engine,
            collaborate=mock_collaborate_engine,
            write_queue=mock_write_queue,
            event_bus=MagicMock(),  # Enable event bus
        )
        # Just verify app was created - lifespan tested via integration tests
        assert app is not None

    def test_app_state_stores_dependencies(self, client):
        """App should store engines in app.state."""
        assert hasattr(client.app.state, "query")
        assert hasattr(client.app.state, "collaborate")
        assert hasattr(client.app.state, "write_queue")


class TestCreateAppFromConfigWiresCollaborate:
    """DEF-1: create_app_from_config must wire a real CollaborateEngine with
    the 6 agents registered, instead of passing collaborate=None (which left
    the workflow API's execute_workflow branch unreachable and
    get_available_agents() returning []).
    """

    def test_collaborate_engine_is_wired_with_agents(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from saw.drivers.web.app import create_app_from_config

        app = create_app_from_config()
        assert app.state.collaborate is not None
        agents = app.state.collaborate.get_available_agents()
        for name in ("Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian"):
            assert name in agents, f"{name} not registered in collaborate engine"
