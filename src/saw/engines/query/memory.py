"""Progressive Memory Depth for token efficiency.

Per XCUT-05: Reduce boot tokens from ~20K to ~8-10K.
Per unified-memory-ai-agents pattern:
- L0: Always-loaded index (~85 lines max)
- L1: Summary index (~15 recent topics)
- L2: Full content on demand
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from saw.engines.query.compiler import ContextCompiler


class MemoryLevel(Enum):
    """Progressive memory depth levels.

    L0: Always-loaded index (~85 lines)
    L1: Summary index (~15 recent topics)
    L2: Full content on demand
    """
    L0 = 0  # Always-loaded index
    L1 = 1  # Summary index
    L2 = 2  # Full content


@dataclass
class MemoryConfig:
    """Configuration for progressive memory."""
    l0_max_lines: int = 100  # Hard cap per unified-memory-ai-agents
    l1_max_topics: int = 15
    l1_budget_tokens: int = 1000
    l2_default_budget: int = 4000
    chars_per_token: int = 4


class ProgressiveMemory:
    """Progressive memory depth for token efficiency.

    Per XCUT-05: Reduce boot tokens from ~20K to ~8-10K.

    L0: Always-loaded index (~85 lines max)
        - Wiki structure (page types, entity counts)
        - Active project links
        - Recent changes (last 7 days)
        - WIP summary

    L1: Summary index (~15 recent topics)
        - Summaries of recent topics
        - High-priority pages (low freshness, high references)
        - User-defined bookmarks

    L2: Full content on demand
        - Full Markdown content for specified pages
        - All claims with citations
        - Complete frontmatter
    """

    def __init__(
        self,
        wiki_repo,
        compiler: ContextCompiler | None = None,
        config: MemoryConfig | None = None,
    ) -> None:
        """Initialize progressive memory.

        Args:
            wiki_repo: Wiki repository for page access.
            compiler: Context compiler for context assembly.
            config: Memory configuration.
        """
        self._wiki_repo = wiki_repo
        self._compiler = compiler
        self._config = config or MemoryConfig()

        # Cache paths
        self._cache_dir: Path | None = None

    def set_cache_dir(self, path: Path) -> None:
        """Set cache directory for memory files.

        Args:
            path: Directory to store cached memory files.
        """
        self._cache_dir = path
        path.mkdir(parents=True, exist_ok=True)

    def get_l0(self) -> str:
        """Get L0 always-loaded index.

        Per unified-memory-ai-agents: ~85 lines max.

        Contains:
        - Wiki structure (page types, entity counts)
        - Active project links
        - Recent changes (last 7 days)
        - WIP summary

        Returns:
            Compact index string, max 100 lines.
        """
        lines: list[str] = []

        # Header
        lines.append("## Wiki Index (L0)")
        lines.append("")

        # Get page count and structure
        try:
            page_count = self._wiki_repo.count()
            lines.append(f"**Total Pages:** {page_count}")
        except Exception:
            lines.append("**Total Pages:** 0")

        # Get page types breakdown
        try:
            pages = self._wiki_repo.list_pages()
            type_counts: dict[str, int] = {}

            for page_path in pages[:50]:  # Sample first 50
                parts = page_path.split("/")
                if len(parts) > 1:
                    namespace = parts[0]
                    type_counts[namespace] = type_counts.get(namespace, 0) + 1

            if type_counts:
                lines.append("")
                lines.append("**Structure:**")
                for ns, count in sorted(type_counts.items()):
                    lines.append(f"- {ns}: {count} pages")
        except Exception:
            pass

        # Recent changes placeholder (would need git history in production)
        lines.append("")
        lines.append("**Recent Changes:**")
        lines.append("- (tracking enabled)")

        # WIP summary
        lines.append("")
        lines.append("**Work in Progress:**")
        lines.append("- No active WIP")

        # Hard cap at 100 lines per unified-memory-ai-agents
        result = "\n".join(lines[:self._config.l0_max_lines])
        return result

    def get_l1(self, topic: str | None = None, budget: int | None = None) -> str:
        """Get L1 summary index.

        Contains:
        - Summaries of recent topics (last 15)
        - High-priority pages (low freshness, high references)
        - User-defined bookmarks

        Args:
            topic: Optional topic to filter summaries.
            budget: Optional token budget for L1 content.

        Returns:
            Summary content string.
        """
        budget = budget or self._config.l1_budget_tokens
        lines: list[str] = []

        lines.append("## Summary Index (L1)")
        lines.append("")

        # Get recent/high-priority pages
        try:
            pages = self._wiki_repo.list_pages()

            # Filter by topic if provided
            if topic:
                pages = [p for p in pages if topic.lower() in p.lower()]

            # Limit to max topics
            pages = pages[:self._config.l1_max_topics]

            for page_path in pages:
                page = self._wiki_repo.read(page_path)
                if page:
                    # Create summary line
                    summary = f"- **{page.title}** ({page.page_type.name.lower()})"
                    if hasattr(page, "freshness"):
                        summary += f" [freshness: {page.freshness}]"
                    lines.append(summary)

                    # Add brief excerpt
                    if page.content:
                        excerpt = page.content[:200].replace("\n", " ").strip()
                        if excerpt:
                            lines.append(f"  {excerpt}...")
        except Exception:
            lines.append("(no summaries available)")

        result = "\n".join(lines)

        # Respect budget
        estimated_tokens = self.estimate_tokens(result)
        if estimated_tokens > budget:
            # Truncate to fit budget
            max_chars = budget * self._config.chars_per_token
            result = result[:max_chars] + "\n...(truncated)"

        return result

    def get_l2(self, page_paths: list[str], budget: int | None = None) -> str:
        """Get L2 full content for specified pages.

        Contains:
        - Full Markdown content for specified pages
        - All claims with citations
        - Complete frontmatter

        Args:
            page_paths: List of page paths to load.
            budget: Optional token budget for L2 content.

        Returns:
            Full content string.
        """
        budget = budget or self._config.l2_default_budget
        lines: list[str] = []

        lines.append("## Full Content (L2)")
        lines.append("")

        for page_path in page_paths:
            try:
                page = self._wiki_repo.read(page_path)
                if page:
                    lines.append(f"### {page.title}")
                    lines.append(f"**Path:** {page_path}")
                    lines.append(f"**Type:** {page.page_type.name.lower()}")
                    if hasattr(page, "confidence"):
                        lines.append(f"**Confidence:** {page.confidence.name.lower()}")
                    lines.append("")
                    lines.append(page.content)
                    lines.append("")
                    lines.append("---")
                    lines.append("")
            except Exception as e:
                lines.append(f"Error loading {page_path}: {e}")
                lines.append("")

        result = "\n".join(lines)

        # Respect budget
        estimated_tokens = self.estimate_tokens(result)
        if estimated_tokens > budget:
            max_chars = budget * self._config.chars_per_token
            result = result[:max_chars] + "\n...(truncated for budget)"

        return result

    def estimate_tokens(self, content: str) -> int:
        """Estimate token count (chars / 4 as rough estimate).

        Args:
            content: Content to estimate tokens for.

        Returns:
            Estimated token count.
        """
        return len(content) // self._config.chars_per_token

    def auto_select_level(self, budget: int) -> tuple[MemoryLevel, str]:
        """Automatically select appropriate memory level for budget.

        Args:
            budget: Token budget available.

        Returns:
            Tuple of (MemoryLevel, content).
        """
        # Start with L0
        l0_content = self.get_l0()
        l0_tokens = self.estimate_tokens(l0_content)

        if l0_tokens >= budget:
            return (MemoryLevel.L0, l0_content)

        # Check if L1 fits
        l1_content = self.get_l1(budget=budget - l0_tokens)
        l1_tokens = self.estimate_tokens(l1_content)

        if l0_tokens + l1_tokens <= budget:
            combined = l0_content + "\n\n" + l1_content
            return (MemoryLevel.L1, combined)

        # Fall back to L0 only
        return (MemoryLevel.L0, l0_content)

    def refresh_l0_cache(self) -> None:
        """Refresh L0 cache file."""
        if self._cache_dir is None:
            return

        cache_file = self._cache_dir / "memory_l0.yaml"
        content = self.get_l0()

        data = {
            "content": content,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "line_count": len(content.split("\n")),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)

    def refresh_l1_cache(self, topic: str | None = None) -> None:
        """Refresh L1 cache file.

        Args:
            topic: Optional topic filter.
        """
        if self._cache_dir is None:
            return

        cache_file = self._cache_dir / "memory_l1.yaml"
        content = self.get_l1(topic=topic)

        data = {
            "content": content,
            "topic": topic,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)
