"""Plugin event types.

Defines events that plugins can subscribe to for reacting to SAW operations.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PluginEvent:
    """Base event class."""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class PageCreated(PluginEvent):
    """Fired when a wiki page is created."""
    page_id: str = ""
    title: str = ""
    content: str = ""
    author: str = ""


@dataclass
class PageUpdated(PluginEvent):
    """Fired when a wiki page is updated."""
    page_id: str = ""
    title: str = ""
    old_content: str = ""
    new_content: str = ""
    author: str = ""


@dataclass
class PageDeleted(PluginEvent):
    """Fired when a wiki page is deleted."""
    page_id: str = ""
    title: str = ""
    author: str = ""


@dataclass
class ClaimCreated(PluginEvent):
    """Fired when a claim is created."""
    claim_id: str = ""
    content: str = ""
    source: str = ""


@dataclass
class IngestCompleted(PluginEvent):
    """Fired when ingestion pipeline completes."""
    items_processed: int = 0
    claims_created: int = 0
    source_type: str = ""


@dataclass
class QueryExecuted(PluginEvent):
    """Fired when a query is executed."""
    query_text: str = ""
    results_count: int = 0
    execution_time_ms: float = 0.0
