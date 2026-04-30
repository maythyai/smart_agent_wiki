"""Document format classifier for ingestion routing.

Per D-08: Format detection -> structured path vs unstructured path.
Routes documents to appropriate extractors based on file extension or URL pattern.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DocumentFormat(Enum):
    """Supported document formats."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    URL = "url"
    CODE = "code"
    JSON = "json"
    TABLE = "table"
    VIDEO = "video"  # MP4, WebM, MOV
    AUDIO = "audio"  # MP3, WAV, M4A, OGG
    UNKNOWN = "unknown"


# Code file extensions and their languages
CODE_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
}

# Markdown extensions
MARKDOWN_EXTENSIONS: set[str] = {".md", ".markdown"}

# Table/data extensions
TABLE_EXTENSIONS: set[str] = {".csv", ".tsv"}

# Structured data extensions
JSON_EXTENSIONS: set[str] = {".json", ".jsonl"}

# PDF extensions
PDF_EXTENSIONS: set[str] = {".pdf"}

# Video extensions (Phase 4: Media Ingestion)
VIDEO_EXTENSIONS: set[str] = {".mp4", ".webm", ".mov"}

# Audio extensions (Phase 4: Media Ingestion)
AUDIO_EXTENSIONS: set[str] = {".mp3", ".wav", ".m4a", ".ogg"}


@dataclass
class ClassifiedSource:
    """Result of classifying a source."""
    format: DocumentFormat
    path: Path | None = None
    url: str | None = None
    language: str | None = None  # For code files
    media_type: str | None = None  # For video/audio: "video" or "audio"


def classify(source: str) -> ClassifiedSource:
    """Classify a source string into document format.

    Args:
        source: File path, URL, or directory path.

    Returns:
        ClassifiedSource with format and metadata.
    """
    # URL detection
    if source.startswith("http://") or source.startswith("https://"):
        return ClassifiedSource(
            format=DocumentFormat.URL,
            url=source,
        )

    # File extension detection
    source_path = Path(source)
    ext = source_path.suffix.lower()

    # PDF
    if ext in PDF_EXTENSIONS:
        return ClassifiedSource(
            format=DocumentFormat.PDF,
            path=source_path,
        )

    # Markdown
    if ext in MARKDOWN_EXTENSIONS:
        return ClassifiedSource(
            format=DocumentFormat.MARKDOWN,
            path=source_path,
        )

    # Code
    if ext in CODE_EXTENSIONS:
        return ClassifiedSource(
            format=DocumentFormat.CODE,
            path=source_path,
            language=CODE_EXTENSIONS[ext],
        )

    # JSON
    if ext in JSON_EXTENSIONS:
        return ClassifiedSource(
            format=DocumentFormat.JSON,
            path=source_path,
        )

    # Table (CSV/TSV)
    if ext in TABLE_EXTENSIONS:
        return ClassifiedSource(
            format=DocumentFormat.TABLE,
            path=source_path,
        )

    # Video (Phase 4: Media Ingestion)
    if ext in VIDEO_EXTENSIONS:
        return ClassifiedSource(
            format=DocumentFormat.VIDEO,
            path=source_path,
            media_type="video",
        )

    # Audio (Phase 4: Media Ingestion)
    if ext in AUDIO_EXTENSIONS:
        return ClassifiedSource(
            format=DocumentFormat.AUDIO,
            path=source_path,
            media_type="audio",
        )

    # Directory - detect from first supported file
    if source_path.is_dir():
        for child in source_path.iterdir():
            if child.is_file():
                child_class = classify(str(child))
                if child_class.format != DocumentFormat.UNKNOWN:
                    return ClassifiedSource(
                        format=child_class.format,
                        path=source_path,
                        language=child_class.language,
                    )

    # Unknown format
    return ClassifiedSource(
        format=DocumentFormat.UNKNOWN,
        path=source_path,
    )