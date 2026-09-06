"""Custom agent role registry tests — T-F-T-1 (AC-A-1/2/3).

Tests loading custom agent definitions from ``.saw/agents/*.yaml`` and
their additive merge into the built-in roster. All tests use ``tmp_path``
fixtures — no real files, no LLM calls (``llm_router=None``).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


def _make_agents_dir(tmp_path: Path) -> Path:
    """Create a ``.saw/agents`` directory inside *tmp_path* and return it."""
    d = tmp_path / ".saw" / "agents"
    d.mkdir(parents=True)
    return d


# ── AC-A-1: custom role appears in roster ──────────────────────────

def test_ac_a_1_custom_agent_in_roster(tmp_path: Path) -> None:
    """AC-A-1: create ``.saw/agents/expert.yaml`` → ``build_agent_roster``
    contains the custom role with correct ``model_tier``."""
    agents_dir = _make_agents_dir(tmp_path)
    (agents_dir / "expert.yaml").write_text(
        "name: MedicalExpert\n"
        "model_tier: sonnet\n"
        "system_prompt: >\n"
        "  You are a medical expert agent.\n"
        "tools_allowed:\n"
        "  - search\n"
        "  - read\n",
        encoding="utf-8",
    )

    from saw.engines.collaborate.agents import load_custom_agents

    custom = load_custom_agents(llm_router=None, agents_dir=agents_dir)
    assert "MedicalExpert" in custom
    assert custom["MedicalExpert"].model_tier == "sonnet"
    assert custom["MedicalExpert"].name == "MedicalExpert"


def test_ac_a_1_build_agent_roster_merges_custom(tmp_path: Path) -> None:
    """AC-A-1 (full roster): ``build_agent_roster`` merges custom + built-in."""
    agents_dir = _make_agents_dir(tmp_path)
    (agents_dir / "expert.yaml").write_text(
        "name: MedicalExpert\n"
        "model_tier: sonnet\n"
        "system_prompt: Medical expert.\n"
        "tools_allowed: [search]\n",
        encoding="utf-8",
    )

    # chdir so build_agent_roster's default Path(".saw/agents") resolves.
    prev = os.getcwd()
    os.chdir(tmp_path)
    try:
        from saw.engines.collaborate.agents import build_agent_roster

        roster = build_agent_roster(llm_router=None)
        assert "MedicalExpert" in roster
        assert "Librarian" in roster  # built-in still present
        assert roster["MedicalExpert"].model_tier == "sonnet"
    finally:
        os.chdir(prev)


# ── AC-A-2: workflow validate accepts custom agent ─────────────────

def test_ac_a_2_workflow_validate_accepts_custom_agent(tmp_path: Path) -> None:
    """AC-A-2: custom agent in roster → workflow YAML step.agent=Custom
    → ``WorkflowParser.validate()`` returns no errors."""
    agents_dir = _make_agents_dir(tmp_path)
    (agents_dir / "expert.yaml").write_text(
        "name: MedicalExpert\n"
        "model_tier: sonnet\n"
        "system_prompt: Medical expert.\n",
        encoding="utf-8",
    )

    from saw.engines.collaborate.agents import build_agent_roster
    from saw.engines.collaborate.workflow_parser import WorkflowDefinition, WorkflowParser, WorkflowStep

    prev = os.getcwd()
    os.chdir(tmp_path)
    try:
        roster = build_agent_roster(llm_router=None)
        available = set(roster.keys())
        assert "MedicalExpert" in available

        wf = WorkflowDefinition(
            name="test_wf",
            steps=[WorkflowStep(agent="MedicalExpert", action="analyze")],
        )
        parser = WorkflowParser()
        errors = parser.validate(wf, available)
        assert errors == []
    finally:
        os.chdir(prev)


def test_ac_a_2_validate_defaults_to_roster(tmp_path: Path) -> None:
    """AC-A-2 (default): ``validate()`` with ``available_agents=None``
    defaults to ``build_agent_roster`` (includes custom roles)."""
    agents_dir = _make_agents_dir(tmp_path)
    (agents_dir / "expert.yaml").write_text(
        "name: MedicalExpert\n"
        "model_tier: sonnet\n"
        "system_prompt: Medical expert.\n",
        encoding="utf-8",
    )

    from saw.engines.collaborate.workflow_parser import WorkflowDefinition, WorkflowParser, WorkflowStep

    prev = os.getcwd()
    os.chdir(tmp_path)
    try:
        wf = WorkflowDefinition(
            name="test_wf",
            steps=[WorkflowStep(agent="MedicalExpert", action="analyze")],
        )
        parser = WorkflowParser()
        errors = parser.validate(wf)  # available_agents=None → defaults
        assert errors == []
    finally:
        os.chdir(prev)


# ── AC-A-3: duplicate name is skipped ──────────────────────────────

def test_ac_a_3_duplicate_builtin_name_skipped(tmp_path: Path) -> None:
    """AC-A-3: a custom yaml with ``name: Librarian`` (built-in) is skipped."""
    agents_dir = _make_agents_dir(tmp_path)
    (agents_dir / "dup.yaml").write_text(
        "name: Librarian\n"
        "model_tier: sonnet\n"
        "system_prompt: Duplicate.\n",
        encoding="utf-8",
    )

    from saw.engines.collaborate.agents import load_custom_agents

    custom = load_custom_agents(llm_router=None, agents_dir=agents_dir)
    assert "Librarian" not in custom  # skipped, not overriding built-in


def test_ac_a_3_invalid_model_tier_skipped(tmp_path: Path) -> None:
    """AC-A-3 (variant): invalid ``model_tier`` is skipped."""
    agents_dir = _make_agents_dir(tmp_path)
    (agents_dir / "bad_tier.yaml").write_text(
        "name: BadAgent\n"
        "model_tier: gpt-4\n"
        "system_prompt: Bad tier.\n",
        encoding="utf-8",
    )

    from saw.engines.collaborate.agents import load_custom_agents

    custom = load_custom_agents(llm_router=None, agents_dir=agents_dir)
    assert "BadAgent" not in custom


def test_ac_a_3_empty_prompt_skipped(tmp_path: Path) -> None:
    """AC-A-3 (variant): empty ``system_prompt`` is skipped."""
    agents_dir = _make_agents_dir(tmp_path)
    (agents_dir / "empty.yaml").write_text(
        "name: EmptyAgent\n"
        "model_tier: sonnet\n"
        "system_prompt: ''\n",
        encoding="utf-8",
    )

    from saw.engines.collaborate.agents import load_custom_agents

    custom = load_custom_agents(llm_router=None, agents_dir=agents_dir)
    assert "EmptyAgent" not in custom


def test_ac_a_3_no_agents_dir_returns_empty(tmp_path: Path) -> None:
    """AC-A-3 (degradation): no ``.saw/agents/`` dir → empty dict."""
    from saw.engines.collaborate.agents import load_custom_agents

    custom = load_custom_agents(
        llm_router=None, agents_dir=tmp_path / "nonexistent"
    )
    assert custom == {}
