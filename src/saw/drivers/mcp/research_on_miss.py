"""Research-on-Miss Handler for automatic knowledge gap filling.

Per XCUT-08 and FEATURES.md (llm-wiki1 pattern):
When query coverage falls below threshold, trigger parallel web/academic/code
searches and auto-ingest top results.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from saw.engines.ingest.pipeline import IngestPipeline
    from saw.config.settings import WikiSettings
    from saw.adapters.llm.router import LLMRouter


@dataclass
class ResearchResult:
    """Result of a research-on-miss operation.

    Attributes:
        query: Original query that triggered research.
        sources: List of sources found and processed.
        coverage_before: Coverage before research.
        coverage_after: Coverage after research (estimated).
        pages_added: List of wiki pages created.
        duration_ms: Duration in milliseconds.
    """
    query: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    coverage_before: float = 0.0
    coverage_after: float = 0.0
    pages_added: list[str] = field(default_factory=list)
    duration_ms: int = 0


class RateLimiter:
    """Simple rate limiter for external API calls.

    Per PITFALLS.md: External API rate limits respected.

    Attributes:
        calls_per_minute: Maximum calls per minute.
        _calls: List of timestamps for recent calls.
    """

    def __init__(self, calls_per_minute: int = 10) -> None:
        """Initialize rate limiter.

        Args:
            calls_per_minute: Maximum allowed calls per minute.
        """
        self._calls_per_minute = calls_per_minute
        self._calls: list[float] = []
        self._window = 60.0  # seconds

    def allow(self) -> bool:
        """Check if a call is allowed under rate limit.

        Returns:
            True if call is allowed, False if rate limit exceeded.
        """
        now = time.time()

        # Remove calls outside the window
        self._calls = [t for t in self._calls if now - t < self._window]

        # Check if under limit
        if len(self._calls) < self._calls_per_minute:
            self._calls.append(now)
            return True

        return False

    def time_until_next_call(self) -> float:
        """Get seconds until next call is allowed.

        Returns:
            Seconds to wait, or 0 if call is allowed.
        """
        if self.allow():
            return 0.0

        now = time.time()
        self._calls = [t for t in self._calls if now - t < self._window]

        if not self._calls:
            return 0.0

        # Time until oldest call falls out of window
        oldest = min(self._calls)
        return max(0.0, (oldest + self._window) - now)


class ResearchOnMissHandler:
    """Handler for automatic knowledge gap filling.

    Per XCUT-08: When coverage < threshold, trigger parallel research.

    Workflow:
    1. Check if coverage below threshold
    2. Generate optimized search queries via LLM
    3. Execute parallel web/academic/code searches
    4. Deduplicate and rank sources
    5. Auto-ingest top N sources
    """

    # Maximum sources to ingest per research trigger
    MAX_SOURCES_TO_INGEST = 5

    def __init__(
        self,
        ingest_pipeline: IngestPipeline,
        config: WikiSettings,
        llm_router: LLMRouter,
        calls_per_minute: int = 10,
    ) -> None:
        """Initialize research-on-miss handler.

        Args:
            ingest_pipeline: Pipeline for auto-ingestion.
            config: Wiki settings with coverage threshold.
            llm_router: LLM router for query generation.
            calls_per_minute: Rate limit for external API calls.
        """
        self._ingest = ingest_pipeline
        self._config = config
        self._llm = llm_router
        self._threshold = getattr(config, "coverage_threshold", 0.5)
        self._rate_limiter = RateLimiter(calls_per_minute)

    def should_trigger(self, coverage: float) -> bool:
        """Check if coverage falls below threshold.

        Args:
            coverage: Current coverage ratio (0.0 to 1.0).

        Returns:
            True if research should be triggered.
        """
        return coverage < self._threshold

    async def trigger_research(self, query: str) -> ResearchResult:
        """Trigger parallel research when coverage is low.

        Args:
            query: Original query that needs more coverage.

        Returns:
            ResearchResult with sources and pages added.
        """
        start_time = time.time()

        result = ResearchResult(query=query)

        try:
            # 1. Generate search queries using LLM
            search_queries = await self._generate_search_queries(query)

            # 2. Execute parallel searches
            web_results, academic_results, code_results = await asyncio.gather(
                self._web_search(search_queries.get("web", query)),
                self._academic_search(search_queries.get("academic", query)),
                self._code_search(search_queries.get("code", query)),
            )

            # 3. Combine all results
            all_sources = web_results + academic_results + code_results

            # 4. Deduplicate and rank
            deduped_sources = self._dedupe_sources(all_sources)

            # 5. Auto-ingest top sources
            pages_added: list[str] = []
            for source in deduped_sources[:self.MAX_SOURCES_TO_INGEST]:
                if self._rate_limiter.allow():
                    try:
                        ingest_result = self._ingest.ingest(source.get("url", ""))
                        if hasattr(ingest_result, "pages_created"):
                            pages_added.extend(ingest_result.pages_created or [])
                    except Exception as e:
                        # Log error but continue
                        pass

            result.sources = deduped_sources[:self.MAX_SOURCES_TO_INGEST]
            result.pages_added = pages_added

            # Estimate coverage improvement (placeholder)
            result.coverage_after = result.coverage_before + 0.1 * len(pages_added)

        except Exception as e:
            result.sources = [{"error": str(e)}]

        result.duration_ms = int((time.time() - start_time) * 1000)
        return result

    async def _generate_search_queries(self, query: str) -> dict[str, str]:
        """Use LLM to generate optimized search queries.

        Args:
            query: Original user query.

        Returns:
            Dict mapping search type to optimized query.
        """
        # Generate domain-specific queries
        # In production, this would use the LLM
        return {
            "web": query,
            "academic": f"{query} research paper",
            "code": f"{query} github",
        }

    async def _web_search(self, query: str) -> list[dict]:
        """Execute web search.

        Per PITFALLS.md: Use httpx for async.

        Args:
            query: Search query.

        Returns:
            List of search results with url, title, snippet.
        """
        results: list[dict] = []

        # In production, would call DuckDuckGo or SerpAPI
        # For now, return placeholder
        try:
            # Simulate web search
            results = [
                {"url": f"https://example.com/search?q={query}", "title": query, "snippet": ""}
            ]
        except Exception:
            pass

        return results

    async def _academic_search(self, query: str) -> list[dict]:
        """Execute academic paper search.

        Args:
            query: Search query.

        Returns:
            List of academic sources.
        """
        results: list[dict] = []

        # In production, would call arXiv or Semantic Scholar API
        try:
            results = [
                {"url": f"https://arxiv.org/search/?query={query}", "title": f"Academic: {query}", "snippet": ""}
            ]
        except Exception:
            pass

        return results

    async def _code_search(self, query: str) -> list[dict]:
        """Execute code repository search.

        Args:
            query: Search query.

        Returns:
            List of code repositories.
        """
        results: list[dict] = []

        # In production, would call GitHub search API
        try:
            results = [
                {"url": f"https://github.com/search?q={query}", "title": f"Code: {query}", "snippet": ""}
            ]
        except Exception:
            pass

        return results

    def _dedupe_sources(self, sources: list[dict]) -> list[dict]:
        """Deduplicate sources by URL.

        Args:
            sources: List of source dicts with url field.

        Returns:
            Deduplicated list of sources.
        """
        seen_urls: set[str] = set()
        deduped: list[dict] = []

        for source in sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduped.append(source)

        return deduped
