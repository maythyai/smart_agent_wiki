"""Configuration settings with capability tier detection.

Per D-22: Three-tier degradation (FULL > LIGHTWEIGHT > OFFLINE).
Per D-24: Agent compatibility layer.
Per D-23: WIP file structure.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from saw.domain.exceptions import ConfigError
from saw.domain.value_objects import CapabilityTier


class LLMSettings(BaseModel):
    """LLM configuration."""
    extraction_model: str = ""
    query_model: str = ""
    api_key: str = ""


class WikiSettings(BaseModel):
    """Main wiki configuration."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path = Path(".")
    agent: str | None = None
    llm: LLMSettings = LLMSettings()


# File extension to format mapping
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".md": "markdown",
    ".markdown": "markdown",
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".rs": "code",
    ".go": "code",
    ".java": "code",
    ".json": "json",
    ".jsonl": "json",
    ".csv": "table",
    ".tsv": "table",
}


def detect_tier() -> CapabilityTier:
    """Detect system capability tier on startup (per D-22).

    - OFFLINE: BM25+TF-IDF, zero LLM
    - LIGHTWEIGHT: LLM + BM25 only
    - FULL: LLM + embeddings + vector

    Returns:
        CapabilityTier enum value.
    """
    tier = CapabilityTier.OFFLINE

    # Check if any LLM API key is configured
    if _llm_available():
        tier = CapabilityTier.LIGHTWEIGHT

    # Check if embeddings are available
    if _embeddings_available():
        tier = CapabilityTier.FULL

    return tier


def _llm_available() -> bool:
    """Check if any LLM API key is configured."""
    import os
    # Check common LLM API key environment variables
    llm_keys = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "LITELLM_API_KEY",
    ]
    return any(os.environ.get(k) for k in llm_keys)


def _embeddings_available() -> bool:
    """Check if sentence-transformers is available for local embeddings."""
    try:
        import importlib
        importlib.import_module("sentence_transformers")
        return True
    except ImportError:
        return False


def load_config(config_path: Path) -> WikiSettings:
    """Load wiki configuration from .saw/config.yaml."""
    if not config_path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return WikiSettings(**data)
    except Exception as e:
        raise ConfigError(f"Failed to load config: {e}") from e


def scan_directory(dir_path: Path) -> list[Path]:
    """Recursively find all supported files in a directory.

    Args:
        dir_path: Directory to scan.

    Returns:
        List of file paths with supported extensions.
    """
    supported_files: list[Path] = []
    dir_path = Path(dir_path)

    if not dir_path.is_dir():
        return supported_files

    for ext in SUPPORTED_EXTENSIONS:
        for file_path in dir_path.rglob(f"*{ext}"):
            # Skip hidden files and directories
            if any(part.startswith(".") for part in file_path.parts):
                continue
            # Skip common non-content directories
            if any(part in ("node_modules", "venv", ".venv", "__pycache__") for part in file_path.parts):
                continue
            supported_files.append(file_path)

    return sorted(supported_files)
