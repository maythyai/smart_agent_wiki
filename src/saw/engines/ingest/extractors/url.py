"""URL extractor for ingestion engine.

Per INGE-03: URL ingestion with trafilatura content extraction.
Per D-22: Three-tier degradation (offline mode without LLM).
"""
from __future__ import annotations

import uuid

from saw.adapters.llm.router import LLMRouter
from saw.adapters.parsers.html_parser import HTMLParser, HTMLParseResult
from saw.domain.claims import Claim
from saw.engines.ingest.extractors.llm_extract import LLMExtractor
from saw.engines.ingest.extractors.markdown import ExtractionResult


class URLExtractor:
    """Extract claims, entities, and relations from URLs."""

    def __init__(
        self,
        parser: HTMLParser,
        llm: LLMRouter | None,
    ) -> None:
        self._parser = parser
        self._llm = llm

    def extract(self, url: str, source_uuid: str) -> ExtractionResult:
        """Extract from a URL.

        Args:
            url: URL to extract from.
            source_uuid: UUID of the source document in Vault.

        Returns:
            ExtractionResult with claims, entities, relations, and metadata.
        """
        # Parse HTML
        parse_result = self._parser.parse(url)

        # Metadata
        metadata = {
            "title": parse_result.title,
            "url": parse_result.url,
            "format": parse_result.format,
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

    def _extract_offline(self, parse_result: HTMLParseResult, source_uuid: str) -> list[Claim]:
        """Extract basic claims in offline mode (no LLM)."""
        claims: list[Claim] = []

        paragraphs = [p.strip() for p in parse_result.content.split("\n\n") if p.strip()]

        for para in paragraphs[:15]:  # Limit to first 15 paragraphs
            if len(para) > 50:
                claim = Claim(
                    uuid=str(uuid.uuid4()),
                    content=para,
                    source_uuid=source_uuid,
                    content_hash=Claim.compute_hash(para),
                    tags=["url_paragraph"],
                )
                claims.append(claim)

        return claims