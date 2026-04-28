"""Tests for YAML workflow parser.

Per PLAN.md Task 2: WorkflowParser validates YAML and applies defaults.
Per PITFALLS.md Pitfall 17: max_retries defaults to 3.
"""
import tempfile
from pathlib import Path

import pytest


class TestWorkflowParser:
    """Tests for WorkflowParser."""

    def test_parse_valid_yaml_with_name_and_steps(self):
        """WorkflowParser parses valid YAML with name and steps."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        yaml_content = """
name: test_workflow
steps:
  - agent: Librarian
    action: search
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            workflow = parser.parse(yaml_path)

            assert workflow.name == "test_workflow"
            assert len(workflow.steps) == 1
            assert workflow.steps[0].agent == "Librarian"
            assert workflow.steps[0].action == "search"

    def test_rejects_yaml_without_name_field(self):
        """WorkflowParser rejects YAML without name field."""
        from saw.engines.collaborate.workflow_parser import (
            WorkflowParser,
            WorkflowParseError,
        )

        yaml_content = """
steps:
  - agent: Librarian
    action: search
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            with pytest.raises(WorkflowParseError, match="name"):
                parser.parse(yaml_path)

    def test_rejects_yaml_without_steps_field(self):
        """WorkflowParser rejects YAML without steps field."""
        from saw.engines.collaborate.workflow_parser import (
            WorkflowParser,
            WorkflowParseError,
        )

        yaml_content = """
name: test_workflow
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            with pytest.raises(WorkflowParseError, match="steps"):
                parser.parse(yaml_path)

    def test_each_step_has_agent_and_action(self):
        """WorkflowParser validates each step has agent and action."""
        from saw.engines.collaborate.workflow_parser import (
            WorkflowParser,
            WorkflowParseError,
        )

        yaml_content = """
name: test_workflow
steps:
  - agent: Librarian
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            with pytest.raises(WorkflowParseError, match="action"):
                parser.parse(yaml_path)

    def test_extracts_gates_as_list_of_conditions(self):
        """WorkflowParser extracts gates as list of conditions."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        yaml_content = """
name: test_workflow
steps:
  - agent: Critic
    action: review
    gates:
      - confidence: ">= 3"
      - contradiction_count: "== 0"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            workflow = parser.parse(yaml_path)

            assert workflow.steps[0].gates is not None
            assert len(workflow.steps[0].gates) == 2
            assert workflow.steps[0].gates[0] == {"confidence": ">= 3"}
            assert workflow.steps[0].gates[1] == {"contradiction_count": "== 0"}

    def test_extracts_fallback_action_from_step(self):
        """WorkflowParser extracts fallback_action from step."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        yaml_content = """
name: test_workflow
steps:
  - agent: Critic
    action: review
    fallback_action: accept_with_flag
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            workflow = parser.parse(yaml_path)

            assert workflow.steps[0].fallback_action == "accept_with_flag"

    def test_applies_defaults_max_retries_and_timeout(self):
        """WorkflowParser applies defaults: max_retries=3, timeout=300."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        yaml_content = """
name: test_workflow
steps:
  - agent: Librarian
    action: search
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            workflow = parser.parse(yaml_path)

            # Per PITFALLS.md Pitfall 17: max_retries defaults to 3
            assert workflow.steps[0].max_retries == 3
            # Per plan: timeout defaults to 300 (5 minutes)
            assert workflow.timeout == 300

    def test_handles_jinja2_template_variables_in_input(self):
        """WorkflowParser handles Jinja2 template variables in input."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        yaml_content = """
name: test_workflow
steps:
  - agent: Librarian
    action: search
    input: "{{ query }}"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            workflow = parser.parse(yaml_path)

            # Input key should be extracted
            assert workflow.steps[0].input_key == "{{ query }}"

            # Render template
            rendered = parser.render_template(workflow.steps[0].input_key, {"query": "machine learning"})
            assert rendered == "machine learning"


