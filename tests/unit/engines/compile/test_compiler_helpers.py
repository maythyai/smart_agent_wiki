"""TC-COMP-05/06/07/11/17: scan / detect / assess / slugify / title tests."""
from __future__ import annotations

from pathlib import Path

from saw.domain.wiki_compile import WikiConfidence, WikiPageType
from saw.engines.compile.compiler import WikiCompileEngine


# ── TC-COMP-05: _scan_vault_sources excludes _wiki/.saw/.git ────────

def test_scan_vault_sources_excludes_wiki_dir(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    sources = engine._scan_vault_sources()
    # Should find the 3 source md files, NOT the _wiki/ dir
    assert len(sources) == 3
    for src in sources:
        rel = src.relative_to(tmp_vault)
        assert not rel.parts[0].startswith("_")
        assert rel.parts[0] not in ("_wiki", ".saw", ".git")


def test_scan_vault_sources_excludes_internal_files(tmp_vault: Path):
    """Vault-internal storage files (original.md, transcript.md, meta.yaml)
    should be excluded from compilation sources."""
    (tmp_vault / "doc1").mkdir(exist_ok=True)
    (tmp_vault / "doc1" / "original.md").write_text("# Original\n\nContent", encoding="utf-8")
    (tmp_vault / "doc1" / "transcript.md").write_text("# Transcript\n\nContent", encoding="utf-8")

    engine = WikiCompileEngine(vault_root=tmp_vault)
    sources = engine._scan_vault_sources()
    source_names = [s.name for s in sources]
    assert "original.md" not in source_names
    assert "transcript.md" not in source_names


# ── TC-COMP-06: _detect_page_type ────────────────────────────────────

def test_detect_page_type_faq(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    path = Path("faq/question.md")
    ptype = engine._detect_page_type(path, "Q: What is AI?\nA: It is...")
    assert ptype == WikiPageType.FAQ


def test_detect_page_type_howto(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    path = Path("guides/how-to-train.md")
    ptype = engine._detect_page_type(path, "```python\nstep 1\n```")
    assert ptype == WikiPageType.HOWTO


def test_detect_page_type_concept(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    path = Path("concepts/ml.md")
    ptype = engine._detect_page_type(path, "Machine learning is...")
    assert ptype == WikiPageType.CONCEPT


# ── TC-COMP-07: _assess_confidence ──────────────────────────────────

def test_assess_confidence_high(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    content = "word " * 600 + "\n[1] ref\n# Heading\n# Sub"
    conf = engine._assess_confidence(content)
    assert conf == WikiConfidence.HIGH


def test_assess_confidence_medium(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    content = "word " * 250 + "\n[1] ref\n"
    conf = engine._assess_confidence(content)
    assert conf == WikiConfidence.MEDIUM


def test_assess_confidence_low(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    content = "short text"
    conf = engine._assess_confidence(content)
    assert conf == WikiConfidence.LOW


# ── TC-COMP-11: _slugify ─────────────────────────────────────────────

def test_slugify_basic(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    assert engine._slugify("My Page!") == "my-page"


def test_slugify_spaces(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    assert engine._slugify("  hello world  ") == "hello-world"


def test_slugify_special_chars(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    assert engine._slugify("C++ & Python?") == "c-python"


def test_slugify_underscores(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    assert engine._slugify("my_awesome_page") == "my-awesome-page"


# ── TC-COMP-17: _extract_title ──────────────────────────────────────

def test_extract_title_from_h1(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    title = engine._extract_title("# My Title\n\nbody", "fallback")
    assert title == "My Title"


def test_extract_title_fallback(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    title = engine._extract_title("No heading here", "my-fallback-name")
    assert title == "My Fallback Name"


# ── _classify_sources_by_topic / _infer_topic / _ensure_topic_dirs ──

def test_classify_sources_by_topic(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    sources = engine._scan_vault_sources()
    topics = engine._classify_sources_by_topic(sources)
    assert "concepts" in topics
    assert "guides" in topics
    assert "faq" in topics


def test_infer_topic_from_dir(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    path = tmp_vault / "concepts" / "ml.md"
    topic = engine._infer_topic(path)
    assert topic == "concepts"


def test_infer_topic_fallback_general(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    # File at root level, no topic in filename
    path = tmp_vault / "random.md"
    topic = engine._infer_topic(path)
    assert topic == "general"


def test_ensure_topic_directories(tmp_vault: Path):
    engine = WikiCompileEngine(vault_root=tmp_vault)
    topics = {"concepts": [], "guides": []}
    engine._ensure_topic_directories(topics)
    assert (engine.wiki_root / "concepts").exists()
    assert (engine.wiki_root / "guides").exists()
