"""Ingestion pipeline orchestrating classify -> extract -> fuse -> validate -> enqueue.

Per D-12: Ingestion output flow.
Per D-04: Write Queue single entry point.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from saw.adapters.llm.router import LLMRouter
from saw.adapters.parsers.html_parser import HTMLParser
from saw.adapters.parsers.markdown_parser import MarkdownParser
from saw.adapters.parsers.pdf_parser import PDFParser
from saw.domain.claims import Claim
from saw.domain.entities import Entity, EntityRelation
from saw.domain.protocols import ClaimsRepository, VaultRepository, WikiRepository, WriteQueue
from saw.engines.ingest.classifier import DocumentFormat, classify
from saw.engines.ingest.extractors.code_ast import CodeASTExtractor
from saw.engines.ingest.extractors.markdown import ExtractionResult, MarkdownExtractor
from saw.engines.ingest.extractors.media import MediaExtractor, MediaIngestConfig
from saw.engines.ingest.extractors.pdf import PDFExtractor
from saw.engines.ingest.extractors.url import URLExtractor
from saw.engines.ingest.fuser import Fuser
from saw.engines.ingest.validator import Validator
from saw.write_queue.queue import WriteOp


@dataclass
class IngestResult:
    """Result of an ingestion operation."""
    session_id: str
    claim_count: int
    entity_count: int
    relation_count: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parser: str = "unknown"
    preview_id: str | None = None  # For media previews


class IngestPipeline:
    """Orchestrate the complete ingestion flow.

    Flow: classify -> extract -> fuse -> validate -> enqueue
    """

    def __init__(
        self,
        claims_repo: ClaimsRepository,
        write_queue: WriteQueue,
        llm_router: LLMRouter | None,
        vault_repo: VaultRepository,
        wiki_repo: WikiRepository,
    ) -> None:
        self._claims_repo = claims_repo
        self._write_queue = write_queue
        self._llm_router = llm_router
        self._vault_repo = vault_repo
        self._wiki_repo = wiki_repo

        # Initialize extractors
        self._markdown_extractor = MarkdownExtractor(
            parser=MarkdownParser(),
            llm=llm_router,
        )
        self._pdf_extractor = PDFExtractor(
            parser=PDFParser(),
            llm=llm_router,
        )
        self._url_extractor = URLExtractor(
            parser=HTMLParser(),
            llm=llm_router,
        )
        self._code_extractor = CodeASTExtractor()
        self._media_extractor: MediaExtractor | None = None  # Lazy init

        self._fuser = Fuser()
        self._validator = Validator()

    def _get_media_extractor(self, options: dict | None = None) -> MediaExtractor:
        """Get or create media extractor with config."""
        if self._media_extractor is None:
            config = MediaIngestConfig()
            if options:
                if "whisper_model" in options:
                    config.whisper_model = options["whisper_model"]
                if "whisper_device" in options:
                    config.whisper_device = options["whisper_device"]
                if "api_fallback" in options:
                    config.api_fallback = options["api_fallback"]
            self._media_extractor = MediaExtractor(config)
        return self._media_extractor

    def ingest(
        self,
        source: str,
        options: dict | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> IngestResult:
        """Ingest a document source.

        Args:
            source: File path, URL, or directory to ingest.
            options: Optional ingestion options (format override, etc.).
            progress_callback: Optional ``callback(stage, fraction)`` for
                coarse progress reporting (F-INGEST-01), so callers can show
                progress instead of a silent long-running call.

        Returns:
            IngestResult with session ID, counts, and any errors/warnings.
        """
        session_id = str(uuid.uuid4())
        options = options or {}
        errors: list[str] = []
        warnings: list[str] = []

        def report(stage: str, frac: float) -> None:
            # F-INGEST-01: coarse progress hooks (classify/extract/fuse/
            # validate/enqueue) so callers can surface progress + cancel.
            if progress_callback is not None:
                try:
                    progress_callback(stage, frac)
                except Exception:
                    pass

        report("classify", 0.1)
        # 1. Classify source
        classified = classify(source)
        if classified.format == DocumentFormat.UNKNOWN:
            errors.append(f"Unknown format for source: {source}. Supported: Markdown, PDF, URL, code, audio, video.")
            return IngestResult(
                session_id=session_id,
                claim_count=0,
                entity_count=0,
                relation_count=0,
                errors=errors,
            )

        # 2. Generate vault UUID for this source
        source_uuid = str(uuid.uuid4())

        # 3. Route to appropriate extractor
        extraction_result: ExtractionResult | None = None
        parser_used = "unknown"

        try:
            if classified.format == DocumentFormat.MARKDOWN and classified.path:
                extraction_result = self._markdown_extractor.extract(
                    classified.path, source_uuid
                )
                parser_used = "markdown"

            elif classified.format == DocumentFormat.PDF and classified.path:
                extraction_result = self._pdf_extractor.extract(
                    classified.path, source_uuid
                )
                parser_used = extraction_result.metadata.get("parser", "pdf")

            elif classified.format == DocumentFormat.URL and classified.url:
                extraction_result = self._url_extractor.extract(
                    classified.url, source_uuid
                )
                parser_used = "html"

            elif classified.format == DocumentFormat.CODE and classified.path:
                extraction_result = self._code_extractor.extract(
                    classified.path, source_uuid
                )
                parser_used = "ast"

            elif classified.format in (DocumentFormat.VIDEO, DocumentFormat.AUDIO) and classified.path:
                # Phase 4: Media Ingestion
                media_extractor = self._get_media_extractor(options)
                extraction_result = media_extractor.extract(
                    classified.path, source_uuid
                )
                parser_used = "whisper"

            else:
                errors.append(f"Unsupported format '{classified.format.name}' for {source}: no extractor available. JSON/TABLE ingestion is not yet supported.")
                return IngestResult(
                    session_id=session_id,
                    claim_count=0,
                    entity_count=0,
                    relation_count=0,
                    errors=errors,
                )

        except Exception as e:
            errors.append(f"Extraction failed for {source}: {e}. Verify the file is not corrupted and its extension matches the content.")
            return IngestResult(
                session_id=session_id,
                claim_count=0,
                entity_count=0,
                relation_count=0,
                errors=errors,
            )

        if extraction_result is None:
            return IngestResult(
                session_id=session_id,
                claim_count=0,
                entity_count=0,
                relation_count=0,
                errors=["Extraction returned no results. The source may be empty or in an unsupported structure."],
            )

        report("extract", 0.5)
        # 4. Fuse with existing claims
        existing_claims = self._get_existing_claims(extraction_result.claims)
        fused = self._fuser.fuse(extraction_result.claims, existing_claims)

        report("fuse", 0.7)
        # 5. Validate
        validated = self._validator.validate(
            fused.to_insert,
            extraction_result.entities,
            extraction_result.relations,
        )
        errors.extend(validated.errors)

        report("validate", 0.8)
        # 6. Build WriteOp list for all sinks
        ops = self._build_write_ops(
            session_id=session_id,
            source=source,
            source_uuid=source_uuid,
            claims=validated.valid_claims,
            entities=validated.valid_entities,
            relations=validated.valid_relations,
            metadata=extraction_result.metadata,
        )

        report("enqueue", 0.95)
        # 7. Enqueue all operations atomically
        try:
            self._write_queue.enqueue_atomic(ops)
        except Exception as e:
            errors.append(f"Failed to enqueue write operations: {e}. The database may be locked (saw.db); retry or check for a stuck process.")
            return IngestResult(
                session_id=session_id,
                claim_count=0,
                entity_count=0,
                relation_count=0,
                errors=errors,
            )

        report("done", 1.0)
        return IngestResult(
            session_id=session_id,
            claim_count=len(validated.valid_claims),
            entity_count=len(validated.valid_entities),
            relation_count=len(validated.valid_relations),
            errors=errors,
            warnings=warnings,
            parser=parser_used,
        )

    def _get_existing_claims(self, new_claims: list[Claim]) -> list[Claim]:
        """Get existing claims that might overlap with new claims.

        Queries by ``content_hash`` (which has a partial index) so the fuser
        can dedup re-ingested claims instead of always inserting duplicates.
        Returns ``[]`` on a non-SQLite repo (e.g. a Mock) or DB error.
        Previously a ``return []`` placeholder.
        """
        import sqlite3

        conn = getattr(self._claims_repo, "_conn", None)
        if not isinstance(conn, sqlite3.Connection):
            return []
        hashes = {c.content_hash for c in new_claims if c.content_hash}
        if not hashes:
            return []
        placeholders = ",".join("?" for _ in hashes)
        try:
            rows = conn.execute(
                f"SELECT * FROM claim WHERE content_hash IN ({placeholders}) "
                f"AND deleted_at IS NULL",
                tuple(hashes),
            ).fetchall()
        except sqlite3.Error:
            return []
        # Use the concrete repo's row converter when available.
        row_to_claim = getattr(self._claims_repo, "_row_to_claim", None)
        if row_to_claim is None:
            return []
        return [row_to_claim(r) for r in rows]

    def _build_write_ops(
        self,
        session_id: str,
        source: str,
        source_uuid: str,
        claims: list[Claim],
        entities: list[Entity],
        relations: list[EntityRelation],
        metadata: dict,
    ) -> list[WriteOp]:
        """Build WriteOp list for all sinks."""
        ops: list[WriteOp] = []
        now = datetime.now(timezone.utc)

        # Vault operation
        ops.append(WriteOp(
            op_id=str(uuid.uuid4()),
            session_id=session_id,
            sink_name="vault",
            payload={
                "source": source,
                "source_path": source,  # Add source_path for VaultSink
                "source_uuid": source_uuid,
                "metadata": metadata,
                "claims_count": len(claims),
            },
        ))

        # Claims operations
        for claim in claims:
            ops.append(WriteOp(
                op_id=str(uuid.uuid4()),
                session_id=session_id,
                sink_name="claims",
                payload={
                    "uuid": claim.uuid,
                    "content": claim.content,
                    "source_uuid": claim.source_uuid,
                    "content_hash": claim.content_hash,
                    "confidence": claim.confidence.name,
                    "source_mark": claim.source_mark.name,
                    "tags": claim.tags,
                    "entities": claim.entities,
                    "created_at": claim.created_at.isoformat(),
                },
            ))

        # Wiki operations (entity pages)
        for entity in entities:
            # Generate content from entity description
            entity_content = f"# {entity.name}\n\n"
            if entity.entity_type:
                entity_content += f"Type: {entity.entity_type}\n\n"
            if entity.description:
                entity_content += entity.description
            ops.append(WriteOp(
                op_id=str(uuid.uuid4()),
                session_id=session_id,
                sink_name="wiki",
                payload={
                    "path": f"entities/{entity.name}.md",
                    "title": entity.name,
                    "content": entity_content,
                    "tags": [entity.entity_type] if entity.entity_type else [],
                    "page_type": "entity",
                    "source_uuid": source_uuid,
                },
            ))

        # FTS5 operations (index new content)
        for claim in claims:
            ops.append(WriteOp(
                op_id=str(uuid.uuid4()),
                session_id=session_id,
                sink_name="fts5",
                payload={
                    "claim_uuid": claim.uuid,
                    "content": claim.content,
                    "tags": " ".join(claim.tags),
                },
            ))

        # Graph operations (entities and relations)
        for entity in entities:
            ops.append(WriteOp(
                op_id=str(uuid.uuid4()),
                session_id=session_id,
                sink_name="graph",
                payload={
                    "type": "entity",
                    "uuid": entity.uuid,
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                },
            ))

        for relation in relations:
            ops.append(WriteOp(
                op_id=str(uuid.uuid4()),
                session_id=session_id,
                sink_name="graph",
                payload={
                    "type": "relation",
                    "source_uuid": relation.source_uuid,
                    "target_uuid": relation.target_uuid,
                    "relation_type": relation.relation_type,
                },
            ))

        return ops