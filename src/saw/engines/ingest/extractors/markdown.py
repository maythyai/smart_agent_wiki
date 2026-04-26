"""Markdown extractor for ingestion engine.

Per INGE-01: Markdown file ingestion with LLM extraction.
Per D-08: Structured path routing for Markdown files.
Per D-22: Three-tier degradation (offline mode without LLM).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from saw.adapters.llm.router import LLMRouter
from saw.adapters.parsers.markdown_parser import MarkdownParser, MarkdownParseResult
from saw.domain.claims import Claim
from saw.domain.entities import Entity, EntityRelation
from saw.engines.ingest.extractors.llm_extract import LLMExtractor


@dataclass
class ExtractionResult:
    """Result of extracting from a document."""
    claims: list[Claim]
    entities: list[Entity]
    relations: list[EntityRelation]
    metadata: dict


class MarkdownExtractor:
    """Extract claims, entities, and relations from Markdown files."""

    def __init__(
        self,
        parser: MarkdownParser,
        llm: LLMRouter | None,
    ) -> None:
        self._parser = parser
        self._llm = llm

    def extract(self, file_path: Path, source_uuid: str) -> ExtractionResult:
        """Extract from a Markdown file.

        Args:
            file_path: Path to the markdown file.
            source_uuid: UUID of the source document in Vault.

        Returns:
            ExtractionResult with claims, entities, relations, and metadata.
        """
        # Parse markdown
        parse_result = self._parser.parse(file_path)

        # Metadata from frontmatter
        metadata = {
            "title": parse_result.title,
            "tags": parse_result.frontmatter.get("tags", []),
            "date": parse_result.frontmatter.get("date", ""),
            "source_file": str(file_path),
            "headings_count": len(parse_result.headings),
        }

        # Extract claims
        if self._llm:
            # LLM-based extraction
            llm_extractor = LLMExtractor(self._llm)
            claims = llm_extractor.extract_claims(parse_result.content, source_uuid)
            entities = llm_extractor.extract_entities(parse_result.content)
            relations = llm_extractor.extract_relations(parse_result.content, entities)
        else:
            # Offline mode: create basic claims from headings and paragraphs
            claims = self._extract_offline(parse_result, source_uuid)
            entities = self._extract_entities_from_headings(parse_result)
            relations = []

        return ExtractionResult(
            claims=claims,
            entities=entities,
            relations=relations,
            metadata=metadata,
        )

    def _extract_offline(self, parse_result: MarkdownParseResult, source_uuid: str) -> list[Claim]:
        """Extract basic claims in offline mode (no LLM).

        Creates claims from headings (as topic markers) and paragraphs.
        """
        claims: list[Claim] = []

        # Create claims from significant headings
        for heading in parse_result.headings:
            if heading.level <= 3:  # Only h1-h3
                claim = Claim(
                    uuid=str(uuid.uuid4()),
                    content=f"Topic: {heading.text}",
                    source_uuid=source_uuid,
                    content_hash=Claim.compute_hash(f"Topic: {heading.text}"),
                    tags=["heading", f"h{heading.level}"],
                )
                claims.append(claim)

        # Create claims from paragraphs (text blocks between headings)
        paragraphs = [p.strip() for p in parse_result.content.split("\n\n") if p.strip()]
        for para in paragraphs[:10]:  # Limit to first 10 paragraphs
            if len(para) > 50:  # Only significant paragraphs
                claim = Claim(
                    uuid=str(uuid.uuid4()),
                    content=para,
                    source_uuid=source_uuid,
                    content_hash=Claim.compute_hash(para),
                    tags=["paragraph"],
                )
                claims.append(claim)

        return claims

    def _extract_entities_from_headings(self, parse_result: MarkdownParseResult) -> list[Entity]:
        """Extract entities from heading text (offline heuristic)."""
        entities: list[Entity] = []
        seen_names: set[str] = set()

        for heading in parse_result.headings:
            # Each heading could be an entity
            name = heading.text.strip()
            if name and name not in seen_names and len(name) > 2:
                seen_names.add(name)
                entity = Entity(
                    uuid=str(uuid.uuid4()),
                    name=name,
                    entity_type="topic",
                )
                entities.append(entity)

        return entities