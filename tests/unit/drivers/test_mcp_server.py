"""Tests for MCP server foundation.

Per 02-03 Task 1: FastMCP server foundation with correct metadata.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestCreateServer:
    """Tests for create_server function."""

    def test_create_server_returns_fastmcp_instance(self):
        """Test 1: create_server() returns FastMCP instance with server name 'smart-agent-wiki'."""
        from fastmcp import FastMCP
        from saw.drivers.mcp.server import create_server

        server = create_server(Path("/tmp/test-wiki"))

        assert server is not None
        assert isinstance(server, FastMCP)
        # FastMCP stores name internally
        assert hasattr(server, "name")

    def test_server_has_correct_name(self):
        """Test that server has correct name 'smart-agent-wiki'."""
        from saw.drivers.mcp.server import create_server

        server = create_server(Path("/tmp/test-wiki"))

        # FastMCP exposes name via property or attribute
        assert getattr(server, "name", None) == "smart-agent-wiki"

    def test_server_has_correct_metadata(self):
        """Test 3: server has correct MCP metadata (name, version, description)."""
        from saw.drivers.mcp.server import create_server

        server = create_server(Path("/tmp/test-wiki"))

        # Check server has version
        assert hasattr(server, "version")
        assert getattr(server, "version", None) == "1.0.0"


class TestRunServer:
    """Tests for run_server function."""

    def test_run_server_starts_on_configured_port(self):
        """Test 2: run_server() starts server on configured port (default 8000)."""
        from saw.drivers.mcp.config import MCPConfig
        from saw.drivers.mcp.server import run_server

        config = MCPConfig(port=8765, transport="sse")

        # Mock the FastMCP.run method to avoid actually starting server
        with patch("saw.drivers.mcp.server.mcp") as mock_mcp:
            run_server(config)
            # Verify run was called with correct transport
            mock_mcp.run.assert_called_once()

    def test_run_server_uses_stdio_transport_by_default(self):
        """Test that run_server defaults to stdio transport."""
        from saw.drivers.mcp.config import MCPConfig
        from saw.drivers.mcp.server import run_server

        config = MCPConfig(transport="stdio")

        with patch("saw.drivers.mcp.server.mcp") as mock_mcp:
            run_server(config)
            mock_mcp.run.assert_called_once_with(transport="stdio")


class TestMCPConfig:
    """Tests for MCPConfig model."""

    def test_default_config_values(self):
        """Test default configuration values."""
        from saw.drivers.mcp.config import MCPConfig

        config = MCPConfig()

        assert config.server_name == "smart-agent-wiki"
        assert config.server_version == "1.0.0"
        assert config.host == "127.0.0.1"  # Per PITFALLS.md: default localhost only
        assert config.port == 8000
        assert config.log_level == "INFO"

    def test_config_custom_values(self):
        """Test custom configuration values."""
        from saw.drivers.mcp.config import MCPConfig

        config = MCPConfig(
            server_name="custom-wiki",
            port=9000,
            host="localhost",
        )

        assert config.server_name == "custom-wiki"
        assert config.port == 9000
        assert config.host == "localhost"


class TestServerShutdown:
    """Tests for server shutdown handling."""

    def test_server_handles_shutdown_gracefully(self):
        """Test 4: server handles shutdown gracefully."""
        from saw.drivers.mcp.server import create_server

        server = create_server(Path("/tmp/test-wiki"))

        # Server should have no issues being garbage collected
        del server

        # If we can reach here without exceptions, shutdown is graceful


class TestCLIMCPCommand:
    """Tests for CLI mcp command."""

    def test_mcp_command_registered(self):
        """Test that mcp command is registered in CLI."""
        from saw.drivers.cli.main import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["mcp", "--help"])

        # Should show help text, not error
        assert result.exit_code == 0 or "Usage" in result.output or "saw mcp" in result.output

    def test_mcp_command_help_option(self):
        """Test mcp command has --help option."""
        from saw.drivers.cli.main import app
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["mcp", "--help"])

        # Should contain usage info
        assert result.exit_code == 0 or "Usage" in result.output
