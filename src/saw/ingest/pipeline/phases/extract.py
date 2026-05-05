"""Extract phase: Extract claims, entities, and relations."""
from __future__ import annotations
import time
import re
from typing import Any

from ..types import PipelinePhase, PipelineContext, PhaseResults
from . import ExtractOutput, ParseOutput


async def extract_execute(
    ctx: PipelineContext,
    deps: PhaseResults
) -> ExtractOutput:
    """
    Extract claims, entities, and relations.

    Phase 3: Depends on parse
    """
    import time

    # Get parse output (type-safe)
    parse_output: ParseOutput = deps.get_output('parse')

    content = parse_output['raw_content']
    sections = parse_output['sections']

    start = time.time()

    # Extract claims
    claims = await _extract_claims(content, sections)

    # Extract entities
    entities = await _extract_entities(content)

    # Extract relations
    relations = await _extract_relations(claims, entities)

    extraction_time_ms = (time.time() - start) * 1000

    ctx.report_progress('extract', 1.0)

    return ExtractOutput(
        claims=claims,
        entities=entities,
        relations=relations,
        extraction_time_ms=extraction_time_ms
    )


async def _extract_claims(content: str, sections: list[dict]) -> list[dict]:
    """Extract claims from content and sections."""
    claims = []

    # Extract from sections
    for section in sections:
        if section.get('title'):
            claim = {
                'type': 'section_claim',
                'source': section['title'],
                'content': section.get('content', ''),
                'confidence': 0.8,
                'metadata': {
                    'level': section.get('level', 1),
                    'section_type': section.get('type', 'section')
                }
            }
            claims.append(claim)

    # Extract explicit claims (statements with certainty)
    # Pattern: "X is Y", "X means Y", etc.
    claim_patterns = [
        r'([^.]+)\s+is\s+([^.]+)',
        r'([^.]+)\s+means\s+([^.]+)',
        r'([^.]+)\s+defines\s+([^.]+)',
        r'([^.]+)\s+provides\s+([^.]+)',
    ]

    sentences = content.split('.')
    for sentence in sentences:
        for pattern in claim_patterns:
            matches = re.findall(pattern, sentence)
            for match in matches:
                if len(match) == 2:
                    claim = {
                        'type': 'explicit_claim',
                        'subject': match[0].strip(),
                        'predicate': 'is',
                        'object': match[1].strip(),
                        'source': sentence.strip(),
                        'confidence': 0.7,
                    }
                    claims.append(claim)

    return claims


async def _extract_entities(content: str) -> list[dict]:
    """Extract entities from content."""
    entities = []

    # Code entities (function names, class names)
    code_patterns = [
        (r'def\s+(\w+)\s*\(', 'function'),
        (r'class\s+(\w+)', 'class'),
        (r'function\s+(\w+)\s*\(', 'function'),
        (r'const\s+(\w+)\s*=', 'variable'),
        (r'let\s+(\w+)\s*=', 'variable'),
        (r'var\s+(\w+)\s*=', 'variable'),
    ]

    for pattern, entity_type in code_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            entity = {
                'name': match,
                'type': entity_type,
                'confidence': 0.9,
            }
            entities.append(entity)

    # Mentioned entities (capitalized words)
    cap_pattern = r'\b([A-Z][a-zA-Z]+)\b'
    cap_matches = re.findall(cap_pattern, content)
    for match in cap_matches:
        if len(match) > 2:  # Skip short words
            entity = {
                'name': match,
                'type': 'mentioned',
                'confidence': 0.5,
            }
            entities.append(entity)

    # Deduplicate
    seen = set()
    unique_entities = []
    for entity in entities:
        key = (entity['name'], entity['type'])
        if key not in seen:
            seen.add(key)
            unique_entities.append(entity)

    return unique_entities


async def _extract_relations(claims: list[dict], entities: list[dict]) -> list[dict]:
    """Extract relations between entities."""
    relations = []

    entity_names = {e['name'] for e in entities}

    for claim in claims:
        subject = claim.get('subject', '')
        object_ = claim.get('object', '')

        if subject in entity_names and object_ in entity_names:
            relation = {
                'source': subject,
                'target': object_,
                'type': claim.get('predicate', 'related_to'),
                'confidence': claim.get('confidence', 0.5),
                'claim_id': claim.get('source', ''),
            }
            relations.append(relation)

    return relations


# Phase definition
EXTRACT_PHASE = PipelinePhase(
    name='extract',
    deps=['parse'],
    execute=extract_execute,
    description='Extract claims, entities, and relations from parsed content'
)