"""T-F-R-4: code_wiki.py coverage tests (coverage ratchet 65→67).

Tests the CodeWikiEngine generate(), status(), diff_since_last(),
and helper methods to raise coverage from 14%.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.domain.code_wiki import CodeWikiConfig
from saw.engines.compile.code_wiki import CodeWikiEngine


def _make_repo(tmp_path: Path) -> Path:
    """Create a small fake repo with source files."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "auth").mkdir()
    (repo / "auth" / "login.py").write_text(
        "def login(user, password):\n    return True\n"
        "\n\nclass AuthService:\n    pass\n",
        encoding="utf-8",
    )
    (repo / "models").mkdir()
    (repo / "models" / "user.py").write_text(
        "class User:\n    pass\n",
        encoding="utf-8",
    )
    return repo


@pytest.mark.asyncio
async def test_generate_creates_overview_and_module_pages(tmp_path):
    """generate() creates overview page + per-module pages."""
    wiki = tmp_path / "wiki"
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=wiki)

    result = await engine.generate(config)
    assert len(result.pages_generated) >= 1
    # Overview page
    overview = wiki / "code" / "README.md"
    assert overview.exists()
    # Module pages
    auth_page = wiki / "code" / "modules" / "auth.md"
    assert auth_page.exists()
    models_page = wiki / "code" / "modules" / "models.md"
    assert models_page.exists()


@pytest.mark.asyncio
async def test_generate_skip_if_exists(tmp_path):
    """skip_if_exists=True skips existing module pages."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo, skip_if_exists=True)
    engine = CodeWikiEngine(wiki_root=wiki)

    # First generate creates pages
    result1 = await engine.generate(config)
    # Second generate skips existing
    config2 = CodeWikiConfig(repo_path=repo, skip_if_exists=True)
    result2 = await engine.generate(config2)
    assert len(result2.pages_skipped) >= 1


@pytest.mark.asyncio
async def test_diff_since_last_no_status(tmp_path):
    """diff_since_last() returns [] when no .status file exists."""
    wiki = tmp_path / "wiki"
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=wiki)

    diff = await engine.diff_since_last(config)
    assert diff == []


@pytest.mark.asyncio
async def test_diff_since_last_same_commit(tmp_path):
    """diff_since_last() returns [] when commit unchanged."""
    wiki = tmp_path / "wiki"
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=wiki)

    await engine.generate(config)
    diff = await engine.diff_since_last(config)
    # No git repo → commit "unknown" → same → no diff
    assert diff == []


def test_get_commit_hash_no_git(tmp_path):
    """_get_commit_hash returns 'unknown' for non-git directory."""
    repo = tmp_path / "nogit"
    repo.mkdir()
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    assert engine._get_commit_hash(repo) == "unknown"


def test_scan_sources_finds_files(tmp_path):
    """_scan_sources finds .py files in repo."""
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    files = engine._scan_sources(config)
    assert len(files) >= 2
    assert any(f.name == "login.py" for f in files)
    assert any(f.name == "user.py" for f in files)


def test_scan_sources_excludes_patterns(tmp_path):
    """_scan_sources respects exclude_patterns."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "keep.py").write_text("x = 1\n")
    (repo / "node_modules").mkdir()
    (repo / "node_modules" / "exclude.py").write_text("x = 2\n")
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    files = engine._scan_sources(config)
    assert any(f.name == "keep.py" for f in files)
    assert not any(f.name == "exclude.py" for f in files)


def test_group_by_module(tmp_path):
    """_group_by_module groups files by top-level directory."""
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    files = engine._scan_sources(config)
    modules = engine._group_by_module(files, config)
    assert "auth" in modules
    assert "models" in modules
    assert len(modules["auth"]) == 1


def test_generate_overview(tmp_path):
    """_generate_overview produces a README.md page."""
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    files = engine._scan_sources(config)
    modules = engine._group_by_module(files, config)
    page = engine._generate_overview(config, modules)
    assert page.filename == "code/README.md"
    assert "repo" in page.title
    assert "auth" in page.content


def test_generate_module_page(tmp_path):
    """_generate_module_page produces a module page."""
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    files = engine._scan_sources(config)
    modules = engine._group_by_module(files, config)
    module_files = modules["auth"]
    page = engine._generate_module_page("auth", module_files, config)
    assert "auth" in page.filename
    assert "login" in page.content


def test_extract_key_symbols_finds_defs(tmp_path):
    """_extract_key_symbols finds class/def names from Python files."""
    repo = _make_repo(tmp_path)
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    files = engine._scan_sources(config)
    auth_files = [f for f in files if f.name == "login.py"]
    symbols = engine._extract_key_symbols(auth_files)
    assert "login" in symbols
    assert "AuthService" in symbols


def test_extract_key_symbols_empty(tmp_path):
    """_extract_key_symbols returns placeholder for no symbols."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "empty.py").write_text("# just a comment\n")
    config = CodeWikiConfig(repo_path=repo)
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    files = engine._scan_sources(config)
    result = engine._extract_key_symbols(files)
    assert "No key symbols" in result


def test_write_page_creates_file(tmp_path):
    """_write_page creates the file with metadata."""
    from saw.domain.code_wiki import CodeWikiPage
    wiki = tmp_path / "wiki"
    engine = CodeWikiEngine(wiki_root=wiki)
    page = CodeWikiPage(
        filename="code/modules/test.md",
        title="test",
        content="# Test\n\n",
        commit_hash="abc123",
    )
    engine._write_page(page)
    page_path = wiki / "code" / "modules" / "test.md"
    assert page_path.exists()
    content = page_path.read_text()
    assert "type: reference" in content
    assert "abc123" in content
    # Status file
    status = wiki / "code" / ".status"
    assert status.exists()


def test_code_graph_overview_section_no_graph(tmp_path):
    """_code_graph_overview_section returns '' when no code_graph attached."""
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    assert engine._code_graph_overview_section() == ""


def test_matches_pattern(tmp_path):
    """_matches_pattern correctly matches file paths."""
    engine = CodeWikiEngine(wiki_root=tmp_path / "wiki")
    # fnmatch: "bar.py" does NOT match "foo/bar.py" (full path)
    assert not engine._matches_pattern("foo/bar.py", "bar.py")
    # But glob does match same path
    assert engine._matches_pattern("foo/bar.py", "foo/bar.py")
    assert engine._matches_pattern("test.py", "test.py")
