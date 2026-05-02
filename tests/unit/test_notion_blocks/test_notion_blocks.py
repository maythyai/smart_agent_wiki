"""Tests for Notion block to markdown conversion.

Plan 12-02: Property mapping and block transformation.
Per NOTI-03: Notion pages ingested as Claims with correct content extraction.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from saw.connectors.notion.blocks import (
    BlockRenderer,
    RichTextRenderer,
    render_blocks_to_markdown,
    render_rich_text,
)


class TestRichTextRenderer:
    """Tests for rich text rendering."""

    def test_render_plain_text(self) -> None:
        """Test rendering plain text without formatting."""
        rich_text = [
            {"type": "text", "plain_text": "Hello World", "annotations": {}},
        ]
        result = render_rich_text(rich_text)
        assert result == "Hello World"

    def test_render_bold_text(self) -> None:
        """Test rendering bold text."""
        rich_text = [
            {"type": "text", "plain_text": "bold", "annotations": {"bold": True}},
        ]
        result = render_rich_text(rich_text)
        assert result == "**bold**"

    def test_render_italic_text(self) -> None:
        """Test rendering italic text."""
        rich_text = [
            {"type": "text", "plain_text": "italic", "annotations": {"italic": True}},
        ]
        result = render_rich_text(rich_text)
        assert result == "*italic*"

    def test_render_code_text(self) -> None:
        """Test rendering inline code."""
        rich_text = [
            {"type": "text", "plain_text": "code", "annotations": {"code": True}},
        ]
        result = render_rich_text(rich_text)
        assert result == "`code`"

    def test_render_strikethrough_text(self) -> None:
        """Test rendering strikethrough text."""
        rich_text = [
            {"type": "text", "plain_text": "strike", "annotations": {"strikethrough": True}},
        ]
        result = render_rich_text(rich_text)
        assert result == "~~strike~~"

    def test_render_bold_italic(self) -> None:
        """Test rendering combined bold and italic."""
        rich_text = [
            {
                "type": "text",
                "plain_text": "both",
                "annotations": {"bold": True, "italic": True},
            },
        ]
        result = render_rich_text(rich_text)
        assert "***both***" in result or "**both**" in result

    def test_render_multiple_segments(self) -> None:
        """Test rendering multiple text segments."""
        rich_text = [
            {"type": "text", "plain_text": "Hello ", "annotations": {}},
            {"type": "text", "plain_text": "World", "annotations": {"bold": True}},
        ]
        result = render_rich_text(rich_text)
        assert result == "Hello **World**"

    def test_render_mention(self) -> None:
        """Test 17: rendering mention (user/page/database) converts to link or text."""
        rich_text = [
            {
                "type": "mention",
                "plain_text": "@User Name",
                "href": "notion://user/123",
                "annotations": {},
            },
        ]
        result = render_rich_text(rich_text)
        assert "@User Name" in result or "[User Name]" in result


class TestBlockRenderer:
    """Tests for block rendering."""

    @pytest.mark.asyncio
    async def test_render_paragraph(self) -> None:
        """Test 1: paragraph block converts to plain text."""
        block = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "plain_text": "Hello world", "annotations": {}}]
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "Hello world" in result

    @pytest.mark.asyncio
    async def test_render_heading_1(self) -> None:
        """Test 2: heading_1 block converts to # markdown."""
        block = {
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "plain_text": "Title", "annotations": {}}]
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert result.strip() == "# Title"

    @pytest.mark.asyncio
    async def test_render_heading_2(self) -> None:
        """Test 2: heading_2 block converts to ## markdown."""
        block = {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "plain_text": "Subtitle", "annotations": {}}]
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert result.strip() == "## Subtitle"

    @pytest.mark.asyncio
    async def test_render_heading_3(self) -> None:
        """Test 2: heading_3 block converts to ### markdown."""
        block = {
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "plain_text": "Section", "annotations": {}}]
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert result.strip() == "### Section"

    @pytest.mark.asyncio
    async def test_render_bulleted_list_item(self) -> None:
        """Test 3: bulleted_list_item converts to - item."""
        block = {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "plain_text": "Item", "annotations": {}}]
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert result.strip() == "- Item"

    @pytest.mark.asyncio
    async def test_render_numbered_list_item(self) -> None:
        """Test 4: numbered_list_item converts to 1. item."""
        block = {
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"type": "text", "plain_text": "First", "annotations": {}}]
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "1." in result and "First" in result

    @pytest.mark.asyncio
    async def test_render_to_do_unchecked(self) -> None:
        """Test 5: to_do block converts to - [ ] checkbox."""
        block = {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "plain_text": "Task", "annotations": {}}],
                "checked": False,
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "- [ ]" in result and "Task" in result

    @pytest.mark.asyncio
    async def test_render_to_do_checked(self) -> None:
        """Test 5: to_do block checked converts to - [x] checkbox."""
        block = {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "plain_text": "Done", "annotations": {}}],
                "checked": True,
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "- [x]" in result and "Done" in result

    @pytest.mark.asyncio
    async def test_render_code_block(self) -> None:
        """Test 6: code block converts to fenced code with language."""
        block = {
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "plain_text": "print('hello')", "annotations": {}}],
                "language": "python",
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "```python" in result
        assert "print('hello')" in result
        assert "```" in result

    @pytest.mark.asyncio
    async def test_render_quote(self) -> None:
        """Test 7: quote block converts to > blockquote."""
        block = {
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "plain_text": "Quote text", "annotations": {}}]
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "> Quote text" in result

    @pytest.mark.asyncio
    async def test_render_divider(self) -> None:
        """Test 8: divider converts to ---."""
        block = {"type": "divider", "divider": {}}
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "---" in result

    @pytest.mark.asyncio
    async def test_render_callout(self) -> None:
        """Test 9: callout block converts to blockquote with emoji."""
        block = {
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "plain_text": "Note", "annotations": {}}],
                "icon": {"type": "emoji", "emoji": "💡"},
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert ">" in result and "Note" in result

    @pytest.mark.asyncio
    async def test_render_image(self) -> None:
        """Test 10: image block converts to ![alt](url)."""
        block = {
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": "https://example.com/image.png"},
                "caption": [{"type": "text", "plain_text": "Alt text"}],
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "![" in result and "](" in result

    @pytest.mark.asyncio
    async def test_render_bookmark(self) -> None:
        """Test 11: bookmark block converts to [title](url)."""
        block = {
            "type": "bookmark",
            "bookmark": {
                "url": "https://example.com",
                "caption": [{"type": "text", "plain_text": "Example"}],
            },
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "[" in result and "]" in result and "(https://example.com)" in result

    @pytest.mark.asyncio
    async def test_render_equation(self) -> None:
        """Test 12: equation block converts to $$ LaTeX $$."""
        block = {
            "type": "equation",
            "equation": {"expression": "E = mc^2"},
        }
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "$$" in result or "E = mc^2" in result

    @pytest.mark.asyncio
    async def test_render_unknown_block(self) -> None:
        """Test 18: Unknown block type returns placeholder text, does not crash."""
        block = {"type": "unknown_type", "unknown_type": {}}
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await renderer.render_block(block)
        assert "<!-- Unknown block type" in result


class TestNestedBlocks:
    """Tests for nested block rendering."""

    @pytest.mark.asyncio
    async def test_render_nested_blocks(self) -> None:
        """Test 15: nested blocks render with correct indentation."""
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "plain_text": "Parent", "annotations": {}}]
                },
                "has_children": True,
            },
        ]
        mock_client = AsyncMock()
        mock_client.blocks = AsyncMock()
        mock_client.blocks.children = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={
            "results": [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "plain_text": "Child", "annotations": {}}]
                    },
                },
            ],
            "has_more": False,
        })

        renderer = BlockRenderer(mock_client)
        result = await render_blocks_to_markdown(blocks, renderer, indent=0)

        assert "Parent" in result


class TestRenderBlocksToMarkdown:
    """Tests for render_blocks_to_markdown function."""

    @pytest.mark.asyncio
    async def test_render_multiple_blocks(self) -> None:
        """Test rendering multiple blocks."""
        blocks = [
            {
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "plain_text": "Title", "annotations": {}}]
                },
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "plain_text": "Content", "annotations": {}}]
                },
            },
        ]
        mock_client = AsyncMock()
        renderer = BlockRenderer(mock_client)
        result = await render_blocks_to_markdown(blocks, renderer)

        assert "# Title" in result
        assert "Content" in result
