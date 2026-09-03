"""CLI commands for RSS feed management.

Phase 9: RSS Subscription — CLI commands.
Per RSSS-01~07: Feed subscription management commands.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="feed",
    help="RSS feed subscription management",
    no_args_is_help=True,
)
console = Console()


def _get_db_session():
    """Get database session."""
    from saw.db.config import get_engine, get_session_factory
    from saw.db.models import Base

    engine = get_engine()
    Base.metadata.create_all(engine)

    factory = get_session_factory(engine)
    return factory()


def _get_feed_manager(db):
    """Get FeedManager instance."""
    from saw.engines.ingest.feed_manager import FeedManager
    return FeedManager(db)


@app.command("add")
def add_feed(
    url: str = typer.Argument(..., help="RSS/Atom feed URL"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Feed category"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated filter keywords"),
    interval: int = typer.Option(3600, "--interval", "-i", help="Poll interval in seconds"),
) -> None:
    """Subscribe to an RSS/Atom feed.

    Per RSSS-01: Subscribe to RSS/Atom Feed.
    Per RSSS-04: Configure sync frequency.
    Per RSSS-07: Filter by keywords.
    """
    async def _add():
        db = _get_db_session()
        try:
            manager = _get_feed_manager(db)
            tag_list = [t.strip() for t in tags.split(",")] if tags else None

            feed_id = await manager.add_feed(
                url=url,
                category=category,
                tags=tag_list,
                poll_interval=interval,
            )
            console.print(f"[green]Subscribed to feed:[/green] {feed_id}")
            console.print(f"  URL: {url}")
            if category:
                console.print(f"  Category: {category}")
            if tag_list:
                console.print(f"  Tags: {', '.join(tag_list)}")
            console.print(f"  Interval: {interval}s")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        finally:
            db.close()

    asyncio.run(_add())


@app.command("list")
def list_feeds(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    all_feeds: bool = typer.Option(False, "--all", "-a", help="Show inactive feeds too"),
) -> None:
    """List all feed subscriptions.

    Per RSSS-06: Feed classification management.
    """
    from saw.db.feed_models import Feed

    db = _get_db_session()
    try:
        query = db.query(Feed)
        if not all_feeds:
            query = query.filter(Feed.active == True)
        if category:
            query = query.filter(Feed.category == category)

        feeds = query.all()

        if not feeds:
            console.print("[yellow]No feeds found[/yellow]")
            return

        table = Table(title="Feed Subscriptions")
        table.add_column("ID", style="cyan", no_wrap=True, width=10)
        table.add_column("Title", style="green", width=30)
        table.add_column("URL", style="blue", width=40)
        table.add_column("Category", style="magenta", width=12)
        table.add_column("Interval", justify="right", width=8)
        table.add_column("Status", style="yellow", width=10)

        for feed in feeds:
            status = "[green]Active[/green]" if feed.active else "[red]Inactive[/red]"
            title = feed.title[:28] + ".." if feed.title and len(feed.title) > 30 else (feed.title or "-")
            url_display = feed.url[:38] + ".." if len(feed.url) > 40 else feed.url
            table.add_row(
                feed.id[:8],
                title,
                url_display,
                feed.category or "-",
                f"{feed.poll_interval}s",
                status,
            )

        console.print(table)
        console.print(f"\nTotal: {len(feeds)} feed(s)")

    finally:
        db.close()


@app.command("poll")
def poll_feed(
    feed_id: str = typer.Argument(..., help="Feed ID to poll"),
) -> None:
    """Manually poll a feed for new entries."""
    async def _poll():
        db = _get_db_session()
        try:
            manager = _get_feed_manager(db)
            result = await manager.poll_feed(feed_id)

            console.print(f"[green]Poll complete for feed:[/green] {feed_id}")
            console.print(f"  New entries: {result.new_entries}")
            console.print(f"  Updated entries: {result.updated_entries}")
            console.print(f"  Skipped: {result.skipped_entries}")
            if result.not_modified:
                console.print("  [yellow]Feed not modified (304)[/yellow]")
            if result.errors:
                for err in result.errors:
                    console.print(f"  [red]Error:[/red] {err}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        finally:
            db.close()

    asyncio.run(_poll())


@app.command("remove")
def remove_feed(
    feed_id: str = typer.Argument(..., help="Feed ID to remove"),
) -> None:
    """Unsubscribe from a feed (soft delete)."""
    from saw.db.feed_models import Feed

    db = _get_db_session()
    try:
        feed = db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            console.print(f"[red]Feed not found:[/red] {feed_id}")
            raise typer.Exit(1)

        feed.active = False
        db.commit()
        console.print(f"[green]Unsubscribed from feed:[/green] {feed_id}")
    finally:
        db.close()


@app.command("update")
def update_feed(
    feed_id: str = typer.Argument(..., help="Feed ID to update"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="New category"),
    interval: Optional[int] = typer.Option(None, "--interval", "-i", help="New poll interval"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="New filter keywords"),
) -> None:
    """Update feed settings."""
    from saw.db.feed_models import Feed

    db = _get_db_session()
    try:
        feed = db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            console.print(f"[red]Feed not found:[/red] {feed_id}")
            raise typer.Exit(1)

        if category is not None:
            feed.category = category
        if interval is not None:
            feed.poll_interval = interval
        if tags is not None:
            feed.tags = json.dumps([t.strip() for t in tags.split(",")])

        db.commit()
        console.print(f"[green]Updated feed:[/green] {feed_id}")
    finally:
        db.close()


@app.command("entries")
def list_entries(
    feed_id: str = typer.Argument(..., help="Feed ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (new/updated/historical)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum entries to show"),
) -> None:
    """List entries for a feed."""
    from saw.db.feed_models import Feed, FeedEntry

    db = _get_db_session()
    try:
        feed = db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            console.print(f"[red]Feed not found:[/red] {feed_id}")
            raise typer.Exit(1)

        query = db.query(FeedEntry).filter(FeedEntry.feed_id == feed_id)
        if status:
            query = query.filter(FeedEntry.status == status)

        entries = query.order_by(FeedEntry.first_seen_at.desc()).limit(limit).all()

        if not entries:
            console.print("[yellow]No entries found[/yellow]")
            return

        table = Table(title=f"Entries for Feed {feed_id[:8]}")
        table.add_column("Title", style="green", width=50)
        table.add_column("Status", style="yellow", width=12)
        table.add_column("First Seen", style="blue", width=16)

        for entry in entries:
            title_display = entry.title[:48] + ".." if len(entry.title) > 50 else entry.title
            first_seen = entry.first_seen_at.strftime("%Y-%m-%d %H:%M") if entry.first_seen_at else "-"
            table.add_row(
                title_display,
                entry.status,
                first_seen,
            )

        console.print(table)
        console.print(f"\nShowing {len(entries)} entries")

    finally:
        db.close()


@app.command("info")
def feed_info(
    feed_id: str = typer.Argument(..., help="Feed ID"),
) -> None:
    """Show detailed feed information."""
    from saw.db.feed_models import Feed, FeedEntry

    db = _get_db_session()
    try:
        feed = db.query(Feed).filter(Feed.id == feed_id).first()
        if not feed:
            console.print(f"[red]Feed not found:[/red] {feed_id}")
            raise typer.Exit(1)

        # Get entry stats
        total_entries = db.query(FeedEntry).filter(FeedEntry.feed_id == feed_id).count()
        new_entries = db.query(FeedEntry).filter(
            FeedEntry.feed_id == feed_id, FeedEntry.status == "new"
        ).count()
        updated_entries = db.query(FeedEntry).filter(
            FeedEntry.feed_id == feed_id, FeedEntry.status == "updated"
        ).count()

        console.print(f"\n[bold]Feed: {feed.title or feed.url}[/bold]")
        console.print(f"  ID: {feed.id}")
        console.print(f"  URL: {feed.url}")
        console.print(f"  Description: {feed.description or '-'}")
        console.print(f"  Category: {feed.category or '-'}")
        console.print(f"  Tags: {feed.tags or '-'}")
        console.print(f"  Poll Interval: {feed.poll_interval}s")
        console.print(f"  Active: {'Yes' if feed.active else 'No'}")
        console.print(f"  Last Poll: {feed.last_poll_at or '-'}")
        console.print(f"  Created: {feed.created_at}")
        console.print("\n[bold]Entry Stats:[/bold]")
        console.print(f"  Total: {total_entries}")
        console.print(f"  New: {new_entries}")
        console.print(f"  Updated: {updated_entries}")

    finally:
        db.close()


@app.command("import")
def import_opml(
    file_path: str = typer.Argument(..., help="Path to OPML file"),
) -> None:
    """Import feeds from OPML file."""
    async def _import():
        from saw.db.feed_models import Feed

        db = _get_db_session()
        try:
            manager = _get_feed_manager(db)

            with open(file_path, 'r') as f:
                opml_content = f.read()

            import xml.etree.ElementTree as ET
            root = ET.fromstring(opml_content)
            outlines = root.findall(".//outline[@xmlUrl]")

            imported = 0
            skipped = 0
            errors = []

            for outline in outlines:
                url = outline.get("xmlUrl")
                if not url:
                    skipped += 1
                    continue

                existing = db.query(Feed).filter(Feed.url == url).first()
                if existing:
                    skipped += 1
                    continue

                try:
                    await manager.add_feed(url=url)
                    imported += 1
                except Exception as e:
                    errors.append(f"{url}: {e}")
                    skipped += 1

            console.print(f"[green]Imported:[/green] {imported}")
            console.print(f"[yellow]Skipped:[/yellow] {skipped}")
            if errors:
                console.print(f"[red]Errors:[/red] {len(errors)}")
                for err in errors[:5]:
                    console.print(f"  - {err}")

        finally:
            db.close()

    asyncio.run(_import())


@app.command("export")
def export_opml(
    output: str = typer.Option("feeds.opml", "--output", "-o", help="Output file path"),
) -> None:
    """Export feeds to OPML file."""
    from saw.db.feed_models import Feed

    db = _get_db_session()
    try:
        feeds = db.query(Feed).filter(Feed.active == True).all()

        import xml.etree.ElementTree as ET

        opml = ET.Element("opml", version="2.0")
        head = ET.SubElement(opml, "head")
        ET.SubElement(head, "title").text = "Smart Agent Wiki Feeds"
        ET.SubElement(head, "dateCreated").text = datetime.utcnow().isoformat()

        body = ET.SubElement(opml, "body")

        # Group by category
        categories: dict[str, list[Feed]] = {}
        for feed in feeds:
            cat = feed.category or "Uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(feed)

        for category, cat_feeds in categories.items():
            cat_elem = ET.SubElement(body, "outline", text=category)
            for feed in cat_feeds:
                ET.SubElement(
                    cat_elem,
                    "outline",
                    type="rss",
                    text=feed.title or feed.url,
                    title=feed.title or "",
                    xmlUrl=feed.url,
                )

        xml_str = ET.tostring(opml, encoding="unicode", xml_declaration=True)

        with open(output, 'w') as f:
            f.write(xml_str)

        console.print(f"[green]Exported {len(feeds)} feeds to:[/green] {output}")

    finally:
        db.close()
