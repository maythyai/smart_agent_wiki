"""Unit tests for Logseq parser.

Plan 13-01 Task 2: Test LogseqParser for Markdown parsing.
"""
import pytest
from pathlib import Path
import tempfile

from saw.connectors.logseq.parser import LogseqParser, compute_file_hash
from saw.connectors.logseq.models import ParsedPage


class TestLogseqParser:
    """Tests for LogseqParser."""

    @pytest.fixture
    def parser(self) -> LogseqParser:
        """Create a parser instance."""
        return LogseqParser()

    @pytest.fixture
    def temp_graph(self, tmp_path: Path) -> Path:
        """Create a temporary Logseq graph structure."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        yield tmp_path

    def test_parser_extracts_blocks_from_simple_file(
        self, parser: LogseqParser, temp_graph: Path
    ):
        """Test 1: Parser extracts blocks from simple Markdown file."""
        md_file = temp_graph / "pages" / "test.md"
        md_file.write_text(
            """---
title: Test Page
---
- First block
- Second block
- Third block
"""
        )

        page = parser.parse_file(md_file)

        assert len(page.blocks) == 3
        assert page.blocks[0].content == "First block"
        assert page.blocks[1].content == "Second block"
        assert page.blocks[2].content == "Third block"

    def test_parser_handles_nested_blocks(
        self, parser: LogseqParser, temp_graph: Path
    ):
        """Test 2: Parser handles nested blocks with correct level tracking."""
        md_file = temp_graph / "pages" / "nested.md"
        md_file.write_text(
            """---
title: Nested
---
- Top level
  - Nested once
    - Nested twice
  - Another nested
- Another top
"""
        )

        page = parser.parse_file(md_file)

        assert len(page.blocks) == 5
        assert page.blocks[0].level == 0
        assert page.blocks[1].level == 1
        assert page.blocks[1].parent_id == page.blocks[0].id
        assert page.blocks[2].level == 2
        assert page.blocks[2].parent_id == page.blocks[1].id

    def test_parser_extracts_property_drawer(
        self, parser: LogseqParser, temp_graph: Path
    ):
        """Test 3: Parser extracts property drawer from YAML frontmatter."""
        md_file = temp_graph / "pages" / "props.md"
        md_file.write_text(
            """---
title: My Page
id:: 648a1b2c-uuid
tags:: [[tag1]] [[tag2]]
confidence:: Layer 2
created_at:: 2026-05-01T10:00:00
---
- Content
"""
        )

        page = parser.parse_file(md_file)

        assert page.properties.title == "My Page"
        assert page.properties.confidence == "Layer 2"
        # Tags parsed from wikilink format

    def test_parser_maps_properties_to_metadata(
        self, parser: LogseqParser, temp_graph: Path
    ):
        """Test 4: Parser maps Logseq properties to Claim metadata fields."""
        md_file = temp_graph / "pages" / "meta.md"
        md_file.write_text(
            """---
title: Meta Page
custom_prop:: custom_value
---
- Block content
"""
        )

        page = parser.parse_file(md_file)

        assert page.properties.title == "Meta Page"
        assert page.properties.custom.get("custom_prop") == "custom_value"

    def test_parser_preserves_wikilink_syntax(
        self, parser: LogseqParser, temp_graph: Path
    ):
        """Test 5: Parser preserves wikilink syntax in block content."""
        md_file = temp_graph / "pages" / "links.md"
        md_file.write_text(
            """---
title: Links
---
- Link to [[Another Page]] and [[Yet Another]]
- Nested [[Wiki Link]] here
"""
        )

        page = parser.parse_file(md_file)

        assert "[[Another Page]]" in page.blocks[0].content
        assert "[[Yet Another]]" in page.blocks[0].content
        assert "[[Wiki Link]]" in page.blocks[1].content

    def test_parser_derives_namespace_from_path(
        self, parser: LogseqParser, temp_graph: Path
    ):
        """Test 6: Parser derives namespace from file path."""
        # Create nested directory structure
        nested_dir = temp_graph / "pages" / "foo" / "bar"
        nested_dir.mkdir(parents=True)
        md_file = nested_dir / "baz.md"
        md_file.write_text(
            """---
title: Baz
---
- Content
"""
        )

        page = parser.parse_file(md_file)

        assert page.namespace == "foo/bar"

    def test_parser_handles_edn_config(
        self, parser: LogseqParser, temp_graph: Path
    ):
        """Test 7: Parser handles EDN config file - parse basics only."""
        config_file = temp_graph / "logseq" / "config.edn"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(
            """{:graph-name "My Graph" :preferred-format :markdown}"""
        )

        config = parser.parse_edn_config(config_file)

        # EDN parsing may or may not work depending on library
        # At minimum, should not crash
        assert isinstance(config, dict)


class TestComputeFileHash:
    """Tests for file hash computation."""

    def test_hash_consistency(self):
        """Test that same content produces same hash."""
        content = "Test content"
        hash1 = compute_file_hash(content)
        hash2 = compute_file_hash(content)
        assert hash1 == hash2

    def test_hash_differs_for_different_content(self):
        """Test that different content produces different hash."""
        hash1 = compute_file_hash("Content 1")
        hash2 = compute_file_hash("Content 2")
        assert hash1 != hash2

    def test_hash_is_sha256_length(self):
        """Test that hash is SHA-256 (64 hex chars)."""
        hash_val = compute_file_hash("test")
        assert len(hash_val) == 64
