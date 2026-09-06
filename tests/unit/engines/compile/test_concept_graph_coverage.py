"""T-F-R-4: concept_graph.py coverage tests (coverage ratchet 65→67).

Tests the ConceptGraphEngine relation management, navigation, inference,
and persistence to raise coverage from 20%.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.domain.concept import (
    ConceptNode,
    ConceptRelation,
    ConceptRelationType,
    KnowledgeStability,
)
from saw.engines.compile.concept_graph import ConceptGraphEngine


def _make_graph(tmp_path: Path) -> ConceptGraphEngine:
    """Create a ConceptGraphEngine with a fresh DB path."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    db = tmp_path / "concepts.json"
    return ConceptGraphEngine(wiki_root=wiki, db_path=db)


# ── Relation management ───────────────────────────────────────────────

def test_add_relation_creates_nodes(tmp_path):
    """add_relation creates nodes for source and target."""
    graph = _make_graph(tmp_path)
    rel = ConceptRelation(
        source="alpha", target="beta",
        relation_type=ConceptRelationType.RELATED_TO,
    )
    assert graph.add_relation(rel) is True
    assert "alpha" in graph._nodes
    assert "beta" in graph._nodes


def test_add_relation_duplicate_returns_false(tmp_path):
    """Adding the same relation twice returns False."""
    graph = _make_graph(tmp_path)
    rel = ConceptRelation(
        source="alpha", target="beta",
        relation_type=ConceptRelationType.RELATED_TO,
    )
    assert graph.add_relation(rel) is True
    assert graph.add_relation(rel) is False


def test_remove_relation(tmp_path):
    """remove_relation removes and returns True; returns False if not found."""
    graph = _make_graph(tmp_path)
    rel = ConceptRelation(
        source="alpha", target="beta",
        relation_type=ConceptRelationType.RELATED_TO,
    )
    graph.add_relation(rel)
    assert graph.remove_relation("alpha", "beta", ConceptRelationType.RELATED_TO) is True
    assert graph.remove_relation("alpha", "beta", ConceptRelationType.RELATED_TO) is False


def test_get_relations_filtered(tmp_path):
    """get_relations filters by node and type."""
    graph = _make_graph(tmp_path)
    graph.add_relation(ConceptRelation(
        source="a", target="b",
        relation_type=ConceptRelationType.RELATED_TO,
    ))
    graph.add_relation(ConceptRelation(
        source="a", target="c",
        relation_type=ConceptRelationType.DEPENDS_ON,
    ))
    # Filter by node
    assert len(graph.get_relations(node="a")) == 2
    assert len(graph.get_relations(node="b")) == 1
    # Filter by type
    deps = graph.get_relations(relation_type=ConceptRelationType.DEPENDS_ON)
    assert len(deps) == 1
    assert deps[0].target == "c"


# ── Concept management ────────────────────────────────────────────────

def test_get_concept_nonexistent(tmp_path):
    """get_concept returns None for non-existent concept."""
    graph = _make_graph(tmp_path)
    assert graph.get_concept("nonexistent") is None


def test_get_concept_with_relations(tmp_path):
    """get_concept returns node with incoming/outgoing relations."""
    graph = _make_graph(tmp_path)
    graph.add_relation(ConceptRelation(
        source="alpha", target="beta",
        relation_type=ConceptRelationType.RELATED_TO,
    ))
    graph.add_relation(ConceptRelation(
        source="gamma", target="alpha",
        relation_type=ConceptRelationType.DEPENDS_ON,
    ))
    node = graph.get_concept("alpha")
    assert node is not None
    assert len(node.relations_out) == 1  # alpha→beta
    assert len(node.relations_in) == 1   # gamma→alpha


def test_list_concepts(tmp_path):
    """list_concepts returns all nodes."""
    graph = _make_graph(tmp_path)
    graph.add_relation(ConceptRelation(
        source="a", target="b",
        relation_type=ConceptRelationType.RELATED_TO,
    ))
    concepts = graph.list_concepts()
    assert len(concepts) >= 2


def test_create_concept(tmp_path):
    """create_concept creates a new node."""
    graph = _make_graph(tmp_path)
    node = graph.create_concept("test", definition="test def")
    assert node.name == "test"
    assert node.definition == "test def"
    # Retrieve
    found = graph.get_concept("test")
    assert found is not None


# ── Overview ──────────────────────────────────────────────────────────

def test_get_overview_empty(tmp_path):
    """get_overview on empty graph returns zeros."""
    graph = _make_graph(tmp_path)
    overview = graph.get_overview()
    assert overview.total_concepts == 0
    assert overview.total_relations == 0


def test_get_overview_with_data(tmp_path):
    """get_overview returns correct counts."""
    graph = _make_graph(tmp_path)
    graph.create_concept("a", wiki_page="concepts/a.md")
    graph.add_relation(ConceptRelation(
        source="a", target="b",
        relation_type=ConceptRelationType.RELATED_TO,
    ))
    overview = graph.get_overview()
    assert overview.total_concepts >= 2
    assert overview.total_relations >= 1
    assert "related_to" in overview.relation_type_distribution
    assert "concepts" in overview.topics


# ── Navigation ────────────────────────────────────────────────────────

def test_navigate_simple(tmp_path):
    """navigate traverses from start node."""
    graph = _make_graph(tmp_path)
    graph.add_relation(ConceptRelation(
        source="a", target="b",
        relation_type=ConceptRelationType.RELATED_TO,
    ))
    graph.add_relation(ConceptRelation(
        source="b", target="c",
        relation_type=ConceptRelationType.RELATED_TO,
    ))
    result = graph.navigate("a", depth=2)
    assert result.start == "a"
    assert len(result.nodes_visited) >= 1
    assert len(result.relations_traversed) >= 1


