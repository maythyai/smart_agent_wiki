"""Notion API models using Pydantic.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-01: Notion API models for pages, databases, properties.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Literal, Optional, Union
import enum

from pydantic import BaseModel, ConfigDict, Field


class NotionUser(BaseModel):
    """Notion user (person or bot).

    Attributes:
        id: User identifier.
        name: Display name.
        avatar_url: Avatar URL (optional).
        type: User type (person or bot).
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    avatar_url: Optional[str] = None
    type: Literal["person", "bot"] = "person"


class NotionRichText(BaseModel):
    """Notion rich text segment.

    Attributes:
        type: Text type (text, mention, equation).
        plain_text: Plain text content.
        annotations: Formatting annotations.
        href: Link URL (for mentions).
    """
    model_config = ConfigDict(from_attributes=True)

    type: Literal["text", "mention", "equation"] = "text"
    plain_text: str
    annotations: dict[str, bool] = field(default_factory=dict)
    href: Optional[str] = None


class NotionFile(BaseModel):
    """Notion file attachment.

    Attributes:
        name: File name.
        type: File type (file or external).
        url: File URL.
        expiry_time: Expiration time for signed URLs.
    """
    model_config = ConfigDict(from_attributes=True)

    name: str
    type: Literal["file", "external"] = "file"
    url: str
    expiry_time: Optional[datetime] = None


# Property type models - discriminated union

class TitleProperty(BaseModel):
    """Title property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["title"] = "title"
    title: list[NotionRichText]


class RichTextProperty(BaseModel):
    """Rich text property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["rich_text"] = "rich_text"
    rich_text: list[NotionRichText]


class NumberProperty(BaseModel):
    """Number property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["number"] = "number"
    number: Optional[Union[int, float]] = None
    number_format: Literal["number", "number_with_commas", "percent", "dollar", "euro", "pound", "yen", "ruble", "rupee", "won", "yuan", "real"] = "number"


class SelectOption(BaseModel):
    """Select option in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    color: str = "default"


class SelectProperty(BaseModel):
    """Select property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["select"] = "select"
    select: dict[str, Any]  # {"id", "name", "color"}


class MultiSelectProperty(BaseModel):
    """Multi-select property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["multi_select"] = "multi_select"
    multi_select: list[dict[str, Any]] = field(default_factory=list)


class DateProperty(BaseModel):
    """Date property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["date"] = "date"
    date: Optional[dict[str, Any]] = None  # {"start", "end"}


class CheckboxProperty(BaseModel):
    """Checkbox property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["checkbox"] = "checkbox"
    checkbox: bool = False


class URLProperty(BaseModel):
    """URL property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["url"] = "url"
    url: Optional[str] = None


class EmailProperty(BaseModel):
    """Email property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["email"] = "email"
    email: Optional[str] = None


class PhoneProperty(BaseModel):
    """Phone property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["phone_number"] = "phone_number"
    phone_number: Optional[str] = None


class FilesProperty(BaseModel):
    """Files property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["files"] = "files"
    files: list[NotionFile] = field(default_factory=list)


class RelationProperty(BaseModel):
    """Relation property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["relation"] = "relation"
    relation: list[dict[str, str]] = field(default_factory=list)  # [{"id": "..."}]
    database_id: Optional[str] = None
    synced_property_name: Optional[str] = None


class RollupProperty(BaseModel):
    """Rollup property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["rollup"] = "rollup"
    rollup: dict[str, Any] = field(default_factory=dict)


class CreatedTimeProperty(BaseModel):
    """Created time property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["created_time"] = "created_time"
    created_time: datetime


class LastEditedTimeProperty(BaseModel):
    """Last edited time property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["last_edited_time"] = "last_edited_time"
    last_edited_time: datetime


class CreatedByProperty(BaseModel):
    """Created by property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["created_by"] = "created_by"
    created_by: NotionUser


class LastEditedByProperty(BaseModel):
    """Last edited by property in Notion."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: Literal["last_edited_by"] = "last_edited_by"
    last_edited_by: NotionUser


# Discriminated union for all property types
NotionProperty = Annotated[
    Union[
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
    ],
    Field(discriminator="type"),
]


class NotionPage(BaseModel):
    """Notion page.

    Attributes:
        id: Page identifier.
        parent: Parent reference (database_id or page_id).
        properties: Page properties dict.
        created_time: Creation timestamp.
        last_edited_time: Last edit timestamp.
        url: Page URL.
        archived: Whether page is archived.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    parent: dict[str, str]  # {"database_id": "..."} or {"page_id": "..."}
    properties: dict[str, Any] = field(default_factory=dict)
    created_time: datetime
    last_edited_time: datetime
    url: str
    archived: bool = False


class NotionDatabase(BaseModel):
    """Notion database.

    Attributes:
        id: Database identifier.
        title: Database title (rich text).
        properties: Property schema.
        description: Database description.
        url: Database URL.
        is_selected: Whether selected for sync.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: list[NotionRichText] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    url: str = ""
    is_selected: bool = True


class NotionSearchResult(BaseModel):
    """Notion search result.

    Attributes:
        results: List of results (pages or databases).
        has_more: Whether more results exist.
        next_cursor: Pagination cursor.
    """
    model_config = ConfigDict(from_attributes=True)

    results: list[Any] = field(default_factory=list)
    has_more: bool = False
    next_cursor: Optional[str] = None


class NotionErrorResponse(BaseModel):
    """Notion error response.

    Attributes:
        code: Error code.
        message: Error message.
    """
    model_config = ConfigDict(from_attributes=True)

    code: str
    message: str
