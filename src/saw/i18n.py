"""i18n groundwork (v1.28.0): internationalization foundation.

A minimal gettext-like helper: ``tr(key)`` returns the localized string for
the current language (``SAW_LANG`` env, default ``zh`` = Chinese). The English
table covers key CLI surface messages; the rest stay Chinese (the product's
primary language). This is groundwork — downstream code adopts ``tr()`` for
user-facing strings gradually.

Design: no external dep, no .po/.mo files — a flat dict per language. Simple,
testable, and good enough until the string count warrants a real catalog.
"""
from __future__ import annotations

import os

_DEFAULT_LANG = "zh"

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "not_in_wiki": "Error: Not in a Smart Agent Wiki directory. Run 'saw init' first.",
        "no_results": "No results found.",
        "dry_run": "Dry run — no changes written. Run with --confirm to apply.",
        "links_applied": "{n} links applied to {page}.",
        "health_report": "Knowledge Base Health Report",
        "freshness_report": "Freshness Distribution Report",
        "review_queue": "Review Queue",
        "no_claims": "No claims found for '{topic}'.",
        "distilled": "Distilled {n} claims into {path}.",
        "feedback_recorded": "Feedback recorded: {claim} marked {status}.",
        "heartbeat_disabled": "Heartbeat disabled (set SAW_HEARTBEAT_INTERVAL > 0 to enable).",
        "queue_healthy": "Write Queue healthy: {pending} pending, {dl} dead-letter.",
    },
    # zh = passthrough (the source strings are already Chinese)
    "zh": {},
}


def get_lang() -> str:
    """Current language code (``SAW_LANG`` env, default ``zh``)."""
    return os.environ.get("SAW_LANG", _DEFAULT_LANG).lower()


def tr(key: str, **kwargs) -> str:
    """Translate a message key for the current language.

    For ``zh`` (default), returns ``key`` verbatim (the source IS Chinese).
    For ``en``, looks up the English table; falls back to ``key`` if missing.
    Supports ``{placeholder}`` interpolation via ``**kwargs``.
    """
    lang = get_lang()
    table = _STRINGS.get(lang, {})
    msg = table.get(key, key)  # fallback: return key verbatim
    if kwargs:
        try:
            return msg.format(**kwargs)
        except (KeyError, IndexError):
            return msg
    return msg


def available_languages() -> list[str]:
    """List available language codes."""
    return sorted(_STRINGS.keys())
