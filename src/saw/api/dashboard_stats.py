"""Dashboard Statistics API.

Provides real-time statistics for the Dashboard UI.
"""

from fastapi import APIRouter, Request
from pathlib import Path
import psutil
from datetime import datetime

router = APIRouter()

# Track startup time
_start_time = datetime.now()


@router.get("/api/dashboard/stats")
async def get_dashboard_stats(request: Request) -> dict:
    """Get dashboard statistics.

    Returns:
        Dict with total_pages, recent_edits, active_agents, uptime_hours.
    """
    # Calculate uptime
    uptime_seconds = (datetime.now() - _start_time).total_seconds()
    uptime_hours = round(uptime_seconds / 3600, 1)

    # Get active agents count from collaborate engine
    active_agents = 0
    if hasattr(request.app.state, "collaborate") and request.app.state.collaborate:
        try:
            # Count running agents
            agents = request.app.state.collaborate.get_agents()
            active_agents = len([a for a in agents if a.get("status") == "running"])
        except Exception:
            active_agents = 0

    # Get page statistics from wiki repository
    total_pages = 0
    recent_edits = 0
    try:
        wiki_path = Path(".")
        if wiki_path.exists():
            # Count markdown files
            total_pages = len(list(wiki_path.rglob("*.md")))
            # Count files modified in last 24h
            cutoff = datetime.now().timestamp() - 86400
            recent_edits = sum(
                1 for f in wiki_path.rglob("*.md")
                if f.stat().st_mtime > cutoff
            )
    except Exception:
        pass

    return {
        "total_pages": total_pages,
        "recent_edits": recent_edits,
        "active_agents": active_agents,
        "uptime_hours": uptime_hours,
    }
