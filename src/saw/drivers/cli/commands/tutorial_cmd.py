#!/usr/bin/env python3
"""
Interactive Tutorial Command for Smart Agent Wiki.

This module provides a guided tour for new users to learn the basics
in approximately 5 minutes.

Usage:
    saw tutorial
    saw tutorial --skip-web
    saw tutorial --reset
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

app = typer.Typer(
    name="tutorial",
    help="Interactive guided tour for new users (5 minutes)",
)
console = Console()


# Tutorial steps configuration
TUTORIAL_STEPS = [
    {
        "title": "Welcome to Smart Agent Wiki",
        "content": """
Smart Agent Wiki is a knowledge management platform that helps you:
• Store documents securely
• Extract knowledge automatically
• Search and query your knowledge base
• Visualize connections in a graph

This tutorial will guide you through the basics in about 5 minutes.
""",
        "action": None,
    },
    {
        "title": "Creating a Demo Wiki",
        "content": """
Let's create a wiki with some demo content so you can explore.

We'll create:
• 3 sample documents (Markdown, PDF, code)
• A working wiki database
• Some extracted claims to query
""",
        "action": "create_demo",
    },
    {
        "title": "Checking Wiki Status",
        "content": """
Your wiki is ready! Let's see what we have:

Run: saw status

This shows:
• Number of documents
• Number of claims extracted
• Wiki pages created
""",
        "action": "run_status",
    },
    {
        "title": "Searching Your Knowledge",
        "content": """
Now let's try searching the knowledge base.

Run: saw query "project"

This will find all claims related to 'project' in your documents.
""",
        "action": "run_query",
    },
    {
        "title": "Launching the Web UI",
        "content": """
The web interface provides:
• Search and browse your wiki
• Visualize knowledge graphs
• Edit wiki pages
• View document sources

Run: saw web
""",
        "action": "launch_web",
    },
    {
        "title": "Tutorial Complete!",
        "content": """
🎉 Congratulations! You've completed the tutorial.

What you learned:
• How to initialize a wiki
• How documents get ingested
• How to search your knowledge
• How to use the web UI

Next steps:
• Ingest your own documents: saw ingest ./my-documents
• Read the docs: https://github.com/chensaics/smart_agent_wiki
• Try examples: https://github.com/chensaics/smart_agent_wiki/tree/master/examples
""",
        "action": None,
    },
]


def create_demo_wiki(path: Path) -> bool:
    """Create a demo wiki with sample content."""
    from saw.tutorial.demo_content import create_sample_documents

    console.print("\n[blue]Creating demo wiki...[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up...", total=None)

        # Create wiki directory
        wiki_path = path / "tutorial-wiki"
        wiki_path.mkdir(parents=True, exist_ok=True)

        progress.update(task, description="Creating sample documents...")

        # Create sample documents
        docs_path = wiki_path / "documents"
        docs_path.mkdir(exist_ok=True)
        create_sample_documents(docs_path)

        progress.update(task, description="Initializing wiki...")

        # Initialize wiki (would call saw init internally)
        # For now, just create the structure
        db_path = wiki_path / "wiki.db"
        vault_path = wiki_path / "vault"
        vault_path.mkdir(exist_ok=True)

        progress.update(task, description="Demo wiki created!")

    console.print("[green]✓[/green] Demo wiki created at: tutorial-wiki/")
    console.print("[green]✓[/green] 3 sample documents added")

    return True


def run_command(cmd: str, wiki_path: Optional[Path] = None) -> None:
    """Run a SAW command and show output."""
    console.print(f"\n[cyan]> {cmd}[/cyan]")

    try:
        # Simulate command output for tutorial
        if cmd == "saw status":
            console.print("""
Documents: 3
  - project-notes.md (Markdown)
  - meeting-summary.pdf (PDF)
  - utils.py (Python)

Claims: 15 extracted
  - Verified: 5 (33%)
  - Cross-validated: 3 (20%)
  - Single-source: 7 (47%)

