"""Tests for i18n groundwork (v1.28.0)."""
from __future__ import annotations

import os

from saw.i18n import tr, get_lang, available_languages


def test_default_lang_zh():
    assert get_lang() == "zh"


def test_en_lang_returns_english():
    os.environ["SAW_LANG"] = "en"
    try:
        assert get_lang() == "en"
        assert tr("no_results") == "No results found."
        assert "Health" in tr("health_report")
    finally:
        del os.environ["SAW_LANG"]


def test_zh_passthrough():
    """Chinese = passthrough (key returned verbatim — source IS Chinese)."""
    os.environ["SAW_LANG"] = "zh"
    try:
        assert tr("some_chinese_key") == "some_chinese_key"
    finally:
        del os.environ["SAW_LANG"]


def test_en_interpolation():
    os.environ["SAW_LANG"] = "en"
    try:
        result = tr("links_applied", n=3, page="alpha")
        assert "3" in result and "alpha" in result
    finally:
        del os.environ["SAW_LANG"]


def test_en_fallback_to_key():
    os.environ["SAW_LANG"] = "en"
    try:
        assert tr("unknown_key_xyz") == "unknown_key_xyz"
    finally:
        del os.environ["SAW_LANG"]


def test_available_languages():
    langs = available_languages()
    assert "en" in langs and "zh" in langs
