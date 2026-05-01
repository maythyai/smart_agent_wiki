"""Domain entities and value objects for RSS feed management.

Phase 9: RSS Subscription — Domain layer.
Per RSSS-01~07: Feed configuration and entry deduplication.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saw.db.feed_models import FeedEntry


class EntryStatus(str, Enum):
    """Status of a feed entry."""
    NEW = "new"
    UPDATED = "updated"
    HISTORICAL = "historical"


@dataclass
class EntryHash:
    """Compute and store content hash for deduplication."""

    @staticmethod
    def compute(content: str) -> str:
        """Compute SHA256 hash of normalized content.

        Normalization:
        - Strip HTML tags
        - Collapse whitespace
        - Lowercase

        Args:
            content: Raw content string.

        Returns:
            SHA256 hex digest.
        """
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Lowercase and strip
        text = text.lower().strip()

        return hashlib.sha256(text.encode('utf-8')).hexdigest()


@dataclass
class DeduplicationKey:
    """Multi-key deduplication identifier.

    Per Pitfall 25: Use GUID + title hash + content hash for stable identification.
    """
    guid: str
    title_hash: str  # MD5 of title (first 8 chars)
    content_hash: str  # SHA256 of content (first 8 chars)

    def compute_id(self) -> str:
        """Generate composite deduplication ID.

        Returns:
            Composite key: f"{guid}:{title_hash}:{content_hash}"
        """
        return f"{self.guid}:{self.title_hash}:{self.content_hash}"

    @classmethod
    def from_entry(cls, guid: str, title: str, content: str) -> "DeduplicationKey":
        """Create DeduplicationKey from entry data.

        Args:
            guid: Entry GUID from feed.
            title: Entry title.
            content: Entry content.

        Returns:
            DeduplicationKey instance.
        """
        title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
        content_hash = EntryHash.compute(content)[:8]

        return cls(
            guid=guid,
            title_hash=title_hash,
            content_hash=content_hash,
        )


@dataclass
class FeedConfig:
    """Configuration for a feed subscription.

    Validates poll_interval bounds per Pitfall 27.
    """
    url: str
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    poll_interval: int = 3600  # Default 1 hour
    active: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate URL scheme
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with http:// or https://: {self.url}")

        # Validate poll_interval bounds
        if not (900 <= self.poll_interval <= 86400):
            raise ValueError(
                f"poll_interval must be between 900 (15 min) and 86400 (24 hours), "
                f"got {self.poll_interval}"
            )


def normalize_url(url: str) -> str:
    """Remove tracking parameters from URL.

    Per Pitfall 25: Normalize URLs before comparison.

    Args:
        url: Raw URL with potential tracking parameters.

    Returns:
        Cleaned URL without tracking parameters.
    """
    # List of tracking parameters to remove
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'ref', 'source', 'campaign', 'fbclid', 'gclid', 'msclkid',
    }

    try:
        parsed = urlparse(url)

        # Parse query parameters
        params = parse_qs(parsed.query, keep_blank_values=True)

        # Remove tracking parameters
        filtered_params = {
            k: v for k, v in params.items()
            if k.lower() not in tracking_params
        }

        # Rebuild query string
        new_query = urlencode(filtered_params, doseq=True)

        # Reconstruct URL
        cleaned = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            None,  # Remove fragment for deduplication
        ))

        return cleaned

    except Exception:
        # If parsing fails, return original URL
        return url


def title_similarity(title1: str, title2: str) -> float:
    """Compute normalized Levenshtein similarity between titles.

    Args:
        title1: First title.
        title2: Second title.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    # Normalize both titles
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()

    # Use SequenceMatcher for edit distance
    return SequenceMatcher(None, t1, t2).ratio()


@dataclass
class DeduplicationResult:
    """Result of a deduplication check."""
    is_duplicate: bool
    entry_id: str | None
    similarity_score: float
    match_type: str  # "exact_guid" | "fuzzy_title" | "content_hash" | "none"


class DeduplicationService:
    """Service for detecting duplicate feed entries.

    Per Pitfall 25: Multi-key deduplication with fuzzy matching.
    """

    def check_duplicate(
        self,
        guid: str,
        title: str,
        content: str,
        existing_entries: list[FeedEntry],
    ) -> DeduplicationResult:
        """Check if entry is duplicate of existing entries.

        Checks in order:
        1. Exact GUID match
        2. Content hash match
        3. Fuzzy title match (similarity > 0.9)

        Args:
            guid: Entry GUID from feed.
            title: Entry title.
            content: Entry content.
            existing_entries: List of existing entries to check against.

        Returns:
            DeduplicationResult with match information.
        """
        content_hash = EntryHash.compute(content)

        for entry in existing_entries:
            # 1. Exact GUID match
            if entry.guid == guid:
                return DeduplicationResult(
                    is_duplicate=True,
                    entry_id=entry.id,
                    similarity_score=1.0,
                    match_type="exact_guid",
                )

            # 2. Content hash match
            if entry.content_hash and entry.content_hash == content_hash:
                return DeduplicationResult(
                    is_duplicate=True,
                    entry_id=entry.id,
                    similarity_score=1.0,
                    match_type="content_hash",
                )

            # 3. Fuzzy title match
            if entry.title:
                similarity = title_similarity(title, entry.title)
                if similarity > 0.9:
                    return DeduplicationResult(
                        is_duplicate=True,
                        entry_id=entry.id,
                        similarity_score=similarity,
                        match_type="fuzzy_title",
                    )

        return DeduplicationResult(
            is_duplicate=False,
            entry_id=None,
            similarity_score=0.0,
            match_type="none",
        )
