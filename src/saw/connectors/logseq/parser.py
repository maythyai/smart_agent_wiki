"""Logseq Markdown parser.

Plan 13-01 Task 2: Logseq file parsing.
Per LOGS-02: Parse Markdown files and extract blocks as Claims.
Per LOGS-03: Extract property drawers as Claim metadata.
Per LOGS-08: Handle EDN format for Logseq configuration.
Per LOGS-09: Map Logseq namespaces to SAW Wiki page hierarchy.
Per LOGS-10: Preserve Logseq wikilink syntax during sync.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import edn_format
    EDN_AVAILABLE = True
except ImportError:
    EDN_AVAILABLE = False

from saw.connectors.logseq.models import (
    BlockNode,
    PropertyDrawer,
    ParsedPage,
)


class LogseqParser:
    """Parse Logseq Markdown files into structured data.

    Per LOGS-02: Extract blocks with correct nesting.
    Per LOGS-03: Parse property drawers.
    Per LOGS-09: Derive namespace from file path.
    Per LOGS-10: Preserve wikilink syntax.
    """

    # Regex patterns
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    BLOCK_PATTERN = re.compile(r"^(\s*)-\s+(.*)$", re.MULTILINE)
    WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
    PROPERTY_PATTERN = re.compile(r"^(\w+)::\s*(.*)$", re.MULTILINE)
    TAG_PATTERN = re.compile(r"#(\w+)")

    def __init__(self) -> None:
        """Initialize parser."""
        pass

    def parse_file(self, file_path: Path) -> ParsedPage:
        """Parse a Logseq Markdown file.

        Args:
            file_path: Path to the .md file.

        Returns:
            ParsedPage with all extracted data.
        """
        content = file_path.read_text(encoding="utf-8")

        # Extract frontmatter
        frontmatter, body = self._extract_frontmatter(content)
        properties = self._parse_frontmatter(frontmatter)

        # Derive namespace from file path
        namespace = self._derive_namespace(file_path)

        # Parse blocks
        blocks = self._parse_blocks(body, file_path)

        # Determine title
        title = properties.title or file_path.stem

        return ParsedPage(
            file_path=file_path,
            title=title,
            namespace=namespace,
            blocks=blocks,
            properties=properties,
        )

    def parse_edn_config(self, file_path: Path) -> dict[str, Any]:
        """Parse Logseq EDN configuration file.

        Per LOGS-08: Handle EDN format for Logseq configuration.

        Args:
            file_path: Path to config.edn file.

        Returns:
            Parsed configuration as dict.
        """
        if not EDN_AVAILABLE:
            return {}

        content = file_path.read_text(encoding="utf-8")
        try:
            parsed = edn_format.loads(content)
            # Convert edn_format types to regular Python types
            result = self._edn_to_dict(parsed)
            # Ensure we return a dict
            if isinstance(result, dict):
                return result
            return {}
        except Exception:
            return {}

    def _edn_to_dict(self, data: Any) -> Any:
        """Convert EDN data to Python types."""
        if isinstance(data, dict):
            return {str(k): self._edn_to_dict(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._edn_to_dict(item) for item in data]
        else:
            return data

    def _extract_frontmatter(self, content: str) -> tuple[str, str]:
        """Extract YAML frontmatter from content.

        Returns:
            Tuple of (frontmatter_str, body_str).
        """
        match = self.FRONTMATTER_PATTERN.match(content)
        if match:
            frontmatter = match.group(1)
            body = content[match.end():]
            return frontmatter, body
        return "", content

    def _parse_frontmatter(self, frontmatter: str) -> PropertyDrawer:
        """Parse YAML frontmatter into PropertyDrawer.

        Per LOGS-03: Extract property drawers as Claim metadata.
        """
        if not frontmatter:
            return PropertyDrawer(title="")

        # Simple YAML-like parsing (avoid pyyaml dependency)
        properties: dict[str, Any] = {}
        for line in frontmatter.split("\n"):
            line = line.strip()
            # Handle Logseq property syntax: key:: value (double colon)
            if "::" in line:
                key, value = line.split("::", 1)
                key = key.strip()
                value = value.strip()
            elif ":" in line and "::" not in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
            else:
                continue

            # Parse values
            if key == "tags":
                # Parse [[tag]] format
                tags = self.WIKILINK_PATTERN.findall(value)
                properties[key] = [[t] for t in tags]
            elif key == "id":
                properties[key] = value
            elif key == "title":
                properties[key] = value
            elif key == "confidence":
                properties[key] = value
            elif key == "created_at":
                try:
                    properties[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
            else:
                properties[key] = value

        return PropertyDrawer(
            title=properties.get("title", ""),
            id=properties.get("id"),
            tags=properties.get("tags", []),
            confidence=properties.get("confidence"),
            created_at=properties.get("created_at"),
            custom={k: v for k, v in properties.items()
                   if k not in ("title", "id", "tags", "confidence", "created_at")},
        )

    def _derive_namespace(self, file_path: Path) -> str:
        """Derive namespace from file path.

        Per LOGS-09: Map Logseq namespaces to SAW Wiki page hierarchy.
        """
        parts = file_path.parts
        # Find 'pages' directory in path
        if "pages" in parts:
            pages_idx = parts.index("pages")
            relative_parts = parts[pages_idx + 1:-1]  # Skip 'pages' and filename
            return "/".join(relative_parts) if relative_parts else ""
        return ""

    def _parse_blocks(self, body: str, file_path: Path) -> list[BlockNode]:
        """Parse bullet blocks from body.

        Per LOGS-02: Extract blocks with correct nesting.
        Per LOGS-10: Preserve wikilink syntax.
        """
        blocks: list[BlockNode] = []
        block_stack: list[tuple[int, str]] = []  # (level, block_id)
        block_idx = 0

        # Generate file ID from path
        file_id = hashlib.md5(str(file_path).encode()).hexdigest()[:8]

        for line in body.split("\n"):
            match = self.BLOCK_PATTERN.match(line)
            if match:
                indent = len(match.group(1))
                level = indent // 2  # Logseq uses 2-space indentation
                content = match.group(2).strip()

                # Extract inline properties (:: syntax)
                props = {}
                prop_match = self.PROPERTY_PATTERN.search(content)
                if prop_match:
                    props[prop_match.group(1)] = prop_match.group(2)

                block_id = f"{file_id}-{block_idx}"
                block_idx += 1

                # Determine parent
                parent_id: Optional[str] = None
                while block_stack and block_stack[-1][0] >= level:
                    block_stack.pop()
                if block_stack and level > 0:
                    parent_id = block_stack[-1][1]

                blocks.append(BlockNode(
                    id=block_id,
                    content=content,  # Wikilinks preserved as-is
                    level=level,
                    parent_id=parent_id,
                    properties=props,
                ))
                block_stack.append((level, block_id))

        return blocks


def compute_file_hash(content: str) -> str:
    """Compute SHA-256 hash of file content.

    Per LOGS-06: Detect concurrent edits via hash comparison.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
