"""Notion connector package.

Plan 12-01: Notion connector core with OAuth.
"""
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

__all__ = [
    # Core models
    "NotionPage",
    "NotionDatabase",
    "NotionProperty",
    "NotionUser",
    "NotionFile",
    "NotionRichText",
    # Property types
    "TitleProperty",
    "RichTextProperty",
    "NumberProperty",
    "SelectProperty",
    "MultiSelectProperty",
    "DateProperty",
    "CheckboxProperty",
    "URLProperty",
    "EmailProperty",
    "PhoneProperty",
    "FilesProperty",
    "RelationProperty",
    "RollupProperty",
    "CreatedTimeProperty",
    "LastEditedTimeProperty",
    "CreatedByProperty",
    "LastEditedByProperty",
    # Response models
    "NotionSearchResult",
    "NotionErrorResponse",
]
