"""Coverage tests for ingest pipeline phases (v1.34.0, AUDIT-F-04).

Tests the pure helper functions in parse.py + validate.py that were
previously uncovered (parse 13%, validate 15%).
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest


class TestParseContent:
    """parse.py _parse_content + _parse_markdown + _parse_code helpers."""

    def test_parse_markdown_file(self, tmp_path):
        from saw.ingest.pipeline.phases.parse import _parse_content

        md = tmp_path / "test.md"
        md.write_text("# Title\n\nSome content here.\n\n## Section\n\nMore.")
        result = _parse_content(str(md), "markdown")
        assert "content" in result
        assert "Title" in result["content"]
        assert "sections" in result

    def test_parse_code_file(self, tmp_path):
        from saw.ingest.pipeline.phases.parse import _parse_content

        py = tmp_path / "test.py"
        py.write_text("def foo():\n    return 42\n")
        result = _parse_content(str(py), "python")
        assert "content" in result
        assert "foo" in result["content"]

    def test_parse_json_file(self, tmp_path):
        from saw.ingest.pipeline.phases.parse import _parse_content

        jf = tmp_path / "data.json"
        jf.write_text(json.dumps({"key": "value"}))
        result = _parse_content(str(jf), "json")
        assert "content" in result

    def test_parse_nonexistent_returns_empty(self):
        from saw.ingest.pipeline.phases.parse import _parse_content

        result = _parse_content("/nonexistent/path.md", "markdown")
        assert result["content"] == ""

    def test_parse_unknown_type_returns_raw(self, tmp_path):
        from saw.ingest.pipeline.phases.parse import _parse_content

        f = tmp_path / "data.txt"
        f.write_text("plain text")
        result = _parse_content(str(f), "unknown")
        assert result["content"] == "plain text"
        assert result["sections"] == []

    def test_parse_yaml_config(self, tmp_path):
        from saw.ingest.pipeline.phases.parse import _parse_content

        yf = tmp_path / "config.yaml"
        yf.write_text("key: value\nlist:\n  - a\n  - b\n")
        result = _parse_content(str(yf), "yaml")
        assert "content" in result


class TestValidateClaims:
    """validate.py _validate_single_claim + _validate_claims + _compute_confidence."""

    def test_valid_claim_passes(self):
        from saw.ingest.pipeline.phases.validate import _validate_single_claim

        claim = {"source": "doc.md", "content": "This is a valid claim.", "confidence": 0.8}
        result = _validate_single_claim(claim)
        assert result["valid"] is True

    def test_missing_source_fails(self):
        from saw.ingest.pipeline.phases.validate import _validate_single_claim

        result = _validate_single_claim({"content": "no source", "confidence": 0.5})
        assert result["valid"] is False
        assert result["error_type"] == "missing_source"

    def test_invalid_confidence_fails(self):
        from saw.ingest.pipeline.phases.validate import _validate_single_claim

        result = _validate_single_claim({"source": "doc", "content": "text", "confidence": 1.5})
        assert result["valid"] is False
        assert result["error_type"] == "invalid_confidence"

    def test_empty_content_fails(self):
        from saw.ingest.pipeline.phases.validate import _validate_single_claim

        result = _validate_single_claim({"source": "doc", "content": "ab", "confidence": 0.5})
        assert result["valid"] is False
        assert result["error_type"] == "empty_content"

    def test_validate_claims_batch(self):
        from saw.ingest.pipeline.phases.validate import _validate_claims

        claims = [
            {"source": "doc1", "content": "valid claim text", "confidence": 0.8},
            {"source": "doc2", "content": "ab", "confidence": 0.5},
        ]
        validated, errors = asyncio.run(_validate_claims(claims))
        # Both claims are "validated" (passed + failed status), not filtered.
        assert len(validated) == 2
        assert validated[0]["validation_status"] == "passed"
        assert validated[1]["validation_status"] == "failed"

    def test_compute_confidence(self):
        from saw.ingest.pipeline.phases.validate import _compute_confidence

        claims = [
            {"source": "c1", "confidence": 0.5, "validation_status": "passed", "type": "section_claim"},
            {"source": "c2", "confidence": 0.7, "validation_status": "failed", "type": ""},
        ]
        scores = asyncio.run(_compute_confidence(claims))
        assert "c1" in scores
        assert "c2" in scores
        # passed → adjusted up; failed → adjusted down
        assert scores["c1"] > 0.5
        assert scores["c2"] < 0.7
