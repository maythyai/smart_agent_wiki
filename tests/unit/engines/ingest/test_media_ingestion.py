"""Tests for Media Ingestion (Phase 4).

Tests MediaExtractor, PreviewManager, BatchMediaProcessor.
Uses mock transcription for faster testing.
"""
import pytest
from pathlib import Path
import tempfile
import json

from saw.engines.ingest.classifier import DocumentFormat, classify, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS
from saw.engines.ingest.extractors.media import (
    MediaExtractor,
    MediaIngestConfig,
    MediaInfo,
    TranscriptionResult,
    Segment,
    UnsupportedFormatError,
)
from saw.engines.ingest.preview import PreviewManager, PreviewRecord


class TestClassifierMediaFormats:
    """Test classifier recognizing video/audio formats."""

    def test_classify_mp4_as_video(self):
        result = classify("video.mp4")
        assert result.format == DocumentFormat.VIDEO
        assert result.media_type == "video"

    def test_classify_webm_as_video(self):
        result = classify("video.webm")
        assert result.format == DocumentFormat.VIDEO

    def test_classify_mov_as_video(self):
        result = classify("video.mov")
        assert result.format == DocumentFormat.VIDEO

    def test_classify_mp3_as_audio(self):
        result = classify("audio.mp3")
        assert result.format == DocumentFormat.AUDIO
        assert result.media_type == "audio"

    def test_classify_wav_as_audio(self):
        result = classify("audio.wav")
        assert result.format == DocumentFormat.AUDIO

    def test_classify_m4a_as_audio(self):
        result = classify("audio.m4a")
        assert result.format == DocumentFormat.AUDIO

    def test_classify_ogg_as_audio(self):
        result = classify("audio.ogg")
        assert result.format == DocumentFormat.AUDIO

    def test_video_extensions_constant(self):
        assert ".mp4" in VIDEO_EXTENSIONS
        assert ".webm" in VIDEO_EXTENSIONS
        assert ".mov" in VIDEO_EXTENSIONS
        assert len(VIDEO_EXTENSIONS) == 3

    def test_audio_extensions_constant(self):
        assert ".mp3" in AUDIO_EXTENSIONS
        assert ".wav" in AUDIO_EXTENSIONS
        assert ".m4a" in AUDIO_EXTENSIONS
        assert ".ogg" in AUDIO_EXTENSIONS
        assert len(AUDIO_EXTENSIONS) == 4


class TestMediaIngestConfig:
    """Test MediaIngestConfig defaults."""

    def test_default_config(self):
        config = MediaIngestConfig()
        assert config.whisper_model == "base"
        assert config.whisper_device == "auto"
        assert config.whisper_language == "auto"
        assert config.max_file_size_mb == 500
        assert config.batch_concurrency == 3
        assert config.keep_original_file is True
        assert config.api_fallback is True

    def test_custom_config(self):
        config = MediaIngestConfig(
            whisper_model="medium",
            whisper_device="cuda",
            max_file_size_mb=1000,
            batch_concurrency=5,
        )
        assert config.whisper_model == "medium"
        assert config.whisper_device == "cuda"
        assert config.max_file_size_mb == 1000
        assert config.batch_concurrency == 5


class TestMediaInfo:
    """Test MediaInfo dataclass."""

    def test_media_info_to_dict(self):
        info = MediaInfo(
            duration_seconds=120.5,
            format="mp4",
            bitrate_kbps=1500,
            whisper_model="base",
            language="zh",
        )
        d = info.to_dict()
        assert d["duration_seconds"] == 120.5
        assert d["format"] == "mp4"
        assert d["bitrate_kbps"] == 1500
        assert d["whisper_model"] == "base"
        assert d["language"] == "zh"

    def test_media_info_optional_fields(self):
        info = MediaInfo(
            duration_seconds=60.0,
            format="mp3",
        )
        assert info.bitrate_kbps is None
        assert info.video_codec is None


