"""REST API endpoints for feed management.

Phase 9: RSS Subscription — API endpoints.
Per RSSS-01, RSSS-06, RSSS-07: Feed CRUD and filtering.
"""
from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from saw.db.feed_models import Feed, FeedEntry
from saw.engines.ingest.feed_manager import FeedManager, FeedManagerError, PollResult

logger = logging.getLogger(__name__)


# ============================================================================
# Request Models
# ============================================================================

class FeedCreateRequest(BaseModel):
    """Request model for creating a new feed."""
    url: str = Field(..., description="RSS/Atom feed URL")
    category: Optional[str] = Field(None, description="User-defined category")
    tags: Optional[list[str]] = Field(None, description="Filter keywords")
    poll_interval: int = Field(3600, ge=900, le=86400, description="Poll interval in seconds")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class FeedUpdateRequest(BaseModel):
    """Request model for updating a feed."""
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    poll_interval: Optional[int] = Field(None, ge=900, le=86400)
    active: Optional[bool] = None


class OPMLImportRequest(BaseModel):
    """Request model for importing OPML."""
    opml_content: str = Field(..., description="OPML XML content")


# ============================================================================
# Response Models
# ============================================================================

class FeedResponse(BaseModel):
    """Response model for a single feed."""
    id: str
    url: str
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    tags: list[str]
    poll_interval: int
    last_poll_at: Optional[datetime]
    active: bool
    created_at: datetime
    entry_count: int = 0

    model_config = {"from_attributes": True}


class FeedEntryResponse(BaseModel):
    """Response model for a feed entry."""
    id: str
    feed_id: str
    title: str
    url: Optional[str]
    summary: Optional[str]
    status: str
    published_at: Optional[datetime]
    first_seen_at: datetime
    vault_uuid: Optional[str]

    model_config = {"from_attributes": True}


class FeedListResponse(BaseModel):
    """Response model for feed list."""
    feeds: list[FeedResponse]
    total: int


class FeedEntryListResponse(BaseModel):
    """Response model for entry list."""
    entries: list[FeedEntryResponse]
    total: int
    feed_id: str


class PollResponse(BaseModel):
    """Response model for manual poll."""
    feed_id: str
    new_entries: int
    updated_entries: int
    skipped_entries: int
    status_code: int
    not_modified: bool
    errors: list[str]


class OPMLExportResponse(BaseModel):
    """Response model for OPML export."""
    opml_content: str
    feed_count: int


class OPMLImportResponse(BaseModel):
    """Response model for OPML import."""
    imported: int
    skipped: int
    errors: list[str]


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/api/v1/feeds", tags=["feeds"])


# ============================================================================
# Dependencies
# ============================================================================

# Module-level singleton engine so feed data survives across requests.
# Previously get_db_session built a fresh ``sqlite:///:memory:`` engine on
# every call, so every feed created/updated in one request vanished by the
# next. The engine is shared (one persistent file), created once, with
# check_same_thread=False because FastAPI runs sync endpoints in a threadpool.
_feeds_engine = None
_feeds_session_factory = None


def _get_feeds_engine():
    global _feeds_engine, _feeds_session_factory
    if _feeds_engine is None:
        from pathlib import Path

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        db_path = Path(".saw/db/feeds.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _feeds_engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        # Create feed/sync tables once. Safe to call repeatedly.
        from saw.db.models import Base

        Base.metadata.create_all(_feeds_engine)
        _feeds_session_factory = sessionmaker(
            bind=_feeds_engine, expire_on_commit=False
        )
    return _feeds_engine


def get_db_session() -> Session:
    """Yield a persistent SQLAlchemy session backed by the shared feed engine."""
    _get_feeds_engine()
    session = _feeds_session_factory()
    try:
        yield session
    finally:
        session.close()


async def get_feed_manager(db: Session = Depends(get_db_session)) -> FeedManager:
    """Get FeedManager instance."""
    return FeedManager(db)


# ============================================================================
# Feed CRUD Endpoints
# ============================================================================

@router.get("", response_model=FeedListResponse)
async def list_feeds(
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db_session),
) -> FeedListResponse:
    """List all feed subscriptions.

    Per RSSS-06: Support filtering by category.
    """
    query = db.query(Feed)
    if active_only:
        query = query.filter(Feed.active == True)
    if category:
        query = query.filter(Feed.category == category)

    feeds = query.all()

    # Build response with entry counts
    feed_responses = []
    for feed in feeds:
        entry_count = db.query(FeedEntry).filter(
            FeedEntry.feed_id == feed.id
        ).count()

        tags = json.loads(feed.tags) if feed.tags else []

        feed_responses.append(FeedResponse(
            id=feed.id,
            url=feed.url,
            title=feed.title,
            description=feed.description,
            category=feed.category,
            tags=tags,
            poll_interval=feed.poll_interval,
            last_poll_at=feed.last_poll_at,
            active=feed.active,
            created_at=feed.created_at,
            entry_count=entry_count,
        ))

    return FeedListResponse(feeds=feed_responses, total=len(feed_responses))


