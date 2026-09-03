"""FastAPI endpoints for Logseq connector.

Plan 13-01 Task 4: API endpoints for Logseq sync.
Per LOGS-01: Configure graph path via API.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from saw.connectors.logseq.connector import LogseqConnector

router = APIRouter(prefix="/api/v1/logseq", tags=["logseq"])

# Global connector instance (in production, use proper DI)
_connector: Optional[LogseqConnector] = None


class ConnectRequest(BaseModel):
    """Request to connect Logseq graph."""
    graph_path: str
    sync_enabled: bool = True
    watch_enabled: bool = True


class ConnectResponse(BaseModel):
    """Response after connecting."""
    status: str
    graph_path: str


class SyncStatusResponse(BaseModel):
    """Sync status response."""
    graph_path: str
    connected: bool
    watching: bool
    files_count: int
    blocks_count: int
    last_sync_at: Optional[datetime] = None


class SyncResponse(BaseModel):
    """Sync operation response."""
    status: str
    files_processed: int
    blocks_created: int
    errors: list[str] = []


@router.post("/connect", response_model=ConnectResponse)
async def connect_graph(request: ConnectRequest):
    """Connect to a Logseq graph directory.

    Per LOGS-01: Configure graph path.
    """
    global _connector

    graph_path = Path(request.graph_path)

    # Validate path exists
    if not graph_path.exists():
        raise HTTPException(400, f"Graph path does not exist: {graph_path}")
    if not graph_path.is_dir():
        raise HTTPException(400, f"Graph path is not a directory: {graph_path}")

    _connector = LogseqConnector()
    result = await _connector.authenticate({"graph_path": str(graph_path)})

    if result.access_token == "":
        raise HTTPException(400, result.raw_response.get("error", "Authentication failed"))

    return ConnectResponse(
        status="connected",
        graph_path=str(graph_path),
    )


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """Get current sync status."""
    global _connector

    if _connector is None:
        return SyncStatusResponse(
            graph_path="",
            connected=False,
            watching=False,
            files_count=0,
            blocks_count=0,
        )

    # Get items to count
    items = await _connector.get_items()

    return SyncStatusResponse(
        graph_path=str(_connector._config.graph_path) if _connector._config else "",
        connected=True,
        watching=_connector._watching,
        files_count=0,  # Would need to count files separately
        blocks_count=len(items),
    )


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync():
    """Trigger manual sync of the graph."""
    global _connector

    if _connector is None:
        raise HTTPException(400, "Not connected to a graph")

    items = await _connector.get_items()

    return SyncResponse(
        status="completed",
        files_processed=0,
        blocks_created=len(items),
        errors=[],
    )


@router.post("/watch/start", response_model=SyncStatusResponse)
async def start_watching():
    """Start real-time file watching.

    Per LOGS-04: Watch directory for changes.
    """
    global _connector

    if _connector is None:
        raise HTTPException(400, "Not connected to a graph")

    # Define a simple callback
    def on_file_changed(file_path: Path):
        # In production, this would trigger async processing
        pass

    _connector.start_watching(on_file_changed)

    items = await _connector.get_items()

    return SyncStatusResponse(
        graph_path=str(_connector._config.graph_path) if _connector._config else "",
        connected=True,
        watching=True,
        files_count=0,
        blocks_count=len(items),
    )


@router.post("/watch/stop", response_model=SyncStatusResponse)
async def stop_watching():
    """Stop file watching."""
    global _connector

    if _connector is None:
        raise HTTPException(400, "Not connected to a graph")

    _connector.stop_watching()

    items = await _connector.get_items()

    return SyncStatusResponse(
        graph_path=str(_connector._config.graph_path) if _connector._config else "",
        connected=True,
        watching=False,
        files_count=0,
        blocks_count=len(items),
    )