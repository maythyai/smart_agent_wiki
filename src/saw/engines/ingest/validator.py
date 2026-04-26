"""Claim validator for field-level validation.

Per D-04: Validate required fields and dedup.
"""
from __future__ import annotations

from dataclasses import dataclass

from saw.domain.claims import Claim
from saw.domain.entities import Entity, EntityRelation


@dataclass
class ValidationResult:
    """Result of validating claims, entities, and relations."""
    valid_claims: list[Claim]
    valid_entities: list[Entity]
    valid_relations: list[EntityRelation]
    errors: list[str]


class Validator:
    """Validate claims, entities, and relations before storage."""

    def validate(
        self,
        claims: list[Claim],
        entities: list[Entity],
        relations: list[EntityRelation],
    ) -> ValidationResult:
        """Validate all extracted data.

        Args:
            claims: Claims to validate.
            entities: Entities to validate.
            relations: Relations to validate.

        Returns:
            ValidationResult with valid items and errors.
        """
        errors: list[str] = []
        valid_claims: list[Claim] = []
        valid_entities: list[Entity] = []
        valid_relations: list[EntityRelation] = []

        # Dedup claims by content_hash (per D-04)
        seen_hashes: set[str] = set()
        for claim in claims:
            if claim.content_hash in seen_hashes:
                errors.append(f"Duplicate claim by hash: {claim.uuid}")
                continue
            seen_hashes.add(claim.content_hash)

            # Validate required fields
            if not claim.content:
                errors.append(f"Claim {claim.uuid} has empty content")
                continue
            if not claim.source_uuid:
                errors.append(f"Claim {claim.uuid} missing source_uuid")
                continue

            valid_claims.append(claim)

        # Validate entities
        seen_entity_names: set[str] = set()
        for entity in entities:
            if not entity.name:
                errors.append(f"Entity {entity.uuid} has empty name")
                continue
            if not entity.entity_type:
                errors.append(f"Entity {entity.uuid} missing entity_type")
                continue
            if entity.name in seen_entity_names:
                continue  # Skip duplicate entity names
            seen_entity_names.add(entity.name)

            valid_entities.append(entity)

        # Validate relations
        entity_uuids = {e.uuid for e in valid_entities}
        for relation in relations:
            if not relation.source_uuid:
                errors.append("Relation missing source_uuid")
                continue
            if not relation.target_uuid:
                errors.append("Relation missing target_uuid")
                continue
            if relation.source_uuid not in entity_uuids:
                errors.append(f"Relation source_uuid {relation.source_uuid} not in entities")
                continue
            if relation.target_uuid not in entity_uuids:
                errors.append(f"Relation target_uuid {relation.target_uuid} not in entities")
                continue

            valid_relations.append(relation)

        return ValidationResult(
            valid_claims=valid_claims,
            valid_entities=valid_entities,
            valid_relations=valid_relations,
            errors=errors,
        )