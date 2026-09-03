"""Validate phase: Validate claims and compute confidence scores."""
from __future__ import annotations

from ..types import PipelinePhase, PipelineContext, PhaseResults
from . import ValidateOutput, MergeOutput


async def validate_execute(ctx: PipelineContext, deps: PhaseResults) -> ValidateOutput:
    """Validate merged claims and compute confidence."""
    merge_output: MergeOutput = deps.get_output('merge')

    claims = merge_output['merged_claims']

    # Validate claims
    validated_claims, errors = await _validate_claims(claims)

    # Compute confidence scores
    confidence_scores = await _compute_confidence(validated_claims)

    ctx.report_progress('validate', 1.0)

    return ValidateOutput(
        validated_claims=validated_claims,
        validation_errors=errors,
        confidence_scores=confidence_scores
    )


async def _validate_claims(claims: list[dict]) -> tuple[list[dict], list[dict]]:
    """Validate claims and return validated claims + errors."""
    validated = []
    errors = []

    for claim in claims:
        validation_result = _validate_single_claim(claim)

        if validation_result['valid']:
            validated_claim = claim.copy()
            validated_claim['validation_status'] = 'passed'
            validated.append(validated_claim)
        else:
            error = {
                'claim_id': claim.get('source', ''),
                'error_type': validation_result['error_type'],
                'error_message': validation_result['error_message'],
            }
            errors.append(error)

            # Still include invalid claims but mark them
            validated_claim = claim.copy()
            validated_claim['validation_status'] = 'failed'
            validated_claim['validation_error'] = validation_result['error_message']
            validated.append(validated_claim)

    return validated, errors


async def _compute_confidence(claims: list[dict]) -> dict[str, float]:
    """Compute confidence scores for claims."""
    scores = {}

    for i, claim in enumerate(claims):
        claim_id = claim.get('source', '') or f'claim_{i}'

        # Base confidence from extraction
        base_confidence = claim.get('confidence', 0.5)

        # Adjust based on validation
        if claim.get('validation_status') == 'passed':
            adjusted = min(1.0, base_confidence + 0.1)
        else:
            adjusted = max(0.1, base_confidence - 0.2)

        # Adjust based on source type
        source_type = claim.get('type', '')
        if source_type == 'section_claim':
            adjusted = min(1.0, adjusted + 0.05)
        elif source_type == 'explicit_claim':
            adjusted = min(1.0, adjusted + 0.1)

        scores[claim_id] = adjusted

    return scores


def _validate_single_claim(claim: dict) -> dict:
    """Validate a single claim."""
    # Check required fields
    if not claim.get('source'):
        return {
            'valid': False,
            'error_type': 'missing_source',
            'error_message': 'Claim missing source field'
        }

    # Check confidence range
    confidence = claim.get('confidence', 0)
    if confidence < 0 or confidence > 1:
        return {
            'valid': False,
            'error_type': 'invalid_confidence',
            'error_message': f'Confidence {confidence} out of range [0, 1]'
        }

    # Check content
    content = claim.get('content', '') or claim.get('source', '')
    if not content or len(content.strip()) < 3:
        return {
            'valid': False,
            'error_type': 'empty_content',
            'error_message': 'Claim content is too short'
        }

    return {'valid': True, 'error_type': None, 'error_message': None}


# Phase definition
VALIDATE_PHASE = PipelinePhase(
    name='validate',
    deps=['merge'],
    execute=validate_execute,
    description='Validate claims and compute confidence scores'
)