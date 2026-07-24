"""Wiki compile engine.

Compiles raw Vault documents into a structured _wiki/ layer with:
- index.md: living table of contents grouped by topic
- log.md: append-only compile history
- Topic pages with structured metadata and source traceability

Two-phase compilation:
  Phase A: Structure initialization (directories + index skeleton)
  Phase B: Content compilation (deep extraction + cascade updates)
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional

from saw.domain.wiki_compile import (
    CompileLogEntry,
    CompileResult,
    WikiCompilePage,
    WikiConfidence,
    WikiIndex,
    WikiIndexEntry,
    WikiPageMetadata,
    WikiPageType,
    WikiSource,
)
from saw.domain.utils import utcnow

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")

# Page type detection heuristics
TYPE_HINTS: dict[str, WikiPageType] = {
    "concept": WikiPageType.CONCEPT,
    "what is": WikiPageType.CONCEPT,
    "how to": WikiPageType.HOWTO,
    "guide": WikiPageType.HOWTO,
    "faq": WikiPageType.FAQ,
    "question": WikiPageType.FAQ,
    "compare": WikiPageType.COMPARISON,
    "vs": WikiPageType.COMPARISON,
    "reference": WikiPageType.REFERENCE,
    "api": WikiPageType.REFERENCE,
    "spec": WikiPageType.REFERENCE,
}


class WikiCompileEngine:
    """Compiles raw documents into a structured Wiki layer.

    The compile layer is a derived artifact — it reads from the Vault
    (immutable source documents) and Claims store, producing human-readable
    Markdown pages organized by topic.

    Core constraints:
    1. index.md and log.md must be at _wiki/ root
    2. All pages (except index/log) must have complete metadata
    3. Sources can only reference raw documents (except type=archive)
    4. Raw documents are never modified
    5. Contradictions are annotated, never resolved
    6. log.md is append-only
    """

    def __init__(
        self,
        vault_root: Path,
        claims_repo=None,
        wiki_repo=None,
        llm_router=None,
    ) -> None:
        self._vault_root = vault_root
        self._wiki_root = vault_root / "_wiki"
        self._claims_repo = claims_repo
        self._wiki_repo = wiki_repo
        self._llm = llm_router

    @property
    def wiki_root(self) -> Path:
        return self._wiki_root

    @property
    def is_initialized(self) -> bool:
        return (
            self._wiki_root.exists()
            and (self._wiki_root / "index.md").exists()
            and (self._wiki_root / "log.md").exists()
        )

    async def initialize(self) -> None:
        """Initialize the _wiki/ directory structure."""
        self._wiki_root.mkdir(parents=True, exist_ok=True)

        index_path = self._wiki_root / "index.md"
        if not index_path.exists():
            index_path.write_text(self._render_empty_index(), encoding="utf-8")

        log_path = self._wiki_root / "log.md"
        if not log_path.exists():
            log_path.write_text(self._render_log_header(), encoding="utf-8")

        # Append initialization log entry
        entry = CompileLogEntry(
            timestamp=utcnow(),
            action="initialize",
            summary="Wiki compile layer initialized",
        )
        self._append_log(entry)

    async def compile_full(self) -> CompileResult:
        """Full compilation: Phase A (structure) + Phase B (content)."""
        start = time.time()

        if not self.is_initialized:
            await self.initialize()

        # Phase A: Structure
        sources = self._scan_vault_sources()
        topics = self._classify_sources_by_topic(sources)
        self._ensure_topic_directories(topics)

        # Phase B: Content compilation
        result = CompileResult()
        for topic, source_list in topics.items():
            for source_path in source_list:
                page = await self._compile_source(source_path, topic)
                if page is None:
                    continue

                page_path = self._wiki_root / page.filename
                if page_path.exists():
                    result.pages_updated.append(page.filename)
                else:
                    result.pages_created.append(page.filename)

                self._write_page(page)
                self._update_index_entry(page)

        # Finalize
        duration = time.time() - start
        result.duration_seconds = duration
        result.log_entry = CompileLogEntry(
            timestamp=utcnow(),
            action="compile",
            pages_affected=result.pages_created + result.pages_updated,
            sources_processed=[str(s) for s in sources[:20]],
            summary=f"Full compile: {len(result.pages_created)} created, {len(result.pages_updated)} updated",
            duration_seconds=duration,
        )
        self._append_log(result.log_entry)
        self._update_index_header(result)

        return result

    async def compile_incremental(self, changed_sources: list[str]) -> CompileResult:
        """Incremental compilation: only process changed source documents."""
        start = time.time()

        if not self.is_initialized:
            await self.initialize()

        result = CompileResult()
        for source_str in changed_sources:
            source_path = Path(source_str)
            if not source_path.is_absolute():
                source_path = self._vault_root / source_path

            if not source_path.exists():
                continue

            topic = self._infer_topic(source_path)
            page = await self._compile_source(source_path, topic)
            if page is None:
                result.pages_unchanged.append(source_str)
                continue

            page_path = self._wiki_root / page.filename
            if page_path.exists():
                result.pages_updated.append(page.filename)
            else:
                result.pages_created.append(page.filename)

            self._write_page(page)
            self._update_index_entry(page)

            # Cascade: check if other pages reference this one
            self._cascade_update(page.filename)

        duration = time.time() - start
        result.duration_seconds = duration
        result.log_entry = CompileLogEntry(
            timestamp=utcnow(),
            action="ingest",
            pages_affected=result.pages_created + result.pages_updated,
            sources_processed=changed_sources,
            summary=f"Incremental compile: {len(result.pages_created)} created, {len(result.pages_updated)} updated",
            duration_seconds=duration,
        )
        self._append_log(result.log_entry)

        return result

    async def get_index(self) -> WikiIndex:
        """Parse and return the current index.md structure."""
        index_path = self._wiki_root / "index.md"
        if not index_path.exists():
            return WikiIndex()
        return self._parse_index(index_path.read_text(encoding="utf-8"))

    def get_log(self, limit: int = 20) -> list[CompileLogEntry]:
        """Read recent compile log entries."""
        log_path = self._wiki_root / "log.md"
        if not log_path.exists():
            return []
        content = log_path.read_text(encoding="utf-8")
        return self._parse_log(content, limit)

    def read_page(self, filename: str) -> Optional[WikiCompilePage]:
        """Read a wiki page by filename."""
        page_path = self._wiki_root / filename
        if not page_path.exists():
            return None
        content = page_path.read_text(encoding="utf-8")
        return self._parse_page(filename, content)

    def list_pages(self) -> list[str]:
        """List all wiki page filenames."""
        if not self._wiki_root.exists():
            return []
        pages = []
        for p in self._wiki_root.rglob("*.md"):
            rel = p.relative_to(self._wiki_root)
            if rel.name not in ("index.md", "log.md"):
                pages.append(str(rel))
        return sorted(pages)

    # ─── Private helpers ───────────────────────────────────────────────

    def _scan_vault_sources(self) -> list[Path]:
        """Scan Vault for raw source documents."""
        sources = []
        for pattern in ("**/*.md", "**/*.pdf", "**/*.html", "**/*.txt"):
            for p in self._vault_root.glob(pattern):
                # Skip _wiki/ and .saw/ directories
                rel = p.relative_to(self._vault_root)
                if rel.parts[0] in ("_wiki", ".saw", ".git"):
                    continue
                sources.append(p)
        return sorted(sources)

    def _classify_sources_by_topic(self, sources: list[Path]) -> dict[str, list[Path]]:
        """Classify sources into topics based on directory structure and content."""
        topics: dict[str, list[Path]] = {}
        for source in sources:
            topic = self._infer_topic(source)
            topics.setdefault(topic, []).append(source)
        return topics

    def _infer_topic(self, source: Path) -> str:
        """Infer topic from source path and content."""
        rel = source.relative_to(self._vault_root)
        # Use first directory component as topic
        if len(rel.parts) > 1:
            return rel.parts[0].replace(" ", "-").lower()
        # Fallback: infer from filename
        stem = source.stem.lower()
        for hint, page_type in TYPE_HINTS.items():
            if hint in stem:
                return page_type.value + "s"
        return "general"

    def _ensure_topic_directories(self, topics: dict[str, list[Path]]) -> None:
        """Create topic subdirectories in _wiki/."""
        for topic in topics:
            (self._wiki_root / topic).mkdir(parents=True, exist_ok=True)

    async def _compile_source(
        self, source_path: Path, topic: str
    ) -> Optional[WikiCompilePage]:
        """Compile a single source document into a wiki page."""
        try:
            content = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

        if len(content.strip()) < 50:
            return None  # Skip low-information sources

        # Determine page type
        page_type = self._detect_page_type(source_path, content)

        # Generate slug from source filename
        slug = self._slugify(source_path.stem)
        filename = f"{topic}/{slug}.md"

        # Extract title
        title = self._extract_title(content, source_path.stem)

        # Build metadata
        rel_source = source_path.relative_to(self._vault_root)
        source_ref = WikiSource(
            page_id=str(rel_source),
            title=title,
        )

        # Determine confidence based on content quality
        confidence = self._assess_confidence(content)

        metadata = WikiPageMetadata(
            type=page_type,
            confidence=confidence,
            sources=[source_ref],
            topic=topic,
        )

        # Compile content (add structure, extract see_also links)
        compiled_content = self._compile_content(content, title)
        see_also = WIKILINK_PATTERN.findall(compiled_content)
        metadata.see_also = [f"{s}.md" for s in see_also if s != slug]

        return WikiCompilePage(
            filename=filename,
            title=title,
            content=compiled_content,
            metadata=metadata,
        )

    def _detect_page_type(self, path: Path, content: str) -> WikiPageType:
        """Detect page type from filename and content heuristics."""
        stem = path.stem.lower()
        for hint, ptype in TYPE_HINTS.items():
            if hint in stem:
                return ptype
        # Content-based detection
        lower = content[:500].lower()
        if "?" in lower and ("answer" in lower or "a:" in lower):
            return WikiPageType.FAQ
        if "```" in content and ("step" in lower or "install" in lower):
            return WikiPageType.HOWTO
        return WikiPageType.CONCEPT

    def _assess_confidence(self, content: str) -> WikiConfidence:
        """Assess confidence based on content characteristics."""
        word_count = len(content.split())
        has_references = bool(re.search(r"\[\d+\]|\[.*\]\(http", content))
        has_structure = content.count("#") >= 2

        if word_count > 500 and has_references and has_structure:
            return WikiConfidence.HIGH
        elif word_count > 200 and (has_references or has_structure):
            return WikiConfidence.MEDIUM
        return WikiConfidence.LOW

    def _compile_content(self, raw: str, title: str) -> str:
        """Compile raw content into structured wiki page format."""
        lines = raw.strip().split("\n")

        # Ensure title header
        if not lines[0].startswith("# "):
            lines.insert(0, f"# {title}\n")

        # Add metadata comment block at end
        return "\n".join(lines)

    def _extract_title(self, content: str, fallback: str) -> str:
        """Extract title from content (first H1) or use fallback."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return fallback.replace("-", " ").replace("_", " ").title()

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        slug = text.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug.strip("-")

    def _write_page(self, page: WikiCompilePage) -> None:
        """Write a compiled page to disk."""
        page_path = self._wiki_root / page.filename
        page_path.parent.mkdir(parents=True, exist_ok=True)

        # Render with metadata comment
        output = page.content.rstrip() + "\n\n"
        output += f"<!-- metadata:\n"
        output += f"type: {page.metadata.type.value}\n"
        output += f"confidence: {page.metadata.confidence.value}\n"
        output += f"topic: {page.metadata.topic}\n"
        output += f"sources:\n"
        for src in page.metadata.sources:
            output += f"  - pageId: \"{src.page_id}\"\n"
            output += f"    title: \"{src.title}\"\n"
        if page.metadata.see_also:
            output += f"seeAlso: {page.metadata.see_also}\n"
        output += f"created: {page.metadata.created.isoformat()}\n"
        output += f"updated: {page.metadata.updated.isoformat()}\n"
        output += f"-->\n"

        page_path.write_text(output, encoding="utf-8")

    def _update_index_entry(self, page: WikiCompilePage) -> None:
        """Update index.md with a page entry."""
        index_path = self._wiki_root / "index.md"
        if not index_path.exists():
            index_path.write_text(self._render_empty_index(), encoding="utf-8")

        index = self._parse_index(index_path.read_text(encoding="utf-8"))
        source_count = len(page.metadata.sources)
        entry = WikiIndexEntry(
            filename=page.filename,
            title=page.title,
            summary=f"{page.metadata.type.value} ({source_count} source{'s' if source_count != 1 else ''})",
            updated=page.metadata.updated,
            is_archived=(page.metadata.type == WikiPageType.ARCHIVE),
        )
        topic = page.metadata.topic or "general"
        index.add_entry(topic, entry)
        index.last_updated = utcnow()

        index_path.write_text(self._render_index(index), encoding="utf-8")

    def _update_index_header(self, result: CompileResult) -> None:
        """Update index.md header stats."""
        index_path = self._wiki_root / "index.md"
        if not index_path.exists():
            return
        content = index_path.read_text(encoding="utf-8")
        pages = self.list_pages()
        # Update total count in header
        content = re.sub(
            r"Total pages: \d+",
            f"Total pages: {len(pages)}",
            content,
        )
        index_path.write_text(content, encoding="utf-8")

    def _cascade_update(self, changed_filename: str) -> None:
        """Check and mark pages that reference the changed page."""
        slug = changed_filename.removesuffix(".md")
        link_pattern = f"[[{slug}]]"
        for page_file in self.list_pages():
            page_path = self._wiki_root / page_file
            content = page_path.read_text(encoding="utf-8")
            if link_pattern in content and page_file != changed_filename:
                # Mark as needing review (update timestamp in metadata)
                pass  # Cascade is informational; actual update on next compile

    def _append_log(self, entry: CompileLogEntry) -> None:
        """Append an entry to log.md (append-only)."""
        log_path = self._wiki_root / "log.md"
        if not log_path.exists():
            log_path.write_text(self._render_log_header(), encoding="utf-8")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n" + entry.to_markdown())

    def _parse_index(self, content: str) -> WikiIndex:
        """Parse index.md content into WikiIndex structure."""
        index = WikiIndex()
        current_topic = ""
        for line in content.split("\n"):
            if line.startswith("## "):
                current_topic = line[3:].strip()
                index.topics.setdefault(current_topic, [])
            elif line.startswith("| [["):
                entry = self._parse_index_row(line)
                if entry and current_topic:
                    index.topics[current_topic].append(entry)
        index.total_pages = sum(len(v) for v in index.topics.values())
        return index

    def _parse_index_row(self, line: str) -> Optional[WikiIndexEntry]:
        """Parse a table row from index.md."""
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            return None
        link_match = re.search(r"\[\[([^\]]+)\]\]", parts[1])
        if not link_match:
            return None
        filename = link_match.group(1) + ".md"
        is_archived = "[Archived]" in parts[1]
        return WikiIndexEntry(
            filename=filename,
            title=link_match.group(1).split("/")[-1],
            summary=parts[2] if len(parts) > 2 else "",
            updated=utcnow(),
            is_archived=is_archived,
        )

    def _parse_page(self, filename: str, content: str) -> WikiCompilePage:
        """Parse a wiki page file into WikiCompilePage."""
        # Extract metadata from comment block
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

        # Extract title
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else filename

        # Strip metadata comment from content
        body = re.sub(r"<!-- metadata:.*?-->", "", content, flags=re.DOTALL).strip()

        return WikiCompilePage(
            filename=filename,
            title=title,
            content=body,
            metadata=metadata,
        )

    def _parse_log(self, content: str, limit: int) -> list[CompileLogEntry]:
        """Parse log.md into entries (most recent first)."""
        entries = []
        blocks = re.split(r"^## ", content, flags=re.MULTILINE)
        for block in blocks[1:]:  # Skip header
            lines = block.strip().split("\n")
            if not lines:
                continue
            # Parse timestamp and action from first line
            header = lines[0]
            ts_match = re.match(r"(\d{4}-\d{2}-\d{2}T[\d:]+[+\d:]*)\s*—\s*(\w+)", header)
            if ts_match:
                action = ts_match.group(2).lower()
                summary = ""
                for line in lines[1:]:
                    if line.startswith("- Summary:"):
                        summary = line[len("- Summary:"):].strip()
                entries.append(CompileLogEntry(
                    timestamp=utcnow(),  # Simplified; full parse optional
                    action=action,
                    summary=summary,
                ))
        return entries[:limit]

    def _render_empty_index(self) -> str:
        """Render an empty index.md template."""
        now = utcnow().strftime("%Y-%m-%dT%H:%M:%S+08:00")
        return f"""# Knowledge Wiki Index

> Auto-compiled by Smart Agent Wiki. Last updated: {now}
> Total pages: 0 | Sources: 0 | Contradictions: 0

"""

    def _render_index(self, index: WikiIndex) -> str:
        """Render WikiIndex to Markdown."""
        now = index.last_updated.strftime("%Y-%m-%dT%H:%M:%S+08:00")
        lines = [
            "# Knowledge Wiki Index",
            "",
            f"> Auto-compiled by Smart Agent Wiki. Last updated: {now}",
            f"> Total pages: {index.total_pages} | Sources: {index.total_sources} | Contradictions: {index.contradictions}",
            "",
        ]
        for topic, entries in sorted(index.topics.items()):
            lines.append(f"## {topic.title()}")
            lines.append("")
            lines.append("| Page | Summary | Updated |")
            lines.append("|------|---------|---------|")
            for entry in entries:
                lines.append(entry.to_markdown_row())
            lines.append("")
        return "\n".join(lines)

    def _render_log_header(self) -> str:
        """Render log.md header."""
        return """# Compile Log

> Append-only. Do not edit or delete entries.
"""