def test_navigate_nonexistent_start(tmp_path):
    """navigate from non-existent node returns empty result."""
    graph = _make_graph(tmp_path)
    result = graph.navigate("nonexistent")
    assert result.start == "nonexistent"
    assert len(result.nodes_visited) == 0


def test_navigate_with_type_filter(tmp_path):
    """navigate filters by relation type."""
    graph = _make_graph(tmp_path)
    graph.add_relation(ConceptRelation(
        source="a", target="b",
        relation_type=ConceptRelationType.RELATED_TO,
    ))
    graph.add_relation(ConceptRelation(
        source="a", target="c",
        relation_type=ConceptRelationType.DEPENDS_ON,
    ))
    result = graph.navigate("a", relation_types=[ConceptRelationType.RELATED_TO])
    # Should only traverse RELATED_TO relations (a→b)
    assert all(r.relation_type == ConceptRelationType.RELATED_TO
               for r in result.relations_traversed)


# ── Inference ─────────────────────────────────────────────────────────

def test_infer_relations_wiki_links(tmp_path):
    """infer_relations_from_page finds wiki-link RELATED_TO."""
    graph = _make_graph(tmp_path)
    relations = graph.infer_relations_from_page(
        "alpha.md", "# Alpha\n\nSee [[beta]] for details.\n"
    )
    assert any(r.target == "beta" for r in relations)
    assert all(r.relation_type == ConceptRelationType.RELATED_TO
               for r in relations if r.target == "beta")


def test_infer_relations_dependency(tmp_path):
    """infer_relations_from_page finds DEPENDS_ON from 'uses' keyword."""
    graph = _make_graph(tmp_path)
    relations = graph.infer_relations_from_page(
        "alpha.md", "# Alpha\n\nAlpha uses external_lib for processing.\n"
    )
    deps = [r for r in relations if r.relation_type == ConceptRelationType.DEPENDS_ON]
    assert len(deps) >= 1
    assert deps[0].target == "external_lib"


def test_infer_relations_topic_membership(tmp_path):
    """infer_relations_from_page adds BELONGS_TO_TOPIC for topic/page.md."""
    graph = _make_graph(tmp_path)
    relations = graph.infer_relations_from_page(
        "concepts/ml.md", "# ML\n\n[[neural_networks]]\n"
    )
    topic_rels = [r for r in relations if r.relation_type == ConceptRelationType.BELONGS_TO_TOPIC]
    assert len(topic_rels) >= 1
    assert topic_rels[0].target == "concepts"


def test_infer_relations_no_self_reference(tmp_path):
    """infer_relations_from_page does not create self-reference."""
    graph = _make_graph(tmp_path)
    relations = graph.infer_relations_from_page(
        "alpha.md", "# Alpha\n\n[[alpha]]\n"
    )
    # Self-reference to "alpha" should be filtered out for RELATED_TO
    related = [r for r in relations if r.relation_type == ConceptRelationType.RELATED_TO]
    assert all(r.target != "alpha" for r in related)


# ── Rebuild from wiki ─────────────────────────────────────────────────

def test_rebuild_from_wiki_empty(tmp_path):
    """rebuild_from_wiki on non-existent wiki returns 0."""
    graph = ConceptGraphEngine(
        wiki_root=tmp_path / "nonexistent",
        db_path=tmp_path / "concepts.json",
    )
    assert graph.rebuild_from_wiki() == 0


def test_rebuild_from_wiki_with_pages(tmp_path):
    """rebuild_from_wiki scans pages and infers relations."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "alpha.md").write_text("# Alpha\n\nSee [[beta]] for more.\n")
    (wiki / "beta.md").write_text("# Beta\n\n[[alpha]]\n")
    graph = ConceptGraphEngine(wiki_root=wiki, db_path=tmp_path / "concepts.json")
    count = graph.rebuild_from_wiki()
    assert count >= 2  # alpha→beta + beta→alpha


# ── Persistence ───────────────────────────────────────────────────────

def test_persistence_save_load(tmp_path):
    """Relations persist across save/load cycles."""
    db = tmp_path / "concepts.json"
    graph1 = ConceptGraphEngine(wiki_root=tmp_path / "wiki", db_path=db)
    graph1.add_relation(ConceptRelation(
        source="a", target="b",
        relation_type=ConceptRelationType.RELATED_TO,
    ))
    # DB file should exist
    assert db.exists()
    # New instance loads from DB
    graph2 = ConceptGraphEngine(wiki_root=tmp_path / "wiki", db_path=db)
    rels = graph2.get_relations()
    assert len(rels) >= 1
    assert any(r.source == "a" for r in rels)


def test_load_corrupt_json(tmp_path):
    """_load handles corrupt JSON gracefully."""
    db = tmp_path / "concepts.json"
    db.write_text("not valid json {{{", encoding="utf-8")
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    graph = ConceptGraphEngine(wiki_root=wiki, db_path=db)
    # Should not crash, should have empty state
    assert len(graph.get_relations()) == 0


# ── Ensure node ───────────────────────────────────────────────────────

def test_ensure_node(tmp_path):
    """_ensure_node creates a node if it doesn't exist."""
    graph = _make_graph(tmp_path)
    graph._ensure_node("newnode")
    assert "newnode" in graph._nodes
    # Idempotent
    graph._ensure_node("newnode")
    assert len(graph._nodes) == 1
