"""CLI commands for impact analysis."""
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from saw.analysis.impact import analyze_impact, NodeNotFoundError
from saw.analysis.types import ImpactResult


console = Console()


@click.command()
@click.argument('target')
@click.option('--direction', '-d', type=click.Choice(['upstream', 'downstream']),
              default='upstream', help='Analysis direction')
@click.option('--max-depth', '-m', type=int, default=3,
              help='Maximum traversal depth (1-5)')
@click.option('--min-confidence', '-c', type=float, default=0.8,
              help='Minimum confidence threshold (0.0-1.0)')
@click.option('--json', '-j', 'json_output', is_flag=True,
              help='Output as JSON')
@click.option('--include-tests', is_flag=False,
              help='Include test files')
def impact(target, direction, max_depth, min_confidence, json_output, include_tests):
    """
    Analyze code modification impact.

    Identifies what will be affected if you modify the target symbol.
    Use this BEFORE making changes to understand blast radius.

    \b
    Examples:
        saw impact UserService
        saw impact handleLogin --direction downstream
        saw impact AuthModule --max-depth 5 --min-confidence 0.9
        saw impact UserService --json
    """
    # Get graph (placeholder - will use actual graph)
    from saw.graph import get_graph
    graph = get_graph()

    try:
        result = analyze_impact(
            graph, target, direction, max_depth,
            min_confidence, None, include_tests
        )

        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            _print_impact_report(result)

    except NodeNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Tip:[/yellow] Check if the symbol name is correct.")
        raise click.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


def _print_impact_report(result: ImpactResult):
    """Print formatted impact report."""
    target = result['target']
    direction = result['direction']
    summary = result['summary']

    # Header
    direction_text = "depends on" if direction == "downstream" else "is depended on by"
    console.print(Panel(
        f"Modifying [bold]{target}[/bold] {direction_text}",
        title="Impact Analysis",
        style="blue"
    ))

    # Summary
    console.print(f"\n[cyan]Summary:[/cyan]")
    console.print(f"  Total affected: {summary['total_affected']}")
    console.print(f"  Depth 1 (will break): {summary['depth_1_count']}")
    console.print(f"  Depth 2 (likely affected): {summary['depth_2_count']}")
    console.print(f"  Depth 3 (may need testing): {summary['depth_3_count']}")

    if summary['high_risk_count'] > 0:
        console.print(f"\n[red bold]⚠ HIGH RISK: {summary['high_risk_count']} direct dependents will break![/red bold]")

    # Impact table
    if result['impacts']:
        table = Table(title="\nAffected Nodes")
        table.add_column("Depth", style="cyan", width=6)
        table.add_column("Risk", style="red", width=18)
        table.add_column("Name", style="white")
        table.add_column("Type", style="dim", width=10)
        table.add_column("Relation", style="dim", width=10)
        table.add_column("Confidence", width=10)

        for impact in result['impacts'][:20]:  # Limit display
            risk_style = {
                'WILL_BREAK': 'red bold',
                'LIKELY_AFFECTED': 'yellow',
                'MAY_NEED_TESTING': 'blue'
            }.get(impact['risk_level'], 'white')

            table.add_row(
                str(impact['depth']),
                f"[{risk_style}]{impact['risk_level']}[/{risk_style}]",
                impact['name'],
                impact['kind'],
                impact['relation_type'],
                f"{impact['confidence']:.0%}"
            )

        console.print(table)

        if len(result['impacts']) > 20:
            console.print(f"\n[dim]... and {len(result['impacts']) - 20} more[/dim]")

    # Execution time
    console.print(f"\n[dim]Analysis completed in {result['execution_time_ms']:.2f}ms[/dim]")


# For CLI registration
__all__ = ['impact']