Wiki Pages: 4 created
  - Project Overview
  - Meeting Notes
  - Code Reference
  - Getting Started

Last activity: Just now
""")
        elif cmd.startswith("saw query"):
            term = cmd.split('"')[1] if '"' in cmd else "project"
            console.print(f"""
Searching for: "{term}"

Results found: 5

[1] Project Timeline (confidence: 0.85)
    Source: project-notes.md
    → "Phase 1 complete by end of Q2"
    → "Team assigned to implementation"

[2] Meeting Decisions (confidence: 0.72)
    Source: meeting-summary.pdf
    → "Approved budget for phase 2"
    → "Launch target: September"

[3] Code Structure (confidence: 0.95)
    Source: utils.py (AST parsed)
    → "Helper functions for data processing"
    → "Main entry point: process_data()"
""")
        elif cmd == "saw web":
            console.print("""
Starting Smart Agent Wiki Web UI...

Server running at: http://localhost:8000
Web interface at: http://localhost:3000

Features available:
  • Search interface
  • Knowledge graph visualization
  • Wiki page editor
  • Document browser

Press Ctrl+C to stop the server.
""")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def tutorial(
    skip_web: bool = typer.Option(
        False, "--skip-web", help="Skip the web UI launch step"
    ),
    reset: bool = typer.Option(
        False, "--reset", help="Reset tutorial progress and start fresh"
    ),
) -> None:
    """
    Interactive guided tour for new users.

    This tutorial will guide you through the basics of Smart Agent Wiki
    in approximately 5 minutes. You'll learn how to:

    • Create and initialize a wiki
    • Ingest documents
    • Search your knowledge base
    • Use the web interface

    Examples:
        saw tutorial
        saw tutorial --skip-web
    """
    console.print(Panel.fit(
        "[bold blue]🎮 Smart Agent Wiki Interactive Tutorial[/bold blue]\n"
        "[dim]Learn the basics in 5 minutes[/dim]",
        border_style="blue",
    ))

    # Ask if user wants to proceed
    if not Confirm.ask("\nReady to start the tutorial?", default=True):
        console.print("[yellow]Tutorial cancelled. Run 'saw tutorial' anytime to start.[/yellow]")
        raise typer.Exit()

    # Determine wiki path
    wiki_path = Path.cwd()

    # Run tutorial steps
    steps = TUTORIAL_STEPS.copy()
    if skip_web:
        # Remove web launch step
        steps = [s for s in steps if s["action"] != "launch_web"]

    for i, step in enumerate(steps, 1):
        console.print(f"\n[bold]Step {i}/{len(steps)}: {step['title']}[/bold]")
        console.print(step["content"])

        # Pause for user to read
        if step["action"]:
            Prompt.ask("\nPress Enter to continue", default="")

        # Execute action
        if step["action"] == "create_demo":
            create_demo_wiki(wiki_path)
        elif step["action"] == "run_status":
            run_command("saw status", wiki_path)
        elif step["action"] == "run_query":
            run_command("saw query \"project\"", wiki_path)
        elif step["action"] == "launch_web":
            console.print("\n[yellow]Note: Web UI requires a running server.[/yellow]")
            console.print("[yellow]In a real setup, run 'saw web' in a separate terminal.[/yellow]")
            run_command("saw web", wiki_path)

            if Confirm.ask("\nWould you like to open the demo page in your browser?", default=False):
                console.print("[dim]Opening http://localhost:8000...[/dim]")

    # Final message
    console.print(Panel.fit(
        "[bold green]✓ Tutorial Complete![/bold green]\n"
        "You're ready to use Smart Agent Wiki!\n\n"
        "[cyan]Next steps:[/cyan]\n"
        "  saw ingest ./my-documents  # Add your documents\n"
        "  saw query 'topic'          # Search your wiki\n"
        "  saw web                    # Launch web UI\n\n"
        "[dim]Docs: https://github.com/chensaics/smart_agent_wiki[/dim]",
        border_style="green",
    ))


if __name__ == "__main__":
    app()