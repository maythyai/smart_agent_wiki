"""Tests for Agent definitions - AgentProtocol, BaseAgent, and data classes.

Per PLAN.md Task 1: Defines the core agent types and protocols.
"""
from __future__ import annotations

import pytest


class TestAgentProtocol:
    """Tests for AgentProtocol definition."""

    def test_protocol_has_name_property(self):
        """Test 1: AgentProtocol has name property returning agent role name."""
        # We test by checking the protocol signature via runtime_checkable
        from typing import Protocol, runtime_checkable
        from saw.domain.protocols import AgentProtocol

        # Check that name is defined as a property in the protocol
        # Protocol classes define properties as methods with @property decorator
        assert hasattr(AgentProtocol, 'name')

    def test_protocol_has_model_tier_property(self):
        """Test 2: AgentProtocol has model_tier property returning tier string."""
        from saw.domain.protocols import AgentProtocol

        assert hasattr(AgentProtocol, 'model_tier')

    def test_protocol_has_execute_method(self):
        """Test 3: AgentProtocol has execute() async method."""
        from saw.domain.protocols import AgentProtocol

        assert hasattr(AgentProtocol, 'execute')


class TestAgentTask:
    """Tests for AgentTask dataclass."""

    def test_task_has_type_field(self):
        """Test 5a: AgentTask has type field."""
        from saw.domain.agent import AgentTask

        task = AgentTask(type="search", payload={"query": "test"})
        assert task.type == "search"

    def test_task_has_payload_field(self):
        """Test 5b: AgentTask has payload field."""
        from saw.domain.agent import AgentTask

        task = AgentTask(type="search", payload={"query": "test"})
        assert task.payload == {"query": "test"}

    def test_task_has_correlation_id_field(self):
        """Test 5c: AgentTask has correlation_id field."""
        from saw.domain.agent import AgentTask

        task = AgentTask(type="search", payload={"query": "test"}, correlation_id="abc-123")
        assert task.correlation_id == "abc-123"

    def test_task_correlation_id_optional(self):
        """Test 5d: AgentTask correlation_id is optional (defaults to None)."""
        from saw.domain.agent import AgentTask

        task = AgentTask(type="search", payload={"query": "test"})
        assert task.correlation_id is None


class TestAgentContext:
    """Tests for AgentContext dataclass."""

    def test_context_has_wiki_state_field(self):
        """Test 7a: AgentContext has wiki_state field."""
        from saw.domain.agent import AgentContext

        context = AgentContext(wiki_state={}, claims_context=[])
        assert context.wiki_state == {}

    def test_context_has_claims_context_field(self):
        """Test 7b: AgentContext has claims_context field."""
        from saw.domain.agent import AgentContext

        context = AgentContext(wiki_state={}, claims_context=[{"claim": "test"}])
        assert context.claims_context == [{"claim": "test"}]

    def test_context_has_workflow_id_field(self):
        """Test 7c: AgentContext has workflow_id field."""
        from saw.domain.agent import AgentContext

        context = AgentContext(wiki_state={}, claims_context=[], workflow_id="wf-001")
        assert context.workflow_id == "wf-001"

    def test_context_workflow_id_optional(self):
        """Test 7d: AgentContext workflow_id is optional."""
        from saw.domain.agent import AgentContext

        context = AgentContext(wiki_state={}, claims_context=[])
        assert context.workflow_id is None


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_result_has_success_field(self):
        """Test 6a: AgentResult has success field."""
        from saw.domain.agent import AgentResult

        result = AgentResult(success=True, payload={"data": "test"})
        assert result.success is True

    def test_result_has_payload_field(self):
        """Test 6b: AgentResult has payload field."""
        from saw.domain.agent import AgentResult

        result = AgentResult(success=True, payload={"data": "test"})
        assert result.payload == {"data": "test"}

    def test_result_has_confidence_field(self):
        """Test 6c: AgentResult has confidence field (0-4)."""
        from saw.domain.agent import AgentResult

        result = AgentResult(success=True, payload={"data": "test"}, confidence=3)
        assert result.confidence == 3

    def test_result_confidence_defaults_to_zero(self):
        """Test 6d: AgentResult confidence defaults to 0."""
        from saw.domain.agent import AgentResult

        result = AgentResult(success=True, payload={"data": "test"})
        assert result.confidence == 0

    def test_result_has_error_field(self):
        """Test 6e: AgentResult has error field."""
        from saw.domain.agent import AgentResult

        result = AgentResult(success=False, payload={}, error="Something failed")
        assert result.error == "Something failed"

    def test_result_error_optional(self):
        """Test 6f: AgentResult error is optional."""
        from saw.domain.agent import AgentResult

        result = AgentResult(success=True, payload={"data": "test"})
        assert result.error is None

    def test_result_has_metadata_field(self):
        """Test 6g: AgentResult has metadata field."""
        from saw.domain.agent import AgentResult

        result = AgentResult(success=True, payload={}, metadata={"model": "haiku"})
        assert result.metadata == {"model": "haiku"}

    def test_result_metadata_defaults_to_empty_dict(self):
        """Test 6h: AgentResult metadata defaults to empty dict."""
        from saw.domain.agent import AgentResult

        result = AgentResult(success=True, payload={"data": "test"})
        assert result.metadata == {}


