"""MCP tools for ingestion operations.

Per 02-03 Task 2: Ingest tools (saw_ingest, saw_reparse).
"""
from __future__ import annotations

from typing import Any

from saw.drivers.mcp.server import mcp

# Global pipeline reference (set during initialization)
_pipeline = None


def init_ingest_tools(pipeline) -> None:
    """Initialize ingest tools with pipeline reference.

    Args:
        pipeline: IngestPipeline instance.
    """
    global _pipeline
    _pipeline = pipeline


@mcp.tool
async def saw_ingest(source: str, options: dict[str, Any] | None = None) -> dict:
    """Ingest a document, URL, or directory into the knowledge base.

    Per PITFALLS.md: Backward-compatible parameter handling (new params have defaults).

    Args:
        source: Path to file/directory or URL to ingest.
        options: Optional ingest options (no_llm, reparse, format, etc.).

    Returns:
        Ingest result with claim_count, entity_count, duration_ms.
    """
    import time

    start = time.time()
    options = options or {}

    result = {
        "source": source,
        "claim_count": 0,
        "entity_count": 0,
        "relation_count": 0,
        "errors": [],
        "warnings": [],
        "duration_ms": 0,
        "version": "1.0.0",
    }

    if _pipeline is None:
        result["errors"].append("Ingest pipeline not initialized")
        return result

    try:
        ingest_result = _pipeline.ingest(source, options)
        result["claim_count"] = ingest_result.claim_count
        result["entity_count"] = ingest_result.entity_count
        result["relation_count"] = ingest_result.relation_count
        result["errors"] = ingest_result.errors
        result["warnings"] = ingest_result.warnings
        result["parser"] = ingest_result.parser
    except Exception as e:
        result["errors"].append(str(e))

    result["duration_ms"] = int((time.time() - start) * 1000)
    return result


@mcp.tool
async def saw_reparse(document_uuid: str) -> dict:
    """Re-parse a previously ingested document with current parser.

    Args:
        document_uuid: UUID of the document to re-parse.

    Returns:
        Re-parse result with claim_count, entity_count, duration_ms.
    """
    import time

    start = time.time()

    result = {
        "document_uuid": document_uuid,
        "claim_count": 0,
        "entity_count": 0,
        "errors": [],
        "duration_ms": 0,
        "version": "1.0.0",
    }

    if _pipeline is None:
        result["errors"].append("Ingest pipeline not initialized")
        return result

    try:
        # In production, would look up document path by UUID and re-parse
        result["warnings"] = ["Re-parse not fully implemented"]
    except Exception as e:
        result["errors"].append(str(e))

    result["duration_ms"] = int((time.time() - start) * 1000)
    return result
