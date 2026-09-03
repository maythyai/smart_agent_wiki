"""PDF extractor for ingestion engine.

Per INGE-02: PDF ingestion with 3-tier fallback parsing.
Per D-09: PDF parsing with quality validation.
Per D-22: Three-tier degradation (offline mode without LLM).
"""
from __future__ import annotations

import uuid
from pathlib import Path

from saw.adapters.llm.router import LLMRouter
from saw.adapters.parsers.pdf_parser import PDFParser, PDFParseResult
from saw.domain.claims import Claim
from saw.engines.ingest.extractors.llm_extract import LLMExtractor
from saw.engines.ingest.extractors.markdown import ExtractionResult


class PDFExtractor:
    """Extract claims, entities, and relations from PDF files."""

    def __init__(
        self,
        parser: PDFParser,
        llm: LLMRouter | None,
    ) -> None:
        self._parser = parser
        self._llm = llm

    def extract(self, file_path: Path, source_uuid: str) -> ExtractionResult:
        """Extract from a PDF file.

        Args:
            file_path: Path to the PDF file.
            source_uuid: UUID of the source document in Vault.

        Returns:
            ExtractionResult with claims, entities, relations, and metadata.
        """
        # Parse PDF (3-tier fallback)
        parse_result = self._parser.parse(file_path)

        # Metadata with parser tier
        metadata = {
            "title": parse_result.title,
            "source_file": str(file_path),
            "page_count": parse_result.page_count,
            "word_count": parse_result.word_count,
            "char_count": parse_result.char_count,
            "paragraph_count": parse_result.paragraph_count,
            "parser": parse_result.parser,  # For confidence adjustment
        }

        # Extract claims
        if self._llm:
            # LLM-based extraction
            llm_extractor = LLMExtractor(self._llm)
            claims = llm_extractor.extract_claims(parse_result.content, source_uuid)
            entities = llm_extractor.extract_entities(parse_result.content)
            relations = llm_extractor.extract_relations(parse_result.content, entities)
        else:
            # Offline mode: create claims from paragraphs
            claims = self._extract_offline(parse_result, source_uuid)
            entities = []
            relations = []

        return ExtractionResult(
            claims=claims,
            entities=entities,
            relations=relations,
            metadata=metadata,
        )

    def _extract_offline(self, parse_result: PDFParseResult, source_uuid: str) -> list[Claim]:
        """Extract basic claims in offline mode (no LLM).

        Creates claims from paragraphs extracted from PDF.
        """
        claims: list[Claim] = []

        # Split content into paragraphs
        paragraphs = [p.strip() for p in parse_result.content.split("\n\n") if p.strip()]

        for para in paragraphs[:20]:  # Limit to first 20 paragraphs
            if len(para) > 50:  # Only significant paragraphs
                claim = Claim(
                    uuid=str(uuid.uuid4()),
                    content=para,
                    source_uuid=source_uuid,
                    content_hash=Claim.compute_hash(para),
                    tags=["pdf_paragraph", parse_result.parser],
                )
                claims.append(claim)

        return claims