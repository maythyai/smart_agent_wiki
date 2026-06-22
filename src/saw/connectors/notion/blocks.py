"""Notion block to markdown conversion.

Plan 12-02: Property mapping and block transformation.
Per NOTI-03: Notion blocks (paragraphs, lists, code) convert to markdown content.
"""
from __future__ import annotations

from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


def render_rich_text(rich_text: list[dict]) -> str:
    """Render Notion rich_text list to markdown-formatted string.

    Handles text formatting (bold, italic, code, strikethrough) and
    mentions (user, page, database).

    Args:
        rich_text: List of rich_text objects from Notion API.

    Returns:
        Markdown-formatted string.
    """
    if not rich_text:
        return ""

    result = []
    for segment in rich_text:
        text = segment.get("plain_text", "")
        segment_type = segment.get("type", "text")
        annotations = segment.get("annotations", {})

        if segment_type == "mention":
            # Handle mentions
            href = segment.get("href", "")
            if href:
                text = f"[{text}]({href})"
            # Otherwise keep plain text
        elif segment_type == "equation":
            # Inline equation
            text = f"${text}$"

        # Apply annotations
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if annotations.get("code"):
            text = f"`{text}`"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("bold"):
            text = f"**{text}**"

        result.append(text)

    return "".join(result)


class RichTextRenderer:
    """Class-based rich text renderer."""

    @staticmethod
    def render(rich_text: list[dict]) -> str:
        """Render rich text to markdown.

        Args:
            rich_text: List of rich_text objects.

        Returns:
            Markdown-formatted string.
        """
        return render_rich_text(rich_text)


