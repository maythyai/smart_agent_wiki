"""Store phase: Store validated claims to vault and claims DB."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any

from ..types import PipelinePhase, PipelineContext, PhaseResults
from . import StoreOutput, ValidateOutput


async def store_execute(ctx: PipelineContext, deps: PhaseResults) -> StoreOutput:
    """Store validated claims to vault and claims DB."""
    validate_output: ValidateOutput = deps.get_output('validate')

    claims = validate_output['validated_claims']

    # Store to vault (immutable)
    vault_path = await _store_to_vault(claims, ctx.repo_path)

    # Store to claims DB (placeholder)
    claims_db_path = await _store_to_claims_db(claims, ctx.graph)

    # Create wiki pages (placeholder)
    wiki_pages = await _create_wiki_pages(claims, ctx.graph)

    ctx.report_progress('store', 1.0)

    return StoreOutput(
        vault_path=vault_path,
        claims_db_path=claims_db_path,
        stored_count=len(claims),
        wiki_pages_created=wiki_pages
    )


async def _store_to_vault(claims: list[dict], source_path: str) -> str:
    """Store claims to immutable vault."""
    # Create vault directory
    vault_dir = Path('.saw/vault')
    vault_dir.mkdir(parents=True, exist_ok=True)

    # Generate vault file name
    source_name = Path(source_path).stem
    timestamp = _get_timestamp().replace(':', '-').replace('.', '-')
    vault_file = vault_dir / f'{source_name}_{timestamp}.json'

    # Write claims to vault
    import json

    vault_data = {
        'source': source_path,
        'timestamp': _get_timestamp(),
        'claims_count': len(claims),
        'claims': claims
    }

    vault_file.write_text(json.dumps(vault_data, indent=2, ensure_ascii=False))

    return str(vault_file)


async def _store_to_claims_db(claims: list[dict], graph: Any) -> str:
    """Store claims to claims database."""
    # Placeholder - actual implementation depends on graph/DB structure
    claims_db_path = '.saw/claims.db'

    return claims_db_path


async def _create_wiki_pages(claims: list[dict], graph: Any) -> list[str]:
    """Create wiki pages from validated claims."""
    # Placeholder - actual implementation creates wiki pages
    wiki_pages = []

    for claim in claims:
        if claim.get('validation_status') == 'passed':
            # Would create wiki page here
            wiki_pages.append(f'claim_{claim.get("source", "unknown")}')

    return wiki_pages


def _get_timestamp() -> str:
    """Get current timestamp."""
    from datetime import datetime
    return datetime.utcnow().isoformat()


# Phase definition
STORE_PHASE = PipelinePhase(
    name='store',
    deps=['validate'],
    execute=store_execute,
    description='Store claims to vault, claims DB, and wiki'
)