"""Markdown Formatter Plugin.

Adds custom admonition blocks and heading styles to wiki pages.
"""

from saw.plugins.base import PluginBase, PluginContext
from saw.plugins.events import PageCreated, PageUpdated


class MarkdownFormatterPlugin(PluginBase):
    name = "markdown-formatter"
    version = "0.1.0"
    description = "Custom Markdown rendering rules"

    def __init__(self):
        self.context = None

    def activate(self, context: PluginContext) -> None:
        """Activate plugin and subscribe to events."""
        self.context = context
        context.subscribe_event("page_created", self.on_event)
        context.subscribe_event("page_updated", self.on_event)

    def deactivate(self) -> None:
        """Cleanup."""
        self.context = None

    def on_event(self, event) -> None:
        """Process page content with custom formatting."""
        if isinstance(event, (PageCreated, PageUpdated)):
            content = getattr(event, "new_content", "") or getattr(event, "content", "")
            # Add custom admonition syntax
            formatted = self._format_admonitions(content)
            # Add heading anchors
            formatted = self._add_heading_anchors(formatted)
            # Store formatted version in plugin data dir
            if self.context:
                data_file = self.context.data_dir / f"{event.page_id}.md"
                data_file.write_text(formatted)

    def _format_admonitions(self, content: str) -> str:
        """Convert :::note blocks to styled HTML."""
        import re
        pattern = r":::(note|warning|tip|info)\n(.*?):::"
        replacement = r'<div class="admonition \1">\2</div>'
        return re.sub(pattern, replacement, content, flags=re.DOTALL)

    def _add_heading_anchors(self, content: str) -> str:
        """Add anchor links to headings."""
        import re
        def add_anchor(match):
            level = len(match.group(1))
            title = match.group(2)
            anchor = title.lower().replace(" ", "-")
            return f'<h{level} id="{anchor}"><a href="#{anchor}">#</a> {title}</h{level}>'

        return re.sub(r"^(#{1,6})\s+(.+)$", add_anchor, content, flags=re.MULTILINE)
