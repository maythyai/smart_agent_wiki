"""Batch media processor for concurrent transcription.

Phase 4: Media Ingestion — Batch processing.
Per MING-07: Batch transcription support.

Provides concurrent processing with progress tracking and cancellation.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from saw.engines.ingest.extractors.media import (
    MediaExtractor,
    MediaIngestConfig,
    TranscriptionResult,
)
from saw.engines.ingest.preview import PreviewManager


@dataclass
class BatchProgress:
    """Progress information for batch processing."""
    total: int
    completed: int
    failed: int
    current_file: str
    percent: float

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "current_file": self.current_file,
            "percent": self.percent,
        }


@dataclass
class FileResult:
    """Result for a single file in batch."""
    file_path: str
    success: bool
    preview_id: str | None = None
    error: str | None = None
    duration_seconds: float = 0.0
    claim_count: int = 0


@dataclass
class BatchResult:
    """Result of batch processing."""
    batch_id: str
    total_files: int
    successful: int
    failed: int
    file_results: list[FileResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "total_files": self.total_files,
            "successful": self.successful,
            "failed": self.failed,
            "elapsed_seconds": self.elapsed_seconds,
            "file_results": [r.__dict__ for r in self.file_results],
        }


@dataclass
class BatchOptions:
    """Options for batch processing."""
    preview: bool = True  # Create previews instead of direct ingest
    concurrency: int = 3  # Number of concurrent transcriptions
    stop_on_error: bool = False  # Continue processing on errors
    model: str = "base"  # Whisper model to use


class BatchMediaProcessor:
    """Process multiple media files concurrently.

    Uses asyncio for concurrent whisper transcription.
    """

    def __init__(
        self,
        config: MediaIngestConfig,
        preview_manager: PreviewManager | None = None,
    ) -> None:
        self.config = config
        self.preview_manager = preview_manager or PreviewManager()
        self._extractor = MediaExtractor(config)
        self._cancelled = False
        self._progress_callback: Callable[[BatchProgress], None] | None = None
        self._current_progress: BatchProgress | None = None

    def set_progress_callback(
        self,
        callback: Callable[[BatchProgress], None],
    ) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback

    def cancel(self) -> None:
        """Cancel batch processing."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if batch processing was cancelled."""
        return self._cancelled

    async def process_batch(
        self,
        files: list[str],
        options: BatchOptions | None = None,
    ) -> BatchResult:
        """Process multiple media files concurrently.

        Args:
            files: List of file paths to process.
            options: Batch processing options.

        Returns:
            BatchResult with success/failure details.
        """
        options = options or BatchOptions()
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()

        results: list[FileResult] = []
        completed = 0
        failed = 0
        self._cancelled = False

        # Filter valid files
        valid_files = []
        for f in files:
            path = Path(f)
            if path.exists() and self._extractor.can_handle(path):
                valid_files.append(f)
            else:
                results.append(FileResult(
                    file_path=f,
                    success=False,
                    error="Invalid file or format",
                ))
                failed += 1

        total = len(valid_files)

        # Process with semaphore for concurrency control
        semaphore = asyncio.Semaphore(options.concurrency)

        async def process_one(file_path: str) -> FileResult:
            """Process a single file."""
            if self._cancelled:
                return FileResult(
                    file_path=file_path,
                    success=False,
                    error="Cancelled",
                )

            async with semaphore:
                result = await self._process_file(file_path, options)

                # Update progress
                nonlocal completed, failed
                if result.success:
                    completed += 1
                else:
                    failed += 1

                progress = BatchProgress(
                    total=total,
                    completed=completed,
                    failed=failed,
                    current_file=file_path,
                    percent=(completed + failed) / total * 100 if total > 0 else 0,
                )
                self._current_progress = progress

                if self._progress_callback:
                    self._progress_callback(progress)

                return result

        # Create tasks
        tasks = [process_one(f) for f in valid_files]

        # Run concurrently
        file_results = await asyncio.gather(*tasks, return_exceptions=True)

        # F-INGEST-14: map each result to its file path (was "unknown" on
        # exception, losing the context of which file failed).
        for fr, fpath in zip(file_results, valid_files):
            if isinstance(fr, Exception):
                results.append(FileResult(
                    file_path=fpath,
                    success=False,
                    error=str(fr),
                ))
                failed += 1
            else:
                results.append(fr)

        elapsed = time.time() - start_time

        return BatchResult(
            batch_id=batch_id,
            total_files=len(files),
            successful=completed,
            failed=sum(1 for r in results if not r.success),
            file_results=results,
            elapsed_seconds=elapsed,
            started_at=datetime.fromtimestamp(start_time, timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    async def _process_file(
        self,
        file_path: str,
        options: BatchOptions,
    ) -> FileResult:
        """Process a single media file.

        Runs transcription in thread pool to avoid blocking.
        """
        loop = asyncio.get_running_loop()
        start_time = time.time()

        try:
            # Run extraction in thread pool (whisper is CPU-bound)
            result = await loop.run_in_executor(
                None,
                lambda: self._extractor.extract(Path(file_path), "")
            )

            duration = time.time() - start_time

            if options.preview:
                # Save to preview
                from saw.engines.ingest.extractors.media import MediaInfo
                media_info = MediaInfo(
                    duration_seconds=result.metadata.get("media_info", {}).get("duration_seconds", 0),
                    format=Path(file_path).suffix.lower().lstrip("."),
                )
                if "media_info" in result.metadata:
                    mi = result.metadata["media_info"]
                    media_info = MediaInfo(**mi)

                preview_id = self.preview_manager.save_preview(
                    transcription=TranscriptionResult(
                        text=" ".join(c.content for c in result.claims[:100]),
                        language=result.metadata.get("media_info", {}).get("language", "unknown"),
                        segments=[],
                    ),
                    media_info=media_info,
                    source_path=file_path,
                )
                return FileResult(
                    file_path=file_path,
                    success=True,
                    preview_id=preview_id,
                    duration_seconds=duration,
                    claim_count=len(result.claims),
                )
            else:
                # Direct ingest (no preview)
                return FileResult(
                    file_path=file_path,
                    success=True,
                    duration_seconds=duration,
                    claim_count=len(result.claims),
                )

        except Exception as e:
            return FileResult(
                file_path=file_path,
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def get_progress(self) -> BatchProgress | None:
        """Get current progress."""
        return self._current_progress

    async def process_directory(
        self,
        directory: str,
        options: BatchOptions | None = None,
        recursive: bool = False,
    ) -> BatchResult:
        """Process all media files in a directory.

        Args:
            directory: Path to directory.
            options: Batch processing options.
            recursive: Process subdirectories.

        Returns:
            BatchResult with all processed files.
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            return BatchResult(
                batch_id="invalid",
                total_files=0,
                successful=0,
                failed=1,
            )

        # Find all media files
        files: list[str] = []
        pattern = "**/*" if recursive else "*"

        for ext in self._extractor._supported_extensions():
            files.extend(str(p) for p in dir_path.glob(f"{pattern}{ext}"))

        return await self.process_batch(files, options)
