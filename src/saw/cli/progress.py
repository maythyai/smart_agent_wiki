"""Progress indicators for Smart Agent Wiki CLI.

This module provides Rich-based progress bars and spinners
for long-running operations.

Usage:
    from saw.cli.progress import ProgressTracker

    tracker = ProgressTracker("Ingesting files")
    tracker.start()
    for file in files:
        tracker.update(file.name)
    tracker.complete()
"""

from __future__ import annotations

import signal
import sys
from typing import Optional, Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text

console = Console()


class ProgressTracker:
    """Progress tracker for long-running CLI operations.

    Features:
    - Spinner for indeterminate progress
    - Bar for determinate progress
    - Graceful Ctrl+C handling
    """

    def __init__(
        self,
        description: str = "Processing",
        total: Optional[int] = None,
        console: Optional[Console] = None,
    ):
        """Initialize progress tracker.

        Args:
            description: Task description
            total: Total items (None for indeterminate spinner)
            console: Console instance (default: global console)
        """
        self.description = description
        self.total = total
        self.console = console or Console()
        self._progress: Optional[Progress] = None
        self._task_id: Optional[int] = None
        self._interrupted = False
        self._original_handler = None

    def start(self) -> None:
        """Start progress tracking."""
        # Setup Ctrl+C handler
        self._setup_interrupt_handler()

        if self.total:
            # Determinate progress bar
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self.console,
            )
            self._progress.start()
            self._task_id = self._progress.add_task(self.description, total=self.total)
        else:
            # Indeterminate spinner
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=self.console,
            )
            self._progress.start()
            self._task_id = self._progress.add_task(self.description, total=None)

    def update(
        self,
        description: Optional[str] = None,
        advance: int = 1,
    ) -> None:
        """Update progress.

        Args:
            description: New description (optional)
            advance: Number of items to advance (default: 1)
        """
        if self._progress and self._task_id is not None:
            if description:
                self._progress.update(self._task_id, description=description, advance=advance)
            else:
                self._progress.update(self._task_id, advance=advance)

    def complete(
        self,
        message: Optional[str] = None,
        success: bool = True,
    ) -> None:
        """Complete progress tracking.

        Args:
            message: Completion message (optional)
            success: Whether operation succeeded
        """
        self._restore_interrupt_handler()

        if self._progress:
            self._progress.stop()
            self._progress = None

        if self._interrupted:
            self.console.print("\n[yellow]Operation cancelled by user.[/yellow]")
            return

        if message:
            if success:
                self.console.print(f"[green]✓ {message}[/green]")
            else:
                self.console.print(f"[red]✗ {message}[/red]")

    def _setup_interrupt_handler(self) -> None:
        """Setup graceful Ctrl+C handler."""
        self._original_handler = signal.getsignal(signal.SIGINT)

        def handler(signum, frame):
            self._interrupted = True
            if self._progress:
                self._progress.stop()
            self._restore_interrupt_handler()
            self.console.print("\n[yellow]Operation cancelled by user.[/yellow]")
            sys.exit(0)

        signal.signal(signal.SIGINT, handler)

    def _restore_interrupt_handler(self) -> None:
        """Restore original interrupt handler."""
        if self._original_handler:
            signal.signal(signal.SIGINT, self._original_handler)


class MultiProgressTracker:
    """Multi-task progress tracker for parallel operations.

    Example:
        tracker = MultiProgressTracker()
        tracker.add_task("Ingesting files", total=10)
        tracker.add_task("Processing claims", total=50)
        tracker.start()
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._progress: Optional[Progress] = None
        self._tasks: dict[str, int] = {}
        self._interrupted = False
        self._original_handler = None

    def add_task(
        self,
        name: str,
        description: str,
        total: Optional[int] = None,
    ) -> None:
        """Add a task to track.

        Args:
            name: Task identifier
            description: Task description
            total: Total items (None for indeterminate)
        """
        if self._progress:
            self._tasks[name] = self._progress.add_task(description, total=total)
        else:
            # Store for later
            self._tasks[name] = (description, total)

    def start(self) -> None:
        """Start multi-task progress."""
        self._setup_interrupt_handler()

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )
        self._progress.start()

        # Add stored tasks
        for name, value in self._tasks.items():
            if isinstance(value, tuple):
                desc, total = value
                self._tasks[name] = self._progress.add_task(desc, total=total)

    def update(
        self,
        name: str,
        description: Optional[str] = None,
        advance: int = 1,
    ) -> None:
        """Update a specific task.

        Args:
            name: Task identifier
            description: New description (optional)
            advance: Number to advance
        """
        if self._progress and name in self._tasks:
            task_id = self._tasks[name]
            if description:
                self._progress.update(task_id, description=description, advance=advance)
            else:
                self._progress.update(task_id, advance=advance)

    def complete(self) -> None:
        """Complete all tasks."""
        self._restore_interrupt_handler()

        if self._progress:
            self._progress.stop()
            self._progress = None

        if self._interrupted:
            self.console.print("\n[yellow]Operations cancelled by user.[/yellow]")

    def _setup_interrupt_handler(self) -> None:
        """Setup graceful Ctrl+C handler."""
        self._original_handler = signal.getsignal(signal.SIGINT)

        def handler(signum, frame):
            self._interrupted = True
            if self._progress:
                self._progress.stop()
            self._restore_interrupt_handler()
            self.console.print("\n[yellow]Operations cancelled by user.[/yellow]")
            sys.exit(0)

        signal.signal(signal.SIGINT, handler)

    def _restore_interrupt_handler(self) -> None:
        """Restore original interrupt handler."""
        if self._original_handler:
            signal.signal(signal.SIGINT, self._original_handler)


def show_spinner(message: str, task: Callable) -> any:
    """Run a task with a spinner.

    Args:
        message: Spinner message
        task: Function to execute

    Returns:
        Task result
    """
    tracker = ProgressTracker(message)
    tracker.start()
    try:
        result = task()
        tracker.complete()
        return result
    except Exception as e:
        tracker.complete(success=False)
        raise


__all__ = ["ProgressTracker", "MultiProgressTracker", "show_spinner"]