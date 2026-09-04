"""CLI `saw summarize` command — T-F-L-3 (AC-SUM-1).

AI summary of a wiki page via LLMRouter.answer_query. Online path —
errors loudly when no LLM is configured (no silent fallback, per PRD §4).
"""
from __future__ import annotations

from pathlib import Path

import typer

_SUMMARY_SYSTEM_PROMPT = (
    "You are a knowledge curator. Summarize the given wiki page in 3-5 "
    "bullet points, preserving key entities and any cited claims. Be concise."
)


def _wiki(path: str):
    from saw.drivers.cli.main import console

    wiki_path = Path(path).resolve()
    config_path = wiki_path / ".saw" / "config.yaml"
    if not config_path.is_file():
        console.print("[red]Error:[/red] Not a Smart Agent Wiki. Run `saw init` first.")
        raise typer.Exit(code=1)
    from saw.adapters.storage.wiki_repository import WikiRepository

    return WikiRepository(wiki_path / "wiki"), console, config_path


def _resolve(wiki, page: str) -> str | None:
    from saw.engines.query.wiki_links import slugify

    if wiki.read(page) is not None:
        return page
    target = slugify(Path(page).stem if page.endswith(".md") else page)
    for p in wiki.list_pages():
        if slugify(Path(p).stem) == target:
            return p
    return None


def summarize(
    page: str = typer.Argument(..., help="Page slug/path to summarize"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """AI-summarize a wiki page (AC-SUM-1, online)."""
    from rich.panel import Panel

    wiki, console, config_path = _wiki(path)

    resolved = _resolve(wiki, page)
    if resolved is None:
        console.print(f"[red]Error:[/red] page not found: {page}")
        raise typer.Exit(code=1)

    src = wiki.read(resolved)
    if not src.content.strip():
        console.print(f"[yellow]Page {resolved} has no content to summarize.[/yellow]")
        raise typer.Exit(code=0)

    from saw.config.settings import load_config, detect_tier
    from saw.domain.value_objects import CapabilityTier

    settings = load_config(config_path)
    tier = detect_tier(settings.llm)
    if tier < CapabilityTier.LIGHTWEIGHT or not settings.llm:
        console.print(
            "[red]Error:[/red] LLM unavailable. `saw summarize` requires an "
            "online LLM (configure .saw/config.yaml llm)."
        )
        raise typer.Exit(code=1)

    from saw.adapters.llm.router import LLMRouter

    try:
        llm = LLMRouter(settings.llm)
    except Exception as e:
        console.print(f"[red]Error initialising LLM router:[/red] {e}")
        raise typer.Exit(code=1)

    try:
        summary = llm.answer_query(
            src.content, "Summarize this page", _SUMMARY_SYSTEM_PROMPT
        )
    except Exception as e:
        console.print(f"[red]LLM summarization failed:[/red] {e}")
        raise typer.Exit(code=1)

    if not summary or not summary.strip():
        console.print("[red]Error:[/red] LLM returned an empty summary.")
        raise typer.Exit(code=1)

    console.print(Panel(summary.strip(), title=f"Summary — {resolved}", border_style="cyan"))
    raise typer.Exit(code=0)
