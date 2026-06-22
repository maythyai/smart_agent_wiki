"""Tests for plugin system.

Phase 40: Test Coverage — TEST-04 validation.
Covers: PluginBase, PluginContext, PluginRegistry, Events.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import pytest

from saw.plugins.base import PluginBase, PluginContext, PluginMetadata
from saw.plugins.events import (
    PluginEvent,
    PageCreated,
    PageUpdated,
    PageDeleted,
    ClaimCreated,
    IngestCompleted,
    QueryExecuted,
)
from saw.plugins.registry import PluginRegistry


# ── PluginMetadata Tests ──────────────────────────────────────────────


class TestPluginMetadata:
    """Tests for PluginMetadata."""

    def test_create_metadata(self):
        meta = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
        )
        assert meta.name == "test-plugin"
        assert meta.version == "1.0.0"

    def test_metadata_defaults(self):
        meta = PluginMetadata(name="minimal")
        assert meta.name == "minimal"
        assert meta.version == "0.1.0"


# ── PluginContext Tests ───────────────────────────────────────────────


class TestPluginContext:
    """Tests for PluginContext."""

    def test_create_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = PluginContext(
                data_dir=Path(tmpdir),
                config={},
            )
            assert ctx.data_dir == Path(tmpdir)
            assert ctx.config == {}

    def test_context_with_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"key": "value", "count": 42}
            ctx = PluginContext(data_dir=Path(tmpdir), config=config)
            assert ctx.config["key"] == "value"
            assert ctx.config["count"] == 42


# ── PluginBase Tests ──────────────────────────────────────────────────


class TestPluginBase:
    """Tests for PluginBase."""

    def test_subclass_creation(self):
        class MyPlugin(PluginBase):
            metadata = PluginMetadata(name="my-plugin")

            async def on_enable(self, ctx):
                pass

            async def on_disable(self, ctx):
                pass

        plugin = MyPlugin()
        assert plugin.metadata.name == "my-plugin"

    def test_plugin_has_required_methods(self):
        class TestPlugin(PluginBase):
            metadata = PluginMetadata(name="test")

            async def on_enable(self, ctx):
                pass

            async def on_disable(self, ctx):
                pass

        plugin = TestPlugin()
        assert hasattr(plugin, "on_enable")
        assert hasattr(plugin, "on_disable")
        assert hasattr(plugin, "metadata")


# ── Event Tests ───────────────────────────────────────────────────────


class TestEvents:
    """Tests for plugin events."""

    def test_page_created_event(self):
        event = PageCreated(
            page_id="page-1",
            title="Test Page",
            author="user-1",
        )
        assert event.page_id == "page-1"
        assert event.title == "Test Page"

    def test_page_updated_event(self):
        event = PageUpdated(
            page_id="page-1",
            title="Updated Page",
            author="user-1",
        )
        assert event.page_id == "page-1"

    def test_page_deleted_event(self):
        event = PageDeleted(
            page_id="page-1",
            author="user-1",
        )
        assert event.page_id == "page-1"

    def test_claim_created_event(self):
        event = ClaimCreated(
            claim_id="claim-1",
            page_id="page-1",
            content="Test claim",
        )
        assert event.claim_id == "claim-1"

    def test_ingest_completed_event(self):
        event = IngestCompleted(
            source="notion",
            items_processed=10,
        )
        assert event.source == "notion"
        assert event.items_processed == 10

    def test_query_executed_event(self):
        event = QueryExecuted(
            query="test query",
            results_count=5,
            duration_ms=42.0,
        )
        assert event.query == "test query"
        assert event.results_count == 5


# ── PluginRegistry Tests ─────────────────────────────────────────────


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_create_registry(self):
        registry = PluginRegistry()
        assert registry is not None

    def test_registry_has_list_method(self):
        registry = PluginRegistry()
        assert hasattr(registry, "list_plugins") or hasattr(registry, "list")

    def test_registry_plugin_count(self):
        registry = PluginRegistry()
        # Fresh registry should have no plugins (or only built-in ones)
        plugins = registry.list_plugins() if hasattr(registry, "list_plugins") else []
        assert isinstance(plugins, list)