@router.post("", response_model=FeedResponse, status_code=status.HTTP_201_CREATED)
async def create_feed(
    request: FeedCreateRequest,
    feed_manager: FeedManager = Depends(get_feed_manager),
    db: Session = Depends(get_db_session),
) -> FeedResponse:
    """Add new feed subscription.

    Per RSSS-01: Subscribe to RSS/Atom Feed.
    Per RSSS-07: Support keyword filtering via tags.
    """
    try:
        feed_id = await feed_manager.add_feed(
            url=request.url,
            category=request.category,
            tags=request.tags,
            poll_interval=request.poll_interval,
        )
    except FeedManagerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Feed created but not found",
        )

    tags = json.loads(feed.tags) if feed.tags else []

    return FeedResponse(
        id=feed.id,
        url=feed.url,
        title=feed.title,
        description=feed.description,
        category=feed.category,
        tags=tags,
        poll_interval=feed.poll_interval,
        last_poll_at=feed.last_poll_at,
        active=feed.active,
        created_at=feed.created_at,
        entry_count=0,
    )


@router.get("/{feed_id}", response_model=FeedResponse)
async def get_feed(
    feed_id: str,
    db: Session = Depends(get_db_session),
) -> FeedResponse:
    """Get feed details."""
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed not found: {feed_id}",
        )

    entry_count = db.query(FeedEntry).filter(
        FeedEntry.feed_id == feed.id
    ).count()

    tags = json.loads(feed.tags) if feed.tags else []

    return FeedResponse(
        id=feed.id,
        url=feed.url,
        title=feed.title,
        description=feed.description,
        category=feed.category,
        tags=tags,
        poll_interval=feed.poll_interval,
        last_poll_at=feed.last_poll_at,
        active=feed.active,
        created_at=feed.created_at,
        entry_count=entry_count,
    )


@router.put("/{feed_id}", response_model=FeedResponse)
async def update_feed(
    feed_id: str,
    request: FeedUpdateRequest,
    db: Session = Depends(get_db_session),
) -> FeedResponse:
    """Update feed settings.

    Per RSSS-04: Configure sync frequency.
    Per RSSS-06: Feed category management.
    Per RSSS-07: Keyword filter management.
    """
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed not found: {feed_id}",
        )

    if request.category is not None:
        feed.category = request.category
    if request.tags is not None:
        feed.tags = json.dumps(request.tags)
    if request.poll_interval is not None:
        feed.poll_interval = request.poll_interval
    if request.active is not None:
        feed.active = request.active

    db.commit()
    db.refresh(feed)

    entry_count = db.query(FeedEntry).filter(
        FeedEntry.feed_id == feed.id
    ).count()

    tags = json.loads(feed.tags) if feed.tags else []

    return FeedResponse(
        id=feed.id,
        url=feed.url,
        title=feed.title,
        description=feed.description,
        category=feed.category,
        tags=tags,
        poll_interval=feed.poll_interval,
        last_poll_at=feed.last_poll_at,
        active=feed.active,
        created_at=feed.created_at,
        entry_count=entry_count,
    )


@router.delete("/{feed_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feed(
    feed_id: str,
    db: Session = Depends(get_db_session),
) -> None:
    """Unsubscribe from feed.

    Soft delete: sets active=False to preserve entry history.
    """
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed not found: {feed_id}",
        )

    feed.active = False
    db.commit()


