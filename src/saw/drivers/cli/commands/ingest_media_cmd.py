"""saw ingest-media CLI command.

Phase 4: Media Ingestion — CLI interface.
Per MING-01~08: Video/audio upload, transcription, preview, batch.
Per CLI-02: saw ingest-media <file> for media transcription.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

from saw.config.settings import load_config
from saw.engines.ingest.extractors.media import MediaExtractor, MediaIngestConfig
from saw.engines.ingest.batch import BatchMediaProcessor, BatchOptions, BatchProgress
from saw.engines.ingest.preview import PreviewManager

console = Console()


def ingest_media(
    source: Annotated[str, typer.Argument(help="Media file or directory path")],
    path: Annotated[str, typer.Option("--path", "-p", help="Wiki directory path")] = ".",
    model: Annotated[str, typer.Option("--model", "-m", help="Whisper model: tiny|base|small|medium|large")] = "base",
    device: Annotated[str, typer.Option("--device", "-d", help="Device: auto|cuda|cpu")] = "auto",
    preview: Annotated[bool, typer.Option("--preview", help="Create preview before ingest")] = True,
    batch: Annotated[bool, typer.Option("--batch", "-b", help="Batch process directory")] = False,
    concurrency: Annotated[int, typer.Option("--concurrency", "-c", help="Batch concurrency")] = 3,
    language: Annotated[str | None, typer.Option("--language", "-l", help="Force language code")] = None,
    no_api_fallback: Annotated[bool, typer.Option("--no-api-fallback", help="Disable OpenAI API fallback")] = False,
) -> None:
    """Ingest video/audio files via Whisper transcription.

    Examples:
        saw ingest-media podcast.mp3
        saw ingest-media lecture.mp4 --model medium
        saw ingest-media ./videos --batch --concurrency 2
        saw ingest-media interview.m4a --preview
    """
    wiki_path = Path(path).expanduser().resolve()

    # Check wiki exists
    config_path = wiki_path / ".saw" / "config.yaml"
    if not config_path.exists():
        console.print(f"[red]Error: Wiki not initialized at {path}[/red]")
        console.print("Run [cyan]saw init {path}[/cyan] first")
        raise typer.Exit(1)

    # Load configuration
    try:
        settings = load_config(config_path)
        settings.path = wiki_path
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(1)

    # Initialize media config
    media_config = MediaIngestConfig(
        whisper_model=model,
        whisper_device=device,
        whisper_language=language or "auto",
        api_fallback=not no_api_fallback,
        batch_concurrency=concurrency,
    )

    source_path = Path(source).expanduser().resolve()

    if batch or source_path.is_dir():
        # Batch processing
        _process_batch(source_path, wiki_path, media_config, preview, concurrency)
    else:
        # Single file processing
        _process_single(source_path, wiki_path, media_config, preview)


def _process_single(
    file_path: Path,
    wiki_path: Path,
    config: MediaIngestConfig,
    preview: bool,
) -> None:
    """Process a single media file."""
    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    extractor = MediaExtractor(config)

    if not extractor.can_handle(file_path):
        console.print(f"[red]Unsupported format: {file_path.suffix}[/red]")
        console.print("Supported: .mp4, .webm, .mov, .mp3, .wav, .m4a, .ogg")
        raise typer.Exit(1)

    console.print(f"[yellow]Transcribing: {file_path.name}[/yellow]")
    console.print(f"[dim]Model: {config.whisper_model}, Device: {config.whisper_device}[/dim]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting audio and transcribing...", total=None)

        try:
            result = extractor.extract(file_path, "")

            if preview:
                # Save to preview manager
                preview_manager = PreviewManager(
                    vault_path=wiki_path / "vault",
                    db_path=str(wiki_path / ".saw" / "previews.db"),
                )

                from saw.engines.ingest.extractors.media import MediaInfo
                media_info = MediaInfo(
                    duration_seconds=result.metadata.get("media_info", {}).get("duration_seconds", 0),
                    format=file_path.suffix.lower().lstrip("."),
                )
                if "media_info" in result.metadata:
                    media_info = MediaInfo(**result.metadata["media_info"])

                from saw.engines.ingest.extractors.media import TranscriptionResult, Segment
                # Reconstruct TranscriptionResult from claims
                segments = [
                    Segment(start=0.0, end=0.0, text=c.content)
                    for c in result.claims
                    if not c.content.startswith("Full transcription:")
                ]

                trans_result = TranscriptionResult(
                    text=" ".join(s.text for s in segments),
                    language=result.metadata.get("media_info", {}).get("language", "unknown"),
                    segments=segments,
                )

                preview_id = preview_manager.save_preview(
                    transcription=trans_result,
                    media_info=media_info,
                    source_path=str(file_path),
                )

                progress.update(task, description="Transcription complete!")

                panel = Panel(
                    f"Preview ID: {preview_id}\n"
                    f"Duration: {media_info.duration_seconds:.1f}s\n"
                    f"Language: {trans_result.language}\n"
                    f"Segments: {len(segments)}\n"
                    f"Claims: {len(result.claims)}\n\n"
                    f"To confirm: [cyan]saw preview confirm {preview_id}[/cyan]\n"
                    f"To discard: [cyan]saw preview discard {preview_id}[/cyan]",
                    title="[green]Preview Created[/green]",
                    border_style="green",
                )
                console.print(panel)

            else:
                # Direct ingest via Write Queue
                progress.update(task, description="Transcription complete!")

                from saw.write_queue.queue import WriteQueue, WriteOp
                from saw.domain.value_objects import WriteOpStatus
                import uuid as _uuid

                ops = []
                for claim in result.claims:
                    op = WriteOp(
                        op_id=f"media-{_uuid.uuid4().hex[:8]}",
                        session_id=f"media-ingest-{file_path.stem}",
                        sink_name="claims",
                        payload={
                            "content": claim.content if hasattr(claim, "content") else str(claim),
                            "source_platform": "media",
                            "source_id": str(file_path),
                        },
                        status=WriteOpStatus.PENDING,
                    )
                    ops.append(op)

                if ops:
                    write_queue = WriteQueue()
                    write_queue.enqueue(ops)

                panel = Panel(
                    f"File: {file_path.name}\n"
                    f"Duration: {result.metadata.get('media_info', {}).get('duration_seconds', 0):.1f}s\n"
                    f"Claims: {len(result.claims)}\n"
                    f"Parser: whisper\n"
                    f"Queued: {len(ops)} write ops",
                    title="[green]Ingestion Complete[/green]",
                    border_style="green",
                )
                console.print(panel)

        except Exception as e:
            console.print(f"[red]Transcription failed: {e}[/red]")
            raise typer.Exit(1)


def _process_batch(
    directory: Path,
    wiki_path: Path,
    config: MediaIngestConfig,
    preview: bool,
    concurrency: int,
) -> None:
    """Process multiple media files in batch."""
    if not directory.is_dir():
        console.print(f"[red]Not a directory: {directory}[/red]")
        raise typer.Exit(1)

    # Find media files
    extractor = MediaExtractor(config)
    media_files: list[str] = []

    for ext in extractor._supported_extensions():
        media_files.extend(str(p) for p in directory.glob(f"*{ext}"))
        media_files.extend(str(p) for p in directory.glob(f"**/*{ext}"))

    if not media_files:
        console.print(f"[yellow]No media files found in {directory}[/yellow]")
        return

    console.print(f"[blue]Found {len(media_files)} media files[/blue]")
    console.print(f"[dim]Concurrency: {concurrency}, Model: {config.whisper_model}[/dim]")

    preview_manager = PreviewManager(
        vault_path=wiki_path / "vault",
        db_path=str(wiki_path / ".saw" / "previews.db"),
    )

    processor = BatchMediaProcessor(config, preview_manager)

    options = BatchOptions(
        preview=preview,
        concurrency=concurrency,
        stop_on_error=False,
        model=config.whisper_model,
    )

    # Progress callback
    current_task = None

    def on_progress(prog: BatchProgress):
        nonlocal current_task

    processor.set_progress_callback(on_progress)

    # Run batch processing
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Processing {len(media_files)} files...",
            total=len(media_files),
        )

        async def run_batch():
            result = await processor.process_batch(media_files, options)
            return result

        # Run async batch
        result = asyncio.run(run_batch())

        progress.update(task, completed=len(media_files))

    # Print summary
    table = Table(title="Batch Results")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Duration", style="dim")
    table.add_column("Claims", style="blue")

    for fr in result.file_results[:20]:  # Show first 20
        status = "✓" if fr.success else "✗"
        status_style = "green" if fr.success else "red"
        table.add_row(
            Path(fr.file_path).name,
            f"[{status_style}]{status}[/{status_style}]",
            f"{fr.duration_seconds:.1f}s",
            str(fr.claim_count) if fr.success else fr.error[:30] if fr.error else "-",
        )

    if len(result.file_results) > 20:
        table.add_row("...", f"({len(result.file_results) - 20} more)", "", "")

    console.print(table)

    panel = Panel(
        f"Total: {result.total_files}\n"
        f"Successful: {result.successful}\n"
        f"Failed: {result.failed}\n"
        f"Elapsed: {result.elapsed_seconds:.1f}s",
        title=f"[{'green' if result.failed == 0 else 'yellow'}]Batch Complete[/]",
        border_style="green" if result.failed == 0 else "yellow",
    )
    console.print(panel)


# Preview management commands
preview_app = typer.Typer(help="Manage transcription previews")


@preview_app.command("list")
def list_previews(
    path: Annotated[str, typer.Option("--path", "-p", help="Wiki directory path")] = ".",
    status: Annotated[str | None, typer.Option("--status", "-s", help="Filter by status: pending|confirmed|discarded")] = None,
) -> None:
    """List all transcription previews."""
    wiki_path = Path(path).expanduser().resolve()
    preview_db = wiki_path / ".saw" / "previews.db"

    if not preview_db.exists():
        console.print("[yellow]No previews found[/yellow]")
        return

    preview_manager = PreviewManager(db_path=str(preview_db))
    previews = preview_manager.list_previews(status)

    if not previews:
        console.print("[yellow]No previews found[/yellow]")
        return

    table = Table(title="Transcription Previews")
    table.add_column("Preview ID", style="cyan")
    table.add_column("File", style="white")
    table.add_column("Duration", style="dim")
    table.add_column("Language", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")

    for p in previews:
        table.add_row(
            p.preview_id,
            Path(p.source_path).name,
            f"{p.duration_seconds:.1f}s",
            p.language,
            p.status,
            p.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@preview_app.command("show")
def show_preview(
    preview_id: Annotated[str, typer.Argument(help="Preview ID")],
    path: Annotated[str, typer.Option("--path", "-p", help="Wiki directory path")] = ".",
) -> None:
    """Show preview details and transcription."""
    wiki_path = Path(path).expanduser().resolve()
    preview_db = wiki_path / ".saw" / "previews.db"

    preview_manager = PreviewManager(db_path=str(preview_db))
    record = preview_manager.get_preview(preview_id)

    if not record:
        console.print(f"[red]Preview not found: {preview_id}[/red]")
        raise typer.Exit(1)

    panel = Panel(
        f"Source: {record.source_path}\n"
        f"Duration: {record.media_info.duration_seconds:.1f}s\n"
        f"Language: {record.transcription.language}\n"
        f"Segments: {len(record.transcription.segments)}\n"
        f"Status: {record.status}\n\n"
        f"Transcription:\n{record.transcription.text[:500]}...",
        title=f"[cyan]{preview_id}[/cyan]",
        border_style="blue",
    )
    console.print(panel)


@preview_app.command("confirm")
def confirm_preview(
    preview_id: Annotated[str, typer.Argument(help="Preview ID")],
    path: Annotated[str, typer.Option("--path", "-p", help="Wiki directory path")] = ".",
) -> None:
    """Confirm a preview for ingestion."""
    wiki_path = Path(path).expanduser().resolve()
    preview_db = wiki_path / ".saw" / "previews.db"

    preview_manager = PreviewManager(db_path=str(preview_db))

    try:
        vault_id = preview_manager.confirm(preview_id)
        console.print(f"[green]Preview confirmed: {preview_id}[/green]")
        console.print(f"[dim]Vault ID: {vault_id}[/dim]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@preview_app.command("discard")
def discard_preview(
    preview_id: Annotated[str, typer.Argument(help="Preview ID")],
    path: Annotated[str, typer.Option("--path", "-p", help="Wiki directory path")] = ".",
) -> None:
    """Discard a preview."""
    wiki_path = Path(path).expanduser().resolve()
    preview_db = wiki_path / ".saw" / "previews.db"

    preview_manager = PreviewManager(db_path=str(preview_db))

    try:
        preview_manager.discard(preview_id)
        console.print(f"[green]Preview discarded: {preview_id}[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
