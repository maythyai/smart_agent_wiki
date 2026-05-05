"""Merge phase: Merge extracted claims with existing knowledge."""
from __future__ import annotations
from typing import Any

from ..types import PipelinePhase, PipelineContext, PhaseResults
from . import MergeOutput, ExtractOutput


async def merge_execute(ctx: PipelineContext, deps: PhaseResults) -> MergeOutput:
    """Merge extracted claims with existing knowledge."""
    extract_output: ExtractOutput = deps.get_output('extract')

    claims = extract_output['claims']
    entities = extract_output['entities']

    # Merge with existing knowledge (if graph exists)
    merged_claims = await _merge_claims(claims, ctx.graph)
    conflicts = await _detect_conflicts(merged_claims, ctx.graph)

    ctx.report_progress('merge', 1.0)

    return MergeOutput(
        merged_claims=merged_claims,
        conflicts=conflicts,
        merged_entities=entities
    )


async def _merge_claims(claims: list[dict], graph: Any) -> list[dict]:
    """Merge claims with existing knowledge."""
    merged = []

    for claim in claims:
        merged_claim = claim.copy()

        # Add merge metadata
        merged_claim['merge_status'] = 'new'
        merged_claim['merge_timestamp'] = _get_timestamp()

        # Check if claim exists in graph
        if graph is not None:
            existing = _find_existing_claim(claim, graph)
            if existing:
                merged_claim['merge_status'] = 'duplicate'
                merged_claim['existing_id'] = existing.get('id')

        merged.append(merged_claim)

    return merged


async def _detect_conflicts(claims: list[dict], graph: Any) -> list[dict]:
    """Detect conflicts between new and existing claims."""
    conflicts = []

    for claim in claims:
        if claim.get('merge_status') == 'duplicate':
            conflict = {
                'type': 'potential_duplicate',
                'new_claim': claim,
                'confidence': claim.get('confidence', 0.5),
            }
            conflicts.append(conflict)

    return conflicts


def _find_existing_claim(claim: dict, graph: Any) -> dict | None:
    """Find existing claim in knowledge graph."""
    # Placeholder - actual implementation depends on graph structure
    return None


def _get_timestamp() -> str:
    """Get current timestamp."""
    from datetime import datetime
    return datetime.utcnow().isoformat()


# Phase definition
MERGE_PHASE = PipelinePhase(
    name='merge',
    deps=['extract'],
    execute=merge_execute,
    description='Merge extracted claims with existing knowledge'
)