# ============================================================================
# Entry Endpoints
# ============================================================================

@router.get("/{feed_id}/entries", response_model=FeedEntryListResponse)
async def list_feed_entries(
    feed_id: str,
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db_session),
) -> FeedEntryListResponse:
    """List entries for a feed.

    Per RSSS-02: View ingested articles.
    """
    feed = db.query(Feed).filter(Feed.id == feed_id).first()
    if not feed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feed not found: {feed_id}",
        )

    query = db.query(FeedEntry).filter(FeedEntry.feed_id == feed_id)

    if status_filter:
        query = query.filter(FeedEntry.status == status_filter)

    total = query.count()
    entries = query.order_by(
        FeedEntry.first_seen_at.desc()
    ).offset(offset).limit(limit).all()

    return FeedEntryListResponse(
        entries=[FeedEntryResponse.model_validate(e) for e in entries],
        total=total,
        feed_id=feed_id,
    )


@router.post("/{feed_id}/poll", response_model=PollResponse)
async def poll_feed(
    feed_id: str,
    feed_manager: FeedManager = Depends(get_feed_manager),
) -> PollResponse:
    """Trigger immediate poll.

    Manual trigger for immediate feed check, bypassing scheduler.
    """
    try:
        result = await feed_manager.poll_feed(feed_id)
    except FeedManagerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return PollResponse(
        feed_id=result.feed_id,
        new_entries=result.new_entries,
        updated_entries=result.updated_entries,
        skipped_entries=result.skipped_entries,
        status_code=result.status_code,
        not_modified=result.not_modified,
        errors=result.errors,
    )


# ============================================================================
# OPML Import/Export Endpoints
# ============================================================================

@router.post("/import", response_model=OPMLImportResponse)
async def import_opml(
    request: OPMLImportRequest,
    feed_manager: FeedManager = Depends(get_feed_manager),
    db: Session = Depends(get_db_session),
) -> OPMLImportResponse:
    """Import feeds from OPML file.

    Per RSSS-01: Bulk subscribe via OPML.
    """
    imported = 0
    skipped = 0
    errors: list[str] = []

    try:
        root = ET.fromstring(request.opml_content)
        outlines = root.findall(".//outline[@xmlUrl]")

        for outline in outlines:
            url = outline.get("xmlUrl")
            title = outline.get("title", "")
            category = outline.get("category", None)

            if not url:
                skipped += 1
                continue

            # Check if feed already exists
            existing = db.query(Feed).filter(Feed.url == url).first()
            if existing:
                skipped += 1
                continue

            try:
                await feed_manager.add_feed(
                    url=url,
                    category=category,
                )
                imported += 1
            except FeedManagerError as e:
                errors.append(f"{url}: {str(e)}")
                skipped += 1

    except ET.ParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OPML XML: {str(e)}",
        )

    return OPMLImportResponse(
        imported=imported,
        skipped=skipped,
        errors=errors,
    )


@router.get("/export", response_model=OPMLExportResponse)
async def export_opml(
    db: Session = Depends(get_db_session),
) -> OPMLExportResponse:
    """Export feeds as OPML.

    Per RSSS-01: Export subscriptions for backup/migration.
    """
    feeds = db.query(Feed).filter(Feed.active == True).all()

    # Build OPML XML
    opml = ET.Element("opml", version="2.0")
    head = ET.SubElement(opml, "head")
    ET.SubElement(head, "title").text = "Smart Agent Wiki Feeds"
    ET.SubElement(head, "dateCreated").text = datetime.now(timezone.utc).isoformat()

    body = ET.SubElement(opml, "body")

    # Group by category
    categories: dict[str, list[Feed]] = {}
    for feed in feeds:
        cat = feed.category or "Uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(feed)

    for category, cat_feeds in categories.items():
        cat_elem = ET.SubElement(body, "outline", text=category)
        for feed in cat_feeds:
            ET.SubElement(
                cat_elem,
                "outline",
                type="rss",
                text=feed.title or feed.url,
                title=feed.title or "",
                xmlUrl=feed.url,
            )

    # Convert to string
    xml_str = ET.tostring(opml, encoding="unicode", xml_declaration=True)

    return OPMLExportResponse(
        opml_content=xml_str,
        feed_count=len(feeds),
    )
