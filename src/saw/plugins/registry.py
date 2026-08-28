"""Plugin registry and lifecycle management.

Discovers, loads, and manages plugin instances.
"""

import importlib.util
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import yaml

from saw.plugins.base import PluginBase, PluginContext

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Plugin metadata loaded from plugin.yaml."""
    name: str
    version: str
    description: str
    author: str = ""
    hooks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class PluginRegistry:
    """Registry for discovering and managing plugins.

    Scans plugin directories, loads plugin classes, and manages lifecycle.
    """

    def __init__(self, plugins_dir: Optional[Path] = None):
        """Initialize registry.

        Args:
            plugins_dir: Directory containing plugins. Defaults to ~/.saw/plugins.
        """
        self.plugins_dir = plugins_dir or Path.home() / ".saw" / "plugins"
        self.plugins: Dict[str, PluginBase] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.enabled: Dict[str, bool] = {}

    def discover(self) -> List[str]:
        """Scan plugins directory and discover available plugins.

        Returns:
            List of discovered plugin names.
        """
        if not self.plugins_dir.exists():
            return []

        discovered = []
        for path in self.plugins_dir.iterdir():
            if not path.is_dir():
                continue
            yaml_path = path / "plugin.yaml"
            if not yaml_path.exists():
                continue

            try:
                with open(yaml_path) as f:
                    meta = yaml.safe_load(f)
                name = meta.get("name", path.name)
                self.metadata[name] = PluginMetadata(
                    name=name,
                    version=meta.get("version", "0.1.0"),
                    description=meta.get("description", ""),
                    author=meta.get("author", ""),
                    hooks=meta.get("hooks", []),
                    dependencies=meta.get("dependencies", []),
                )
                discovered.append(name)
            except Exception:
                # F-PLUG-01: log instead of silently skipping bad metadata.
                logger.warning("Failed to load plugin metadata from %s", yaml_path, exc_info=True)
                continue

        return discovered

    def load(self, name: str) -> Optional[PluginBase]:
        """Load a plugin by name.

        Args:
            name: Plugin name.

        Returns:
            PluginBase instance or None if not found.
        """
        if name in self.plugins:
            return self.plugins[name]

        plugin_path = self.plugins_dir / name / "plugin.py"
        if not plugin_path.exists():
            return None

        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{name}", plugin_path)
            if not spec or not spec.loader:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugin_{name}"] = module
            spec.loader.exec_module(module)

            # Find PluginBase subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, PluginBase) and attr is not PluginBase:
                    instance = attr()
                    self.plugins[name] = instance
                    return instance
        except Exception:
            # F-PLUG-01: log load failures so bad plugins are visible.
            logger.warning("Failed to load plugin '%s'", name, exc_info=True)
            return None

        return None

    def enable(self, name: str, context: PluginContext) -> bool:
        """Enable a plugin.

        Args:
            name: Plugin name.
            context: PluginContext to pass to activate().

        Returns:
            True if enabled successfully.
        """
        plugin = self.load(name)
        if not plugin:
            return False

        try:
            plugin.activate(context)
            self.enabled[name] = True
            return True
        except Exception:
            # F-PLUG-01: log activation failures.
            logger.warning("Failed to enable plugin '%s'", name, exc_info=True)
            return False

    def disable(self, name: str) -> bool:
        """Disable a plugin.

        Args:
            name: Plugin name.

        Returns:
            True if disabled successfully.
        """
        plugin = self.plugins.get(name)
        if not plugin:
            return False

        try:
            plugin.deactivate()
            self.enabled[name] = False
            return True
        except Exception:
            # F-PLUG-01: log deactivation failures.
            logger.warning("Failed to disable plugin '%s'", name, exc_info=True)
            return False

    def list_plugins(self) -> List[dict]:
        """List all discovered plugins with status.

        Returns:
            List of plugin info dicts.
        """
        result = []
        for name, meta in self.metadata.items():
            result.append({
                "name": name,
                "version": meta.version,
                "description": meta.description,
                "enabled": self.enabled.get(name, False),
            })
        return result
