"""Media extractor for video/audio transcription.

Phase 4: Media Ingestion — Whisper-based transcription.
Per D-08: Structured path routing for media files.
Per MING-01~08: Video/audio upload, transcription, preview, batch.

Uses faster-whisper (CTranslate2) for local GPU/CPU transcription,
with fallback to OpenAI Whisper API.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from saw.domain.claims import Claim, ConfidenceLevel, SourceMark
from saw.engines.ingest.extractors.markdown import ExtractionResult

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

# Supported formats
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}


class MediaExtractionError(Exception):
    """Base error for media extraction."""
    pass


class FFmpegNotAvailableError(MediaExtractionError):
    """ffmpeg not available on system."""
    pass


class WhisperModelLoadError(MediaExtractionError):
    """Failed to load Whisper model."""
    pass


class TranscriptionTimeoutError(MediaExtractionError):
    """Transcription timed out."""
    pass


class UnsupportedFormatError(MediaExtractionError):
    """Unsupported media format."""
    pass


@dataclass
class MediaInfo:
    """Media file metadata."""
    duration_seconds: float
    format: str
    bitrate_kbps: int | None = None
    whisper_model: str = "base"
    language: str = "auto"
    transcription_timestamp: str = ""
    sample_rate: int | None = None
    channels: int | None = None
    video_codec: str | None = None
    audio_codec: str | None = None

    def to_dict(self) -> dict:
        return {
            "duration_seconds": self.duration_seconds,
            "format": self.format,
            "bitrate_kbps": self.bitrate_kbps,
            "whisper_model": self.whisper_model,
            "language": self.language,
            "transcription_timestamp": self.transcription_timestamp,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
        }


@dataclass
class Segment:
    """Transcription segment with timestamp."""
    start: float
    end: float
    text: str
    confidence: float = 1.0


@dataclass
class TranscriptionResult:
    """Whisper transcription result."""
    text: str
    language: str
    segments: list[Segment] = field(default_factory=list)


@dataclass
class MediaIngestConfig:
    """Configuration for media ingestion."""
    whisper_model: str = "base"
    whisper_device: str = "auto"
    whisper_language: str = "auto"
    whisper_compute_type: str = "float16"
    max_file_size_mb: int = 500
    batch_concurrency: int = 3
    batch_timeout_seconds: int = 3600
    keep_original_file: bool = True
    temp_dir: str | None = None
    api_fallback: bool = True
    api_key: str | None = None


class MediaExtractor:
    """Extract claims from video/audio via Whisper transcription."""

    def __init__(self, config: MediaIngestConfig | None = None) -> None:
        self.config = config or MediaIngestConfig()
        self._whisper: WhisperModel | None = None
        self._ffmpeg_available: bool | None = None

    def can_handle(self, file_path: Path) -> bool:
        """Check if this extractor can handle the file."""
        ext = file_path.suffix.lower()
        return ext in VIDEO_EXTENSIONS or ext in AUDIO_EXTENSIONS

    def _supported_extensions(self) -> set[str]:
        """Return all supported extensions."""
        return VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

    def extract(self, file_path: Path, source_uuid: str) -> ExtractionResult:
        """Extract transcription from media file.

        Args:
            file_path: Path to media file.
            source_uuid: UUID for the source document.

        Returns:
            ExtractionResult with claims from transcription.
        """
        if not self.can_handle(file_path):
            raise UnsupportedFormatError(f"Not a media file: {file_path}")

        if not file_path.exists():
            raise MediaExtractionError(f"File not found: {file_path}")

        # Check file size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.config.max_file_size_mb:
            raise MediaExtractionError(
                f"File too large: {size_mb:.1f}MB > {self.config.max_file_size_mb}MB"
            )

        # Extract audio if video
        ext = file_path.suffix.lower()
        audio_path = file_path
        temp_audio = None

        if ext in VIDEO_EXTENSIONS:
            audio_path = self._extract_audio_track(file_path)
            temp_audio = audio_path

        try:
            # Get media info
            media_info = self._get_media_info(file_path)

            # Transcribe
            transcription = self._transcribe(audio_path)

            # Update media info
            media_info.whisper_model = self.config.whisper_model
            media_info.language = transcription.language
            media_info.transcription_timestamp = datetime.now(timezone.utc).isoformat()

            # Build claims from segments
            claims = self._build_claims(transcription, source_uuid)

            # Metadata
            metadata = {
                "media_info": media_info.to_dict(),
                "transcription_chars": len(transcription.text),
                "segment_count": len(transcription.segments),
                "source_file": str(file_path),
                "parser": "whisper",
            }

            return ExtractionResult(
                claims=claims,
                entities=[],
                relations=[],
                metadata=metadata,
            )
        finally:
            # Cleanup temp audio file
            if temp_audio and os.path.exists(temp_audio):
                os.unlink(temp_audio)

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        if self._ffmpeg_available is None:
            try:
                subprocess.run(
                    ["ffmpeg", "-version"],
                    capture_output=True,
                    check=True,
                )
                self._ffmpeg_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._ffmpeg_available = False
        return self._ffmpeg_available

    def _extract_audio_track(self, video_path: Path) -> str:
        """Extract audio track from video file."""
        if not self._check_ffmpeg():
            raise FFmpegNotAvailableError(
                "ffmpeg not available. Install: apt-get install ffmpeg"
            )

        # Create temp file for audio
        temp_dir = self.config.temp_dir or tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"{uuid.uuid4()}.wav")

        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            audio_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise MediaExtractionError(f"Audio extraction failed: {e.stderr.decode()}")

        return audio_path

    def _get_media_info(self, file_path: Path) -> MediaInfo:
        """Get media file metadata using ffprobe."""
        ext = file_path.suffix.lower().lstrip(".")

        if not self._check_ffmpeg():
            return MediaInfo(duration_seconds=0.0, format=ext)

        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(file_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            data = json.loads(result.stdout)

            fmt = data.get("format", {})
            streams = data.get("streams", [])

            duration = float(fmt.get("duration", 0))
            bitrate = int(fmt.get("bit_rate", 0)) // 1000 if fmt.get("bit_rate") else None

            info = MediaInfo(
                duration_seconds=duration,
                format=ext,
                bitrate_kbps=bitrate,
            )

            for stream in streams:
                stype = stream.get("codec_type")
                if stype == "video":
                    info.video_codec = stream.get("codec_name")
                elif stype == "audio":
                    info.audio_codec = stream.get("codec_name")
                    info.sample_rate = stream.get("sample_rate")
                    info.channels = stream.get("channels")

            return info
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return MediaInfo(duration_seconds=0.0, format=ext)

    def _get_whisper(self) -> WhisperModel:
        """Lazy load Whisper model."""
        if self._whisper is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as e:
                raise WhisperModelLoadError(
                    "faster-whisper not installed. Install: pip install faster-whisper"
                ) from e

            device = self.config.whisper_device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"

            compute_type = self.config.whisper_compute_type
            if device == "cpu":
                compute_type = "int8"

            try:
                self._whisper = WhisperModel(
                    self.config.whisper_model,
                    device=device,
                    compute_type=compute_type,
                )
            except Exception as e:
                raise WhisperModelLoadError(f"Failed to load model: {e}") from e

        return self._whisper

    def _transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio using Whisper."""
        language = self.config.whisper_language
        if language == "auto":
            language = None

        # Try local Whisper first
        try:
            model = self._get_whisper()
            segments, info = model.transcribe(
                audio_path,
                language=language,
                word_timestamps=False,
            )

            seg_list = []
            for seg in segments:
                seg_list.append(Segment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text.strip(),
                    confidence=getattr(seg, "avg_logprob", 0.0),
                ))

            return TranscriptionResult(
                text=" ".join(s.text for s in seg_list),
                language=info.language,
                segments=seg_list,
            )
        except WhisperModelLoadError:
            # Fall back to API
            if not self.config.api_fallback:
                raise

            return self._transcribe_api(audio_path, language)

    def _transcribe_api(self, audio_path: str, language: str | None) -> TranscriptionResult:
        """Transcribe using OpenAI Whisper API."""
        import httpx

        api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise MediaExtractionError(
                "OpenAI API key required for API fallback. Set OPENAI_API_KEY."
            )

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
            data = {"model": "whisper-1"}
            if language:
                data["language"] = language

            resp = httpx.post(url, headers=headers, files=files, data=data, timeout=600)

        if resp.status_code != 200:
            raise MediaExtractionError(f"API error: {resp.text}")

        result = resp.json()
        text = result.get("text", "")

        # API doesn't return segments, create single segment
        return TranscriptionResult(
            text=text,
            language=result.get("language", "unknown"),
            segments=[Segment(start=0.0, end=0.0, text=text)],
        )

    def _build_claims(
        self,
        transcription: TranscriptionResult,
        source_uuid: str,
    ) -> list[Claim]:
        """Build claims from transcription segments."""
        claims: list[Claim] = []

        # Create a claim for each segment with meaningful content
        for seg in transcription.segments:
            text = seg.text.strip()
            if len(text) < 10:  # Skip very short segments
                continue

            claim = Claim(
                uuid=str(uuid.uuid4()),
                content=text,
                source_uuid=source_uuid,
                content_hash=Claim.compute_hash(text),
                confidence=ConfidenceLevel.SINGLE_SOURCE,
                source_mark=SourceMark.INFERRED,
                tags=["transcription", "whisper", transcription.language],
                media_timestamp=(seg.start, seg.end),
                media_vault_id=source_uuid,
            )
            claims.append(claim)

        # Also create a full-text claim for searchability
        if len(transcription.text) > 100:
            full_claim = Claim(
                uuid=str(uuid.uuid4()),
                content=f"Full transcription: {transcription.text[:2000]}",
                source_uuid=source_uuid,
                content_hash=Claim.compute_hash(transcription.text),
                confidence=ConfidenceLevel.SINGLE_SOURCE,
                source_mark=SourceMark.INFERRED,
                tags=["transcription", "full-text", transcription.language],
            )
            claims.append(full_claim)

        return claims
