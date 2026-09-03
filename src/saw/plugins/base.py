"""Plugin base classes and context.

Defines the PluginBase abstract class and PluginContext for safe plugin execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from pathlib import Path


@dataclass
class PluginContext:
    """Safe context provided to plugins for accessing SAW resources.

    Attributes:
        data_dir: Plugin's isolated data directory.
        wiki_read: Function to read wiki pages.
        wiki_write: Function to write wiki pages.
        claims_read: Function to read claims.
        graph_query: Function to query knowledge graph.
        subscribe_event: Function to subscribe to events.
        publish_event: Function to publish custom events.
    """
    data_dir: Path
    wiki_read: Any  # Callable[[str], Optional[dict]]
    wiki_write: Any  # Callable[[str, str], bool]
    claims_read: Any  # Callable[[dict], list[dict]]
    graph_query: Any  # Callable[[str], list[dict]]
    subscribe_event: Any  # Callable[[str, Callable], None]
    publish_event: Any  # Callable[[str, dict], None]


class PluginBase(ABC):
    """Abstract base class for SAW plugins.

    Plugins must implement activate() and deactivate(). Optional on_event()
    handles event subscriptions.
    """

    name: str = "unnamed-plugin"
    version: str = "0.1.0"
    description: str = ""

    @abstractmethod
    def activate(self, context: PluginContext) -> None:
        """Called when plugin is enabled.

        Args:
            context: PluginContext with safe resource access.
        """
        ...

    @abstractmethod
    def deactivate(self) -> None:
        """Called when plugin is disabled. Cleanup resources here."""
        ...

    def on_event(self, event: Any) -> None:
        """Handle subscribed events.

        Override this to respond to PageCreated, PageUpdated, etc.

        Args:
            event: Event object (see events.py).
        """
        pass
