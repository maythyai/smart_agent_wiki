"""YAML workflow parser for multi-agent orchestration.

Per PLAN.md Task 2: WorkflowParser validates YAML and applies defaults.
Per PITFALLS.md Pitfall 17: max_retries defaults to 3.
Per D-07: YAML workflow definition with name, steps, gates, fallback.
Per D-08: Each step has agent, action, input, output, gates.
Per D-09: Gate conditions support confidence, contradiction_count, freshness.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, BaseLoader, select_autoescape

# WR-04: Use safe Jinja2 environment to prevent template injection
SAFE_ENV = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(enabled_extensions=('html', 'xml')),
)


@dataclass
class WorkflowStep:
    """Definition of a single workflow step.

    Per D-08: Each step specifies agent, action, input, output, gates.
    Per PITFALLS.md Pitfall 17: max_retries defaults to 3.
    """

    agent: str
    action: str
    input_key: str = "input"
    output_key: str = "output"
    gates: list[dict[str, str]] | None = None
    condition: str | None = None
    max_retries: int = 3  # Per Pitfall 17
    fallback_action: str = "abort"  # abort | accept_with_flag | escalate_to_human


@dataclass
class WorkflowDefinition:
    """Complete workflow definition.

    Per D-07: YAML workflow has name, steps, timeout, fallback.
    """

    name: str
    steps: list[WorkflowStep]
    timeout: int = 300  # 5 minutes default
    on_failure: str = "abort"  # abort | rollback
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowParseError(Exception):
    """Raised when workflow YAML parsing fails."""

    pass


class WorkflowParser:
    """YAML workflow parser with validation and defaults.

    Per D-08: Validates agent, action required fields.
    Per PITFALLS.md Pitfall 17: max_retries defaults to 3.
    """

    REQUIRED_STEP_FIELDS = ["agent", "action"]
    VALID_FALLBACK_ACTIONS = ["abort", "accept_with_flag", "escalate_to_human"]

    def parse(self, yaml_path: Path) -> WorkflowDefinition:
        """Parse a YAML file into a workflow definition.

        Args:
            yaml_path: Path to the YAML workflow file

        Returns:
            WorkflowDefinition with validated steps

        Raises:
            WorkflowParseError: If YAML is invalid or missing required fields
        """
        with open(yaml_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not raw:
            raise WorkflowParseError("Empty workflow file")

        # Validate required fields
        if "name" not in raw:
            raise WorkflowParseError("Missing required field: name")
        if "steps" not in raw:
            raise WorkflowParseError("Missing required field: steps")
        if not raw["steps"]:
            raise WorkflowParseError("steps cannot be empty")

        # Parse steps
        steps = []
        for i, step_raw in enumerate(raw["steps"]):
            try:
                step = self._parse_step(step_raw)
                steps.append(step)
            except WorkflowParseError as e:
                raise WorkflowParseError(f"Step {i + 1}: {e}")

        return WorkflowDefinition(
            name=raw["name"],
            steps=steps,
            timeout=raw.get("timeout", 300),
            on_failure=raw.get("on_failure", "abort"),
            metadata=raw.get("metadata", {}),
        )

    def _parse_step(self, raw: dict[str, Any]) -> WorkflowStep:
        """Parse a single step definition.

        Args:
            raw: Raw step dictionary from YAML

        Returns:
            WorkflowStep with validated fields

        Raises:
            WorkflowParseError: If required fields are missing or invalid
        """
        # Validate required fields
        for field_name in self.REQUIRED_STEP_FIELDS:
            if field_name not in raw:
                raise WorkflowParseError(f"Missing required field: {field_name}")

        # Validate fallback_action
        fallback = raw.get("fallback_action", "abort")
        if fallback not in self.VALID_FALLBACK_ACTIONS:
            raise WorkflowParseError(
                f"Invalid fallback_action: {fallback}. "
                f"Must be one of {self.VALID_FALLBACK_ACTIONS}"
            )

        return WorkflowStep(
            agent=raw["agent"],
            action=raw["action"],
            input_key=raw.get("input", "input"),
            output_key=raw.get("output", "output"),
            gates=raw.get("gates"),
            condition=raw.get("condition"),
            max_retries=raw.get("max_retries", 3),
            fallback_action=fallback,
        )

    def validate(
        self, workflow: WorkflowDefinition, available_agents: set[str]
    ) -> list[str]:
        """Validate a workflow definition.

        Args:
            workflow: The workflow to validate
            available_agents: Set of valid agent names

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        for i, step in enumerate(workflow.steps):
            # Check if agent exists
            if step.agent not in available_agents:
                errors.append(f"Step {i + 1}: Unknown agent '{step.agent}'")

            # Check gate condition syntax
            if step.gates:
                for gate in step.gates:
                    if not self._validate_gate(gate):
                        errors.append(f"Step {i + 1}: Invalid gate condition: {gate}")

        return errors

    def _validate_gate(self, gate: dict[str, str]) -> bool:
        """Validate gate condition syntax.

        Per D-09: Supports confidence, contradiction_count, freshness.

        Args:
            gate: Gate condition dictionary (e.g., {"confidence": ">= 3"})

        Returns:
            True if valid, False otherwise
        """
        for key, condition in gate.items():
            if not isinstance(condition, str):
                return False
            # Check condition format: operator + value
            if not re.match(r"^(>=|<=|==|!=|>|<)\s*\d+$", condition):
                return False
        return True

    def render_template(self, template: str, context: dict[str, Any]) -> str:
        """Render Jinja2 template variables.

        WR-04: Uses safe environment to prevent template injection attacks.
        Filters context keys to valid Python identifiers only.

        Args:
            template: Template string with {{ variable }} syntax
            context: Dictionary of variables

        Returns:
            Rendered string
        """
        # Filter context to safe identifiers only
        safe_context = {k: v for k, v in context.items() if k.isidentifier()}
        return SAFE_ENV.from_string(template).render(**safe_context)
