"""Offline documentation generator for Smart Agent Wiki.

This module generates static HTML documentation for offline access.

Usage:
    saw docs --output ./docs-offline/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress

console = Console()

# HTML template for offline docs
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Smart Agent Wiki</title>
    <style>
        :root {
            --bg-color: #1a1a2e;
            --text-color: #eee;
            --accent-color: #4a9eff;
            --border-color: #333;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3 { color: var(--accent-color); }
        code {
            background: #2a2a4e;
            padding: 2px 6px;
            border-radius: 3px;
        }
        pre {
            background: #2a2a4e;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        a { color: var(--accent-color); }
        nav {
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        nav a { margin-right: 15px; }
        .command {
            border: 1px solid var(--border-color);
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .warning { color: #ff6b6b; }
        .success { color: #51cf66; }
    </style>
</head>
<body>
    <nav>
        <a href="index.html">Home</a>
        <a href="commands.html">Commands</a>
        <a href="troubleshooting.html">Troubleshooting</a>
        <a href="migration.html">Migration</a>
    </nav>
    <main>
        {content}
    </main>
</body>
</html>'''

# Command reference data
COMMANDS_DATA = {
    "init": {
        "description": "Initialize a new wiki",
        "aliases": [],
        "arguments": [],
        "options": [
            {"name": "--name TEXT", "description": "Wiki name"},
            {"name": "--description TEXT", "description": "Wiki description"},
            {"name": "--path PATH", "description": "Custom directory path"},
        ],
        "examples": [
            "saw init",
            "saw init --name 'Project Knowledge'",
        ],
    },
    "ingest": {
        "description": "Ingest documents into wiki",
        "aliases": ["i"],
        "arguments": ["PATH - File, directory, or URL"],
        "options": [
            {"name": "--format TEXT", "description": "Override format detection"},
            {"name": "--recursive, -r", "description": "Process directories recursively"},
            {"name": "--dry-run", "description": "Show what would be ingested"},
            {"name": "--validate", "description": "Validate extracted claims"},
        ],
        "examples": [
            "saw ingest document.pdf",
            "saw ingest ./documents/ --recursive",
            "saw i document.pdf",
        ],
    },
    "query": {
        "description": "Search the knowledge base",
        "aliases": ["q"],
        "arguments": ["QUERY - Search query text"],
        "options": [
            {"name": "--mode TEXT", "description": "Query mode (direct/graph/reasoning)"},
            {"name": "--max-results N", "description": "Maximum results"},
            {"name": "--confidence FLOAT", "description": "Minimum confidence filter"},
        ],
        "examples": [
            "saw query 'API design'",
            "saw query 'auth' --mode graph",
            "saw q 'database'",
        ],
    },
    "status": {
        "description": "Show wiki status",
        "aliases": ["s"],
        "arguments": [],
        "options": [
            {"name": "--verbose, -v", "description": "Show detailed statistics"},
            {"name": "--json", "description": "Output as JSON"},
        ],
        "examples": [
            "saw status",
            "saw status --verbose",
            "saw s",
        ],
    },
    "web": {
        "description": "Launch web UI",
        "aliases": ["w"],
        "arguments": [],
        "options": [
            {"name": "--port N", "description": "Server port (default: 8000)"},
            {"name": "--host TEXT", "description": "Server host"},
            {"name": "--open", "description": "Open browser automatically"},
        ],
        "examples": [
            "saw web",
            "saw web --port 8080 --open",
            "saw w",
        ],
    },
    "config": {
        "description": "Configure wiki settings",
        "aliases": [],
        "arguments": [],
        "options": [
            {"name": "--path PATH", "description": "Config file path"},
            {"name": "--show", "description": "Show current config"},
        ],
        "examples": [
            "saw config",
            "saw config --show",
        ],
    },
    "tutorial": {
        "description": "Interactive tutorial",
        "aliases": [],
        "arguments": [],
        "options": [
            {"name": "--step N", "description": "Start from specific step"},
            {"name": "--skip-demo", "description": "Skip demo content"},
            {"name": "--reset", "description": "Reset progress"},
        ],
        "examples": [
            "saw tutorial",
            "saw tutorial --step 3",
        ],
    },
    "completion": {
        "description": "Generate shell completions",
        "aliases": [],
        "arguments": ["SHELL - bash/zsh/fish"],
        "options": [
            {"name": "--install, -i", "description": "Install completion script"},
        ],
        "examples": [
            "saw completion bash",
            "saw completion zsh --install",
        ],
    },
}


def generate_index_html() -> str:
    """Generate index.html content."""
    content = """
    <h1>Smart Agent Wiki Documentation</h1>
    <p>Offline documentation for Smart Agent Wiki CLI.</p>

    <h2>Quick Links</h2>
    <ul>
        <li><a href="commands.html">Command Reference</a></li>
        <li><a href="troubleshooting.html">Troubleshooting Guide</a></li>
        <li><a href="migration.html">Migration Guide</a></li>
    </ul>

    <h2>Quick Start</h2>
    <pre>
