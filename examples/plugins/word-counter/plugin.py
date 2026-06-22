"""Word Counter Plugin.

Analyzes word count and estimates reading time for wiki pages.
"""

import json
from pathlib import Path
from saw.plugins.base import PluginBase, PluginContext
from saw.plugins.events import PageCreated, PageUpdated


class WordCounterPlugin(PluginBase):
    name = "word-counter"
    version = "0.1.0"
    description = "Word count and reading time analysis"

    WORDS_PER_MINUTE = 200

    def __init__(self):
        self.context = None
        self.stats_file = None

    def activate(self, context: PluginContext) -> None:
        """Activate plugin."""
        self.context = context
        self.stats_file = context.data_dir / "word_stats.json"
        context.subscribe_event("page_created", self.on_event)
        context.subscribe_event("page_updated", self.on_event)

    def deactivate(self) -> None:
        """Cleanup."""
        self.context = None

    def on_event(self, event) -> None:
        """Count words and update statistics."""
        if isinstance(event, (PageCreated, PageUpdated)):
            content = getattr(event, "new_content", "") or getattr(event, "content", "")
            word_count = self._count_words(content)
            reading_time = word_count / self.WORDS_PER_MINUTE

            stats = self._load_stats()
            stats[event.page_id] = {
                "word_count": word_count,
                "reading_time_minutes": round(reading_time, 1),
                "last_updated": event.timestamp.isoformat(),
            }
            self._save_stats(stats)

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())

    def _load_stats(self) -> dict:
        """Load statistics from file."""
        if self.stats_file and self.stats_file.exists():
            try:
                return json.loads(self.stats_file.read_text())
            except Exception:
                pass
        return {}

    def _save_stats(self, stats: dict) -> None:
        """Save statistics to file."""
        if self.stats_file:
            self.stats_file.write_text(json.dumps(stats, indent=2))
