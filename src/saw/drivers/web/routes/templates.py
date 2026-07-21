"""Template API endpoints.

GET /api/templates - list all templates.
GET /api/templates/{id} - get template content.
POST /api/templates/{id}/apply - create page from template.
"""
from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel, Field

from saw.templates.registry import get_registry

router = APIRouter()


def get_write_queue(request: Request):
    """Dependency: get WriteQueue from app.state."""
    return request.app.state.write_queue


class TemplateInfoResponse(BaseModel):
    """Template metadata."""
    id: str
    name: str
    description: str
    icon: str
    variables: list[str]


class TemplateDetailResponse(BaseModel):
    """Template with content."""
    id: str
    name: str
    description: str
    icon: str
    content: str
    variables: list[str]


class ApplyTemplateRequest(BaseModel):
    """Request to create a page from template."""
    title: str = Field(..., min_length=1, max_length=200)
    variables: dict[str, str] = {}


class ApplyTemplateResponse(BaseModel):
    """Response after applying template."""
    slug: str
    title: str
    status: str


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    slug = text.strip().lower()
    slug = re.sub(r"[^a-z0-9一-鿿]+", "-", slug)
    return slug.strip("-") or "untitled"


@router.get("/templates", response_model=list[TemplateInfoResponse])
async def list_templates() -> list[TemplateInfoResponse]:
    """List all available templates."""
    registry = get_registry()
    return [
        TemplateInfoResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            icon=t.icon,
            variables=t.variables,
        )
        for t in registry.list_templates()
    ]


@router.get("/templates/{template_id}", response_model=TemplateDetailResponse)
async def get_template(
    template_id: str = Path(..., description="Template ID"),
) -> TemplateDetailResponse:
    """Get template content."""
    registry = get_registry()
    template = registry.get_template(template_id)

    if template is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    variables = registry._extract_variables(template.content)

    return TemplateDetailResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        icon=template.icon,
        content=template.content,
        variables=variables,
    )


@router.post("/templates/{template_id}/apply", response_model=ApplyTemplateResponse)
async def apply_template(
    template_id: str = Path(..., description="Template ID"),
    req: ApplyTemplateRequest = ...,
    write_queue=Depends(get_write_queue),
) -> ApplyTemplateResponse:
    """Create a new page from a template.

    Substitutes variables and creates page via Write Queue.
    """
    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    registry = get_registry()

    # Add title to variables
    variables = dict(req.variables)
    variables["title"] = req.title

    content = registry.apply_template(template_id, variables)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    slug = _slugify(req.title)

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
                "content": content,
                "tags": [],
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
                "content": content,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    write_queue.enqueue_atomic(ops)

    return ApplyTemplateResponse(
        slug=slug,
        title=req.title,
        status="queued",
    )
