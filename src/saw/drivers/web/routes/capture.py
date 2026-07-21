"""Quick Capture API endpoint.

POST /api/capture — frictionless note creation with auto-slug.
"""
from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, Request

from saw.drivers.web.schemas.pages import QuickCaptureRequest, QuickCaptureResponse

router = APIRouter()


def get_write_queue(request: Request):
    """Dependency: get WriteQueue from app.state."""
    return request.app.state.write_queue


def get_query_engine(request: Request):
    """Dependency: get QueryEngine from app.state."""
    return request.app.state.query


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Args:
        text: Input text.

    Returns:
        Lowercase slug with hyphens instead of spaces.
    """
    # Lowercase and strip
    slug = text.strip().lower()
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9一-鿿]+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug or "untitled"


def resolve_slug(base_slug: str, wiki) -> str:
    """Ensure slug is unique by appending numeric suffix if needed.

    Args:
        base_slug: Desired slug.
        wiki: Wiki repository to check against.

    Returns:
        Unique slug.
    """
    if wiki is None:
        return base_slug

    slug = base_slug
    counter = 2
    existing = set()
    try:
        existing = set(wiki.list_pages())
    except Exception:
        pass

    while slug in existing:
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


@router.post("/capture", response_model=QuickCaptureResponse)
async def quick_capture(
    req: QuickCaptureRequest,
    write_queue=Depends(get_write_queue),
    engine=Depends(get_query_engine),
) -> QuickCaptureResponse:
    """Create a new page with minimal input.

    Auto-generates slug from title. If slug collides, appends -2, -3, etc.
    Mutation flows through Write Queue for durability.
    """
    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    # Get wiki repo for slug resolution
    wiki = getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)

    base_slug = slugify(req.title)
    slug = resolve_slug(base_slug, wiki)

    # Build page content with frontmatter
    tags_yaml = ""
    if req.tags:
        tags_yaml = "\ntags:\n" + "\n".join(f"  - {t}" for t in req.tags)

    frontmatter = f"---\ntitle: {req.title}\ntype: note{tags_yaml}\n---\n\n"
    full_content = frontmatter + req.content

    op_id = str(uuid.uuid4())
    ops = [
        WriteOp(
            op_id=op_id,
            session_id="web-api",
            sink_name="wiki",
            payload={
                "op": "create",
                "slug": slug,
                "title": req.title,
                "content": full_content,
                "tags": req.tags,
                "type": "note",
            },
            status=WriteOpStatus.PENDING,
        ),
        WriteOp(
            op_id=f"{op_id}-index",
            session_id="web-api",
            sink_name="fts5",
            payload={
                "op": "upsert",
                "slug": slug,
                "content": full_content,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    write_queue.enqueue_atomic(ops)

    return QuickCaptureResponse(
        slug=slug,
        title=req.title,
        status="queued",
    )