class BlockRenderer:
    """Renders Notion blocks to markdown.

    Per NOTI-03: Converts all common Notion block types to markdown.
    """

    def __init__(self, client: Any) -> None:
        """Initialize block renderer.

        Args:
            client: Notion API client for fetching block children.
        """
        self._client = client

    async def render_block(self, block: dict) -> str:
        """Render a single Notion block to markdown.

        Args:
            block: Block dict from Notion API.

        Returns:
            Markdown-formatted string.
        """
        block_type = block.get("type", "unknown")
        handler = getattr(self, f"_render_{block_type}", self._render_unknown)
        return await handler(block)

    async def _render_paragraph(self, block: dict) -> str:
        """Render paragraph block."""
        rich_text = block.get("paragraph", {}).get("rich_text", [])
        text = render_rich_text(rich_text)
        return f"{text}\n"

    async def _render_heading_1(self, block: dict) -> str:
        """Render heading level 1."""
        rich_text = block.get("heading_1", {}).get("rich_text", [])
        text = render_rich_text(rich_text)
        return f"# {text}\n"

    async def _render_heading_2(self, block: dict) -> str:
        """Render heading level 2."""
        rich_text = block.get("heading_2", {}).get("rich_text", [])
        text = render_rich_text(rich_text)
        return f"## {text}\n"

    async def _render_heading_3(self, block: dict) -> str:
        """Render heading level 3."""
        rich_text = block.get("heading_3", {}).get("rich_text", [])
        text = render_rich_text(rich_text)
        return f"### {text}\n"

    async def _render_bulleted_list_item(self, block: dict) -> str:
        """Render bulleted list item."""
        rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
        text = render_rich_text(rich_text)
        return f"- {text}\n"

    async def _render_numbered_list_item(self, block: dict) -> str:
        """Render numbered list item."""
        rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
        text = render_rich_text(rich_text)
        # Number will be determined by position in sequence
        return f"1. {text}\n"

    async def _render_to_do(self, block: dict) -> str:
        """Render to-do (checkbox) block."""
        todo = block.get("to_do", {})
        rich_text = todo.get("rich_text", [])
        checked = todo.get("checked", False)
        text = render_rich_text(rich_text)
        checkbox = "[x]" if checked else "[ ]"
        return f"- {checkbox} {text}\n"

    async def _render_code(self, block: dict) -> str:
        """Render code block."""
        code = block.get("code", {})
        rich_text = code.get("rich_text", [])
        language = code.get("language", "")
        text = render_rich_text(rich_text)
        return f"```{language}\n{text}\n```\n"

    async def _render_quote(self, block: dict) -> str:
        """Render quote block."""
        rich_text = block.get("quote", {}).get("rich_text", [])
        text = render_rich_text(rich_text)
        # Handle multi-line quotes
        lines = text.split("\n")
        quoted_lines = [f"> {line}" for line in lines]
        return "\n".join(quoted_lines) + "\n"

    async def _render_divider(self, block: dict) -> str:
        """Render divider."""
        return "---\n"

    async def _render_callout(self, block: dict) -> str:
        """Render callout block."""
        callout = block.get("callout", {})
        rich_text = callout.get("rich_text", [])
        icon = callout.get("icon", {})

        text = render_rich_text(rich_text)

        # Get emoji icon if available
        emoji = ""
        if icon and icon.get("type") == "emoji":
            emoji = icon.get("emoji", "")

        # Render as blockquote with icon
        if emoji:
            return f"> {emoji} {text}\n"
        return f"> {text}\n"

    async def _render_image(self, block: dict) -> str:
        """Render image block."""
        image = block.get("image", {})
        image_type = image.get("type", "external")

        url = ""
        if image_type == "external":
            url = image.get("external", {}).get("url", "")
        elif image_type == "file":
            url = image.get("file", {}).get("url", "")

        # Get caption
        caption = image.get("caption", [])
        alt_text = render_rich_text(caption) if caption else "image"

        return f"![{alt_text}]({url})\n"

    async def _render_video(self, block: dict) -> str:
        """Render video block."""
        video = block.get("video", {})
        video_type = video.get("type", "external")

        url = ""
        if video_type == "external":
            url = video.get("external", {}).get("url", "")
        elif video_type == "file":
            url = video.get("file", {}).get("url", "")

        return f"[Video: {url}]({url})\n"

    async def _render_file(self, block: dict) -> str:
        """Render file block."""
        file = block.get("file", {})
        file_type = file.get("type", "external")

        url = ""
        if file_type == "external":
            url = file.get("external", {}).get("url", "")
        elif file_type == "file":
            url = file.get("file", {}).get("url", "")

        name = file.get("name", "file")
        return f"[File: {name}]({url})\n"

    async def _render_bookmark(self, block: dict) -> str:
        """Render bookmark block."""
        bookmark = block.get("bookmark", {})
        url = bookmark.get("url", "")
        caption = bookmark.get("caption", [])

        title = render_rich_text(caption) if caption else url

        return f"[{title}]({url})\n"

    async def _render_equation(self, block: dict) -> str:
        """Render equation block."""
        equation = block.get("equation", {})
        expression = equation.get("expression", "")

        return f"$$\n{expression}\n$$\n"

    async def _render_toggle(self, block: dict) -> str:
        """Render toggle block with child content."""
        toggle = block.get("toggle", {})
        rich_text = toggle.get("rich_text", [])
        text = render_rich_text(rich_text)

        # Fetch and render child blocks if block ID is available
        block_id = block.get("id", "")
        children_md = ""
        if block_id and hasattr(self, "_fetch_children"):
            try:
                children = await self._fetch_children(block_id)
                for child in children:
                    children_md += await self.render_block(child)
            except Exception:
                children_md = "_Failed to load child content._"

        return f"<details><summary>{text}</summary>\n\n{children_md}\n\n</details>\n"

    async def _render_column_list(self, block: dict) -> str:
        """Render column list - flatten columns."""
        # Just return placeholder, children will be rendered
        return ""

    async def _render_column(self, block: dict) -> str:
        """Render column."""
        return ""

    async def _render_table(self, block: dict) -> str:
        """Render table block."""
        table = block.get("table", {})
        table_width = table.get("table_width", 0)

        # Placeholder - actual rows are separate blocks
        return f"\n| {' | '.join(['...'] * max(1, table_width))} |\n"

    async def _render_table_row(self, block: dict) -> str:
        """Render table row."""
        table_row = block.get("table_row", {})
        cells = table_row.get("cells", [])

        cell_texts = []
        for cell in cells:
            cell_texts.append(render_rich_text(cell))

        return f"| {' | '.join(cell_texts)} |\n"

    async def _render_synced_block(self, block: dict) -> str:
        """Render synced block as regular content."""
        return ""

    async def _render_template(self, block: dict) -> str:
        """Render template block."""
        return "<!-- Template block -->\n"

    async def _render_link_to_page(self, block: dict) -> str:
        """Render link to page block."""
        link = block.get("link_to_page", {})
        page_id = link.get("page_id", "")
        return f"[Page: {page_id}](notion://page/{page_id})\n"

    async def _render_child_page(self, block: dict) -> str:
        """Render child page block."""
        child = block.get("child_page", {})
        title = child.get("title", "")
        return f"**{title}**\n"

    async def _render_child_database(self, block: dict) -> str:
        """Render child database block."""
        child = block.get("child_database", {})
        title = child.get("title", "")
        return f"[Database: {title}]\n"

    async def _render_unknown(self, block: dict) -> str:
        """Handle unknown block type gracefully."""
        block_type = block.get("type", "unknown")
        logger.warning(f"Unknown block type: {block_type}")
        return f"<!-- Unknown block type: {block_type} -->\n"


async def render_blocks_to_markdown(
    blocks: list[dict],
    renderer: BlockRenderer,
    indent: int = 0,
) -> str:
    """Render list of blocks to markdown string.

    Handles nested blocks and recursion for children.

    Args:
        blocks: List of block dicts from Notion API.
        renderer: BlockRenderer instance.
        indent: Indentation level for nested content.

    Returns:
        Markdown-formatted string.
    """
    if not blocks:
        return ""

    result = []
    indent_str = "  " * indent

    for block in blocks:
        # Render the block itself
        content = await renderer.render_block(block)

        # Apply indentation
        if indent > 0 and content.strip():
            lines = content.split("\n")
            indented_lines = [f"{indent_str}{line}" if line.strip() else line for line in lines]
            content = "\n".join(indented_lines)

        result.append(content)

        # Handle children
        if block.get("has_children"):
            try:
                children_response = await renderer._client.blocks.children.list(
                    block_id=block["id"]
                )
                children = children_response.get("results", [])
                if children:
                    child_content = await render_blocks_to_markdown(
                        children, renderer, indent=indent + 1
                    )
                    result.append(child_content)
            except Exception as e:
                logger.warning(f"Failed to fetch children for block {block.get('id')}: {e}")

    return "\n".join(result)


def extract_plain_text(rich_text: list[dict]) -> str:
    """Extract plain text from rich_text without formatting.

    Args:
        rich_text: List of rich_text objects.

    Returns:
        Plain text string.
    """
    if not rich_text:
        return ""
    return "".join(seg.get("plain_text", "") for seg in rich_text)
