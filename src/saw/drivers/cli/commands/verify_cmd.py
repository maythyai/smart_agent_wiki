"""CLI command: saw verify - Provenance chain verification."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def verify(
    claim_uuid: str = typer.Argument(..., help="UUID of the claim to verify"),
) -> None:
    """Verify claim provenance by tracing to Vault source.

    Shows the complete provenance chain:
    - Claim UUID and content
    - Source type (EXTRACTED/INFERRED/AMBIGUOUS)
    - Vault source UUID
    - Page location (if available)
    - Original document path
    - Confidence level and derivation

    Per GOVE-02: 3-level source marking orthogonal to confidence.
    """
    from pathlib import Path
    import sqlite3

    from saw.config.settings import load_config
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.govern.governor import Governor

    try:
        config = load_config(Path(".saw/config.yaml"))
    except Exception:
        console.print("[red]Error:[/] Not in a saw wiki directory. Run 'saw init' first.")
        raise typer.Exit(1)

    # Initialize repositories
    db_path = config.path / ".saw" / "db" / "claims.db"
    conn = sqlite3.connect(str(db_path))
    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(config.path / "wiki")

    # Initialize governor
    governor = Governor(claims_repo, wiki_repo)

    # Verify claim
    provenance = governor.verify_claim(claim_uuid)

    if provenance is None:
        console.print(f"[red]Error:[/] Claim not found: {claim_uuid}")
        conn.close()
        raise typer.Exit(1)

    # Display provenance chain
    console.print()
    console.print(Panel.fit(
        f"[bold blue]Provenance Verification[/bold blue]",
        subtitle=f"Claim: {claim_uuid[:8]}...",
    ))

    # Claim info table
    info_table = Table.grid(padding=(0, 2))
    info_table.add_column("Field", style="cyan")
    info_table.add_column("Value")

    info_table.add_row("Claim UUID", provenance.claim_uuid)
    info_table.add_row("Content", provenance.claim_content[:100] + "..."
                       if len(provenance.claim_content) > 100
                       else provenance.claim_content)
    info_table.add_row("Source Type", f"[bold]{provenance.source_type}[/bold]")
    info_table.add_row("Source UUID", provenance.source_uuid)
    info_table.add_row("Page Location", provenance.page_location or "N/A")
    info_table.add_row("Confidence Level", str(provenance.confidence))
    info_table.add_row("Confidence Reason", provenance.confidence_reason)

    console.print(info_table)

    # Source status
    console.print()
    vault_path = config.path / "vault" / provenance.source_uuid
    if vault_path.exists():
        console.print(f"[green]✓[/green] Vault source found: {vault_path}")
    else:
        console.print(f"[yellow]?[/yellow] Vault source not found (may have been pruned)")

    conn.close()


if __name__ == "__main__":
    typer.run(verify)
