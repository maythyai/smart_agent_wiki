"""Agent compatibility layer - template generation for AI agent configs.

Per D-24: Shared template for claude-code, cursor, copilot, gemini.
"""
from __future__ import annotations

from pathlib import Path

from saw.domain.exceptions import ConfigError

# Core instructions shared across all agent templates
_CORE_INSTRUCTIONS = """## Smart Agent Wiki Agent Instructions

This is a Smart Agent Wiki knowledge base. Key conventions:
- All claims trace back to Vault sources via source_uuid
- Wiki pages are in wiki/ with YAML frontmatter
- Claims DB is in .saw/db/claims.db (SQLite)
- Vault originals are immutable in vault/
- Use `saw status` to check knowledge base health
- Use `saw ingest <source>` to add documents
- Use `saw query <question>` for natural language queries
- Use `saw search <keywords>` for keyword search
"""

AGENT_TEMPLATES: dict[str, dict[str, str]] = {
    "claude-code": {
        "filename": "CLAUDE.md",
        "content": _CORE_INSTRUCTIONS,
    },
    "cursor": {
        "filename": ".cursorrules",
        "content": _CORE_INSTRUCTIONS,
    },
    "copilot": {
        "filename": "AGENTS.md",
        "content": _CORE_INSTRUCTIONS,
    },
    "gemini": {
        "filename": "GEMINI.md",
        "content": _CORE_INSTRUCTIONS,
    },
}


def generate_agent_config(agent_name: str, wiki_path: Path) -> Path:
    """Generate agent-specific configuration file.

    Args:
        agent_name: One of 'claude-code', 'cursor', 'copilot', 'gemini'.
        wiki_path: Root path of the wiki.

    Returns:
        Path to the created configuration file.

    Raises:
        ConfigError: If agent_name is not supported.
    """
    if agent_name not in AGENT_TEMPLATES:
        supported = ", ".join(sorted(AGENT_TEMPLATES.keys()))
        raise ConfigError(
            f"Unsupported agent: {agent_name}. Supported: {supported}"
        )

    template = AGENT_TEMPLATES[agent_name]
    dest = wiki_path / template["filename"]
    dest.write_text(template["content"], encoding="utf-8")
    return dest
