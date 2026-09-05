"""Shared fixtures for compile/compiler tests (F-O-2)."""
from __future__ import annotations

import pytest
from pathlib import Path

from saw.engines.compile.compiler import WikiCompileEngine


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """Temporary vault directory seeded with 3 markdown source files."""
    (tmp_path / "concepts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "guides").mkdir(parents=True, exist_ok=True)
    (tmp_path / "faq").mkdir(parents=True, exist_ok=True)

    # Long content → HIGH confidence
    (tmp_path / "concepts" / "ml.md").write_text(
        "# Machine Learning\n\n"
        "Machine learning is a subset of artificial intelligence.\n\n"
        + "word " * 300
        + "\n\n[1] Reference link.\n",
        encoding="utf-8",
    )
    # Code-heavy → HOWTO
    (tmp_path / "guides" / "how-to-train.md").write_text(
        "# How to Train\n\n```python\nstep 1\n```\n" + "word " * 100,
        encoding="utf-8",
    )
    # Q&A → FAQ
    (tmp_path / "faq" / "what-is-ml.md").write_text(
        "# What is ML?\n\nQ: What is ML?\nA: It is a subset of AI.\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def engine(tmp_vault: Path) -> WikiCompileEngine:
    """WikiCompileEngine instance with no LLM (rule-based compile)."""
    return WikiCompileEngine(vault_root=tmp_vault)


@pytest.fixture
def engine_with_llm(tmp_vault: Path) -> WikiCompileEngine:
    """WikiCompileEngine instance with a mock LLM router."""
    from unittest.mock import MagicMock

    mock_llm = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = (
        "# Synthesized Title\n\n"
        "Overview paragraph about the topic.\n\n"
        "## Key Concepts\n\n"
        "- Point one\n- Point two\n- Point three\n\n"
        "## Details\n\n"
        "Detailed body text. " * 20
        + "\n\nSee also [[related-topic]].\n"
    )
    mock_llm.complete.return_value = response
    return WikiCompileEngine(vault_root=tmp_vault, llm_router=mock_llm)
