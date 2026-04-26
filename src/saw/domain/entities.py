"""Entity and relation domain models for the knowledge graph."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entity:
    """A named entity in the knowledge graph."""
    uuid: str
    name: str
    entity_type: str
    aliases: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class EntityRelation:
    """A directed, weighted edge between two entities."""
    source_uuid: str
    target_uuid: str
    relation_type: str
    weight: float = 1.0
