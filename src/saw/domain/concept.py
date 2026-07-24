"""Concept graph domain models.

Defines typed concept relations and knowledge stability classification
for the enhanced knowledge graph with product-level navigation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from saw.domain.utils import utcnow


class ConceptRelationType(str, Enum):
    """Typed relationship between concepts/entities."""

    # Structural relations
    IS_PART_OF = "is_part_of"
    DEPENDS_ON = "depends_on"
    IMPLEMENTS = "implements"

    # Semantic relations
    RELATED_TO = "related_to"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    SPECIALIZES = "specializes"

    # Navigation relations
    BELONGS_TO_TOPIC = "belongs_to"
    REFERENCES_CODE = "references_code"


class KnowledgeStability(str, Enum):
    """Knowledge stability classification.

    STABLE: High-level knowledge requiring strict evidence to update.
            Slow decay (half-life 90 days). AI cannot freely modify.
    FRESH:  Recent/transient knowledge. AI can freely update.
            Fast decay (half-life 14 days). Rolling updates allowed.
    """

    STABLE = "stable"
    FRESH = "fresh"


# Governance rules per stability level
STABILITY_RULES: dict[KnowledgeStability, dict] = {
    KnowledgeStability.STABLE: {
        "half_life_days": 90,
        "auto_update_allowed": False,
        "requires_cr": True,
        "decay_multiplier": 3.0,
    },
    KnowledgeStability.FRESH: {
        "half_life_days": 14,
        "auto_update_allowed": True,
        "requires_cr": False,
        "decay_multiplier": 1.0,
    },
}


@dataclass(frozen=True)
class ConceptRelation:
    """A typed relationship between two concept nodes."""

    source: str  # Source node identifier (page path or concept name)
    target: str  # Target node identifier
    relation_type: ConceptRelationType
    confidence: str = "medium"  # high | medium | low
    evidence: tuple[str, ...] = ()  # Source references supporting this relation
    created: datetime = field(default_factory=utcnow)

    @property
    def key(self) -> tuple[str, str, str]:
        """Unique key for deduplication."""
        return (self.source, self.target, self.relation_type.value)


@dataclass
class ConceptNode:
    """A concept node in the knowledge graph."""

    name: str
    definition: str = ""
    stability: KnowledgeStability = KnowledgeStability.FRESH
    wiki_page: Optional[str] = None  # Associated wiki page path
    code_entities: list[str] = field(default_factory=list)  # Related code paths
    relations_out: list[ConceptRelation] = field(default_factory=list)
    relations_in: list[ConceptRelation] = field(default_factory=list)

    @property
    def total_relations(self) -> int:
        return len(self.relations_out) + len(self.relations_in)


@dataclass
class GraphOverview:
    """Global topology overview for product-level navigation."""

    total_concepts: int = 0
    total_relations: int = 0
    topics: dict[str, int] = field(default_factory=dict)  # topic -> concept count
    relation_type_distribution: dict[str, int] = field(default_factory=dict)
    stability_distribution: dict[str, int] = field(default_factory=dict)
    densest_concepts: list[str] = field(default_factory=list)  # Most connected


@dataclass
class NavigationResult:
    """Result of graph navigation from a starting node."""

    start: str
    nodes_visited: list[ConceptNode] = field(default_factory=list)
    relations_traversed: list[ConceptRelation] = field(default_factory=list)
    depth_reached: int = 0
