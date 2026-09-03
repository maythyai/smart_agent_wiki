"""CLI `saw token` command — T-F-I-3 (AC-TK-1).

Runs a deterministic token-optimization benchmark: the same corpus is
"read" multiple times (simulating an agent re-reading context). Baseline
counts every read; optimized uses ``SessionTracker`` to skip repeated
reads (cache). Output: baseline vs optimized tokens + saved %.
"""
from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True, help="Token optimization benchmark (F-I-3).")


def _collect_corpus(corpus: Path) -> list[Path]:
    """Return a deterministic list of files to benchmark."""
    if corpus.is_file():
        return [corpus]
    files: list[Path] = []
    if corpus.is_dir():
        for p in sorted(corpus.rglob("*")):
            if p.is_file() and p.suffix in {".py", ".md", ".txt", ".json", ".yaml", ".yml"}:
                # skip venvs / caches
                if any(part in {"__pycache__", ".venv", "venv_test", "node_modules", ".git"}
                       for part in p.parts):
                    continue
                files.append(p)
    return files


@app.command(name="bench")
def bench(
    corpus: str = typer.Option(
        "examples", "--corpus", "-c", help="Corpus dir/file to benchmark"
    ),
    reads: int = typer.Option(
        3, "--reads", "-r", help="Times each file is read (simulated repeats)"
    ),
) -> None:
    """Measure token savings vs baseline (AC-TK-1, deterministic)."""
    from rich.table import Table

    from saw.drivers.cli.main import console
    from saw.token_optimizer.anatomy import estimate_tokens
    from saw.token_optimizer.session_tracker import SessionTracker

    corpus_path = Path(corpus).resolve()
    files = _collect_corpus(corpus_path)
    if not files:
        console.print(
            f"[yellow]No corpus files found at {corpus_path}. "
            f"Point --corpus at a dir/file with .py/.md/...[/yellow]"
        )
        raise typer.Exit(code=1)
    if reads < 1:
        raise typer.BadParameter("--reads must be >= 1")

    # Token cost per file (cached; deterministic — same input → same output).
    file_tokens = {}
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = ""
        file_tokens[str(f)] = estimate_tokens(content, is_code=f.suffix != ".md")

    # Baseline: every read counted (no cache).
    baseline_tokens = sum(file_tokens.values()) * reads
    baseline_unique = sum(file_tokens.values())

    # Optimized: SessionTracker skips repeated reads (cache).
    tracker = SessionTracker(session_id="bench")
    optimized_tokens = 0
    for _ in range(reads):
        for fp, toks in file_tokens.items():
            if tracker.was_read(fp):
                # cache hit — no token cost this read.
                continue
            tracker.track_read(fp, toks)
            optimized_tokens += toks
    stats = tracker.get_stats()

    saved = baseline_tokens - optimized_tokens
    saved_pct = (saved / baseline_tokens * 100) if baseline_tokens else 0.0

    table = Table(title="Token Optimization Benchmark")
    table.add_column("metric", style="cyan")
    table.add_column("value", justify="right")
    table.add_row("files", str(len(files)))
    table.add_row("reads/file", str(reads))
    table.add_row("unique tokens (1× corpus)", str(baseline_unique))
    table.add_row("baseline tokens", str(baseline_tokens))
    table.add_row("optimized tokens", str(optimized_tokens))
    table.add_row("saved tokens", str(saved))
    table.add_row("[green]saved %[/green]", f"{saved_pct:.1f}%")
    table.add_row("repeat reads detected", str(stats.repeated_reads))
    console.print(table)
    raise typer.Exit(code=0)
