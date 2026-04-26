"""Cognitive Distillation - SOP extraction from user feedback patterns.

Per D-19: Extract standard operating procedures from approved patterns.
SOPs are generalizable procedures extracted from behavioral patterns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from saw.adapters.llm.router import LLMRouter


@dataclass
class SOP:
    """Standard Operating Procedure extracted from patterns.

    Attributes:
        name: SOP name/title
        trigger: When to apply this SOP
        steps: The procedure steps
        source_patterns: Patterns that led to this SOP
        created_at: Creation timestamp
    """
    name: str
    trigger: str
    steps: list[str]
    source_patterns: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Distiller:
    """Extracts SOPs from approved behavioral patterns.

    Uses LLM to generalize patterns into reusable procedures.
    SOPs are persisted in .saw/sops/ directory.
    """

    def __init__(
        self,
        llm_router: LLMRouter,
        sops_dir: Path | None = None,
    ) -> None:
        self._llm = llm_router
        self._sops_dir = sops_dir or Path(".saw/sops")
        self._sops_dir.mkdir(parents=True, exist_ok=True)

    def extract_sop(self, approved_patterns: list[str]) -> SOP:
        """Extract SOP from approved patterns using LLM (per D-19).

        Args:
            approved_patterns: List of approved behavioral patterns.

        Returns:
            Extracted SOP.
        """
        # Build prompt for SOP extraction
        prompt = f"""
Extract a standard operating procedure (SOP) from these approved patterns.
Generalize the patterns into reusable steps.

Approved patterns:
{chr(10).join('- ' + p for p in approved_patterns)}

Return JSON with:
- name: SOP name
- trigger: When to apply this SOP
- steps: List of procedure steps
- source_patterns: The patterns that led to this SOP
"""

        system_prompt = "You are a knowledge distillation expert. Extract generalizable SOPs from specific behavioral patterns."

        # Call LLM
        result = self._llm.extract_claims(prompt, system_prompt)

        # Parse result into SOP
        sop = SOP(
            name=result.get("name", "Unnamed SOP"),
            trigger=result.get("trigger", ""),
            steps=result.get("steps", []),
            source_patterns=result.get("source_patterns", approved_patterns),
        )

        # Save SOP
        self._save_sop(sop)

        return sop

    def run_distillation(self, approved_file: Path) -> list[SOP]:
        """Process approved.yaml and extract SOPs (per D-19).

        Args:
            approved_file: Path to approved.yaml.

        Returns:
            List of extracted SOPs.
        """
        if not approved_file.is_file():
            return []

        try:
            with open(approved_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or []
        except yaml.YAMLError:
            return []

        # Group patterns by action type
        patterns_by_action: dict[str, list[str]] = {}
        for entry in data:
            action = entry.get("action", "unknown")
            pattern = entry.get("pattern", "")
            if pattern:
                patterns_by_action.setdefault(action, []).append(pattern)

        # Extract SOPs for each action type
        sops: list[SOP] = []
        for action, patterns in patterns_by_action.items():
            if len(patterns) >= 2:  # Need at least 2 patterns for generalization
                sop = self.extract_sop(patterns)
                sops.append(sop)

        return sops

    def _save_sop(self, sop: SOP) -> None:
        """Save SOP to .saw/sops/ directory."""
        # Create filename from SOP name
        filename = sop.name.lower().replace(" ", "_").replace("/", "_") + ".yaml"
        sop_file = self._sops_dir / filename

        data = {
            "name": sop.name,
            "trigger": sop.trigger,
            "steps": sop.steps,
            "source_patterns": sop.source_patterns,
            "created_at": sop.created_at.isoformat(),
        }

        with open(sop_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def get_sops(self) -> list[SOP]:
        """Load all saved SOPs.

        Returns:
            List of all SOPs.
        """
        sops: list[SOP] = []

        for sop_file in self._sops_dir.glob("*.yaml"):
            try:
                with open(sop_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                sops.append(SOP(
                    name=data.get("name", ""),
                    trigger=data.get("trigger", ""),
                    steps=data.get("steps", []),
                    source_patterns=data.get("source_patterns", []),
                    created_at=datetime.fromisoformat(data.get("created_at", ""))
                    if data.get("created_at") else datetime.now(timezone.utc),
                ))
            except (yaml.YAMLError, ValueError):
                continue

        return sops