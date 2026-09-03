"""Query submodule coverage tests — T-F-Z-9 (AC-COV-1).

Adds tests for previously-uncovered query modules: cache, wiki_links,
related_pages, wiki_graph. Raises query-submodule coverage toward the
north-star and supports the project coverage ratchet (60→65).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from saw.domain.wiki import WikiPage
from saw.domain.value_objects import ConfidenceLevel, PageType


# ── cache.py ─────────────────────────────────────────────────────────

def test_cache_set_get_hit_and_miss():
    from saw.engines.query.cache import QueryCache

    c = QueryCache(max_size=4, default_ttl=60)
    assert c.get("q", {"limit": 5}) is None  # miss
    c.set("q", {"limit": 5}, {"answer": "hi"})
    assert c.get("q", {"limit": 5}) == {"answer": "hi"}  # hit
    assert c.get("q", {"limit": 99}) is None  # different params = miss


def test_cache_lru_eviction_and_stats():
    from saw.engines.query.cache import QueryCache

    c = QueryCache(max_size=2, default_ttl=60)
    c.set("a", {}, 1); c.set("b", {}, 2); c.set("c", {}, 3)  # evicts 'a'
    assert c.get("a", {}) is None
    assert c.get("b", {}) == 2
    stats = c.stats()
    assert stats["size"] == 2
    assert stats["hits"] >= 1 and stats["misses"] >= 1


def test_cache_ttl_expiry():
    from datetime import datetime, timedelta

    from saw.engines.query.cache import QueryCache

    c = QueryCache(default_ttl=60)
    c.set("q", {}, "v")
    # Force the stored expiry into the past to exercise the expiry branch
    # without a real-time sleep (deterministic).
    key = c._make_key("q", {})
    result, _ = c._cache[key]
    c._cache[key] = (result, datetime.now() - timedelta(seconds=1))
    assert c.get("q", {}) is None  # expired → evicted


def test_cache_invalidate_and_clear():
    from saw.engines.query.cache import QueryCache

    c = QueryCache()
    c.set("q", {"x": 1}, "v")
    c.invalidate("q", {"x": 1})
    assert c.get("q", {"x": 1}) is None
    c.set("q2", {}, "v2")
    c.clear()
    assert c.get("q2", {}) is None
    assert c.stats()["size"] == 0


# ── wiki_links.py ───────────────────────────────────────────────────

def test_parse_wiki_links_variants():
    from saw.engines.query.wiki_links import parse_wiki_links

    links = parse_wiki_links(
        "See [[Python]] and [[Rust|the Rust lang]] and [[Go#basics|go basics]]"
    )
    targets = [l.target for l in links]
    assert "python" in targets
    assert "rust" in targets
    assert "go" in targets
    rust = next(l for l in links if l.target == "rust")
    assert rust.alias == "the Rust lang"
    go = next(l for l in links if l.target == "go")
    assert go.section == "basics"


def test_slugify_and_unique_targets():
    from saw.engines.query.wiki_links import slugify, extract_unique_targets

    assert slugify("Hello, World!") == "hello-world"
    assert extract_unique_targets("[[a]] [[b]] [[a]]") == {"a", "b"}


# ── related_pages.py ────────────────────────────────────────────────

def _page(slug, title, tags=(), links="", page_type=PageType.SUMMARY):
    return WikiPage(
        path=slug,
        title=title,
        page_type=page_type,
        tags=list(tags),
        confidence=ConfidenceLevel.UNVERIFIED,
        content=links,
    )


def test_related_pages_by_shared_tags_and_links():
    from saw.engines.query.related_pages import compute_related_pages

    wiki = MagicMock()
    pages = {
        "alpha": _page("alpha", "Alpha", tags=["ml"], links="See [[beta]]"),
        "beta": _page("beta", "Beta", tags=["ml"], links="See [[alpha]]"),
        # gamma: different type + no shared tags/links → score 0 → excluded
        "gamma": _page("gamma", "Gamma", tags=["unrelated"], page_type=PageType.COLLECTION),
    }
    wiki.read.side_effect = lambda s: pages.get(s)
    wiki.list_pages.return_value = list(pages.keys())

    related = compute_related_pages("alpha", wiki)
    slugs = [r["slug"] for r in related]
    assert "beta" in slugs
    assert "gamma" not in slugs  # no shared signal (different type too)
    beta = next(r for r in related if r["slug"] == "beta")
    assert beta["score"] > 0
    assert any("shared tags" in x for x in beta["reasons"])


def test_related_pages_missing_page_returns_empty():
    from saw.engines.query.related_pages import compute_related_pages

    wiki = MagicMock()
    wiki.read.return_value = None
    assert compute_related_pages("nope", wiki) == []
    assert compute_related_pages("nope", None) == []


# ── wiki_graph.py ───────────────────────────────────────────────────

def test_wiki_graph_build_nodes_and_edges():
    from saw.engines.query.wiki_graph import WikiGraphBuilder

    wiki = MagicMock()
    pages = {
        "alpha": _page("alpha", "Alpha", links="[[beta]]"),
        "beta": _page("beta", "Beta", links="[[alpha]]"),
        "orphan": _page("orphan", "Orphan", links="[[missing]]"),
    }
    wiki.read.side_effect = lambda s: pages.get(s)
    wiki.list_pages.return_value = list(pages.keys())

    builder = WikiGraphBuilder(wiki)
    nodes, edges = builder.build()
    node_ids = {n.id for n in nodes}
    assert {"alpha", "beta", "orphan"} <= node_ids
    # edges only between existing pages; 'missing' target has no page → no edge
    assert all(e.type == "wiki_link" for e in edges)
    assert any(e.source == "alpha" and e.target == "beta" for e in edges)
    assert not any(e.target == "missing" for e in edges)


def test_wiki_graph_subgraph_bfs():
    from saw.engines.query.wiki_graph import WikiGraphBuilder

    wiki = MagicMock()
    pages = {
        "root": _page("root", "Root", links="[[child]]"),
        "child": _page("child", "Child", links="[[root]]"),
    }
    wiki.read.side_effect = lambda s: pages.get(s)
    wiki.list_pages.return_value = list(pages.keys())

    builder = WikiGraphBuilder(wiki)
    nodes, edges = builder.build_subgraph("root", depth=2)
    assert {n.id for n in nodes} == {"root", "child"}
    assert len(edges) >= 1
