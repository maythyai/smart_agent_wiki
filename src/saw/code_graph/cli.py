"""CLI 集成 — saw code-graph 子命令

提供:
- saw code-graph build [--full] [--lang python,typescript]
- saw code-graph update
- saw code-graph health
- saw code-graph verify
- saw code-graph stats
- saw code-graph search <query>
- saw code-graph impact <target> [--direction upstream|downstream]
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def register_code_graph_commands(app) -> None:
    """注册 code-graph CLI 子命令到 Typer app

    Usage:
        saw code-graph build --full
        saw code-graph update
        saw code-graph health
        saw code-graph verify
        saw code-graph stats
        saw code-graph search "authenticate"
        saw code-graph impact "AuthService" --direction upstream
    """
    try:
        import typer
    except ImportError:
        logger.warning("typer not available, skipping code-graph CLI registration")
        return

    code_graph_app = typer.Typer(
        name="code-graph",
        help="Code graph lifecycle management",
        no_args_is_help=True,
    )
    app.add_typer(code_graph_app)

    @code_graph_app.command()
    def build(
        full: bool = typer.Option(False, "--full", "-f", help="Full rebuild (ignore cache)"),
        lang: Optional[str] = typer.Option(None, "--lang", "-l", help="Comma-separated languages"),
        no_postprocess: bool = typer.Option(False, "--no-postprocess", help="Skip postprocess"),
        root: str = typer.Option(".", "--root", "-r", help="Project root path"),
    ):
        """Build the code graph from source files."""
        from saw.code_graph.engine import CodeGraphEngine

        languages = lang.split(",") if lang else None
        engine = CodeGraphEngine(root)

        typer.echo(f"Building code graph from {Path(root).resolve()}...")
        result = engine.build(full=full, languages=languages, postprocess=not no_postprocess)

        typer.echo(f"  Files: {result.files_parsed} parsed, {result.files_skipped} skipped, {result.files_failed} failed")
        typer.echo(f"  Graph: {result.total_nodes} nodes, {result.total_edges} edges")
        typer.echo(f"  Time:  {result.build_time_ms:.0f}ms")

        if result.errors:
            typer.echo(f"  Errors ({len(result.errors)}):", err=True)
            for e in result.errors[:5]:
                typer.echo(f"    - {e}", err=True)

        engine.close()

    @code_graph_app.command()
    def update(
        root: str = typer.Option(".", "--root", "-r", help="Project root path"),
    ):
        """Incremental update (only changed files)."""
        from saw.code_graph.engine import CodeGraphEngine

        engine = CodeGraphEngine(root)
        typer.echo("Updating code graph (incremental)...")
        result = engine.update()

        if result.files_parsed == 0 and result.files_failed == 0:
            typer.echo("  No changes detected. Graph is up to date.")
        else:
            typer.echo(f"  Updated: {result.files_parsed} files, {result.total_nodes} nodes, {result.total_edges} edges")
            typer.echo(f"  Time: {result.build_time_ms:.0f}ms")

        engine.close()

    @code_graph_app.command()
    def health(
        root: str = typer.Option(".", "--root", "-r", help="Project root path"),
        json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    ):
        """Check code graph health."""
        from saw.code_graph.engine import CodeGraphEngine
        from saw.code_graph.health import HealthMonitor

        engine = CodeGraphEngine(root)
        monitor = HealthMonitor(engine.store)
        report = monitor.check_health()

        if json_output:
            typer.echo(json.dumps({
                "status": report.status,
                "checks": report.checks,
                "alerts": report.alerts,
                "metrics": report.metrics,
            }, indent=2))
        else:
            status_icon = {"healthy": "✓", "degraded": "⚠", "critical": "✗"}.get(report.status, "?")
            typer.echo(f"{status_icon} Status: {report.status}")
            typer.echo(f"  Nodes: {report.metrics.get('nodes', 0)}, Edges: {report.metrics.get('edges', 0)}, Files: {report.metrics.get('files', 0)}")

            for check, result in report.checks.items():
                icon = {"PASS": "✓", "WARN": "⚠", "FAIL": "✗"}.get(result, "?")
                typer.echo(f"  {icon} {check}: {result}")

            if report.alerts:
                typer.echo("\n  Alerts:")
                for alert in report.alerts:
                    typer.echo(f"    ⚠ {alert}")

        engine.close()

    @code_graph_app.command()
    def verify(
        root: str = typer.Option(".", "--root", "-r", help="Project root path"),
    ):
        """Verify graph integrity (orphan edges, FTS consistency)."""
        from saw.code_graph.engine import CodeGraphEngine
        from saw.code_graph.snapshot import SnapshotManager

        engine = CodeGraphEngine(root)
        mgr = SnapshotManager(engine.store)
        result = mgr.verify_integrity()

        typer.echo(f"Integrity: {result['status']}")
        typer.echo(f"  Nodes: {result['node_count']}, Edges: {result['edge_count']}, Files: {result['file_count']}")

        if result.get("issues"):
            typer.echo("  Issues:")
            for issue in result["issues"]:
                typer.echo(f"    - {issue}")
        else:
            typer.echo("  No issues found.")

        engine.close()

    @code_graph_app.command()
    def stats(
        root: str = typer.Option(".", "--root", "-r", help="Project root path"),
    ):
        """Show code graph statistics."""
        from saw.code_graph.engine import CodeGraphEngine

        engine = CodeGraphEngine(root)
        s = engine.stats()
        typer.echo("Code Graph Stats:")
        typer.echo(f"  Nodes: {s['nodes']}")
        typer.echo(f"  Edges: {s['edges']}")
        typer.echo(f"  Files: {s['files']}")
        typer.echo(f"  DB:    {s['db_path']}")
        engine.close()

    @code_graph_app.command()
    def search(
        query: str = typer.Argument(..., help="Search query"),
        kind: Optional[str] = typer.Option(None, "--kind", "-k", help="Filter by kind"),
        limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
        root: str = typer.Option(".", "--root", "-r", help="Project root path"),
    ):
        """Search code symbols."""
        from saw.code_graph.engine import CodeGraphEngine

        engine = CodeGraphEngine(root)
        results = engine.search(query, limit=limit)

        if kind:
            results = [n for n in results if n.kind.value == kind]

        if not results:
            typer.echo(f"No results for '{query}'")
        else:
            typer.echo(f"Found {len(results)} results for '{query}':")
            for n in results:
                typer.echo(f"  [{n.kind.value:8s}] {n.name} @ {n.file_path}:{n.start_line}")
                if n.signature:
                    typer.echo(f"             {n.signature}")

        engine.close()

    @code_graph_app.command()
    def impact(
        target: str = typer.Argument(..., help="Symbol name or UID"),
        direction: str = typer.Option("upstream", "--direction", "-d", help="upstream or downstream"),
        depth: int = typer.Option(3, "--depth", help="Max traversal depth"),
        root: str = typer.Option(".", "--root", "-r", help="Project root path"),
    ):
        """Analyze impact of modifying a symbol."""
        from saw.code_graph.engine import CodeGraphEngine

        engine = CodeGraphEngine(root)
        impacts = engine.impact_analysis(target, direction=direction, max_depth=depth)

        if not impacts:
            typer.echo(f"No impact found for '{target}' (symbol may not exist)")
        else:
            typer.echo(f"Impact analysis for '{target}' ({direction}, depth={depth}):")
            typer.echo(f"  {len(impacts)} affected symbols:\n")
            for imp in impacts:
                typer.echo(f"  [{imp.risk_level:16s}] {imp.name} ({imp.kind}) @ {imp.file_path}")
                typer.echo(f"                     score={imp.score:.3f}, depth={imp.depth}, via={imp.edge_type}")

        engine.close()