class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_base_agent_constructor_accepts_name(self):
        """Test 4a: BaseAgent constructor accepts name."""
        from saw.engines.collaborate.agents.base import BaseAgent

        agent = BaseAgent(
            name="TestAgent",
            model_tier="haiku",
            system_prompt="Test prompt",
            tools_allowed=["saw_search"],
        )
        assert agent.name == "TestAgent"

    def test_base_agent_constructor_accepts_model_tier(self):
        """Test 4b: BaseAgent constructor accepts model_tier."""
        from saw.engines.collaborate.agents.base import BaseAgent

        agent = BaseAgent(
            name="TestAgent",
            model_tier="sonnet",
            system_prompt="Test prompt",
            tools_allowed=["saw_search"],
        )
        assert agent.model_tier == "sonnet"

    def test_base_agent_constructor_accepts_system_prompt(self):
        """Test 4c: BaseAgent constructor accepts system_prompt."""
        from saw.engines.collaborate.agents.base import BaseAgent

        agent = BaseAgent(
            name="TestAgent",
            model_tier="haiku",
            system_prompt="You are a test agent.",
            tools_allowed=["saw_search"],
        )
        # Verify stored (internal attribute)
        assert agent._system_prompt == "You are a test agent."

    def test_base_agent_constructor_accepts_tools_allowed(self):
        """Test 4d: BaseAgent constructor accepts tools_allowed."""
        from saw.engines.collaborate.agents.base import BaseAgent

        agent = BaseAgent(
            name="TestAgent",
            model_tier="haiku",
            system_prompt="Test prompt",
            tools_allowed=["saw_search", "saw_query"],
        )
        assert agent._tools_allowed == ["saw_search", "saw_query"]

    def test_base_agent_model_tier_values(self):
        """Test that model_tier accepts valid values."""
        from saw.engines.collaborate.agents.base import BaseAgent

        for tier in ["haiku", "sonnet", "opus", "rule"]:
            agent = BaseAgent(
                name="TestAgent",
                model_tier=tier,
                system_prompt="Test prompt",
                tools_allowed=["saw_search"],
            )
            assert agent.model_tier == tier

    def test_base_agent_build_messages(self):
        """Test _build_messages creates correct message structure."""
        from saw.engines.collaborate.agents.base import BaseAgent
        from saw.domain.agent import AgentTask, AgentContext

        agent = BaseAgent(
            name="TestAgent",
            model_tier="haiku",
            system_prompt="You are a test agent.",
            tools_allowed=["saw_search"],
        )

        task = AgentTask(type="search", payload={"query": "test"})
        context = AgentContext(
            wiki_state={},
            claims_context=[],
            workflow_id="wf-001",
            calling_agent="CallerAgent",
        )

        messages = agent._build_messages(task, context)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a test agent."
        assert messages[1]["role"] == "user"