class TestWorkflowDefinition:
    """Tests for WorkflowDefinition dataclass."""

    def test_workflow_definition_has_required_fields(self):
        """WorkflowDefinition has name, steps, timeout, on_failure fields."""
        from saw.engines.collaborate.workflow_parser import (
            WorkflowDefinition,
            WorkflowStep,
        )

        step = WorkflowStep(agent="Librarian", action="search")
        workflow = WorkflowDefinition(name="test", steps=[step])

        assert workflow.name == "test"
        assert len(workflow.steps) == 1
        assert workflow.timeout == 300
        assert workflow.on_failure == "abort"

    def test_workflow_step_has_all_fields(self):
        """WorkflowStep has agent, action, input, output, gates, etc."""
        from saw.engines.collaborate.workflow_parser import WorkflowStep

        step = WorkflowStep(
            agent="Critic",
            action="review",
            input_key="draft",
            output_key="reviewed",
            gates=[{"confidence": ">= 3"}],
            max_retries=5,
            fallback_action="escalate_to_human",
        )

        assert step.agent == "Critic"
        assert step.action == "review"
        assert step.input_key == "draft"
        assert step.output_key == "reviewed"
        assert step.gates == [{"confidence": ">= 3"}]
        assert step.max_retries == 5
        assert step.fallback_action == "escalate_to_human"


class TestWorkflowValidation:
    """Tests for workflow validation."""

    def test_validate_unknown_agent(self):
        """WorkflowParser.validate() detects unknown agents."""
        from saw.engines.collaborate.workflow_parser import (
            WorkflowParser,
            WorkflowDefinition,
            WorkflowStep,
        )

        step = WorkflowStep(agent="UnknownAgent", action="search")
        workflow = WorkflowDefinition(name="test", steps=[step])

        parser = WorkflowParser()
        errors = parser.validate(workflow, available_agents={"Librarian", "Writer"})

        assert len(errors) == 1
        assert "UnknownAgent" in errors[0]

    def test_validate_invalid_gate_condition(self):
        """WorkflowParser.validate() detects invalid gate conditions."""
        from saw.engines.collaborate.workflow_parser import (
            WorkflowParser,
            WorkflowDefinition,
            WorkflowStep,
        )

        step = WorkflowStep(
            agent="Librarian",
            action="search",
            gates=[{"confidence": "invalid operator"}],
        )
        workflow = WorkflowDefinition(name="test", steps=[step])

        parser = WorkflowParser()
        errors = parser.validate(workflow, available_agents={"Librarian"})

        assert len(errors) == 1
        assert "Invalid gate" in errors[0]

    def test_validate_invalid_fallback_action(self):
        """WorkflowParser rejects invalid fallback_action."""
        from saw.engines.collaborate.workflow_parser import (
            WorkflowParser,
            WorkflowParseError,
        )

        yaml_content = """
name: test_workflow
steps:
  - agent: Librarian
    action: search
    fallback_action: invalid_action
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            with pytest.raises(WorkflowParseError, match="fallback_action"):
                parser.parse(yaml_path)


class TestGateConditionSyntax:
    """Tests for gate condition syntax validation."""

    def test_valid_operators(self):
        """Gate conditions support >=, <=, ==, !=, >, < operators."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        parser = WorkflowParser()

        # All valid operators
        assert parser._validate_gate({"confidence": ">= 3"}) is True
        assert parser._validate_gate({"confidence": "<= 3"}) is True
        assert parser._validate_gate({"confidence": "== 3"}) is True
        assert parser._validate_gate({"confidence": "!= 3"}) is True
        assert parser._validate_gate({"confidence": "> 3"}) is True
        assert parser._validate_gate({"confidence": "< 3"}) is True

    def test_invalid_operator(self):
        """Gate conditions reject invalid operators."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        parser = WorkflowParser()

        assert parser._validate_gate({"confidence": "~= 3"}) is False
        assert parser._validate_gate({"confidence": "3"}) is False

    def test_non_numeric_value(self):
        """Gate conditions require numeric values."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        parser = WorkflowParser()

        assert parser._validate_gate({"confidence": ">= abc"}) is False
