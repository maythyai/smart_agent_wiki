"""Parse phase: Parse source content into structured format."""
from __future__ import annotations
from pathlib import Path

from ..types import PipelinePhase, PipelineContext, PhaseResults
from . import ParseOutput, ClassifyOutput


async def parse_execute(
    ctx: PipelineContext,
    deps: PhaseResults
) -> ParseOutput:
    """
    Parse the source content.

    Phase 2: Depends on classify
    """
    import time

    # Get classify output (type-safe)
    classify_output: ClassifyOutput = deps.get_output('classify')

    source = classify_output['source_path']
    file_type = classify_output['file_type']

    start = time.time()

    # Parse content based on file type
    result = _parse_content(source, file_type)

    parse_time_ms = (time.time() - start) * 1000

    ctx.report_progress('parse', 1.0)

    return ParseOutput(
        raw_content=result['content'],
        sections=result.get('sections', []),
        metadata=classify_output['metadata'],
        parse_time_ms=parse_time_ms
    )


def _parse_content(source: str, file_type: str) -> dict:
    """Parse content based on file type."""
    path = Path(source)

    # Read content
    if path.exists() and path.is_file():
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = path.read_text(encoding='latin-1')
    else:
        content = ''

    # Parse based on type
    if file_type == 'markdown':
        return _parse_markdown(content)
    elif file_type in ('python', 'javascript', 'typescript', 'rust', 'go'):
        return _parse_code(content, file_type)
    elif file_type == 'json':
        return _parse_json(content)
    elif file_type in ('yaml', 'toml'):
        return _parse_config(content, file_type)
    else:
        return {'content': content, 'sections': []}


def _parse_markdown(content: str) -> dict:
    """Parse markdown content into sections."""
    sections = []
    lines = content.split('\n')

    current_section = None
    current_content = []

    for line in lines:
        if line.startswith('#'):
            # Save previous section
            if current_section:
                current_section['content'] = '\n'.join(current_content)
                sections.append(current_section)

            # Start new section
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('#').strip()
            current_section = {
                'level': level,
                'title': title,
                'content': ''
            }
            current_content = []
        else:
            if current_section:
                current_content.append(line)
            else:
                current_content.append(line)

    # Save last section
    if current_section:
        current_section['content'] = '\n'.join(current_content)
        sections.append(current_section)

    return {
        'content': content,
        'sections': sections
    }


def _parse_code(content: str, language: str) -> dict:
    """Parse code content into sections (functions, classes)."""
    sections = []
    lines = content.split('\n')

    # Simple parsing - look for function/class definitions
    for i, line in enumerate(lines):
        stripped = line.strip()

        if language == 'python':
            if stripped.startswith('def ') or stripped.startswith('class '):
                name = stripped.split('(')[0].replace('def ', '').replace('class ', '').strip()
                sections.append({
                    'type': 'definition',
                    'name': name,
                    'line': i + 1,
                    'language': language
                })
        elif language in ('javascript', 'typescript'):
            if stripped.startswith('function ') or 'function ' in stripped:
                name = stripped.split('function')[1].split('(')[0].strip()
                sections.append({
                    'type': 'function',
                    'name': name,
                    'line': i + 1,
                    'language': language
                })
            elif stripped.startswith('class '):
                name = stripped.split('class')[1].split('{')[0].strip().split('extends')[0].strip()
                sections.append({
                    'type': 'class',
                    'name': name,
                    'line': i + 1,
                    'language': language
                })

    return {
        'content': content,
        'sections': sections
    }


def _parse_json(content: str) -> dict:
    """Parse JSON content."""
    import json

    try:
        data = json.loads(content)
        return {
            'content': content,
            'sections': [{'type': 'json', 'data': data}]
        }
    except json.JSONDecodeError:
        return {'content': content, 'sections': []}


def _parse_config(content: str, file_type: str) -> dict:
    """Parse config files (yaml, toml)."""
    sections = []

    if file_type == 'yaml':
        # Simple YAML section detection
        lines = content.split('\n')
        current_section = None

        for line in lines:
            if line and not line.startswith(' ') and not line.startswith('#'):
                key = line.split(':')[0].strip()
                if key:
                    sections.append({
                        'type': 'key',
                        'name': key,
                    })

    return {
        'content': content,
        'sections': sections
    }


# Phase definition
PARSE_PHASE = PipelinePhase(
    name='parse',
    deps=['classify'],
    execute=parse_execute,
    description='Parse source content into structured format'
)