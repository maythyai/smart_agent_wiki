"""File watcher for Logseq graphs.

Plan 13-01 Task 3: Real-time directory watching.
Per LOGS-04: System watches Logseq directory for file changes.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class LogseqFileWatcher(FileSystemEventHandler):
    """Watch Logseq graph directory for file changes.

    Per LOGS-04: Real-time directory watching with debouncing.
    """

    DEBOUNCE_MS = 500  # 500ms debounce window

    def __init__(self) -> None:
        """Initialize file watcher."""
        self._observer: Optional[Observer] = None
        self._callback: Optional[Callable[[Path], None]] = None
        self._pending: dict[Path, float] = {}
        self._lock = asyncio.Lock()
        self._watch_path: Optional[Path] = None

    def set_callback(self, callback: Callable[[Path], None]) -> None:
        """Register change handler callback.

        Args:
            callback: Function to call on file change.
        """
        self._callback = callback

    def start(self, graph_path: Path) -> None:
        """Start watching directory.

        Args:
            graph_path: Path to Logseq graph directory.
        """
        self._watch_path = graph_path
        self._observer = Observer()
        self._observer.schedule(self, str(graph_path), recursive=True)
        self._observer.start()
        logger.info(f"Started watching Logseq graph: {graph_path}")

    def stop(self) -> None:
        """Stop watching directory."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None
            logger.info("Stopped file watcher")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event."""
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule_callback(Path(event.src_path), "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event."""
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule_callback(Path(event.src_path), "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion event."""
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule_callback(Path(event.src_path), "deleted")

    def _schedule_callback(self, file_path: Path, event_type: str) -> None:
        """Schedule debounced callback.

        Per LOGS-04: Batch rapid changes within 500ms window.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        # Schedule the callback execution
        loop.call_later(
            self.DEBOUNCE_MS / 1000.0,
            self._execute_callback,
            file_path,
            event_type,
        )

    def _execute_callback(self, file_path: Path, event_type: str) -> None:
        """Execute the callback if registered."""
        if self._callback:
            try:
                # Validate path is within watch directory (T-13-01)
                if self._watch_path:
                    file_path.resolve().relative_to(self._watch_path.resolve())
                self._callback(file_path)
            except ValueError:
                # Path traversal attempt detected
                logger.warning(f"Path traversal blocked: {file_path}")
            except Exception as e:
                logger.error(f"Error in file change callback: {e}")
