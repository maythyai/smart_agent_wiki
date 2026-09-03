"""CLI command: saw audit - Audit trail verification.

Per GOVE-08: Offline-verifiable receipt chain.
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def audit(
    export: Path | None = typer.Option(
        None,
        "--export",
        "-e",
        help="Export receipts for offline verification",
    ),
    verify: str | None = typer.Option(
        None,
        "--verify",
        "-v",
        help="Verify specific receipt by operation ID",
    ),
    claim: str | None = typer.Option(
        None,
        "--claim",
        "-c",
        help="Show audit trail for specific claim UUID",
    ),
    session: str | None = typer.Option(
        None,
        "--session",
        "-s",
        help="Verify the DB-backed receipt chain for a session id (T-F-P-3, AC-OBS-4)",
    ),
) -> None:
    """Verify audit trail and receipt chain integrity.

    Per GOVE-08: Ed25519-signed receipt chain for offline verification.

    Output includes:
    - Total operations recorded
    - Operations by type (ingest/query/edit/review)
    - Operations by agent
    - Chain integrity status (VALID/COMPROMISED)
    - First/last operation timestamps
    """
    from saw.config.settings import load_config
    from saw.adapters.crypto.ed25519 import ReceiptSigner
    from saw.engines.govern.audit import AuditTrail

    try:
        config = load_config(Path.cwd() / ".saw" / "config.yaml")
    except Exception:
        console.print("[red]Error:[/] Not in a saw wiki directory. Run 'saw init' first.")
        raise typer.Exit(1)

    # T-F-P-3 (AC-OBS-4): DB-backed receipt chain per session (v1.2.0
    # ReceiptStore), distinct from the file-based AuditTrail below.
    if session:
        import sqlite3

        db_path = config.path / ".saw" / "db" / "claims.db"
        if not db_path.is_file():
            console.print("[red]No claims DB.[/] Run `saw ingest` first.")
            raise typer.Exit(1)
        conn = sqlite3.connect(str(db_path))
        try:
            from saw.write_queue.receipt_store import ReceiptStore

            result = ReceiptStore(conn).verify_chain(session)
        except sqlite3.OperationalError:
            console.print("[yellow]receipts table absent[/] (pre-v1.2.0 DB)")
            raise typer.Exit(1)
        finally:
            conn.close()
        label = "[green]VALID[/green]" if result.valid else "[red]INVALID[/red]"
        console.print(f"Session {session[:8]}..: {label}")
        if result.error:
            console.print(f"  reason: {result.error}")
        raise typer.Exit(0 if result.valid else 1)

    # Display header
    console.print()
    console.print(Panel.fit(
        "[bold blue]Audit Trail Verification[/bold blue]",
        subtitle="Ed25519 receipt chain",
    ))

    # Check for audit directory
    audit_path = config.path / ".saw" / "audit"
    if not audit_path.exists():
        console.print("[yellow]No audit trail found.[/] Operations have not been recorded.")
        console.print("Audit trail starts automatically when using saw commands.")
        return

    receipts_file = audit_path / "receipts.yaml"
    if not receipts_file.exists():
        console.print("[yellow]No receipts found.[/] Audit trail is empty.")
        return

    # Initialize signer and audit trail
    key_path = config.path / ".saw" / "keys" / "ed25519.key"
    signer = ReceiptSigner(key_path)
    audit_trail = AuditTrail(signer, audit_path)

    # Handle export
    if export:
        export.mkdir(parents=True, exist_ok=True)
        audit_trail.export_for_verification(export)
        console.print(f"[green]Exported receipts to:[/] {export}")
        console.print(f"  - {export / 'receipts.yaml'}")
        console.print(f"  - {export / 'public_key.txt'}")
        return

    # Handle specific receipt verification
    if verify:
        receipt = audit_trail.get_receipt(verify)
        if receipt:
            is_valid, invalid_ids = audit_trail.verify_chain(start_id=verify)
            status = "[green]VALID[/green]" if is_valid else "[red]INVALID[/red]"
            console.print(f"Receipt {verify[:8]}...: {status}")
        else:
            console.print(f"[red]Receipt not found:[/] {verify}")
        return

    # Handle claim-specific audit trail
    if claim:
        receipts = audit_trail.get_receipts_for_claim(claim)
        if receipts:
            console.print(f"[bold]Audit trail for claim:[/] {claim}")
            console.print()
            table = Table()
            table.add_column("Operation", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Agent", style="magenta")
            table.add_column("Timestamp", style="white")

            for r in receipts:
                table.add_row(
                    r.operation_id[:8] + "...",
                    r.operation_type,
                    r.agent,
                    r.timestamp.strftime("%Y-%m-%d %H:%M"),
                )
            console.print(table)
        else:
            console.print(f"[yellow]No audit records for claim:[/] {claim}")
        return

    # Get summary
    summary = audit_trail.get_audit_summary()

    # Display chain integrity
    if summary.chain_valid:
        console.print("[green]Chain Integrity: VALID[/green]")
    else:
        console.print("[red]Chain Integrity: COMPROMISED[/red]")

    # Display summary table
    console.print()
    summary_table = Table(title="Operations Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="white")

    summary_table.add_row("Total Operations", str(summary.total_operations))
    summary_table.add_row("Chain Length", str(summary.chain_length))

    if summary.first_operation:
        summary_table.add_row(
            "First Operation",
            summary.first_operation.strftime("%Y-%m-%d %H:%M"),
        )
    if summary.last_operation:
        summary_table.add_row(
            "Last Operation",
            summary.last_operation.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(summary_table)

    # Display by type
    if summary.by_type:
        console.print()
        type_table = Table(title="Operations by Type")
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", justify="right")

        for op_type, count in sorted(summary.by_type.items()):
            type_table.add_row(op_type, str(count))

        console.print(type_table)

    # Display by agent
    if summary.by_agent:
        console.print()
        agent_table = Table(title="Operations by Agent")
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("Count", justify="right")

        for agent, count in sorted(summary.by_agent.items()):
            agent_table.add_row(agent, str(count))

        console.print(agent_table)

    # Footer
    console.print()
    console.print("[dim]Use --export <path> for offline verification[/dim]")


if __name__ == "__main__":
    typer.run(audit)
