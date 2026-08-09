"""CJK-aware tokenization for the FTS5 index.

SQLite's built-in FTS5 tokenizers (unicode61, ascii, porter) do not segment
Chinese/Japanese/Korean text: a whole CJK run becomes a single token, so
searching for a Chinese word returns nothing.

Strategy: at index time and at query time, CJK runs are segmented into
space-separated tokens *before* they reach FTS5 (unicode61 then treats each
segment as an individual token):

- If ``jieba`` is installed, ``jieba.cut_for_search`` provides real word
  segmentation (best precision/recall).
- Otherwise fall back to unigrams + overlapping bigrams, which guarantees
  that any query of one or more characters can still match.

The same segmentation MUST be applied on both the write path (FTS5Sink,
WikiIndexer, claims rebuild) and the query path (``build_match_query``),
otherwise index and query tokens will not align.
"""
from __future__ import annotations

import re
from functools import lru_cache

# CJK Unified Ideographs (+ Extension A + Compatibility), Hiragana,
# Katakana, Hangul syllables.
_CJK_RE = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]+"
)

# Characters with special meaning in FTS5 MATCH syntax are stripped per-token
# in build_match_query (see the ``re.sub(r"[^\w]", ...)`` step).


@lru_cache(maxsize=1)
def _jieba_cut():
    """Return ``jieba.cut_for_search`` or None when jieba is unavailable."""
    try:
        import jieba

        jieba.setLogLevel(60)  # silence jieba's init logging
        return jieba.cut_for_search
    except ImportError:
        return None


def has_cjk(text: str) -> bool:
    """Return True when *text* contains at least one CJK character."""
    return bool(_CJK_RE.search(text))


def _segment_cjk_run(run: str) -> list[str]:
    """Segment a contiguous CJK run into tokens."""
    cut = _jieba_cut()
    if cut is not None:
        tokens = [t for t in cut(run) if t.strip()]
        if tokens:
            return tokens
    # Dependency-free fallback: unigrams + overlapping bigrams.
    tokens = list(run)
    tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens


def tokenize_for_fts(text: str) -> str:
    """Tokenize *text* so FTS5 (unicode61) can index CJK content.

    Non-CJK portions are passed through unchanged (unicode61 already
    segments Latin/Cyrillic/etc. words correctly). CJK runs are replaced
    by space-separated segments.
    """
    if not text or not has_cjk(text):
        return text

    parts: list[str] = []
    pos = 0
    for match in _CJK_RE.finditer(text):
        if match.start() > pos:
            parts.append(text[pos : match.start()])
        parts.append(" ".join(_segment_cjk_run(match.group(0))))
        pos = match.end()
    if pos < len(text):
        parts.append(text[pos:])
    return " ".join(p for p in parts if p.strip())


def build_match_query(query: str) -> str:
    """Build an FTS5 MATCH expression from a raw user query.

    - Latin words are AND-joined (existing behaviour).
    - CJK tokens are OR-joined inside a group: Chinese queries are often
      sentences, and requiring every token (implicit AND) would reject
      relevant documents that miss a single bigram. BM25 still ranks
      documents with more/stronger matches first.
    - Mixed queries become ``word1 word2 (c1 OR c2 OR ...)``.
    """
    if not query or not query.strip():
        return ""

    tokenized = tokenize_for_fts(query.strip())

    latin_words: list[str] = []
    cjk_tokens: list[str] = []
    for raw_token in tokenized.split():
        # Reduce each token to word characters. This drops FTS5 syntax chars
        # and pure punctuation (e.g. full-width ？ ！ ， 。) that are not CJK
        # ideographs and would otherwise be AND-joined as an unsatisfiable term.
        token = re.sub(r"[^\w]", "", raw_token)
        if not token:
            continue
        if has_cjk(token):
            cjk_tokens.append(token)
        else:
            latin_words.append(token)

    # De-duplicate while preserving order (repeated CJK chars are common).
    seen: set[str] = set()
    unique_cjk = [t for t in cjk_tokens if not (t in seen or seen.add(t))]

    fragments = list(latin_words)
    if unique_cjk:
        group = "(" + " OR ".join(unique_cjk) + ")"
        # FTS5 rejects implicit AND between a bare term and a parenthesized
        # group ("vault (storage)" is a syntax error), so use explicit AND.
        if fragments:
            fragments.append("AND")
        fragments.append(group)
    return " ".join(fragments)
