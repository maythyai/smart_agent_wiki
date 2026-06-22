"""Plugin system for Smart Agent Wiki.

Provides extensible plugin architecture with hooks, events, and sandboxing.
"""

from saw.plugins.base import PluginBase, PluginContext
from saw.plugins.events import PluginEvent, PageCreated, PageUpdated, PageDeleted
from saw.plugins.registry import PluginRegistry

__all__ = [
    "PluginBase",
    "PluginContext",
    "PluginEvent",
    "PageCreated",
    "PageUpdated",
    "PageDeleted",
    "PluginRegistry",
]
