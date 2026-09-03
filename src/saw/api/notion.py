"""API endpoints for Notion connector.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-02: Database selection API endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.notion.database_selector import DatabaseSelector
from saw.connectors.registry import ConnectorRegistry


router = APIRouter(prefix="/connectors/notion", tags=["notion"])


class DatabaseListResponse(BaseModel):
    """Response for database list endpoint."""
    databases: list[dict]


class DatabaseSelectRequest(BaseModel):
    """Request for database selection endpoint."""
    database_ids: list[str]


class DatabaseSelectResponse(BaseModel):
    """Response for database selection endpoint."""
    selected: int
    total_accessible: int


class PropertyMappingRequest(BaseModel):
    """Request for property mapping update."""
    property_mapping: dict


class SelectedDatabaseResponse(BaseModel):
    """Response for selected databases endpoint."""
    databases: list[dict]
    sync_status: dict


async def get_session():
    """Get database session (delegates to the shared async session helper)."""
    from saw.db.session import get_session as _shared_session
    async with _shared_session() as session:
        yield session


async def get_database_selector(
    session: AsyncSession = Depends(get_session),
) -> DatabaseSelector:
    """Get database selector instance.

    Requires active Notion connector.
    """
    registry = ConnectorRegistry()
    connector = registry.get("notion")

    if connector is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notion connector not registered",
        )

    # Get connector ID from config
    connector_id = connector._config.id if hasattr(connector, "_config") else "default"

    return DatabaseSelector(
        client=connector._client,
        session=session,
        connector_id=connector_id,
    )


@router.get("/databases", response_model=DatabaseListResponse)
async def list_databases(
    selector: DatabaseSelector = Depends(get_database_selector),
) -> DatabaseListResponse:
    """List accessible Notion databases.

    Returns all databases the authenticated user has access to.
    """
    databases = await selector.list_accessible_databases()

    return DatabaseListResponse(
        databases=[
            {
                "id": db.id,
                "title": db.title[0].plain_text if db.title else "",
                "properties": db.properties,
                "description": db.description,
                "url": db.url,
            }
            for db in databases
        ]
    )


@router.post("/databases/select", response_model=DatabaseSelectResponse)
async def select_databases(
    request: DatabaseSelectRequest,
    selector: DatabaseSelector = Depends(get_database_selector),
) -> DatabaseSelectResponse:
    """Select databases for sync.

    Persist database selection. Clears previous selections.
    """
    # Get total accessible count
    accessible = await selector.list_accessible_databases()
    total_accessible = len(accessible)

    # Persist selections
    await selector.select_databases(request.database_ids)

    return DatabaseSelectResponse(
        selected=len(request.database_ids),
        total_accessible=total_accessible,
    )


@router.get("/databases/selected", response_model=SelectedDatabaseResponse)
async def get_selected_databases(
    selector: DatabaseSelector = Depends(get_database_selector),
) -> SelectedDatabaseResponse:
    """Get currently selected databases with sync status."""
    databases = await selector.get_selected_databases()
    await selector.get_sync_cursors()
    last_sync_times = await selector.get_last_sync_times()

    return SelectedDatabaseResponse(
        databases=[
            {
                "database_id": db.database_id,
                "database_name": db.database_name,
                "sync_direction": db.sync_direction.value,
                "property_mapping": db.property_mapping,
                "last_sync_at": last_sync_times.get(db.database_id),
            }
            for db in databases
        ],
        sync_status={
            "total_synced": sum(
                int(db.property_mapping.get("items_synced", 0))
                for db in databases
            ),
        },
    )


@router.patch("/databases/{database_id}/mapping")
async def update_property_mapping(
    database_id: str,
    request: PropertyMappingRequest,
    selector: DatabaseSelector = Depends(get_database_selector),
) -> dict:
    """Update property mapping for a database.

    Customize which Notion properties map to SAW fields.
    """
    await selector.update_property_mapping(database_id, request.property_mapping)

    return {
        "database_id": database_id,
        "property_mapping": request.property_mapping,
        "updated": True,
    }


def get_notion_router() -> APIRouter:
    """Get Notion API router."""
    return router