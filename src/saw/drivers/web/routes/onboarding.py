"""Onboarding routes for new user setup.

Provides endpoints to check onboarding status and seed starter content.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from saw.onboarding.starter_kits import STARTER_KITS

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def get_wiki_repo(request: Request):
    """Get WikiRepository from app state."""
    if hasattr(request.app.state, "wiki_repo"):
        return request.app.state.wiki_repo
    raise HTTPException(status_code=500, detail="Wiki repository not initialized")


def get_write_queue(request: Request):
    """Get WriteQueue from app state."""
    if hasattr(request.app.state, "write_queue"):
        return request.app.state.write_queue
    raise HTTPException(status_code=500, detail="Write queue not initialized")


@router.get("/status")
async def get_onboarding_status(wiki_repo=Depends(get_wiki_repo)) -> dict[str, Any]:
    """Check if this is a first-run onboarding scenario.

    Returns:
        - is_first_run: True if wiki is empty (no pages)
        - page_count: Number of existing pages
    """
    page_count = len(wiki_repo.list_pages())
    return {
        "is_first_run": page_count == 0,
        "page_count": page_count,
    }


@router.post("/seed")
async def seed_starter_kit(
    request: Request,
    kit_id: str,
    wiki_repo=Depends(get_wiki_repo),
    write_queue=Depends(get_write_queue),
) -> dict[str, Any]:
    """Seed a starter kit into the wiki.

    Args:
        kit_id: Starter kit identifier (personal_pkm, team_wiki, etc.)

    Returns:
        - success: Whether seeding succeeded
        - pages_created: Number of pages created
        - errors: Any errors encountered
    """
    if kit_id not in STARTER_KITS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown starter kit: {kit_id}. Available: {list(STARTER_KITS.keys())}",
        )

    kit = STARTER_KITS[kit_id]
    pages_created = 0
    errors: list[str] = []

    import uuid

    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    for page_def in kit["pages"]:
        try:
            slug = page_def["slug"]
            # C3-1: build a valid WriteOp (op_id/session_id/sink_name are
            # required) and enqueue a list. The wiki sink writes to
            # ``payload['path']`` (== slug); the fts5 sink indexes the
            # same content. Mirrors the pages.py create_page pattern.
            op_id = str(uuid.uuid4())
            content = page_def["content"]
            tags = page_def.get("tags", [])
            ops = [
                WriteOp(
                    op_id=op_id,
                    session_id="onboarding",
                    sink_name="wiki",
                    payload={
                        "path": slug,
                        "title": page_def["title"],
                        "content": content,
                        "tags": tags,
                        "page_type": "summary",
                        "entity_type": page_def.get("entity_type", "note"),
                        "frontmatter": {"entity_type": page_def.get("entity_type", "note")},
                    },
                    status=WriteOpStatus.PENDING,
                ),
                WriteOp(
                    op_id=f"{op_id}-index",
                    session_id="onboarding",
                    sink_name="fts5",
                    payload={
                        "doc_id": slug,
                        "title": page_def["title"],
                        "content": content,
                        "tags": " ".join(tags),
                    },
                    status=WriteOpStatus.PENDING,
                ),
            ]

            write_queue.enqueue_atomic(ops)
            pages_created += 1

        except Exception as e:
            errors.append(f"Failed to create page '{page_def['slug']}': {str(e)}")

    return {
        "success": len(errors) == 0,
        "kit_id": kit_id,
        "kit_name": kit["name"],
        "pages_created": pages_created,
        "errors": errors,
    }