# Install
curl -fsSL https://get.saw.wiki | bash

# Initialize wiki
saw init

# Ingest documents
saw ingest document.pdf

# Query knowledge base
saw query "topic"

# Launch web UI
saw web
    </pre>

    <h2>Short Aliases</h2>
    <table>
        <tr><th>Alias</th><th>Full Command</th></tr>
        <tr><td>saw i</td><td>saw ingest</td></tr>
        <tr><td>saw q</td><td>saw query</td></tr>
        <tr><td>saw s</td><td>saw status</td></tr>
        <tr><td>saw w</td><td>saw web</td></tr>
        <tr><td>saw v</td><td>saw verify</td></tr>
        <tr><td>saw l</td><td>saw lint</td></tr>
    </table>
    """
    return HTML_TEMPLATE.format(title="Documentation", content=content)


def generate_commands_html() -> str:
    """Generate commands.html content."""
    content = "<h1>Command Reference</h1>\n"

    for cmd_name, cmd_data in COMMANDS_DATA.items():
        aliases = " (alias: " + ", ".join(cmd_data.get("aliases", [])) + ")" if cmd_data.get("aliases") else ""
        content += f'''
        <div class="command">
            <h2>saw {cmd_name}{aliases}</h2>
            <p>{cmd_data["description"]}</p>
        '''

        if cmd_data.get("arguments"):
            content += "<h3>Arguments</h3><ul>"
            for arg in cmd_data["arguments"]:
                content += f"<li><code>{arg}</code></li>"
            content += "</ul>"

        if cmd_data.get("options"):
            content += "<h3>Options</h3><ul>"
            for opt in cmd_data["options"]:
                content += f"<li><code>{opt['name']}</code> — {opt['description']}</li>"
            content += "</ul>"

        if cmd_data.get("examples"):
            content += "<h3>Examples</h3><pre>"
            for ex in cmd_data["examples"]:
                content += f"{ex}\n"
            content += "</pre>"

        content += "</div>\n"

    return HTML_TEMPLATE.format(title="Commands", content=content)


def generate_troubleshooting_html() -> str:
    """Generate troubleshooting.html content."""
    content = """
    <h1>Troubleshooting Guide</h1>

    <h2>Installation Issues</h2>

    <h3>Python version not supported</h3>
    <p class="warning">Error: Python 3.11+ required</p>
    <p class="success">Solution: Install Python 3.11+</p>
    <pre>
pyenv install 3.11
pyenv global 3.11
    </pre>

    <h3>pipx not found</h3>
    <p class="warning">Error: pipx: command not found</p>
    <p class="success">Solution: Install pipx</p>
    <pre>
