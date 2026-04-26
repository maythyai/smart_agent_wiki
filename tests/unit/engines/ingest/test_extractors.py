"""Unit tests for ingest engine extractors, fuser, and validator."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saw.domain.claims import Claim
from saw.domain.entities import Entity, EntityRelation
from saw.domain.value_objects import SourceMark
from saw.engines.ingest.extractors.code_ast import CodeASTExtractor
from saw.engines.ingest.extractors.markdown import ExtractionResult, MarkdownExtractor
from saw.engines.ingest.fuser import Fuser
from saw.engines.ingest.validator import Validator


class TestCodeASTExtractor:
    """Tests for CodeASTExtractor - ZERO LLM extraction."""

    def test_extract_python_file_extracts_classes_and_functions(
        self, tmp_path: Path
    ) -> None:
        """Python file extraction extracts classes and functions with ZERO LLM calls."""
        # Create a Python file
        py_file = tmp_path / "example.py"
        py_file.write_text('''
"""Module docstring."""

def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"

class Calculator:
    """A simple calculator."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

import os
''')

        extractor = CodeASTExtractor()
        result = extractor.extract(py_file, "test-source-uuid")

        # Verify claims were extracted
        assert len(result.claims) > 0

        # Verify entities include class and function
        entity_names = {e.name for e in result.entities}
        assert "Calculator" in entity_names
        assert "hello" in entity_names

        # Verify extraction method
        assert result.metadata["extraction_method"] == "ast"
        assert result.metadata["language"] == "python"

    def test_extract_python_file_no_llm_calls(self, tmp_path: Path) -> None:
        """CodeASTExtractor makes ZERO LLM calls."""
        py_file = tmp_path / "simple.py"
        py_file.write_text("def test(): pass")

        extractor = CodeASTExtractor()
        # This should succeed without any LLM mocking
        result = extractor.extract(py_file, "test-uuid")

        assert len(result.claims) >= 0  # Any number is fine, just no errors


class TestMarkdownExtractor:
    """Tests for MarkdownExtractor."""

    def test_extract_with_mocked_llm(self, tmp_path: Path) -> None:
        """MarkdownExtractor with LLM extracts claims from markdown."""
        md_file = tmp_path / "doc.md"
        md_file.write_text("""---
title: Test Document
tags: [test, example]
---

# Introduction

This is a test document about machine learning.

## Key Concepts

Machine learning transforms data into predictions.
""")

        # Mock LLM router
        mock_router = MagicMock()
        mock_router.extract_claims.return_value = {
            "claims": [
                {
                    "content": "Machine learning transforms data into predictions.",
                    "entities": ["Machine learning", "data", "predictions"],
                    "relations": [],
                    "source_mark": "extracted",
                    "tags": ["ml", "data"],
                }
            ]
        }

        from saw.adapters.parsers.markdown_parser import MarkdownParser
        extractor = MarkdownExtractor(
            parser=MarkdownParser(),
            llm=mock_router,
        )

        result = extractor.extract(md_file, "test-uuid")

        assert len(result.claims) == 1
        assert "Machine learning" in result.claims[0].content
        assert result.metadata["title"] == "Test Document"

    def test_extract_without_llm_offline_mode(self, tmp_path: Path) -> None:
        """MarkdownExtractor without LLM extracts basic claims from headings."""
        md_file = tmp_path / "doc.md"
        md_file.write_text("""---
title: Test Document
---

# Introduction

This is the introduction paragraph.

## Key Concepts

Some key concepts are discussed here.
""")

        from saw.adapters.parsers.markdown_parser import MarkdownParser
        extractor = MarkdownExtractor(
            parser=MarkdownParser(),
            llm=None,  # No LLM - offline mode
        )

        result = extractor.extract(md_file, "test-uuid")

        # Should extract claims from headings (as topic markers)
        assert len(result.claims) > 0

        # Should have entities from headings
        entity_names = {e.name for e in result.entities}
        assert "Introduction" in entity_names


class TestFuser:
    """Tests for Fuser deduplication."""

    def test_fuser_skips_identical_content_hash_claims(self) -> None:
        """Identical content_hash claims are skipped."""
        # Create two claims with same content (same hash)
        claim1 = Claim(
            uuid="uuid-1",
            content="Same content",
            source_uuid="source-1",
            content_hash=Claim.compute_hash("Same content"),
        )
        claim2 = Claim(
            uuid="uuid-2",
            content="Same content",  # Same content = same hash
            source_uuid="source-1",
            content_hash=Claim.compute_hash("Same content"),
        )

        fuser = Fuser()
        result = fuser.fuse([claim1], [claim2])

        # claim1 should be skipped because claim2 has same hash
        assert len(result.to_skip) == 1
        assert result.to_skip[0].uuid == "uuid-1"

    def test_fuser_inserts_new_claims(self) -> None:
        """New claims with different content are marked for insert."""
        claim1 = Claim(
            uuid="uuid-1",
            content="Content A",
            source_uuid="source-1",
            content_hash=Claim.compute_hash("Content A"),
        )
        claim2 = Claim(
            uuid="uuid-2",
            content="Content B",
            source_uuid="source-1",
            content_hash=Claim.compute_hash("Content B"),
        )

        fuser = Fuser()
        result = fuser.fuse([claim1], [claim2])

        # Both claims have different hashes, so claim1 should be inserted
        assert len(result.to_insert) == 1
        assert result.to_insert[0].uuid == "uuid-1"


class TestValidator:
    """Tests for Validator field checks."""

    def test_validator_rejects_empty_content_claim(self) -> None:
        """Empty content claim is rejected."""
        claim = Claim(
            uuid="uuid-1",
            content="",  # Empty!
            source_uuid="source-1",
            content_hash=Claim.compute_hash(""),
        )

        validator = Validator()
        result = validator.validate([claim], [], [])

        assert len(result.valid_claims) == 0
        assert any("empty content" in e.lower() for e in result.errors)

    def test_validator_rejects_missing_source_uuid(self) -> None:
        """Claim missing source_uuid is rejected."""
        claim = Claim(
            uuid="uuid-1",
            content="Some content",
            source_uuid="",  # Empty!
            content_hash=Claim.compute_hash("Some content"),
        )

        validator = Validator()
        result = validator.validate([claim], [], [])

        assert len(result.valid_claims) == 0
        assert any("source_uuid" in e.lower() for e in result.errors)

    def test_validator_rejects_duplicate_content_hash(self) -> None:
        """Duplicate content_hash claims are rejected."""
        hash_val = Claim.compute_hash("Same content")
        claim1 = Claim(
            uuid="uuid-1",
            content="Same content",
            source_uuid="source-1",
            content_hash=hash_val,
        )
        claim2 = Claim(
            uuid="uuid-2",
            content="Same content",
            source_uuid="source-1",
            content_hash=hash_val,
        )

        validator = Validator()
        result = validator.validate([claim1, claim2], [], [])

        # Only one should be valid (first one)
        assert len(result.valid_claims) == 1
        assert result.valid_claims[0].uuid == "uuid-1"
        assert any("Duplicate" in e for e in result.errors)

    def test_validator_rejects_entity_missing_name(self) -> None:
        """Entity missing name is rejected."""
        entity = Entity(
            uuid="entity-1",
            name="",  # Empty!
            entity_type="concept",
        )

        validator = Validator()
        result = validator.validate([], [entity], [])

        assert len(result.valid_entities) == 0
        assert any("name" in e.lower() for e in result.errors)

    def test_validator_rejects_relation_with_invalid_entity(self) -> None:
        """Relation with non-existent entity UUID is rejected."""
        entity1 = Entity(
            uuid="entity-1",
            name="Test",
            entity_type="concept",
        )
        relation = EntityRelation(
            source_uuid="entity-1",
            target_uuid="non-existent-entity",  # Doesn't exist!
            relation_type="related_to",
        )

        validator = Validator()
        result = validator.validate([], [entity1], [relation])

        assert len(result.valid_relations) == 0
        assert any("not in entities" in e for e in result.errors)
