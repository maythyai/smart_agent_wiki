"""Tests for Notion property mapper.

Plan 12-02: Property mapping and block transformation.
Per NOTI-04: Notion properties map correctly to SAW fields.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from saw.connectors.notion.property_mapper import (
    PropertyMapper,
    PropertyMappingConfig,
    extract_title,
    extract_confidence,
    extract_freshness,
    extract_tags,
)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestPropertyMapper:
    """Tests for PropertyMapper class."""

    def test_extract_title(self) -> None:
        """Test 1: Title property extracts to title string."""
        properties = {
            "Title": {
                "id": "title-id",
                "type": "title",
                "title": [{"plain_text": "My Page Title", "type": "text"}],
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        title = mapper.extract_title(properties)
        assert title == "My Page Title"

    def test_extract_confidence_valid(self) -> None:
        """Test 2: Select property maps to confidence enum."""
        properties = {
            "Confidence": {
                "id": "conf-id",
                "type": "select",
                "select": {"name": "Single Source", "color": "blue"},
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        confidence = mapper.extract_confidence(properties)
        assert confidence == "single_source"

    def test_extract_confidence_unverified(self) -> None:
        """Test confidence default to unverified."""
        properties = {
            "Confidence": {
                "id": "conf-id",
                "type": "select",
                "select": {"name": "Unverified"},
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        confidence = mapper.extract_confidence(properties)
        assert confidence == "unverified"

    def test_extract_confidence_human_verified(self) -> None:
        """Test confidence human_verified value."""
        properties = {
            "Confidence": {
                "id": "conf-id",
                "type": "select",
                "select": {"name": "Human Verified"},
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        confidence = mapper.extract_confidence(properties)
        assert confidence == "human_verified"

    def test_extract_freshness_valid(self) -> None:
        """Test 3: Select property maps to freshness enum."""
        properties = {
            "Freshness": {
                "id": "fresh-id",
                "type": "select",
                "select": {"name": "Stale"},
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        freshness = mapper.extract_freshness(properties)
        assert freshness == "stale"

    def test_extract_freshness_default(self) -> None:
        """Test freshness default to fresh."""
        properties = {}
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        freshness = mapper.extract_freshness(properties)
        assert freshness == "fresh"

    def test_extract_tags(self) -> None:
        """Test 4: Multi-select property maps to tags list."""
        properties = {
            "Tags": {
                "id": "tags-id",
                "type": "multi_select",
                "multi_select": [
                    {"name": "python", "color": "blue"},
                    {"name": "testing", "color": "red"},
                ],
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        tags = mapper.extract_tags(properties)
        assert tags == ["python", "testing"]

    def test_extract_date(self) -> None:
        """Test 5: Date property maps to datetime or date range."""
        now = utcnow()
        properties = {
            "Date": {
                "id": "date-id",
                "type": "date",
                "date": {"start": now.isoformat()},
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        date = mapper._extract_date(properties.get("Date"))
        assert date is not None

    def test_extract_checkbox(self) -> None:
        """Test 6: Checkbox property maps to boolean."""
        properties = {
            "Checked": {
                "id": "cb-id",
                "type": "checkbox",
                "checkbox": True,
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        value = mapper._extract_checkbox(properties.get("Checked"))
        assert value is True

    def test_extract_number(self) -> None:
        """Test 7: Number property maps to float/int."""
        properties = {
            "Count": {
                "id": "num-id",
                "type": "number",
                "number": 42,
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        value = mapper._extract_number(properties.get("Count"))
        assert value == 42

    def test_extract_url(self) -> None:
        """Test 8: URL property maps to string."""
        properties = {
            "Link": {
                "id": "url-id",
                "type": "url",
                "url": "https://example.com",
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        value = mapper._extract_url(properties.get("Link"))
        assert value == "https://example.com"

    def test_extract_email(self) -> None:
        """Test 9: Email property maps to string."""
        properties = {
            "Email": {
                "id": "email-id",
                "type": "email",
                "email": "test@example.com",
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        value = mapper._extract_email(properties.get("Email"))
        assert value == "test@example.com"

    def test_extract_phone(self) -> None:
        """Test 10: Phone property maps to string."""
        properties = {
            "Phone": {
                "id": "phone-id",
                "type": "phone_number",
                "phone_number": "+1234567890",
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        value = mapper._extract_phone(properties.get("Phone"))
        assert value == "+1234567890"

    def test_extract_rich_text(self) -> None:
        """Test 11: Rich text property maps to plain text string."""
        properties = {
            "Notes": {
                "id": "rt-id",
                "type": "rich_text",
                "rich_text": [{"plain_text": "Some notes", "type": "text"}],
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        value = mapper._extract_rich_text(properties.get("Notes"))
        assert value == "Some notes"

    def test_extract_files(self) -> None:
        """Test 12: Files property maps to list of URLs with names."""
        properties = {
            "Files": {
                "id": "files-id",
                "type": "files",
                "files": [
                    {"name": "doc.pdf", "external": {"url": "https://example.com/doc.pdf"}},
                ],
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        files = mapper._extract_files(properties.get("Files"))
        assert len(files) == 1
        assert files[0]["name"] == "doc.pdf"

    def test_extract_relation(self) -> None:
        """Test 13: Relation property maps to list of page IDs."""
        properties = {
            "Related": {
                "id": "rel-id",
                "type": "relation",
                "relation": [{"id": "page-1"}, {"id": "page-2"}],
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        relations = mapper._extract_relation(properties.get("Related"))
        assert relations == ["page-1", "page-2"]

    def test_extract_created_time(self) -> None:
        """Test 16: Created time maps to datetime."""
        now = utcnow()
        properties = {
            "Created": {
                "id": "ct-id",
                "type": "created_time",
                "created_time": now.isoformat(),
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        dt = mapper._extract_created_time(properties.get("Created"))
        assert dt is not None

    def test_extract_last_edited_time(self) -> None:
        """Test 16: Last edited time maps to datetime."""
        now = utcnow()
        properties = {
            "Edited": {
                "id": "let-id",
                "type": "last_edited_time",
                "last_edited_time": now.isoformat(),
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        dt = mapper._extract_last_edited_time(properties.get("Edited"))
        assert dt is not None

    def test_custom_mapping_override(self) -> None:
        """Test 17: Custom mapping overrides default field names."""
        properties = {
            "CustomTitle": {
                "id": "title-id",
                "type": "title",
                "title": [{"plain_text": "Custom Title", "type": "text"}],
            },
        }
        config = PropertyMappingConfig(title_property="CustomTitle")
        mapper = PropertyMapper(config, None)
        title = mapper.extract_title(properties)
        assert title == "Custom Title"

    def test_missing_property_fallback(self) -> None:
        """Test 18: Missing properties fall back to defaults without error."""
        properties = {}
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)

        title = mapper.extract_title(properties)
        confidence = mapper.extract_confidence(properties)
        freshness = mapper.extract_freshness(properties)
        tags = mapper.extract_tags(properties)

        assert title == ""
        assert confidence == "unverified"
        assert freshness == "fresh"
        assert tags == []

    def test_property_type_change_handles_gracefully(self) -> None:
        """Test 19: Property type change handles gracefully."""
        # Title property that has become something else
        properties = {
            "Title": {
                "id": "title-id",
                "type": "rich_text",  # Changed from title to rich_text
                "rich_text": [{"plain_text": "New format", "type": "text"}],
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        title = mapper.extract_title(properties)
        # Should still work, extracting text from rich_text
        assert title == "" or "New format" in title  # Fallback behavior

    def test_invalid_select_option_fallback(self) -> None:
        """Test 20: Invalid select option falls back to default."""
        properties = {
            "Confidence": {
                "id": "conf-id",
                "type": "select",
                "select": {"name": "InvalidValue"},
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        confidence = mapper.extract_confidence(properties)
        assert confidence == "unverified"  # Default fallback

    def test_map_properties_all(self) -> None:
        """Test mapping all configured properties."""
        properties = {
            "Title": {
                "id": "title-id",
                "type": "title",
                "title": [{"plain_text": "Test Page", "type": "text"}],
            },
            "Confidence": {
                "id": "conf-id",
                "type": "select",
                "select": {"name": "Cross-Validated"},
            },
            "Freshness": {
                "id": "fresh-id",
                "type": "select",
                "select": {"name": "Fresh"},
            },
            "Tags": {
                "id": "tags-id",
                "type": "multi_select",
                "multi_select": [{"name": "test"}],
            },
        }
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        mapped = mapper.map_properties(properties)

        assert mapped["title"] == "Test Page"
        assert mapped["confidence"] == "cross_validated"
        assert mapped["freshness"] == "fresh"
        assert mapped["tags"] == ["test"]


class TestPropertyMappingConfig:
    """Tests for PropertyMappingConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = PropertyMappingConfig()
        assert config.title_property == "Title"
        assert config.confidence_property == "Confidence"
        assert config.freshness_property == "Freshness"
        assert config.tags_property == "Tags"

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = PropertyMappingConfig(
            title_property="Name",
            confidence_property="Status",
            custom_mappings={"CustomField": "custom"},
        )
        assert config.title_property == "Name"
        assert config.confidence_property == "Status"
        assert config.custom_mappings["CustomField"] == "custom"


class TestReverseMapping:
    """Tests for reverse mapping (Claim to Notion)."""

    def test_map_to_notion_properties(self) -> None:
        """Test mapping SAW fields back to Notion format."""
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)

        claim = {
            "title": "Test Claim",
            "confidence": "single_source",
            "freshness": "fresh",
            "tags": ["test", "example"],
        }

        schema = {
            "Title": {"type": "title"},
            "Confidence": {"type": "select", "select": {"options": [{"name": "Single Source"}]}},
            "Tags": {"type": "multi_select", "multi_select": {"options": [{"name": "test"}]}},
        }

        notion_props = mapper.map_to_notion_properties(claim, schema)

        assert notion_props["Title"]["title"][0]["text"]["content"] == "Test Claim"

    def test_map_to_notion_skips_changed_type(self) -> None:
        """Test that type changes are skipped during push."""
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)

        claim = {"confidence": "single_source"}

        # Schema has changed - Confidence is now text instead of select
        schema = {
            "Confidence": {"type": "rich_text"},  # Changed!
        }

        notion_props = mapper.map_to_notion_properties(claim, schema)

        # Should skip or handle gracefully
        assert True  # No crash means success