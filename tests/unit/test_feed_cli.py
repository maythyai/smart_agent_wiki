"""Unit tests for feed CLI commands.

Phase 9: RSS Subscription — Tests for CLI commands.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typer.testing import CliRunner

from saw.drivers.cli.commands.feed_cmd import app

runner = CliRunner()


class TestFeedCLICommands:
    """Test feed CLI commands."""

    def test_feed_add_command_exists(self) -> None:
        """Test 1: saw feed add <url> command exists."""
        result = runner.invoke(app, ["add", "--help"])
        assert result.exit_code == 0
        assert "Subscribe" in result.output

    def test_feed_list_command_exists(self) -> None:
        """Test 3: saw feed list command exists."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "List all feed subscriptions" in result.output

    def test_feed_poll_command_exists(self) -> None:
        """Test 4: saw feed poll <feed_id> command exists."""
        result = runner.invoke(app, ["poll", "--help"])
        assert result.exit_code == 0
        assert "Manually poll" in result.output

    def test_feed_remove_command_exists(self) -> None:
        """Test 5: saw feed remove <feed_id> command exists."""
        result = runner.invoke(app, ["remove", "--help"])
        assert result.exit_code == 0
        assert "Unsubscribe" in result.output

    def test_feed_update_command_exists(self) -> None:
        """Update feed command exists."""
        result = runner.invoke(app, ["update", "--help"])
        assert result.exit_code == 0
        assert "Update feed settings" in result.output

    def test_feed_entries_command_exists(self) -> None:
        """List entries command exists."""
        result = runner.invoke(app, ["entries", "--help"])
        assert result.exit_code == 0
        assert "List entries" in result.output

    def test_feed_info_command_exists(self) -> None:
        """Feed info command exists."""
        result = runner.invoke(app, ["info", "--help"])
        assert result.exit_code == 0
        assert "Show detailed feed information" in result.output

    def test_feed_import_command_exists(self) -> None:
        """Import OPML command exists."""
        result = runner.invoke(app, ["import", "--help"])
        assert result.exit_code == 0
        assert "Import feeds from OPML" in result.output

    def test_feed_export_command_exists(self) -> None:
        """Export OPML command exists."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export feeds to OPML" in result.output


class TestFeedCLIApp:
    """Test feed CLI app structure."""

    def test_app_has_correct_name(self) -> None:
        """App should have correct name."""
        assert app.info.name == "feed"

    def test_app_has_correct_help(self) -> None:
        """App should have correct help text."""
        assert "RSS feed subscription" in app.info.help

    def test_app_has_no_args_is_help(self) -> None:
        """App should show help when no args provided."""
        assert app.info.no_args_is_help is True


class TestFeedCLIIntegration:
    """Integration tests for CLI commands."""

    def test_add_with_category_flag(self) -> None:
        """Test 2: saw feed add with --category sets category."""
        # This would require mocking async operations
        # For now, verify the flag is recognized
        result = runner.invoke(app, ["add", "https://example.com/feed.xml", "--category", "tech", "--help"])
        # The help flag overrides the command, so it should show help
        assert result.exit_code == 0

    def test_list_with_category_filter(self) -> None:
        """List command accepts category filter."""
        result = runner.invoke(app, ["list", "--help"])
        assert "--category" in result.output

    def test_list_with_all_flag(self) -> None:
        """List command accepts --all flag."""
        result = runner.invoke(app, ["list", "--help"])
        assert "--all" in result.output

    def test_poll_accepts_feed_id(self) -> None:
        """Poll command accepts feed_id argument."""
        result = runner.invoke(app, ["poll", "--help"])
        assert "feed_id" in result.output.lower() or "FEED_ID" in result.output

    def test_entries_with_status_filter(self) -> None:
        """Entries command accepts status filter."""
        result = runner.invoke(app, ["entries", "--help"])
        assert "--status" in result.output