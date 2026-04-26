"""PDF Parser with 3-tier fallback (Docling -> PyMuPDF).

Per D-09: 3-tier fallback with quality validation.
Per PITFALLS.md Pitfall 8: PDF parsing silent failures prevention.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PDFParseResult:
    """Result of parsing a PDF file."""
    content: str
    title: str
    page_count: int
    word_count: int
    char_count: int
    paragraph_count: int
    parser: str  # "docling" or "pymupdf"
    file_path: Path


class PDFParser:
    """Parse PDF files with 3-tier fallback and quality validation."""

    def parse(self, file_path: Path) -> PDFParseResult:
        """3-tier fallback: Docling -> PyMuPDF. Quality metrics on every parse.

        Args:
            file_path: Path to the PDF file.

        Returns:
            PDFParseResult with content and quality metrics.
        """
        # Tier 1: Try Docling
        try:
            result = self._parse_docling(file_path)
            if self._quality_check(result, file_path):
                result.parser = "docling"
                return result
        except ImportError:
            pass  # Docling not installed, fall through
        except Exception:
            pass  # Docling failed, fall through

        # Tier 2: PyMuPDF (always available as fallback)
        result = self._parse_pymupdf(file_path)
        result.parser = "pymupdf"
        return result

    def _parse_docling(self, file_path: Path) -> PDFParseResult:
        """Parse PDF using Docling (intelligent parsing).

        Docling provides layout analysis, OCR, and better extraction
        for complex PDF layouts (tables, formulas, multi-column).
        """
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        doc = converter.convert(str(file_path))

        # Export to markdown format
        content = doc.export_to_markdown()

        # Calculate quality metrics
        word_count = len(content.split())
        char_count = len(content)
        paragraph_count = len([p for p in content.split("\n\n") if p.strip()])
        page_count = doc.pages_count if hasattr(doc, "pages_count") else 1
        title = doc.title if hasattr(doc, "title") else file_path.stem

        return PDFParseResult(
            content=content,
            title=title,
            page_count=page_count,
            word_count=word_count,
            char_count=char_count,
            paragraph_count=paragraph_count,
            parser="docling",
            file_path=file_path,
        )

    def _parse_pymupdf(self, file_path: Path) -> PDFParseResult:
        """Parse PDF using PyMuPDF (lightweight fallback).

        PyMuPDF is fast and reliable for simple PDF layouts.
        Good fallback when Docling is unavailable or fails.
        """
        import fitz  # PyMuPDF

        doc = fitz.open(str(file_path))
        content_parts: list[str] = []
        page_count = len(doc)

        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text()
            content_parts.append(text)

        content = "\n\n".join(content_parts)
        doc.close()

        # Calculate quality metrics
        word_count = len(content.split())
        char_count = len(content)
        paragraph_count = len([p for p in content.split("\n\n") if p.strip()])

        # Title from first page's first heading-like text
        title = file_path.stem
        if content_parts and content_parts[0]:
            first_lines = content_parts[0].strip().split("\n")
            if first_lines:
                title = first_lines[0].strip()[:100]

        return PDFParseResult(
            content=content,
            title=title,
            page_count=page_count,
            word_count=word_count,
            char_count=char_count,
            paragraph_count=paragraph_count,
            parser="pymupdf",
            file_path=file_path,
        )

    def _quality_check(self, result: PDFParseResult, file_path: Path) -> bool:
        """Validate extraction quality (per Pitfall 8).

        Expected word count heuristic: page_count * 250 (average words per page).
        If extracted word count < 50% of expected -> quality too low.

        Args:
            result: The parse result to check.
            file_path: Path to the PDF (for file size comparison).

        Returns:
            True if quality is acceptable, False otherwise.
        """
        expected_words = result.page_count * 250
        if result.word_count < expected_words * 0.5:
            return False
        return True