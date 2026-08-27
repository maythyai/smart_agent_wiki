"""Pure parsing helpers extracted from WikiCompileEngine (M-4 god-file split).

These operate on markdown strings and the compile domain models — no I/O, no
self/state — so they live here separately from the engine. Kept
behavior-identical to the original ``WikiCompileEngine._parse_*`` methods.
"""
from __future__ import annotations

import re
from typing import Optional

from saw.domain.utils import utcnow
from saw.domain.wiki_compile import (
    CompileLogEntry,
    WikiCompilePage,
    WikiConfidence,
    WikiIndex,
    WikiIndexEntry,
    WikiPageMetadata,
    WikiPageType,
)


def parse_index(content: str) -> WikiIndex:
    """Parse index.md content into a WikiIndex structure."""
    index = WikiIndex()
    current_topic = ""
    for line in content.split("\n"):
        if line.startswith("## "):
            current_topic = line[3:].strip().lower()
            index.topics.setdefault(current_topic, [])
        elif line.startswith("| [["):
            entry = parse_index_row(line)
            if entry and current_topic:
                index.topics[current_topic].append(entry)
    index.total_pages = sum(len(v) for v in index.topics.values())
    return index


def parse_index_row(line: str) -> Optional[WikiIndexEntry]:
    """Parse a table row from index.md."""
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 4:
        return None
    link_match = re.search(r"\[\[([^\]]+)\]\]", parts[1])
    if not link_match:
        return None
    return WikiIndexEntry(
        filename=link_match.group(1) + ".md",
        title=link_match.group(1).split("/")[-1],
        summary=parts[2] if len(parts) > 2 else "",
        updated=utcnow(),
        is_archived="[Archived]" in parts[1],
    )


def parse_page(filename: str, content: str) -> WikiCompilePage:
    """Parse a wiki page file into a WikiCompilePage."""
    meta_match = re.search(r"<!-- metadata:\n(.*?)-->", content, re.DOTALL)
    metadata = WikiPageMetadata(
        type=WikiPageType.CONCEPT,
        confidence=WikiConfidence.MEDIUM,
    )
    if meta_match:
        meta_text = meta_match.group(1)
        type_match = re.search(r"type:\s*(\S+)", meta_text)
        conf_match = re.search(r"confidence:\s*(\S+)", meta_text)
        if type_match:
            try:
                metadata.type = WikiPageType(type_match.group(1))
            except ValueError:
                pass
        if conf_match:
            try:
                metadata.confidence = WikiConfidence(conf_match.group(1))
            except ValueError:
                pass

    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else filename
    body = re.sub(r"<!-- metadata:.*?-->", "", content, flags=re.DOTALL).strip()

    return WikiCompilePage(
        filename=filename,
        title=title,
        content=body,
        metadata=metadata,
    )


def parse_log(content: str, limit: int) -> list[CompileLogEntry]:
    """Parse log.md into entries (most recent first)."""
    entries: list[CompileLogEntry] = []
    blocks = re.split(r"^## ", content, flags=re.MULTILINE)
    for block in blocks[1:]:  # Skip header
        lines = block.strip().split("\n")
        if not lines:
            continue
        header = lines[0]
        ts_match = re.match(r"(\d{4}-\d{2}-\d{2}T[\d:]+[+\d:]*)\s*—\s*(\w+)", header)
        if ts_match:
            action = ts_match.group(2).lower()
            summary = ""
            for line in lines[1:]:
                if line.startswith("- Summary:"):
                    summary = line[len("- Summary:"):].strip()
            entries.append(
                CompileLogEntry(timestamp=utcnow(), action=action, summary=summary)
            )
    return entries[:limit]


def render_empty_index() -> str:
    """Render an empty index.md template."""
    now = utcnow().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    return (
        "# Knowledge Wiki Index\n\n"
        f"> Auto-compiled by Smart Agent Wiki. Last updated: {now}\n"
        "> Total pages: 0 | Sources: 0 | Contradictions: 0\n\n"
    )
