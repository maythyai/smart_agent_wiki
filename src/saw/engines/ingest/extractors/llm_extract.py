"""LLM-based claim extraction via LiteLLM.

Per D-10: Single LLM extraction in Phase 1.
Per D-12: Claims output with source provenance.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import yaml

from saw.adapters.llm.router import LLMRouter
from saw.domain.claims import Claim
from saw.domain.entities import Entity, EntityRelation
from saw.domain.value_objects import SourceMark


class LLMExtractor:
    """Extract claims, entities, and relations from text using LLM."""

    def __init__(self, router: LLMRouter, prompts_dir: Path | None = None) -> None:
        self._router = router
        # Default prompts directory: resolve to the saw package root (4 levels
        # up from saw/engines/ingest/extractors/) then into adapters/llm/prompts.
        # This works for both the src/ layout and installed site-packages.
        if prompts_dir is None:
            prompts_dir = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "adapters" / "llm" / "prompts"
            )
        self._prompts_dir = prompts_dir

    def extract_claims(self, text: str, source_uuid: str) -> list[Claim]:
        """Extract claims from text using LLM.

        Args:
            text: Document content to extract from.
            source_uuid: UUID of the source document in Vault.

        Returns:
            List of Claim objects.
        """
        # Load system prompt
        system_prompt = self._load_extraction_prompt()

        # Call LLM
        result = self._router.extract_claims(text, system_prompt)

        # Parse JSON response into Claim objects
        claims: list[Claim] = []
        for claim_data in result.get("claims", []):
            if not isinstance(claim_data, dict):
                continue
            content = claim_data.get("content", "")
            # Skip claims without usable content
            if not isinstance(content, str) or not content.strip():
                continue
            claim = Claim(
                uuid=str(uuid.uuid4()),
                content=content,
                source_uuid=source_uuid,
                content_hash=Claim.compute_hash(content),
                source_mark=self._parse_source_mark(claim_data.get("source_mark", "extracted")),
                tags=claim_data.get("tags", []),
                entities=claim_data.get("entities", []),
            )
            claims.append(claim)

        return claims

    def extract_entities(self, text: str) -> list[Entity]:
        """Extract entities from text using LLM.

        Args:
            text: Document content to extract from.

        Returns:
            List of Entity objects.
        """
        system_prompt = self._load_extraction_prompt()
        result = self._router.extract_claims(text, system_prompt)

        entities: list[Entity] = []
        entity_names: set[str] = set()

        # Collect entities from all claims
        for claim_data in result.get("claims", []):
            if not isinstance(claim_data, dict):
                continue
            for entity_name in claim_data.get("entities", []):
                # Skip non-string / empty names (LLM output is not schema-guaranteed)
                if not isinstance(entity_name, str) or not entity_name.strip():
                    continue
                if entity_name not in entity_names:
                    entity_names.add(entity_name)
                    entity = Entity(
                        uuid=str(uuid.uuid4()),
                        name=entity_name,
                        entity_type=self._guess_entity_type(entity_name),
                        description="",
                    )
                    entities.append(entity)

        return entities

    def extract_relations(self, text: str, entities: list[Entity]) -> list[EntityRelation]:
        """Extract relations between entities from text using LLM.

        Args:
            text: Document content to extract from.
            entities: List of extracted entities.

        Returns:
            List of EntityRelation objects.
        """
        system_prompt = self._load_extraction_prompt()
        result = self._router.extract_claims(text, system_prompt)

        # Build entity name to UUID map
        entity_map = {e.name: e.uuid for e in entities}

        relations: list[EntityRelation] = []
        for claim_data in result.get("claims", []):
            for rel_data in claim_data.get("relations", []):
                if not isinstance(rel_data, dict):
                    continue
                source_name = rel_data.get("source", "")
                target_name = rel_data.get("target", "")

                # LLM output is not schema-guaranteed: skip relations whose
                # endpoints are not plain non-empty strings (e.g. lists).
                if not isinstance(source_name, str) or not isinstance(target_name, str):
                    continue
                if not source_name or not target_name:
                    continue

                # Only create relation if both entities exist
                source_uuid = entity_map.get(source_name)
                target_uuid = entity_map.get(target_name)

                if source_uuid and target_uuid:
                    relation = EntityRelation(
                        source_uuid=source_uuid,
                        target_uuid=target_uuid,
                        relation_type=rel_data.get("relation", "related_to"),
                    )
                    relations.append(relation)

        return relations

    def _load_extraction_prompt(self) -> str:
        """Load extraction system prompt from YAML file."""
        prompt_file = self._prompts_dir / "extraction.yaml"
        if prompt_file.exists():
            with open(prompt_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("system_prompt", "")
        # Fallback prompt
        return "Extract structured claims from the text."

    def _parse_source_mark(self, mark: str) -> SourceMark:
        """Parse source mark string to enum."""
        mark_lower = mark.lower()
        if mark_lower == "extracted":
            return SourceMark.EXTRACTED
        elif mark_lower == "inferred":
            return SourceMark.INFERRED
        elif mark_lower == "ambiguous":
            return SourceMark.AMBIGUOUS
        return SourceMark.EXTRACTED

    def _guess_entity_type(self, name: str) -> str:
        """Guess entity type from name (heuristic)."""
        # Simple heuristics for entity type
        if name.startswith(("http://", "https://", "www.")):
            return "website"
        if name.upper() == name and len(name) > 2:
            return "organization"
        if "." in name and not name.startswith(("http", "www")):
            return "technology"
        if " " in name:
            return "person"
        return "concept"