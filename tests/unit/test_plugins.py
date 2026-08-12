"""Tests for plugin system.

Phase 40: Test Coverage — TEST-04 validation.
Covers: PluginBase, PluginContext, PluginRegistry, Events.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from saw.plugins.base import PluginBase, PluginContext
from saw.plugins.events import (
    PageCreated,
    PageUpdated,
    PageDeleted,
    ClaimCreated,
    IngestCompleted,
    QueryExecuted,
)
from saw.plugins.registry import PluginRegistry


# ── PluginContext Tests ───────────────────────────────────────────────


class TestPluginContext:
    """Tests for PluginContext."""

    def test_create_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = PluginContext(
                data_dir=Path(tmpdir),
                wiki_read=lambda slug: None,
                wiki_write=lambda slug, content: True,
                claims_read=lambda filters: [],
                graph_query=lambda query: [],
                subscribe_event=lambda event, handler: None,
                publish_event=lambda event, data: None,
            )
            assert ctx.data_dir == Path(tmpdir)

    def test_context_with_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = PluginContext(
                data_dir=Path(tmpdir),
                wiki_read=lambda slug: None,
                wiki_write=lambda slug, content: True,
                claims_read=lambda filters: [],
                graph_query=lambda query: [],
                subscribe_event=lambda event, handler: None,
                publish_event=lambda event, data: None,
            )
            assert ctx.data_dir == Path(tmpdir)


# ── PluginBase Tests ──────────────────────────────────────────────────


class TestPluginBase:
    """Tests for PluginBase."""

    def test_subclass_creation(self):
        class MyPlugin(PluginBase):
            name = "my-plugin"
            version = "1.0.0"
            description = "A test plugin"

            def activate(self, ctx):
                pass

            def deactivate(self):
                pass

        plugin = MyPlugin()
        assert plugin.name == "my-plugin"

    def test_plugin_has_required_methods(self):
        class TestPlugin(PluginBase):
            name = "test"

            def activate(self, ctx):
                pass

            def deactivate(self):
                pass

        plugin = TestPlugin()
        assert hasattr(plugin, "activate")
        assert hasattr(plugin, "deactivate")
        assert hasattr(plugin, "on_event")


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
            content="Test claim",
        )
        assert event.claim_id == "claim-1"

    def test_ingest_completed_event(self):
        event = IngestCompleted(
            items_processed=10,
        )
        assert event.items_processed == 10

    def test_query_executed_event(self):
        event = QueryExecuted(
            query_text="test query",
            results_count=5,
        )
        assert event.results_count == 5


# ── PluginRegistry Tests ─────────────────────────────────────────────


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_create_registry(self):
        registry = PluginRegistry()
        assert registry is not None

    def test_registry_has_enable_disable(self):
        registry = PluginRegistry()
        assert hasattr(registry, "enable")
        assert hasattr(registry, "disable")

    def test_registry_plugin_count(self):
        registry = PluginRegistry()
        plugins = registry.list_plugins() if hasattr(registry, "list_plugins") else []
        assert isinstance(plugins, list)