brew install pipx  # macOS
pip install pipx   # Linux
    </pre>

    <h2>Database Issues</h2>

    <h3>Database locked</h3>
    <p class="warning">Error: sqlite3.OperationalError: database is locked</p>
    <p class="success">Solution:</p>
    <pre>
# Check running processes
ps aux | grep saw

# Remove lock files
rm -f .saw/*.lock
    </pre>

    <h2>Query Issues</h2>

    <h3>No results found</h3>
    <p class="warning">Query returned 0 results</p>
    <p class="success">Solution:</p>
    <pre>
# Check wiki status
saw status

# Try different mode
saw query "term" --mode graph
    </pre>

    <p>For full troubleshooting guide, see <a href="https://github.com/chensaics/smart_agent_wiki/blob/main/docs/TROUBLESHOOTING.md">TROUBLESHOOTING.md</a></p>
    """
    return HTML_TEMPLATE.format(title="Troubleshooting", content=content)


def generate_migration_html() -> str:
    """Generate migration.html content."""
    content = """
    <h1>Migration Guide</h1>

    <h2>v3.4 → v3.5</h2>
    <p class="success">No breaking changes — fully backward compatible</p>

    <h3>New Features</h3>
    <ul>
        <li>saw tutorial — Interactive 5-step tutorial</li>
        <li>saw config — TUI configuration</li>
        <li>Short aliases: saw i, saw q, etc.</li>
        <li>Shell completion for bash/zsh/fish</li>
    </ul>

    <h3>Recommended Actions</h3>
    <pre>
# Update
pipx upgrade smart-agent-wiki

# Run tutorial
saw tutorial

# Enable completion
saw completion bash --install
    </pre>

    <h2>v3.3 → v3.4</h2>
    <h3>New Features</h3>
    <ul>
        <li>saw impact — Dependency impact analysis</li>
        <li>saw process — Execution flow tracing</li>
        <li>DAG pipeline validation</li>
    </ul>

    <p>For full migration guide, see <a href="https://github.com/chensaics/smart_agent_wiki/blob/main/docs/MIGRATION.md">MIGRATION.md</a></p>
    """
    return HTML_TEMPLATE.format(title="Migration", content=content)


def docs(
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for offline docs",
    ),
    format: str = typer.Option(
        "html",
        "--format", "-f",
        help="Output format: html, json",
    ),
) -> None:
    """
    Generate offline documentation.

    Creates static HTML or JSON documentation for offline access.

    Examples:
        saw docs --output ./docs-offline/
        saw docs --format json --output ./docs-json/
    """
    output_dir = output or Path.cwd() / "docs-offline"
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[cyan]Generating offline documentation to {output_dir}[/cyan]")

    files_to_create = [
        ("index.html", generate_index_html()),
        ("commands.html", generate_commands_html()),
        ("troubleshooting.html", generate_troubleshooting_html()),
        ("migration.html", generate_migration_html()),
    ]

    if format == "json":
        # Export command data as JSON
        json_path = output_dir / "commands.json"
        json_path.write_text(json.dumps(COMMANDS_DATA, indent=2))
        console.print(f"[green]✓ {json_path}[/green]")

    with Progress() as progress:
        task = progress.add_task("Generating...", total=len(files_to_create))

        for filename, content in files_to_create:
            file_path = output_dir / filename
            file_path.write_text(content)
            console.print(f"[green]✓ {file_path}[/green]")
            progress.advance(task)

    console.print(f"\n[green]✓ Offline documentation generated in {output_dir}[/green]")
    console.print(f"[dim]Open {output_dir}/index.html in your browser[/dim]")

    # Create manifest
    manifest = {
        "version": "3.5.0",
        "generated": "2026-05-05",
        "files": [f[0] for f in files_to_create],
        "commands": list(COMMANDS_DATA.keys()),
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))


app = typer.Typer(help="Offline documentation generation")
app.command(name="docs")(docs)


__all__ = ["docs", "COMMANDS_DATA"]