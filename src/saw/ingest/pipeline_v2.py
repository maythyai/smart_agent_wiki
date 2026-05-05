"""DAG-based ingest pipeline implementation."""
from __future__ import annotations
import asyncio
from typing import Optional, Callable

from .pipeline.runner import PipelineRunner
from .pipeline.types import PipelineContext
from .pipeline.phases import get_default_phase_list


async def run_ingest_pipeline(
    source_path: str,
    options: dict = None,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> dict:
    """
    Run the DAG-based ingest pipeline.

    Args:
        source_path: Path to source file/directory
        options: Optional pipeline options
        progress_callback: Optional progress callback

    Returns:
        Pipeline results with all phase outputs
    """
    options = options or {}

    # Create context
    ctx = PipelineContext(
        graph=None,  # Will be populated by phases
        repo_path=source_path,
        options=options,
        progress_callback=progress_callback
    )

    # Get phases
    phases = get_default_phase_list()

    # Create runner
    runner = PipelineRunner(phases)

    # Execute
    results = await runner.run(ctx)

    # Return results
    return {
        'success': True,
        'phases': {name: results.get(name).output for name in results.names()},
        'execution_order': runner.get_execution_order(),
        'total_duration_ms': sum(
            results.get(name).duration_ms for name in results.names()
        )
    }


def run_ingest_pipeline_sync(
    source_path: str,
    options: dict = None,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> dict:
    """
    Synchronous wrapper for run_ingest_pipeline.
    """
    return asyncio.run(run_ingest_pipeline(source_path, options, progress_callback))


__all__ = [
    'run_ingest_pipeline',
    'run_ingest_pipeline_sync',
]