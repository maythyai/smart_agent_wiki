"""Unit tests for CJK-aware FTS tokenization."""
from __future__ import annotations

import pytest

from saw.adapters.storage.fts_tokenize import (
    build_match_query,
    has_cjk,
    tokenize_for_fts,
)


class TestHasCjk:
    def test_chinese(self) -> None:
        assert has_cjk("知识管理")

    def test_pure_latin(self) -> None:
        assert not has_cjk("machine learning")

    def test_mixed(self) -> None:
        assert has_cjk("Vault 存储架构")

    def test_empty(self) -> None:
        assert not has_cjk("")


class TestTokenizeForFts:
    def test_latin_passthrough(self) -> None:
        text = "Machine learning uses neural networks."
        assert tokenize_for_fts(text) == text

    def test_empty(self) -> None:
        assert tokenize_for_fts("") == ""

    def test_chinese_run_is_segmented(self) -> None:
        tokens = tokenize_for_fts("知识管理平台")
        # Segmented output must contain spaces (multiple tokens)
        assert " " in tokens
        # Every original character must still be present
        for ch in "知识管理平台":
            assert ch in tokens

    def test_mixed_text_keeps_latin_intact(self) -> None:
        tokens = tokenize_for_fts("Smart Agent Wiki 是知识平台")
        assert "Smart Agent Wiki" in tokens
        assert "知" in tokens

    def test_punctuation_splits_cjk_runs(self) -> None:
        tokens = tokenize_for_fts("知识编译，而非检索")
        # Comma is not a CJK char, so it separates runs
        assert "，" in tokens


class TestBuildMatchQuery:
    def test_empty(self) -> None:
        assert build_match_query("") == ""
        assert build_match_query("   ") == ""

    def test_latin_and_join(self) -> None:
        assert build_match_query("machine learning") == "machine learning"

    def test_special_chars_stripped(self) -> None:
        expr = build_match_query('neural (networks) "test"')
        assert "(" not in expr
        assert '"' not in expr

    def test_chinese_query_or_group(self) -> None:
        expr = build_match_query("知识编译")
        assert " OR " in expr
        assert expr.startswith("(") and expr.endswith(")")

    def test_mixed_query(self) -> None:
        expr = build_match_query("Vault 存储")
        assert "Vault" in expr
        assert " AND (" in expr  # explicit AND before the CJK group

    def test_single_char_chinese(self) -> None:
        expr = build_match_query("库")
        assert expr  # non-empty, queryable

    def test_fullwidth_punctuation_dropped(self) -> None:
        """Full-width ？！，。 must not become AND-joined search terms."""
        expr = build_match_query("这个平台的核心设计理念是什么？")
        assert "？" not in expr
        assert expr  # still queryable

    def test_question_mark_does_not_kill_recall(self) -> None:
        """A natural question ending in ？ must still match the document."""
        import sqlite3

        doc = "Smart Agent Wiki 是一个本地优先的知识管理平台。"
        indexed = tokenize_for_fts(doc)
        expr = build_match_query("这个平台的核心设计理念是什么？")

        conn = sqlite3.connect(":memory:")
        conn.execute(
            "CREATE VIRTUAL TABLE t USING fts5(body, tokenize='unicode61')"
        )
        conn.execute("INSERT INTO t (body) VALUES (?)", (indexed,))
        rows = conn.execute("SELECT * FROM t WHERE t MATCH ?", (expr,)).fetchall()
        assert len(rows) == 1

    def test_query_tokens_align_with_index(self) -> None:
        """Every query token must appear in the tokenized index text."""
        import sqlite3

        doc = "核心概念是知识编译而非检索。"
        indexed = tokenize_for_fts(doc)
        expr = build_match_query("知识编译")

        conn = sqlite3.connect(":memory:")
        conn.execute(
            "CREATE VIRTUAL TABLE t USING fts5(body, tokenize='unicode61')"
        )
        conn.execute("INSERT INTO t (body) VALUES (?)", (indexed,))
        rows = conn.execute("SELECT * FROM t WHERE t MATCH ?", (expr,)).fetchall()
        assert len(rows) == 1