class TestTranscriptionResult:
    """Test TranscriptionResult dataclass."""

    def test_transcription_result_segments(self):
        result = TranscriptionResult(
            text="Hello world",
            language="en",
            segments=[
                Segment(start=0.0, end=2.5, text="Hello"),
                Segment(start=2.5, end=5.0, text="world"),
            ],
        )
        assert result.text == "Hello world"
        assert result.language == "en"
        assert len(result.segments) == 2
        assert result.segments[0].start == 0.0

    def test_segment_confidence(self):
        seg = Segment(start=0.0, end=1.0, text="test", confidence=0.95)
        assert seg.confidence == 0.95


class TestMediaExtractor:
    """Test MediaExtractor (without actual Whisper)."""

    def test_can_handle_mp4(self):
        extractor = MediaExtractor()
        assert extractor.can_handle(Path("video.mp4"))

    def test_can_handle_mp3(self):
        extractor = MediaExtractor()
        assert extractor.can_handle(Path("audio.mp3"))

    def test_cannot_handle_pdf(self):
        extractor = MediaExtractor()
        assert not extractor.can_handle(Path("doc.pdf"))

    def test_cannot_handle_md(self):
        extractor = MediaExtractor()
        assert not extractor.can_handle(Path("note.md"))

    def test_supported_extensions(self):
        extractor = MediaExtractor()
        exts = extractor._supported_extensions()
        assert ".mp4" in exts
        assert ".mp3" in exts
        assert ".pdf" not in exts
        assert ".md" not in exts

    def test_unsupported_format_raises(self):
        extractor = MediaExtractor()
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            with pytest.raises(UnsupportedFormatError):
                extractor.extract(Path(f.name), "test-uuid")

    def test_file_not_found_raises(self):
        extractor = MediaExtractor()
        with pytest.raises(Exception):  # MediaExtractionError
            extractor.extract(Path("/nonexistent.mp4"), "test-uuid")


