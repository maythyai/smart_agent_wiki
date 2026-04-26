"""HTML Parser for URL content extraction using trafilatura.

Per INGE-03: URL ingestion via trafilatura.
Per RESEARCH.md: Verified trafilatura fetch_url + extract patterns.
"""
from __future__ import annotations

from dataclasses import dataclass

import trafilatura


@dataclass
class HTMLParseResult:
    """Result of parsing HTML from URL."""
    url: str
    content: str
    title: str
    format: str = "html"


class HTMLParser:
    """Extract content from URLs using trafilatura."""

    def parse(self, url: str) -> HTMLParseResult:
        """Parse HTML content from URL.

        Args:
            url: URL to fetch and parse.

        Returns:
            HTMLParseResult with extracted content.

        Raises:
            ValueError: If URL cannot be fetched.
        """
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Failed to fetch URL: {url}")

        # Extract main content (per RESEARCH.md verified pattern)
        result = trafilatura.extract(
            downloaded,
            include_links=True,
            include_tables=True,
        )

        if not result:
            raise ValueError(f"Failed to extract content from URL: {url}")

        # Extract metadata
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else url

        return HTMLParseResult(
            url=url,
            content=result,
            title=title,
            format="html",
        )