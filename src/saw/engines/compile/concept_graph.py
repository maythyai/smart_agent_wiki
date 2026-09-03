"""Concept graph engine.

Provides typed concept relations, product-level navigation,
and Stable/Fresh knowledge governance for the knowledge graph.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from saw.domain.concept import (
    ConceptNode,
    ConceptRelation,
    ConceptRelationType,
    GraphOverview,
    KnowledgeStability,
    NavigationResult,
)

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")

# Patterns that imply DEPENDS_ON relations
DEPENDENCY_PATTERNS = re.compile(
    r"(?:depends on|requires|based on|uses|imports)\s+[`'\"]?(\w[\w.-]*)",
    re.IGNORECASE,
)


class ConceptGraphEngine:
    """Typed concept graph with product-level navigation.

    Extends the existing wiki-link-based graph with:
    - Typed edges (DEPENDS_ON, IMPLEMENTS, IS_PART_OF, etc.)
    - Stable/Fresh knowledge classification
    - Two-level navigation (overview → concept detail)
    - Automatic relation inference from page content
    """

    def __init__(self, wiki_root: Path, db_path: Optional[Path] = None) -> None:
        self._wiki_root = wiki_root
        self._db_path = db_path or (wiki_root.parent / ".saw" / "concepts.json")
        self._relations: list[ConceptRelation] = []
        self._nodes: dict[str, ConceptNode] = {}
        self._load()

    def _load(self) -> None:
        """Load concept graph from persistent storage."""
        if self._db_path.exists():
            try:
                data = json.loads(self._db_path.read_text(encoding="utf-8"))
                self._relations = [
                    ConceptRelation(
                        source=r["source"],
                        target=r["target"],
                        relation_type=ConceptRelationType(r["relation_type"]),
                        confidence=r.get("confidence", "medium"),
                        evidence=tuple(r.get("evidence", [])),
                    )
                    for r in data.get("relations", [])
                ]
                for n in data.get("nodes", []):
                    node = ConceptNode(
                        name=n["name"],
                        definition=n.get("definition", ""),
                        stability=KnowledgeStability(n.get("stability", "fresh")),
                        wiki_page=n.get("wiki_page"),
                        code_entities=n.get("code_entities", []),
                    )
                    self._nodes[node.name] = node
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    def _save(self) -> None:
        """Persist concept graph to storage."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "relations": [
                {
                    "source": r.source,
                    "target": r.target,
                    "relation_type": r.relation_type.value,
                    "confidence": r.confidence,
                    "evidence": list(r.evidence),
                }
                for r in self._relations
            ],
            "nodes": [
                {
                    "name": n.name,
                    "definition": n.definition,
                    "stability": n.stability.value,
                    "wiki_page": n.wiki_page,
                    "code_entities": n.code_entities,
                }
                for n in self._nodes.values()
            ],
        }
        self._db_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ─── Relation management ───────────────────────────────────────────

    def add_relation(self, relation: ConceptRelation) -> bool:
        """Add a typed relation. Returns False if duplicate."""
        if relation.key in {r.key for r in self._relations}:
            return False
        self._relations.append(relation)
        # Ensure nodes exist
        self._ensure_node(relation.source)
        self._ensure_node(relation.target)
        self._save()
        return True

    def remove_relation(
        self, source: str, target: str, relation_type: ConceptRelationType
    ) -> bool:
        """Remove a specific relation (does not delete nodes)."""
        key = (source, target, relation_type.value)
        original_len = len(self._relations)
        self._relations = [r for r in self._relations if r.key != key]
        if len(self._relations) < original_len:
            self._save()
            return True
        return False

    def get_relations(
        self,
        node: Optional[str] = None,
        relation_type: Optional[ConceptRelationType] = None,
    ) -> list[ConceptRelation]:
        """Get relations, optionally filtered by node or type."""
        results = self._relations
        if node:
            results = [r for r in results if r.source == node or r.target == node]
        if relation_type:
            results = [r for r in results if r.relation_type == relation_type]
        return results

    # ─── Concept management ────────────────────────────────────────────

    def get_concept(self, name: str) -> Optional[ConceptNode]:
        """Get concept detail with all relations."""
        node = self._nodes.get(name)
        if not node:
            return None
        # Attach relations
        node.relations_out = [r for r in self._relations if r.source == name]
        node.relations_in = [r for r in self._relations if r.target == name]
        return node

    def list_concepts(self) -> list[ConceptNode]:
        """List all concept nodes."""
        return list(self._nodes.values())

    def create_concept(
        self,
        name: str,
        definition: str = "",
        stability: KnowledgeStability = KnowledgeStability.FRESH,
        wiki_page: Optional[str] = None,
    ) -> ConceptNode:
        """Create or update a concept node."""
        node = ConceptNode(
            name=name,
            definition=definition,
            stability=stability,
            wiki_page=wiki_page,
        )
        self._nodes[name] = node
        self._save()
        return node

    # ─── Navigation ────────────────────────────────────────────────────

    def get_overview(self) -> GraphOverview:
        """Get global topology overview."""
        overview = GraphOverview(
            total_concepts=len(self._nodes),
            total_relations=len(self._relations),
        )

        # Topic distribution
        for node in self._nodes.values():
            if node.wiki_page:
                topic = node.wiki_page.split("/")[0] if "/" in node.wiki_page else "root"
                overview.topics[topic] = overview.topics.get(topic, 0) + 1

        # Relation type distribution
        for rel in self._relations:
            key = rel.relation_type.value
            overview.relation_type_distribution[key] = (
                overview.relation_type_distribution.get(key, 0) + 1
            )

        # Stability distribution
        for node in self._nodes.values():
            key = node.stability.value
            overview.stability_distribution[key] = (
                overview.stability_distribution.get(key, 0) + 1
            )

        # Densest concepts (most connected)
        connection_count: dict[str, int] = {}
        for rel in self._relations:
            connection_count[rel.source] = connection_count.get(rel.source, 0) + 1
            connection_count[rel.target] = connection_count.get(rel.target, 0) + 1
        overview.densest_concepts = sorted(
            connection_count, key=connection_count.get, reverse=True
        )[:10]

        return overview

    def navigate(
        self,
        start: str,
        relation_types: Optional[list[ConceptRelationType]] = None,
        depth: int = 2,
    ) -> NavigationResult:
        """Navigate from a starting node along specified relation types."""
        result = NavigationResult(start=start)
        visited: set[str] = set()
        frontier: list[tuple[str, int]] = [(start, 0)]

        while frontier:
            node_name, current_depth = frontier.pop(0)
            if node_name in visited or current_depth > depth:
                continue
            visited.add(node_name)

            node = self.get_concept(node_name)
            if node:
                result.nodes_visited.append(node)

            if current_depth < depth:
                # Find outgoing relations
                for rel in self._relations:
                    if rel.source == node_name:
                        if relation_types is None or rel.relation_type in relation_types:
                            result.relations_traversed.append(rel)
                            if rel.target not in visited:
                                frontier.append((rel.target, current_depth + 1))
                    elif rel.target == node_name:
                        if relation_types is None or rel.relation_type in relation_types:
                            result.relations_traversed.append(rel)
                            if rel.source not in visited:
                                frontier.append((rel.source, current_depth + 1))

        result.depth_reached = depth
        return result

    # ─── Inference ─────────────────────────────────────────────────────

    def infer_relations_from_page(self, page_path: str, content: str) -> list[ConceptRelation]:
        """Infer typed relations from page content."""
        inferred = []
        page_slug = page_path.removesuffix(".md")

        # Wiki links → RELATED_TO
        for match in WIKILINK_PATTERN.finditer(content):
            target = match.group(1)
            if target != page_slug:
                inferred.append(ConceptRelation(
                    source=page_slug,
                    target=target,
                    relation_type=ConceptRelationType.RELATED_TO,
                    confidence="medium",
                    evidence=(page_path,),
                ))

        # Dependency patterns → DEPENDS_ON
        for match in DEPENDENCY_PATTERNS.finditer(content):
            target = match.group(1)
            if target.lower() != page_slug.split("/")[-1]:
                inferred.append(ConceptRelation(
                    source=page_slug,
                    target=target,
                    relation_type=ConceptRelationType.DEPENDS_ON,
                    confidence="low",
                    evidence=(page_path,),
                ))

        # Topic membership → BELONGS_TO_TOPIC
        if "/" in page_path:
            topic = page_path.split("/")[0]
            inferred.append(ConceptRelation(
                source=page_slug,
                target=topic,
                relation_type=ConceptRelationType.BELONGS_TO_TOPIC,
                confidence="high",
                evidence=(page_path,),
            ))

        return inferred

    def rebuild_from_wiki(self) -> int:
        """Rebuild all relations by scanning wiki pages. Returns count of new relations."""
        if not self._wiki_root.exists():
            return 0

        new_count = 0
        for page_file in self._wiki_root.rglob("*.md"):
            rel = str(page_file.relative_to(self._wiki_root))
            if rel in ("index.md", "log.md"):
                continue
            content = page_file.read_text(encoding="utf-8")
            inferred = self.infer_relations_from_page(rel, content)
            for relation in inferred:
                if self.add_relation(relation):
                    new_count += 1

        return new_count

    # ─── Helpers ───────────────────────────────────────────────────────

    def _ensure_node(self, name: str) -> None:
        """Ensure a node exists in the graph."""
        if name not in self._nodes:
            self._nodes[name] = ConceptNode(name=name)
