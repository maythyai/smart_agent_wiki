"""Classify phase: Detect file type and extract metadata."""
from __future__ import annotations
import mimetypes
from pathlib import Path

from ..types import PipelinePhase, PipelineContext, PhaseResults
from . import ClassifyOutput


async def classify_execute(
    ctx: PipelineContext,
    deps: PhaseResults
) -> ClassifyOutput:
    """
    Classify the source file and extract basic metadata.

    Phase 1: No dependencies
    """
    source = ctx.repo_path

    # Detect file type using multiple methods
    file_type = _detect_file_type(source)

    # Extract basic metadata
    metadata = _extract_metadata(source, file_type)

    # Detect language if code file
    detected_language = None
    if file_type in ('python', 'javascript', 'typescript', 'rust', 'go', 'java', 'kotlin', 'swift'):
        detected_language = file_type
    elif file_type == 'markdown':
        detected_language = 'markdown'

    ctx.report_progress('classify', 1.0)

    return ClassifyOutput(
        file_type=file_type,
        source_path=source,
        metadata=metadata,
        detected_language=detected_language
    )


def _detect_file_type(source: str) -> str:
    """Detect file type using extension and mime type."""
    path = Path(source)

    # Check by extension first
    ext = path.suffix.lower()

    extension_map = {
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.rs': 'rust',
        '.go': 'go',
        '.java': 'java',
        '.kt': 'kotlin',
        '.swift': 'swift',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.txt': 'text',
        '.html': 'html',
        '.css': 'css',
        '.pdf': 'pdf',
        '.doc': 'doc',
        '.docx': 'docx',
    }

    if ext in extension_map:
        return extension_map[ext]

    # Try mime type
    mime_type, _ = mimetypes.guess_type(source)
    if mime_type:
        if mime_type.startswith('text/'):
            if 'markdown' in mime_type:
                return 'markdown'
            return 'text'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type.startswith('application/json'):
            return 'json'

    # Default to text
    return 'text'


def _extract_metadata(source: str, file_type: str) -> dict:
    """Extract basic file metadata."""
    path = Path(source)

    stat = path.stat() if path.exists() else None

    return {
        'file_name': path.name,
        'file_size': stat.st_size if stat else 0,
        'file_type': file_type,
        'extension': path.suffix.lower(),
        'parent_dir': str(path.parent),
        'is_file': path.is_file(),
        'is_dir': path.is_dir(),
    }


# Phase definition
CLASSIFY_PHASE = PipelinePhase(
    name='classify',
    deps=[],
    execute=classify_execute,
    description='Classify source file type and extract metadata'
)