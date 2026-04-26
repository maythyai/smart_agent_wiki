"""Unit tests for document format classifier."""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.engines.ingest.classifier import (
    classify,
    ClassifiedSource,
    DocumentFormat,
)


class TestClassifier:
    """Tests for classify() function."""

    def test_classify_pdf_extension(self) -> None:
        """PDF files are classified as PDF format."""
        result = classify("document.pdf")
        assert result.format == DocumentFormat.PDF
        assert result.path is not None
        assert result.path.name == "document.pdf"

    def test_classify_url_http(self) -> None:
        """HTTP URLs are classified as URL format."""
        result = classify("https://example.com/article")
        assert result.format == DocumentFormat.URL
        assert result.url == "https://example.com/article"
        assert result.path is None

    def test_classify_url_http_nossl(self) -> None:
        """HTTP URLs (no SSL) are classified as URL format."""
        result = classify("http://example.com/page")
        assert result.format == DocumentFormat.URL
        assert result.url == "http://example.com/page"

    def test_classify_python_code(self) -> None:
        """Python files are classified as CODE with language."""
        result = classify("script.py")
        assert result.format == DocumentFormat.CODE
        assert result.language == "python"
        assert result.path is not None

    def test_classify_javascript_code(self) -> None:
        """JavaScript files are classified as CODE with language."""
        result = classify("app.js")
        assert result.format == DocumentFormat.CODE
        assert result.language == "javascript"

    def test_classify_typescript_code(self) -> None:
        """TypeScript files are classified as CODE with language."""
        result = classify("main.ts")
        assert result.format == DocumentFormat.CODE
        assert result.language == "typescript"

    def test_classify_rust_code(self) -> None:
        """Rust files are classified as CODE with language."""
        result = classify("lib.rs")
        assert result.format == DocumentFormat.CODE
        assert result.language == "rust"

    def test_classify_go_code(self) -> None:
        """Go files are classified as CODE with language."""
        result = classify("server.go")
        assert result.format == DocumentFormat.CODE
        assert result.language == "go"

    def test_classify_java_code(self) -> None:
        """Java files are classified as CODE with language."""
        result = classify("Main.java")
        assert result.format == DocumentFormat.CODE
        assert result.language == "java"

    def test_classify_json_file(self) -> None:
        """JSON files are classified as JSON format."""
        result = classify("data.json")
        assert result.format == DocumentFormat.JSON
        assert result.path is not None

    def test_classify_jsonl_file(self) -> None:
        """JSONL files are classified as JSON format."""
        result = classify("records.jsonl")
        assert result.format == DocumentFormat.JSON

    def test_classify_markdown_file(self) -> None:
        """Markdown files are classified as MARKDOWN format."""
        result = classify("readme.md")
        assert result.format == DocumentFormat.MARKDOWN

    def test_classify_markdown_alt_extension(self) -> None:
        """Files with .markdown extension are classified as MARKDOWN."""
        result = classify("notes.markdown")
        assert result.format == DocumentFormat.MARKDOWN

    def test_classify_csv_table(self) -> None:
        """CSV files are classified as TABLE format."""
        result = classify("data.csv")
        assert result.format == DocumentFormat.TABLE

    def test_classify_tsv_table(self) -> None:
        """TSV files are classified as TABLE format."""
        result = classify("export.tsv")
        assert result.format == DocumentFormat.TABLE

    def test_classify_unknown_format(self) -> None:
        """Unknown file extensions are classified as UNKNOWN."""
        result = classify("file.xyz")
        assert result.format == DocumentFormat.UNKNOWN

    def test_classify_no_extension(self) -> None:
        """Files without extension are classified as UNKNOWN."""
        result = classify("README")
        assert result.format == DocumentFormat.UNKNOWN

    def test_classify_directory(self, tmp_path: Path) -> None:
        """Directory classification uses first supported file."""
        # Create directory with a Python file
        py_file = tmp_path / "module.py"
        py_file.write_text("def test(): pass")
        result = classify(str(tmp_path))
        assert result.format == DocumentFormat.CODE
        assert result.language == "python"