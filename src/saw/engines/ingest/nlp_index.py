"""B4 (v1.26.0): cheap NLP noun-phrase extraction — a cost-reduction pre-index tier.

GraphRAG's FastGraphRAG uses NLP noun-phrase + co-occurrence as a ~1000x
cheaper alternative to LLM entity/relationship extraction. SAW lands this as a
no-LLM pre-index signal: ``extract_noun_phrases(text)`` pulls noun-phrases
(jieba for CJK, a regex for Latin) so ingest can run a cheap first pass before
the (expensive) LLM claim extraction — and degrade gracefully to NLP-only when
no LLM is configured (OFFLINE tier). This module is pure-Python + jieba (already
a SAW dep for CJK FTS5); no network, no model.
"""
from __future__ import annotations

import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Minimal English stop-word list (keep it small — this is a pre-filter, not
# a full NLP pipeline; the LLM pass (when available) does the real extraction).
_EN_STOP = {
    "the", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "must", "shall", "can", "need", "a", "an", "and", "or", "but",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "that",
    "this", "these", "those", "it", "its", "they", "them", "their", "we",
    "you", "your", "our", "not", "no", "so", "if", "then", "than", "about",
}
# Latin noun-phrase candidate: 3+ char words (allows hyphen), title-case
# sequences are kept as multi-word phrases (e.g. "Rate Limiting").
_LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z-]{2,}")
_CJK = "一-鿿㐀-䶿"


def _has_cjk(text: str) -> bool:
    return any(ch in _CJK for ch in _CJK[:1] for ch in text) or any(
        "一" <= ch <= "鿿" for ch in text
    )


def extract_noun_phrases(text: str, top_k: int = 20) -> list[str]:
    """Extract noun-phrase candidates from ``text`` (no LLM, no network).

    CJK text → jieba cut (filter stop-words + single chars). Latin text →
    regex 3+ char words (filter stop-words); adjacent Title-Case words are
    merged into a phrase. Mixed text → both. Returns the ``top_k`` most
    frequent phrases (a cheap co-occurrence signal).

    Args:
        text: Source text to extract from.
        top_k: Max phrases to return (1-100).

    Returns:
        List of noun-phrase strings, most frequent first.
    """
    if not text or not text.strip():
        return []
    top_k = max(1, min(int(top_k), 100))
    counter: Counter[str] = Counter()

    # CJK path (jieba) — jieba is a SAW dep for FTS5 CJK segmentation.
    if _has_cjk(text):
        try:
            import jieba.posseg as pseg
            for word, flag in pseg.cut(text):
                if len(word) >= 2 and flag.startswith("n"):  # nouns only
                    counter[word] += 1
        except Exception:  # pragma: no cover — jieba is a hard dep, but be safe
            logger.debug("jieba noun extraction failed; Latin-only fallback")

    # Latin path — regex words + Title-Case phrase merging.
    words = _LATIN_WORD.findall(text)
    phrase: list[str] = []
    for w in words:
        lw = w.lower()
        if lw in _EN_STOP:
            if phrase:
                _add_phrase(counter, phrase)
                phrase = []
            continue
        # Title-Case (proper noun / term) → extend a phrase; else flush + single.
        if w[0].isupper():
            phrase.append(w)
        else:
            if phrase:
                _add_phrase(counter, phrase)
                phrase = []
            counter[lw] += 1
    if phrase:
        _add_phrase(counter, phrase)

    return [p for p, _ in counter.most_common(top_k)]


def _add_phrase(counter: Counter, phrase: list[str]) -> None:
    """Merge a Title-Case run into a phrase (single + multi-word forms)."""
    if not phrase:
        return
    joined = " ".join(phrase)
    counter[joined] += 1
    if len(phrase) > 1:
        # also count each component so a single-word match still ranks.
        for w in phrase:
            counter[w.lower()] += 1
