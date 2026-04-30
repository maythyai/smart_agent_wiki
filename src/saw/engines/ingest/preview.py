"""Preview manager for transcription confirmation.

Phase 4: Media Ingestion — Preview mechanism.
Per MING-08: Transcription preview before ingest.

Allows users to review and edit transcription before confirming.
Stores previews in a temporary SQLite database.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from saw.engines.ingest.extractors.media import TranscriptionResult, MediaInfo


@dataclass
class PreviewRecord:
    """A preview record for transcription confirmation."""
    preview_id: str
    vault_id: str
    transcription: TranscriptionResult
    media_info: MediaInfo
    source_path: str
    created_at: datetime
    status: str = "pending"  # pending, confirmed, discarded

    def to_dict(self) -> dict:
        return {
            "preview_id": self.preview_id,
            "vault_id": self.vault_id,
            "transcription_text": self.transcription.text,
            "transcription_language": self.transcription.language,
            "segment_count": len(self.transcription.segments),
            "media_info": self.media_info.to_dict(),
            "source_path": self.source_path,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


@dataclass
class PreviewSummary:
    """Summary of a preview for listing."""
    preview_id: str
    source_path: str
    duration_seconds: float
    segment_count: int
    language: str
    created_at: datetime
    status: str


class PreviewManager:
    """Manage transcription previews with temporary storage.

    Uses SQLite for durability while waiting for user confirmation.
    Supports both in-memory and file-based storage.
    """

    def __init__(
        self,
        vault_path: Path | None = None,
        db_path: str = ":memory:",
    ) -> None:
        self.vault_path = vault_path
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the previews database."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS previews (
                preview_id TEXT PRIMARY KEY,
                vault_id TEXT,
                transcription TEXT,
                media_info TEXT,
                source_path TEXT,
                created_at TEXT,
                status TEXT
            )
        """)
        self._conn.commit()

    def save_preview(
        self,
        transcription: TranscriptionResult,
        media_info: MediaInfo,
        source_path: str,
        vault_id: str | None = None,
    ) -> str:
        """Save a transcription preview.

        Args:
            transcription: The transcription result.
            media_info: Media file metadata.
            source_path: Original file path.
            vault_id: Optional vault ID (generated if not provided).

        Returns:
            The preview_id for later reference.
        """
        preview_id = f"pv_{uuid.uuid4().hex[:12]}"
        vault_id = vault_id or f"vault_{uuid.uuid4().hex[:12]}"

        record = PreviewRecord(
            preview_id=preview_id,
            vault_id=vault_id,
            transcription=transcription,
            media_info=media_info,
            source_path=source_path,
            created_at=datetime.now(timezone.utc),
        )

        # Serialize segments
        segments_data = [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "confidence": seg.confidence,
            }
            for seg in transcription.segments
        ]

        self._conn.execute("""
            INSERT INTO previews
            (preview_id, vault_id, transcription, media_info, source_path, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            record.preview_id,
            record.vault_id,
            json.dumps({
                "text": transcription.text,
                "language": transcription.language,
                "segments": segments_data,
            }),
            json.dumps(media_info.to_dict()),
            source_path,
            record.created_at.isoformat(),
            "pending",
        ))
        self._conn.commit()

        return preview_id

    def get_preview(self, preview_id: str) -> PreviewRecord | None:
        """Get a preview record by ID."""
        row = self._conn.execute(
            "SELECT * FROM previews WHERE preview_id = ?",
            (preview_id,)
        ).fetchone()

        if row is None:
            return None

        return self._row_to_record(row)

    def _row_to_record(self, row: sqlite3.Row) -> PreviewRecord:
        """Convert database row to PreviewRecord."""
        trans_data = json.loads(row["transcription"])
        media_data = json.loads(row["media_info"])

        # Reconstruct TranscriptionResult
        from saw.engines.ingest.extractors.media import Segment
        segments = [
            Segment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"],
                confidence=seg.get("confidence", 1.0),
            )
            for seg in trans_data.get("segments", [])
        ]

        transcription = TranscriptionResult(
            text=trans_data["text"],
            language=trans_data["language"],
            segments=segments,
        )

        # Reconstruct MediaInfo
        media_info = MediaInfo(
            duration_seconds=media_data.get("duration_seconds", 0),
            format=media_data.get("format", "unknown"),
            bitrate_kbps=media_data.get("bitrate_kbps"),
            whisper_model=media_data.get("whisper_model", "base"),
            language=media_data.get("language", "auto"),
            transcription_timestamp=media_data.get("transcription_timestamp", ""),
            sample_rate=media_data.get("sample_rate"),
            channels=media_data.get("channels"),
            video_codec=media_data.get("video_codec"),
            audio_codec=media_data.get("audio_codec"),
        )

        return PreviewRecord(
            preview_id=row["preview_id"],
            vault_id=row["vault_id"],
            transcription=transcription,
            media_info=media_info,
            source_path=row["source_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            status=row["status"],
        )

    def confirm(self, preview_id: str) -> str:
        """Confirm a preview for ingestion.

        Marks the preview as confirmed and returns the vault_id.

        Args:
            preview_id: The preview to confirm.

        Returns:
            The vault_id for the confirmed content.

        Raises:
            ValueError: If preview not found or already processed.
        """
        row = self._conn.execute(
            "SELECT * FROM previews WHERE preview_id = ?",
            (preview_id,)
        ).fetchone()

        if row is None:
            raise ValueError(f"Preview not found: {preview_id}")

        if row["status"] != "pending":
            raise ValueError(f"Preview already {row['status']}")

        vault_id = row["vault_id"]

        self._conn.execute(
            "UPDATE previews SET status = ? WHERE preview_id = ?",
            ("confirmed", preview_id)
        )
        self._conn.commit()

        return vault_id

    def discard(self, preview_id: str) -> None:
        """Discard a preview.

        Marks the preview as discarded. Original files are not deleted.

        Args:
            preview_id: The preview to discard.

        Raises:
            ValueError: If preview not found or already processed.
        """
        row = self._conn.execute(
            "SELECT * FROM previews WHERE preview_id = ?",
            (preview_id,)
        ).fetchone()

        if row is None:
            raise ValueError(f"Preview not found: {preview_id}")

        if row["status"] != "pending":
            raise ValueError(f"Preview already {row['status']}")

        self._conn.execute(
            "UPDATE previews SET status = ? WHERE preview_id = ?",
            ("discarded", preview_id)
        )
        self._conn.commit()

    def list_previews(
        self,
        status: str | None = None,
    ) -> list[PreviewSummary]:
        """List all previews, optionally filtered by status.

        Args:
            status: Filter by status (pending, confirmed, discarded).

        Returns:
            List of preview summaries.
        """
        if status:
            rows = self._conn.execute(
                "SELECT * FROM previews WHERE status = ? ORDER BY created_at DESC",
                (status,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM previews ORDER BY created_at DESC"
            ).fetchall()

        summaries = []
        for row in rows:
            trans_data = json.loads(row["transcription"])
            media_data = json.loads(row["media_info"])

            summaries.append(PreviewSummary(
                preview_id=row["preview_id"],
                source_path=row["source_path"],
                duration_seconds=media_data.get("duration_seconds", 0),
                segment_count=len(trans_data.get("segments", [])),
                language=trans_data.get("language", "unknown"),
                created_at=datetime.fromisoformat(row["created_at"]),
                status=row["status"],
            ))

        return summaries

    def update_transcription(
        self,
        preview_id: str,
        new_text: str,
    ) -> None:
        """Update the transcription text for a preview.

        Allows users to edit transcription before confirming.

        Args:
            preview_id: The preview to update.
            new_text: The new transcription text.
        """
        row = self._conn.execute(
            "SELECT transcription FROM previews WHERE preview_id = ?",
            (preview_id,)
        ).fetchone()

        if row is None:
            raise ValueError(f"Preview not found: {preview_id}")

        trans_data = json.loads(row["transcription"])
        trans_data["text"] = new_text

        self._conn.execute(
            "UPDATE previews SET transcription = ? WHERE preview_id = ?",
            (json.dumps(trans_data), preview_id)
        )
        self._conn.commit()

    def cleanup(self, days_old: int = 7) -> int:
        """Clean up old confirmed/discarded previews.

        Args:
            days_old: Remove previews older than this many days.

        Returns:
            Number of previews removed.
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)

        cursor = self._conn.execute(
            "DELETE FROM previews WHERE status != ? AND created_at < ?",
            ("pending", cutoff.isoformat())
        )
        self._conn.commit()

        return cursor.rowcount

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
