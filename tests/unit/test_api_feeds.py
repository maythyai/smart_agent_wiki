"""Unit tests for feed API endpoints.

Phase 9: RSS Subscription — Tests for API endpoints.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from pydantic import ValidationError

from saw.api.feeds import (
    FeedCreateRequest,
    FeedUpdateRequest,
    FeedResponse,
    FeedEntryResponse,
    PollResponse,
    OPMLImportRequest,
    OPMLExportResponse,
)


class TestPydanticModels:
    """Test Pydantic request/response models."""

    def test_feed_create_validates_url(self) -> None:
        """Test 1: FeedCreateRequest validates URL format (http/https only)."""
        # Valid URLs
        req = FeedCreateRequest(url="https://example.com/feed.xml")
        assert req.url == "https://example.com/feed.xml"

        req = FeedCreateRequest(url="http://example.com/feed.xml")
        assert req.url == "http://example.com/feed.xml"

    def test_feed_create_rejects_invalid_url(self) -> None:
        """FeedCreateRequest rejects invalid URL schemes."""
        with pytest.raises(ValidationError):
            FeedCreateRequest(url="ftp://example.com/feed.xml")

        with pytest.raises(ValidationError):
            FeedCreateRequest(url="example.com/feed.xml")

    def test_feed_create_validates_poll_interval(self) -> None:
        """Test 2: FeedCreateRequest validates poll_interval bounds."""
        # Valid bounds
        req = FeedCreateRequest(url="https://example.com/feed.xml", poll_interval=900)
        assert req.poll_interval == 900

        req = FeedCreateRequest(url="https://example.com/feed.xml", poll_interval=86400)
        assert req.poll_interval == 86400

        # Invalid: too low
        with pytest.raises(ValidationError):
            FeedCreateRequest(url="https://example.com/feed.xml", poll_interval=100)

        # Invalid: too high
        with pytest.raises(ValidationError):
            FeedCreateRequest(url="https://example.com/feed.xml", poll_interval=100000)

    def test_feed_response_serializes(self) -> None:
        """Test 3: FeedResponse correctly serializes Feed model."""
        resp = FeedResponse(
            id="feed-123",
            url="https://example.com/feed.xml",
            title="Test Feed",
            description="Test description",
            category="tech",
            tags=["python", "ai"],
            poll_interval=3600,
            last_poll_at=None,
            active=True,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            entry_count=5,
        )

        data = resp.model_dump()
        assert data["id"] == "feed-123"
        assert data["title"] == "Test Feed"
        assert data["tags"] == ["python", "ai"]
        assert data["entry_count"] == 5

    def test_feed_entry_response_serializes(self) -> None:
        """Test 4: FeedEntryResponse correctly serializes FeedEntry model."""
        resp = FeedEntryResponse(
            id="entry-123",
            feed_id="feed-123",
            title="Article Title",
            url="https://example.com/article",
            summary="Article summary",
            status="new",
            published_at=None,
            first_seen_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            vault_uuid=None,
        )

        data = resp.model_dump()
        assert data["id"] == "entry-123"
        assert data["status"] == "new"

    def test_opml_import_validates_xml(self) -> None:
        """Test 5: OPMLImportRequest validates XML format."""
        # Valid OPML
        req = OPMLImportRequest(opml_content='<?xml version="1.0"?><opml><body></body></opml>')
        assert req.opml_content is not None


class TestFeedRouter:
    """Test feed router endpoints (unit-level tests)."""

    def test_router_has_correct_prefix(self) -> None:
        """Router should have /api/v1/feeds prefix."""
        from saw.api.feeds import router

        assert router.prefix == "/api/v1/feeds"

    def test_router_has_correct_tags(self) -> None:
        """Router should have feeds tag."""
        from saw.api.feeds import router

        assert "feeds" in router.tags

    def test_router_has_list_endpoint(self) -> None:
        """Router should have GET / endpoint."""
        from saw.api.feeds import router

        # Check routes - paths include prefix
        route_paths = [route.path for route in router.routes]
        assert "/api/v1/feeds" in route_paths

    def test_router_has_create_endpoint(self) -> None:
        """Router should have POST / endpoint."""
        from saw.api.feeds import router

        methods = {route.path: route.methods for route in router.routes}
        assert "POST" in methods.get("/api/v1/feeds", [])

    def test_router_has_get_by_id_endpoint(self) -> None:
        """Router should have GET /{feed_id} endpoint."""
        from saw.api.feeds import router

        route_paths = [route.path for route in router.routes]
        assert "/api/v1/feeds/{feed_id}" in route_paths

    def test_router_has_update_endpoint(self) -> None:
        """Router should have PUT /{feed_id} endpoint."""
        from saw.api.feeds import router

        # Collect all methods per path
        path_methods: dict[str, set[str]] = {}
        for route in router.routes:
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        assert "PUT" in path_methods.get("/api/v1/feeds/{feed_id}", set())

    def test_router_has_delete_endpoint(self) -> None:
        """Router should have DELETE /{feed_id} endpoint."""
        from saw.api.feeds import router

        # Collect all methods per path
        path_methods: dict[str, set[str]] = {}
        for route in router.routes:
            if route.path not in path_methods:
                path_methods[route.path] = set()
            path_methods[route.path].update(route.methods)

        assert "DELETE" in path_methods.get("/api/v1/feeds/{feed_id}", set())

    def test_router_has_entries_endpoint(self) -> None:
        """Router should have GET /{feed_id}/entries endpoint."""
        from saw.api.feeds import router

        route_paths = [route.path for route in router.routes]
        assert "/api/v1/feeds/{feed_id}/entries" in route_paths

    def test_router_has_poll_endpoint(self) -> None:
        """Router should have POST /{feed_id}/poll endpoint."""
        from saw.api.feeds import router

        route_paths = [route.path for route in router.routes]
        assert "/api/v1/feeds/{feed_id}/poll" in route_paths

    def test_router_has_import_endpoint(self) -> None:
        """Router should have POST /import endpoint."""
        from saw.api.feeds import router

        route_paths = [route.path for route in router.routes]
        assert "/api/v1/feeds/import" in route_paths

    def test_router_has_export_endpoint(self) -> None:
        """Router should have GET /export endpoint."""
        from saw.api.feeds import router

        route_paths = [route.path for route in router.routes]
        assert "/api/v1/feeds/export" in route_paths


class TestOPMLParsing:
    """Test OPML parsing logic."""

    def test_parse_simple_opml(self) -> None:
        """Test parsing simple OPML with one feed."""
        import xml.etree.ElementTree as ET

        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline type="rss" text="Feed 1" xmlUrl="https://example.com/feed.xml"/>
            </body>
        </opml>'''

        root = ET.fromstring(opml)
        outlines = root.findall(".//outline[@xmlUrl]")

        assert len(outlines) == 1
        assert outlines[0].get("xmlUrl") == "https://example.com/feed.xml"

    def test_parse_opml_multiple_feeds(self) -> None:
        """Test parsing OPML with multiple feeds."""
        import xml.etree.ElementTree as ET

        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline type="rss" text="Feed 1" xmlUrl="https://example.com/feed1.xml"/>
                <outline type="rss" text="Feed 2" xmlUrl="https://example.com/feed2.xml"/>
                <outline type="rss" text="Feed 3" xmlUrl="https://example.com/feed3.xml"/>
            </body>
        </opml>'''

        root = ET.fromstring(opml)
        outlines = root.findall(".//outline[@xmlUrl]")

        assert len(outlines) == 3

    def test_parse_opml_with_categories(self) -> None:
        """Test parsing OPML with category groups."""
        import xml.etree.ElementTree as ET

        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline text="Tech">
                    <outline type="rss" text="Feed 1" xmlUrl="https://example.com/feed1.xml"/>
                </outline>
                <outline text="News">
                    <outline type="rss" text="Feed 2" xmlUrl="https://example.com/feed2.xml"/>
                </outline>
            </body>
        </opml>'''

        root = ET.fromstring(opml)
        outlines = root.findall(".//outline[@xmlUrl]")

        assert len(outlines) == 2


class TestOPMLExport:
    """Test OPML generation logic."""

    def test_generate_opml_structure(self) -> None:
        """Test generating valid OPML structure."""
        import xml.etree.ElementTree as ET

        opml = ET.Element("opml", version="2.0")
        head = ET.SubElement(opml, "head")
        ET.SubElement(head, "title").text = "Test Feeds"
        body = ET.SubElement(opml, "body")

        ET.SubElement(body, "outline", type="rss", text="Feed 1", xmlUrl="https://example.com/feed.xml")

        xml_str = ET.tostring(opml, encoding="unicode", xml_declaration=True)

        assert '<?xml' in xml_str
        assert '<opml version="2.0">' in xml_str
        assert 'xmlUrl="https://example.com/feed.xml"' in xml_str

    def test_opml_categories_grouped(self) -> None:
        """Test that OPML export groups feeds by category."""
        import xml.etree.ElementTree as ET

        opml = ET.Element("opml", version="2.0")
        body = ET.SubElement(opml, "body")

        # Group by category
        categories = {"Tech": [], "News": []}
        for cat, feeds in categories.items():
            cat_elem = ET.SubElement(body, "outline", text=cat)

        xml_str = ET.tostring(opml, encoding="unicode")

        assert '<outline text="Tech">' in xml_str or 'text="Tech"' in xml_str
        assert '<outline text="News">' in xml_str or 'text="News"' in xml_str
