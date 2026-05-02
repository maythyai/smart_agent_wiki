"""Tests for Notion connector models.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-01: Notion API models for pages, databases, properties.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from saw.connectors.notion.models import (
    NotionPage,
    NotionDatabase,
    NotionProperty,
    NotionUser,
    NotionFile,
    NotionRichText,
    TitleProperty,
    RichTextProperty,
    NumberProperty,
    SelectProperty,
    MultiSelectProperty,
    DateProperty,
    CheckboxProperty,
    URLProperty,
    EmailProperty,
    PhoneProperty,
    FilesProperty,
    RelationProperty,
    RollupProperty,
    CreatedTimeProperty,
    LastEditedTimeProperty,
    CreatedByProperty,
    LastEditedByProperty,
    NotionSearchResult,
    NotionErrorResponse,
)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestNotionUser:
    """Tests for NotionUser model."""

    def test_notion_user_creation(self) -> None:
        """Test 1: NotionUser accepts all required fields."""
        user = NotionUser(
            id="user-123",
            name="Test User",
            avatar_url="https://example.com/avatar.png",
            type="person",
        )
        assert user.id == "user-123"
        assert user.name == "Test User"
        assert user.avatar_url == "https://example.com/avatar.png"
        assert user.type == "person"

    def test_notion_user_bot_type(self) -> None:
        """Test NotionUser with bot type."""
        user = NotionUser(
            id="bot-123",
            name="Test Bot",
            avatar_url=None,
            type="bot",
        )
        assert user.type == "bot"


class TestNotionRichText:
    """Tests for NotionRichText model."""

    def test_rich_text_text_type(self) -> None:
        """Test rich text with text type."""
        rt = NotionRichText(
            type="text",
            plain_text="Hello World",
            annotations={"bold": True, "italic": False},
            href=None,
        )
        assert rt.type == "text"
        assert rt.plain_text == "Hello World"
        assert rt.annotations["bold"] is True

    def test_rich_text_mention_type(self) -> None:
        """Test rich text with mention type."""
        rt = NotionRichText(
            type="mention",
            plain_text="@User",
            annotations={},
            href="notion://user/123",
        )
        assert rt.type == "mention"
        assert rt.href == "notion://user/123"


class TestNotionFile:
    """Tests for NotionFile model."""

    def test_notion_file_creation(self) -> None:
        """Test NotionFile with file type."""
        f = NotionFile(
            name="document.pdf",
            type="file",
            url="https://example.com/file.pdf",
            expiry_time=utcnow(),
        )
        assert f.name == "document.pdf"
        assert f.type == "file"

    def test_notion_file_external(self) -> None:
        """Test NotionFile with external type."""
        f = NotionFile(
            name="external.pdf",
            type="external",
            url="https://external.com/file.pdf",
            expiry_time=None,
        )
        assert f.type == "external"


class TestNotionProperty:
    """Tests for NotionProperty discriminated union."""

    def test_title_property(self) -> None:
        """Test 1: Title property extracts to title string."""
        prop = TitleProperty(
            id="title-id",
            type="title",
            title=[NotionRichText(type="text", plain_text="Page Title", annotations={}, href=None)],
        )
        assert prop.type == "title"
        assert prop.title[0].plain_text == "Page Title"

    def test_rich_text_property(self) -> None:
        """Test 11: Rich text property maps to plain text string."""
        prop = RichTextProperty(
            id="rt-id",
            type="rich_text",
            rich_text=[NotionRichText(type="text", plain_text="Some text", annotations={}, href=None)],
        )
        assert prop.type == "rich_text"
        assert prop.rich_text[0].plain_text == "Some text"

    def test_number_property(self) -> None:
        """Test 7: Number property maps to float/int."""
        prop = NumberProperty(
            id="num-id",
            type="number",
            number=42,
            number_format="number",
        )
        assert prop.type == "number"
        assert prop.number == 42

    def test_select_property(self) -> None:
        """Test 2: Select property maps to confidence enum."""
        prop = SelectProperty(
            id="select-id",
            type="select",
            select={"id": "opt-id", "name": "Unverified", "color": "default"},
        )
        assert prop.type == "select"
        assert prop.select["name"] == "Unverified"

    def test_multi_select_property(self) -> None:
        """Test 4: Multi-select property maps to tags list."""
        prop = MultiSelectProperty(
            id="ms-id",
            type="multi_select",
            multi_select=[
                {"id": "tag1", "name": "tag1", "color": "blue"},
                {"id": "tag2", "name": "tag2", "color": "red"},
            ],
        )
        assert prop.type == "multi_select"
        assert len(prop.multi_select) == 2

    def test_date_property(self) -> None:
        """Test 5: Date property maps to datetime or date range."""
        now = utcnow()
        prop = DateProperty(
            id="date-id",
            type="date",
            date={"start": now.isoformat(), "end": None},
        )
        assert prop.type == "date"
        assert prop.date["start"] == now.isoformat()

    def test_checkbox_property(self) -> None:
        """Test 6: Checkbox property maps to boolean."""
        prop = CheckboxProperty(
            id="cb-id",
            type="checkbox",
            checkbox=True,
        )
        assert prop.type == "checkbox"
        assert prop.checkbox is True

    def test_url_property(self) -> None:
        """Test 8: URL property maps to string."""
        prop = URLProperty(
            id="url-id",
            type="url",
            url="https://example.com",
        )
        assert prop.type == "url"
        assert prop.url == "https://example.com"

    def test_email_property(self) -> None:
        """Test 9: Email property maps to string."""
        prop = EmailProperty(
            id="email-id",
            type="email",
            email="test@example.com",
        )
        assert prop.type == "email"
        assert prop.email == "test@example.com"

    def test_phone_property(self) -> None:
        """Test 10: Phone property maps to string."""
        prop = PhoneProperty(
            id="phone-id",
            type="phone_number",
            phone_number="+1234567890",
        )
        assert prop.type == "phone_number"
        assert prop.phone_number == "+1234567890"

    def test_files_property(self) -> None:
        """Test 12: Files property maps to list of URLs with names."""
        prop = FilesProperty(
            id="files-id",
            type="files",
            files=[
                NotionFile(name="file1.pdf", type="file", url="https://example.com/f1.pdf", expiry_time=None),
            ],
        )
        assert prop.type == "files"
        assert len(prop.files) == 1

    def test_relation_property(self) -> None:
        """Test 13: Relation property maps to list of page IDs."""
        prop = RelationProperty(
            id="rel-id",
            type="relation",
            relation=[{"id": "page-1"}, {"id": "page-2"}],
            database_id="db-123",
            synced_property_name="Related",
        )
        assert prop.type == "relation"
        assert len(prop.relation) == 2

    def test_rollup_property(self) -> None:
        """Test 14: Rollup property maps to aggregated value."""
        prop = RollupProperty(
            id="rollup-id",
            type="rollup",
            rollup={"type": "number", "number": 10},
        )
        assert prop.type == "rollup"
        assert prop.rollup["number"] == 10

    def test_created_time_property(self) -> None:
        """Test 16: Created time maps to datetime."""
        now = utcnow()
        prop = CreatedTimeProperty(
            id="ct-id",
            type="created_time",
            created_time=now,
        )
        assert prop.type == "created_time"
        assert prop.created_time == now

    def test_last_edited_time_property(self) -> None:
        """Test 16: Last edited time maps to datetime."""
        now = utcnow()
        prop = LastEditedTimeProperty(
            id="let-id",
            type="last_edited_time",
            last_edited_time=now,
        )
        assert prop.type == "last_edited_time"
        assert prop.last_edited_time == now

    def test_created_by_property(self) -> None:
        """Test 15: Created by maps to user info."""
        prop = CreatedByProperty(
            id="cb-id",
            type="created_by",
            created_by=NotionUser(id="user-1", name="User 1", avatar_url=None, type="person"),
        )
        assert prop.type == "created_by"
        assert prop.created_by.name == "User 1"

    def test_last_edited_by_property(self) -> None:
        """Test 15: Last edited by maps to user info."""
        prop = LastEditedByProperty(
            id="leb-id",
            type="last_edited_by",
            last_edited_by=NotionUser(id="user-2", name="User 2", avatar_url=None, type="person"),
        )
        assert prop.type == "last_edited_by"
        assert prop.last_edited_by.name == "User 2"


class TestNotionPage:
    """Tests for NotionPage model."""

    def test_notion_page_creation(self) -> None:
        """Test 1: NotionPage dataclass accepts all required fields."""
        now = utcnow()
        page = NotionPage(
            id="page-123",
            parent={"database_id": "db-123"},
            properties={
                "Title": TitleProperty(
                    id="title-id",
                    type="title",
                    title=[NotionRichText(type="text", plain_text="Test Page", annotations={}, href=None)],
                ),
            },
            created_time=now,
            last_edited_time=now,
            url="https://notion.so/page-123",
            archived=False,
        )
        assert page.id == "page-123"
        assert page.parent["database_id"] == "db-123"
        assert page.archived is False

    def test_notion_page_with_page_parent(self) -> None:
        """Test NotionPage with page parent."""
        page = NotionPage(
            id="page-456",
            parent={"page_id": "parent-123"},
            properties={},
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-456",
            archived=False,
        )
        assert page.parent["page_id"] == "parent-123"


class TestNotionDatabase:
    """Tests for NotionDatabase model."""

    def test_notion_database_creation(self) -> None:
        """Test 2: NotionDatabase includes id, title, properties schema, is_selected."""
        db = NotionDatabase(
            id="db-123",
            title=[NotionRichText(type="text", plain_text="My Database", annotations={}, href=None)],
            properties={
                "Title": {"type": "title", "title": {}},
                "Status": {"type": "select", "select": {"options": []}},
            },
            description="Test database",
            url="https://notion.so/db-123",
            is_selected=True,
        )
        assert db.id == "db-123"
        assert db.title[0].plain_text == "My Database"
        assert db.is_selected is True


class TestNotionSearchResult:
    """Tests for NotionSearchResult model."""

    def test_search_result(self) -> None:
        """Test NotionSearchResult pagination."""
        result = NotionSearchResult(
            results=[
                NotionDatabase(
                    id="db-1",
                    title=[NotionRichText(type="text", plain_text="DB 1", annotations={}, href=None)],
                    properties={},
                    description="",
                    url="https://notion.so/db-1",
                ),
            ],
            has_more=True,
            next_cursor="cursor-123",
        )
        assert result.has_more is True
        assert result.next_cursor == "cursor-123"


class TestNotionErrorResponse:
    """Tests for NotionErrorResponse model."""

    def test_error_response(self) -> None:
        """Test NotionErrorResponse parsing."""
        error = NotionErrorResponse(
            code="validation_error",
            message="Invalid request",
        )
        assert error.code == "validation_error"
        assert error.message == "Invalid request"
