"""Entity type API endpoints.

GET /api/entity-types - list all entity types.
GET /api/entity-types/{type_id} - get entity type schema.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path

from saw.domain.entity_types import get_registry

router = APIRouter()


@router.get("/entity-types")
async def list_entity_types() -> list[dict]:
    """List all available entity types with their schemas."""
    registry = get_registry()
    return [t.to_dict() for t in registry.list_types()]


@router.get("/entity-types/{type_id}")
async def get_entity_type(
    type_id: str = Path(..., description="Entity type ID"),
) -> dict:
    """Get a single entity type with its field schema."""
    registry = get_registry()
    entity_type = registry.get(type_id)
    if entity_type is None:
        raise HTTPException(status_code=404, detail=f"Entity type '{type_id}' not found")
    return entity_type.to_dict()