class TestPreviewManager:
    """Test PreviewManager with in-memory SQLite."""

    @pytest.fixture
    def preview_manager(self):
        return PreviewManager(db_path=":memory:")

    def test_save_preview(self, preview_manager):
        transcription = TranscriptionResult(
            text="Test transcription",
            language="en",
            segments=[Segment(start=0.0, end=5.0, text="Test")],
        )
        media_info = MediaInfo(
            duration_seconds=60.0,
            format="mp3",
        )

        preview_id = preview_manager.save_preview(
            transcription=transcription,
            media_info=media_info,
            source_path="/test/audio.mp3",
        )

        assert preview_id.startswith("pv_")
        assert len(preview_id) == 15  # pv_ + 12 hex chars

    def test_get_preview(self, preview_manager):
        transcription = TranscriptionResult(
            text="Sample text",
            language="zh",
            segments=[],
        )
        media_info = MediaInfo(duration_seconds=30.0, format="mp4")

        preview_id = preview_manager.save_preview(
            transcription=transcription,
            media_info=media_info,
            source_path="/test/video.mp4",
        )

        record = preview_manager.get_preview(preview_id)

        assert record is not None
        assert record.preview_id == preview_id
        assert record.transcription.text == "Sample text"
        assert record.transcription.language == "zh"
        assert record.media_info.duration_seconds == 30.0
        assert record.status == "pending"

    def test_get_preview_not_found(self, preview_manager):
        record = preview_manager.get_preview("pv_nonexistent")
        assert record is None

    def test_confirm_preview(self, preview_manager):
        transcription = TranscriptionResult(text="Test", language="en", segments=[])
        media_info = MediaInfo(duration_seconds=10.0, format="wav")

        preview_id = preview_manager.save_preview(
            transcription=transcription,
            media_info=media_info,
            source_path="/test/audio.wav",
        )

        vault_id = preview_manager.confirm(preview_id)

        assert vault_id.startswith("vault_")

        # Check status updated
        record = preview_manager.get_preview(preview_id)
        assert record.status == "confirmed"

    def test_confirm_not_found_raises(self, preview_manager):
        with pytest.raises(ValueError):
            preview_manager.confirm("pv_nonexistent")

    def test_confirm_already_confirmed_raises(self, preview_manager):
        transcription = TranscriptionResult(text="Test", language="en", segments=[])
        media_info = MediaInfo(duration_seconds=10.0, format="wav")

        preview_id = preview_manager.save_preview(
            transcription=transcription,
            media_info=media_info,
            source_path="/test/audio.wav",
        )

        preview_manager.confirm(preview_id)

        with pytest.raises(ValueError, match="already confirmed"):
            preview_manager.confirm(preview_id)

    def test_discard_preview(self, preview_manager):
        transcription = TranscriptionResult(text="Test", language="en", segments=[])
        media_info = MediaInfo(duration_seconds=10.0, format="wav")

        preview_id = preview_manager.save_preview(
            transcription=transcription,
            media_info=media_info,
            source_path="/test/audio.wav",
        )

        preview_manager.discard(preview_id)

        record = preview_manager.get_preview(preview_id)
        assert record.status == "discarded"

    def test_list_previews(self, preview_manager):
        # Create multiple previews
        for i in range(3):
            preview_manager.save_preview(
                transcription=TranscriptionResult(text=f"Test {i}", language="en", segments=[]),
                media_info=MediaInfo(duration_seconds=float(i * 10), format="mp3"),
                source_path=f"/test/audio{i}.mp3",
            )

        previews = preview_manager.list_previews()

        assert len(previews) == 3
        assert all(p.status == "pending" for p in previews)

    def test_list_previews_filter_by_status(self, preview_manager):
        preview_id = preview_manager.save_preview(
            transcription=TranscriptionResult(text="Test", language="en", segments=[]),
            media_info=MediaInfo(duration_seconds=10.0, format="mp3"),
            source_path="/test/audio.mp3",
        )

        preview_manager.confirm(preview_id)

        pending = preview_manager.list_previews(status="pending")
        confirmed = preview_manager.list_previews(status="confirmed")

        assert len(pending) == 0
        assert len(confirmed) == 1

    def test_update_transcription(self, preview_manager):
        preview_id = preview_manager.save_preview(
            transcription=TranscriptionResult(text="Original", language="en", segments=[]),
            media_info=MediaInfo(duration_seconds=10.0, format="mp3"),
            source_path="/test/audio.mp3",
        )

        preview_manager.update_transcription(preview_id, "Edited text")

        record = preview_manager.get_preview(preview_id)
        assert record.transcription.text == "Edited text"

    def test_cleanup_old_previews(self, preview_manager):
        # Create and confirm a preview
        preview_id = preview_manager.save_preview(
            transcription=TranscriptionResult(text="Test", language="en", segments=[]),
            media_info=MediaInfo(duration_seconds=10.0, format="mp3"),
            source_path="/test/audio.mp3",
        )
        preview_manager.confirm(preview_id)

        # Cleanup (should remove confirmed previews older than 7 days)
        # Since it's just created, this won't actually remove it
        removed = preview_manager.cleanup(days_old=7)

        assert removed == 0  # Nothing removed since it's new


class TestClaimMediaFields:
    """Test Claim model with media timestamp fields."""

    def test_claim_with_media_timestamp(self):
        from saw.domain.claims import Claim, ConfidenceLevel, SourceMark

        claim = Claim(
            uuid="test-uuid",
            content="Transcribed segment",
            source_uuid="vault-uuid",
            content_hash="hash123",
            confidence=ConfidenceLevel.SINGLE_SOURCE,
            source_mark=SourceMark.INFERRED,
            media_timestamp=(10.5, 25.0),
            media_vault_id="vault-uuid",
        )

        assert claim.media_timestamp == (10.5, 25.0)
        assert claim.media_vault_id == "vault-uuid"

    def test_claim_without_media_timestamp(self):
        from saw.domain.claims import Claim, ConfidenceLevel, SourceMark

        claim = Claim(
            uuid="test-uuid",
            content="Regular claim",
            source_uuid="vault-uuid",
            content_hash="hash123",
        )

        assert claim.media_timestamp is None
        assert claim.media_vault_id is None