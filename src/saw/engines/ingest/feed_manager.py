"""RSS/Atom feed manager for polling and ingesting content.

Phase 9: RSS Subscription — FeedManager implementation.
Per RSSS-01~07: Feed polling, deduplication, and ingestion.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import fastfeedparser
import httpx
import trafilatura

from saw.db.feed_models import Feed, FeedEntry
from saw.domain.feed import (
    DeduplicationKey,
    DeduplicationResult,
    DeduplicationService,
    EntryHash,
    EntryStatus,
    FeedConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class PollResult:
    """Result of a feed poll operation."""
    feed_id: str
    new_entries: int
    updated_entries: int
    skipped_entries: int
    errors: list[str] = field(default_factory=list)
    status_code: int = 200
    not_modified: bool = False


class FeedManagerError(Exception):
    """Base exception for FeedManager operations."""
    pass


class FeedManager:
    """Manage RSS/Atom feed subscriptions and polling.

    Per RSSS-01: Subscribe to RSS/Atom Feed.
    Per RSSS-02: Auto ingest new articles to Vault.
    Per RSSS-03: Incremental sync (only process new entries).
    Per RSSS-04: Configure sync frequency.
    Per RSSS-05: Content change detection.
    Per RSSS-07: Filter by keywords.

    Per Pitfall 26: fastfeedparser handles encoding issues.
    Per Pitfall 27: Conditional GET prevents aggressive polling.
    """

    def __init__(
        self,
        db_session: Any,  # sqlalchemy.orm.Session
        ingest_pipeline: Any | None = None,  # IngestPipeline
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize FeedManager.

        Args:
            db_session: SQLAlchemy database session.
            ingest_pipeline: Optional ingest pipeline for content ingestion.
            http_client: Optional HTTP client (created if not provided).
        """
        self._db = db_session
        self._ingest = ingest_pipeline
        self._http = http_client or httpx.AsyncClient(timeout=30.0)
        self._dedup = DeduplicationService()

    async def add_feed(
        self,
        url: str,
        category: str | None = None,
        tags: list[str] | None = None,
        poll_interval: int = 3600,
    ) -> str:
        """Subscribe to a new RSS/Atom feed.

        Args:
            url: Feed URL.
            category: Optional user-defined category.
            tags: Optional filter keywords.
            poll_interval: Poll interval in seconds (900-86400).

        Returns:
            Feed ID (UUID).

        Raises:
            FeedManagerError: If URL is not a valid feed.
        """
        # Validate configuration
        config = FeedConfig(
            url=url,
            category=category,
            tags=tags or [],
            poll_interval=poll_interval,
        )

        # Parse feed to get title/description
        try:
            feed_data = await self._parse_feed(url)
        except Exception as e:
            raise FeedManagerError(f"Failed to parse feed: {e}")

        if not feed_data:
            raise FeedManagerError(f"Empty feed response from: {url}")

        # Create feed record
        feed_id = str(uuid.uuid4())
        feed = Feed(
            id=feed_id,
            url=url,
            title=getattr(feed_data.feed, 'title', None),
            description=getattr(feed_data.feed, 'description', None),
            category=category,
            tags=json.dumps(tags) if tags else None,
            poll_interval=poll_interval,
            active=True,
        )
        self._db.add(feed)
        self._db.commit()

        logger.info(f"Added feed: {feed_id} - {feed.title or url}")
        return feed_id

    async def _parse_feed(self, url: str) -> fastfeedparser.FeedParserDict:
        """Parse RSS/Atom feed with fastfeedparser.

        Per Pitfall 26: fastfeedparser handles encoding detection.

        Args:
            url: Feed URL.

        Returns:
            Parsed feed data.
        """
        from saw.adapters.url_guard import assert_safe_url_async

        await assert_safe_url_async(url)  # HI-12: SSRF guard
        response = await self._http.get(url)
        response.raise_for_status()

        feed = fastfeedparser.parse(response.text)

        # Check for bozo (malformed feed) - log warning but don't fail
        if feed.bozo:
            logger.warning(f"Feed {url} has parsing issues: {feed.bozo_exception}")

        return feed

    async def _parse_feed_from_response(
        self, response: httpx.Response
    ) -> fastfeedparser.FeedParserDict:
        """Parse feed from HTTP response.

        Args:
            response: HTTP response object.

        Returns:
            Parsed feed data.
        """
        feed = fastfeedparser.parse(response.text)

        if feed.bozo:
            logger.warning(f"Feed has parsing issues: {feed.bozo_exception}")

        return feed

    def _utcnow(self) -> datetime:
        """Get current UTC datetime."""
        return datetime.now(timezone.utc)

    async def poll_feed(self, feed_id: str) -> PollResult:
        """Poll a feed for new entries.

        Per Pitfall 27: Uses conditional GET with ETag/Last-Modified.

        Args:
            feed_id: Feed ID to poll.

        Returns:
            PollResult with counts of new/updated/skipped entries.
        """
        # Get feed from database
        feed = self._db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            raise FeedManagerError(f"Feed not found: {feed_id}")

        # Build conditional GET headers
        headers: dict[str, str] = {}
        if feed.last_etag:
            headers["If-None-Match"] = feed.last_etag
        if feed.last_modified:
            headers["If-Modified-Since"] = feed.last_modified

        try:
            from saw.adapters.url_guard import assert_safe_url_async

            await assert_safe_url_async(feed.url)  # HI-12: SSRF guard
            response = await self._http.get(feed.url, headers=headers)
        except httpx.HTTPError as e:
            return PollResult(
                feed_id=feed_id,
                new_entries=0,
                updated_entries=0,
                skipped_entries=0,
                errors=[f"HTTP error: {e}"],
                status_code=0,
            )

        # Handle 304 Not Modified
        if response.status_code == 304:
            feed.last_poll_at = self._utcnow()
            self._db.commit()
            return PollResult(
                feed_id=feed_id,
                new_entries=0,
                updated_entries=0,
                skipped_entries=0,
                errors=[],
                status_code=304,
                not_modified=True,
            )

        # Handle non-200 responses
        if response.status_code != 200:
            return PollResult(
                feed_id=feed_id,
                new_entries=0,
                updated_entries=0,
                skipped_entries=0,
                errors=[f"HTTP {response.status_code}"],
                status_code=response.status_code,
            )

        # Parse feed
        try:
            feed_data = await self._parse_feed_from_response(response)
        except Exception as e:
            return PollResult(
                feed_id=feed_id,
                new_entries=0,
                updated_entries=0,
                skipped_entries=0,
                errors=[f"Parse error: {e}"],
                status_code=200,
            )

        # Process entries
        new_count, updated_count, skipped_count, errors = await self._process_entries(
            feed, feed_data.entries
        )

        # Update feed metadata
        feed.last_poll_at = self._utcnow()
        feed.last_etag = response.headers.get("ETag")
        feed.last_modified = response.headers.get("Last-Modified")
        self._db.commit()

        return PollResult(
            feed_id=feed_id,
            new_entries=new_count,
            updated_entries=updated_count,
            skipped_entries=skipped_count,
            errors=errors,
            status_code=200,
        )

    async def _process_entries(
        self,
        feed: Feed,
        entries: list[Any],
    ) -> tuple[int, int, int, list[str]]:
        """Process all entries from a feed poll.

        Args:
            feed: Feed model instance.
            entries: List of parsed entries.

        Returns:
            Tuple of (new_count, updated_count, skipped_count, errors).
        """
        new_count = 0
        updated_count = 0
        skipped_count = 0
        errors: list[str] = []

        # Get existing entries for deduplication
        existing_entries = self._db.query(FeedEntry).filter(
            FeedEntry.feed_id == feed.id
        ).all()

        for entry in entries:
            try:
                result = await self._process_single_entry(feed, entry, existing_entries)
                if result == "new":
                    new_count += 1
                elif result == "updated":
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                guid = getattr(entry, 'id', getattr(entry, 'link', 'unknown'))
                errors.append(f"Entry {guid}: {e}")

        return new_count, updated_count, skipped_count, errors

    async def _process_single_entry(
        self,
        feed: Feed,
        entry: Any,
        existing_entries: list[FeedEntry],
    ) -> str:
        """Process a single entry. Returns 'new', 'updated', or 'skipped'.

        Args:
            feed: Feed model instance.
            entry: Parsed entry from feed.
            existing_entries: List of existing entries for deduplication.

        Returns:
            Status string indicating processing result.
        """
        # Extract entry data
        guid = getattr(entry, 'id', getattr(entry, 'link', ''))
        title = getattr(entry, 'title', 'Untitled')
        link = getattr(entry, 'link', '')
        summary = getattr(entry, 'summary', getattr(entry, 'description', ''))

        # Parse publication date
        published = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            from time import mktime
            published = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            from time import mktime
            published = datetime.fromtimestamp(mktime(entry.updated_parsed), tz=timezone.utc)

        # Check for duplicate
        dup_result = self._dedup.check_duplicate(
            guid=guid,
            title=title,
            content=summary,
            existing_entries=existing_entries,
        )

        if dup_result.is_duplicate and dup_result.entry_id:
            # Find existing entry
            existing = next(
                (e for e in existing_entries if e.id == dup_result.entry_id),
                None
            )

            if existing:
                # Extract content for comparison
                new_content = await self._extract_content(entry, link)
                new_hash = EntryHash.compute(new_content)

                if existing.content_hash != new_hash:
                    # Content updated
                    existing.content = new_content
                    existing.content_hash = new_hash
                    existing.last_seen_at = self._utcnow()
                    existing.status = EntryStatus.UPDATED.value
                    self._db.commit()

                    # Re-ingest to Vault
                    await self._ingest_entry(feed, entry, new_content, existing.id)
                    return "updated"

                # No change
                existing.last_seen_at = self._utcnow()
                self._db.commit()
                return "skipped"

        # Check keyword filter before processing
        if not self._should_include_entry(entry, feed):
            return "skipped"

        # New entry
        content = await self._extract_content(entry, link)
        content_hash = EntryHash.compute(content)

        # Create deduplication key
        dedup_key = DeduplicationKey.from_entry(guid, title, content)
        entry_id = dedup_key.compute_id()

        # Create FeedEntry
        feed_entry = FeedEntry(
            id=entry_id,
            feed_id=feed.id,
            guid=guid,
            title=title,
            url=link,
            content=content,
            summary=summary,
            content_hash=content_hash,
            published_at=published,
            first_seen_at=self._utcnow(),
            last_seen_at=self._utcnow(),
            status=EntryStatus.NEW.value,
        )
        self._db.add(feed_entry)
        self._db.commit()

        # Ingest to Vault
        vault_uuid = await self._ingest_entry(feed, entry, content, entry_id)
        if vault_uuid:
            feed_entry.vault_uuid = vault_uuid
            self._db.commit()

        return "new"

    async def _extract_content(
        self,
        entry: Any,
        link: str,
    ) -> str:
        """Extract full content from entry or fetch from URL.

        Per Decision 3: If feed only has summary, fetch full article.

        Args:
            entry: Parsed entry from feed.
            link: Entry link URL.

        Returns:
            Extracted content string.
        """
        # Check if feed provides full content
        if hasattr(entry, 'content') and entry.content:
            # Some feeds provide content:encoded
            content_value = entry.content[0].get('value', '') if isinstance(entry.content, list) else entry.content
            if content_value:
                return content_value

        # Check description/summary for full content
        summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
        if len(summary) > 500:  # Heuristic: longer summaries might be full content
            return summary

        # Fetch from URL and extract with trafilatura
        if link:
            try:
                from saw.adapters.url_guard import assert_safe_url_async

                await assert_safe_url_async(link)  # HI-12: SSRF guard
                response = await self._http.get(link)
                extracted = trafilatura.extract(
                    response.text,
                    include_comments=False,
                    include_tables=True,
                )
                if extracted:
                    return extracted
            except Exception as e:
                logger.warning(f"Failed to extract content from {link}: {e}")

        return summary

    async def _ingest_entry(
        self,
        feed: Feed,
        entry: Any,
        content: str,
        entry_id: str,
    ) -> str | None:
        """Ingest entry content to Vault via IngestPipeline.

        Args:
            feed: Feed model instance.
            entry: Parsed entry from feed.
            content: Entry content.
            entry_id: FeedEntry ID.

        Returns:
            Vault UUID if successful, None otherwise.
        """
        if not self._ingest:
            logger.warning("No ingest pipeline configured, skipping ingestion")
            return None

        # Create temp file with content
        title = getattr(entry, 'title', 'Untitled')
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
        ) as f:
            f.write(f"# {title}\n\n{content}")
            temp_path = f.name

        try:
            result = self._ingest.ingest(
                temp_path,
                options={
                    'source_type': 'rss',
                    'feed_url': feed.url,
                    'feed_title': feed.title,
                    'entry_id': entry_id,
                },
            )
            # Return the session_id as vault_uuid placeholder
            # In production, would track actual vault_uuid
            return result.session_id
        except Exception as e:
            logger.error(f"Failed to ingest entry {entry_id}: {e}")
            return None
        finally:
            os.unlink(temp_path)

    def _should_include_entry(
        self,
        entry: Any,
        feed: Feed,
    ) -> bool:
        """Check if entry matches feed's keyword filters.

        Per RSSS-07: Filter by keywords.

        Args:
            entry: Parsed entry from feed.
            feed: Feed model instance.

        Returns:
            True if entry should be included.
        """
        if not feed.tags:
            return True

        tags = json.loads(feed.tags) if isinstance(feed.tags, str) else feed.tags

        if not tags:
            return True

        # Check title and summary for keyword matches
        title = getattr(entry, 'title', '').lower()
        summary = getattr(entry, 'summary', getattr(entry, 'description', '')).lower()
        content = title + ' ' + summary

        for tag in tags:
            if tag.lower() in content:
                return True

        return False

    def calculate_adaptive_interval(self, feed_id: str) -> int:
        """Calculate adaptive poll interval based on feed update frequency.

        Per Decision 2: Adjust interval based on observed patterns.

        Args:
            feed_id: Feed ID.

        Returns:
            Adaptive poll interval in seconds.
        """
        entries = self._db.query(FeedEntry).filter(
            FeedEntry.feed_id == feed_id,
            FeedEntry.published_at.isnot(None),
        ).order_by(FeedEntry.published_at).limit(50).all()

        if len(entries) < 2:
            return 3600  # Default 1 hour

        # Calculate intervals between publications
        intervals = []
        for i in range(1, len(entries)):
            if entries[i].published_at and entries[i-1].published_at:
                delta = (entries[i].published_at - entries[i-1].published_at).total_seconds()
                if delta > 0:
                    intervals.append(delta)

        if not intervals:
            return 3600

        # Median
        intervals.sort()
        median = intervals[len(intervals) // 2]

        # Apply 0.75 factor and bounds
        adaptive = int(median * 0.75)
        return max(900, min(86400, adaptive))
