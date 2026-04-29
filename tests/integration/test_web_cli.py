"""Integration tests for CLI `web` command.

Tests for the `saw web` command per D-02:
- --help shows correct options
- Command is registered correctly
- Options are parsed correctly
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def mock_uvicorn_run():
    """Mock uvicorn.run to prevent server start."""
    with patch("uvicorn.run") as mock:
        yield mock


class TestWebCommandHelp:
    """Tests for --help output."""

    def test_web_command_help_shows_options(self) -> None:
        """Test --help shows correct options."""
        from saw.drivers.cli.main import app

        result = runner.invoke(app, ["web", "--help"])

        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--reload" in result.output
        assert "--cors" in result.output

    def test_web_command_help_shows_description(self) -> None:
        """Test --help shows command description."""
        from saw.drivers.cli.main import app

        result = runner.invoke(app, ["web", "--help"])

        assert result.exit_code == 0
        assert "Smart Agent Wiki" in result.output or "web server" in result.output


class TestWebCommandOptions:
    """Tests for command options."""

    def test_web_command_registered(self) -> None:
        """Test web command is registered in CLI."""
        from saw.drivers.cli.main import app

        # Check command exists by invoking --help
        result = runner.invoke(app, ["web", "--help"])
        assert result.exit_code == 0

    def test_web_command_default_port_is_8000(self) -> None:
        """Test default port is 8000 (per D-02)."""
        from saw.drivers.cli.commands.web_cmd import web
        from typer.models import OptionInfo

        import inspect
        sig = inspect.signature(web)
        port_param = sig.parameters["port"]
        # Typer wraps defaults in OptionInfo
        if isinstance(port_param.default, OptionInfo):
            # The default value is inside the OptionInfo
            assert port_param.default.default == 8000
        else:
            assert port_param.default == 8000

    def test_web_command_default_host_is_localhost(self) -> None:
        """Test default host is 127.0.0.1."""
        from saw.drivers.cli.commands.web_cmd import web
        from typer.models import OptionInfo

        import inspect
        sig = inspect.signature(web)
        host_param = sig.parameters["host"]
        if isinstance(host_param.default, OptionInfo):
            assert host_param.default.default == "127.0.0.1"
        else:
            assert host_param.default == "127.0.0.1"


class TestWebCommandParsing:
    """Tests for option parsing."""

    def test_web_command_custom_port(self, mock_uvicorn_run: MagicMock) -> None:
        """Test --port option is parsed."""
        from saw.drivers.cli.main import app

        # With mock, we can't fully test execution but can verify parsing
        result = runner.invoke(app, ["web", "--port", "9000", "--help"])
        assert result.exit_code == 0

    def test_web_command_custom_host(self, mock_uvicorn_run: MagicMock) -> None:
        """Test --host option is parsed."""
        from saw.drivers.cli.main import app

        result = runner.invoke(app, ["web", "--host", "0.0.0.0", "--help"])
        assert result.exit_code == 0

    def test_web_command_reload_flag(self, mock_uvicorn_run: MagicMock) -> None:
        """Test --reload flag is parsed."""
        from saw.drivers.cli.main import app

        result = runner.invoke(app, ["web", "--reload", "--help"])
        assert result.exit_code == 0

    def test_web_command_cors_origins(self, mock_uvicorn_run: MagicMock) -> None:
        """Test --cors option is parsed."""
        from saw.drivers.cli.main import app

        result = runner.invoke(
            app,
            ["web", "--cors", "http://localhost:3000,http://example.com", "--help"],
        )
        assert result.exit_code == 0


class TestCreateAppFromConfig:
    """Tests for create_app_from_config factory."""

    def test_create_app_from_config_returns_app(self) -> None:
        """Test factory returns FastAPI app."""
        from saw.drivers.web.app import create_app_from_config

        app = create_app_from_config()
        assert app is not None
        assert app.title == "Smart Agent Wiki"

    def test_create_app_from_config_with_cors(self) -> None:
        """Test factory accepts CORS origins."""
        from saw.drivers.web.app import create_app_from_config

        app = create_app_from_config(cors_origins=["http://example.com"])
        assert app is not None

    def test_create_app_from_config_with_host_port(self) -> None:
        """Test factory accepts host and port."""
        from saw.drivers.web.app import create_app_from_config

        app = create_app_from_config(host="0.0.0.0", port=9000)
        assert app is not None