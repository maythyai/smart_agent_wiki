#!/usr/bin/env python3
"""
Sample utility module for demonstration.

This file will be parsed using AST, so no LLM calls are needed.
"""

from pathlib import Path
from typing import Optional


def read_config(path: Path) -> dict:
    """Read configuration from a JSON file."""
    import json

    if not path.exists():
        return {}

    return json.loads(path.read_text())


class DataManager:
    """Manages data operations for the application."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize with optional config path."""
        self.config = {}
        if config_path:
            self.config = read_config(config_path)

    def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a value from config."""
        return self.config.get(key, default)

    def set_value(self, key: str, value: str) -> None:
        """Set a value in config."""
        self.config[key] = value


def main():
    """Main entry point."""
    manager = DataManager()
    print("Data manager initialized")


if __name__ == "__main__":
    main()
