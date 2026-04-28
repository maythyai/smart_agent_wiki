"""Tests for CollaborateEngine orchestrator.

Per PLAN.md Task 4: Unified entry point for multi-agent collaboration.
"""
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCollaborateEngine:
    """Tests for CollaborateEngine orchestrator."""

    @pytest.fixture
    def mock_dispatcher(self):
        """Create mock AgentDispatcher."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher

        dispatcher = MagicMock(spec=AgentDispatcher)
        dispatcher._agents = {
            "Librarian": MagicMock(),
            "Scholar": MagicMock(),
            "Critic": MagicMock(),
            "Writer": MagicMock(),
        }
        dispatcher.dispatch = AsyncMock()
        return dispatcher

    @pytest.fixture
    def mock_a2a(self):
        """Create mock A2AAdapter."""
        from saw.engines.collaborate.a2a_protocol import A2AAdapter, A2AResult

        a2a = MagicMock(spec=A2AAdapter)
        a2a.send = AsyncMock()
        a2a.handoff = AsyncMock(return_value=A2AResult(success=True, message_id="msg-123"))
        return a2a

    @pytest.fixture
    def mock_workflow_executor(self):
        """Create mock WorkflowExecutor."""
        from saw.engines.collaborate.workflow_executor import (
            WorkflowExecutor,
            WorkflowResult,
        )
        from datetime import datetime, timezone

        executor = MagicMock(spec=WorkflowExecutor)
        executor.execute = AsyncMock(
            return_value=WorkflowResult(
                workflow_id="wf-123",
                name="test",
                status="completed",
                steps_completed=1,
                steps_total=1,
                outputs={},
                errors=[],
                start_time=datetime.now(timezone.utc),
            )
        )
        return executor

    @pytest.fixture
    def mock_policy_engine(self):
        """Create mock PolicyEngine."""
        from saw.adapters.crypto.cedar_policy import PolicyEngine, PolicyDecision

        engine = MagicMock(spec=PolicyEngine)
        engine.evaluate = MagicMock(
            return_value=PolicyDecision(allowed=True, reason="Permitted")
        )
        engine.is_authorized = MagicMock(return_value=True)
        return engine

    def test_collaborate_config_defaults(self):
        """CollaborateConfig has sensible defaults."""
        from saw.engines.collaborate.orchestrator import CollaborateConfig

        config = CollaborateConfig()
        assert config.max_concurrent_workflows == 5
        assert config.default_workflow_timeout == 300
        assert config.enable_policy_check is True

    def test_dispatch_agent_returns_result_on_success(
        self, mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
    ):
        """CollaborateEngine.dispatch_agent() returns AgentResult on success."""
        from saw.engines.collaborate.orchestrator import CollaborateEngine
        from saw.domain.agent import AgentResult, AgentTask, AgentContext

        # Mock successful dispatch
        mock_dispatcher.dispatch.return_value = AgentResult(
            success=True, payload={"pages": ["p1", "p2"]}, confidence=3
        )

        engine = CollaborateEngine(
            mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
        )

        # Mock async dispatch
        async def run_test():
            task = AgentTask(type="search", payload={"query": "test"})
            context = AgentContext(wiki_state={}, claims_context=[])
            result = await engine.dispatch_agent("Librarian", task, context)
            assert result.success is True
            assert result.payload == {"pages": ["p1", "p2"]}

        import asyncio

        asyncio.run(run_test())

    def test_dispatch_agent_returns_error_when_policy_denies(
        self, mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
    ):
        """CollaborateEngine.dispatch_agent() returns error when policy denies action."""
        from saw.engines.collaborate.orchestrator import CollaborateEngine, CollaborateConfig
        from saw.adapters.crypto.cedar_policy import PolicyDecision
        from saw.domain.agent import AgentTask, AgentContext

        # Mock policy denial
        mock_policy_engine.evaluate.return_value = PolicyDecision(
            allowed=False, reason="Policy denied: Writer cannot verify"
        )

        config = CollaborateConfig(enable_policy_check=True)
        engine = CollaborateEngine(
            mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine, config
        )

        async def run_test():
            task = AgentTask(type="saw_verify", payload={})
            context = AgentContext(wiki_state={}, claims_context=[], calling_agent="Writer")
            result = await engine.dispatch_agent("Writer", task, context)
            assert result.success is False
            assert "Policy denied" in result.error

        import asyncio

        asyncio.run(run_test())

    def test_check_policy_returns_false_for_forbid_rule(
        self, mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
    ):
        """CollaborateEngine.check_policy() returns allowed=False for forbid rule."""
        from saw.engines.collaborate.orchestrator import CollaborateEngine
        from saw.adapters.crypto.cedar_policy import PolicyDecision

        mock_policy_engine.evaluate.return_value = PolicyDecision(
            allowed=False, reason="Explicit forbid rule"
        )

        engine = CollaborateEngine(
            mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
        )

        decision = engine.check_policy("Writer", "saw_verify", "wiki")
        assert decision.allowed is False

    def test_execute_workflow_runs_from_yaml_path(
        self, mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
    ):
        """CollaborateEngine.execute_workflow() runs workflow from YAML path."""
        from saw.engines.collaborate.orchestrator import CollaborateEngine

        engine = CollaborateEngine(
            mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
        )

        async def run_test():
            with tempfile.TemporaryDirectory() as tmpdir:
                yaml_path = Path(tmpdir) / "test.yaml"
                yaml_path.write_text("""
name: test_workflow
steps:
  - agent: Librarian
    action: search
""")
                result = await engine.execute_workflow(yaml_path, {"query": "test"})
                assert result.status == "completed"

        import asyncio

        asyncio.run(run_test())

    def test_handoff_sends_a2a_message(
        self, mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
    ):
        """CollaborateEngine.handoff() sends A2A message between agents."""
        from saw.engines.collaborate.orchestrator import CollaborateEngine
        from saw.engines.collaborate.a2a_protocol import A2AResult

        mock_a2a.handoff.return_value = A2AResult(success=True, message_id="msg-456")

        engine = CollaborateEngine(
            mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
        )

        async def run_test():
            result = await engine.handoff(
                sender="Librarian",
                receiver="Scholar",
                task_type="synthesize",
                payload={"pages": ["p1"]},
                context={"workflow_id": "wf-123"},
            )
            assert result.success is True

        import asyncio

        asyncio.run(run_test())

    def test_get_available_agents_returns_list(
        self, mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
    ):
        """CollaborateEngine.get_available_agents() returns list of registered agents."""
        from saw.engines.collaborate.orchestrator import CollaborateEngine

        engine = CollaborateEngine(
            mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
        )

        agents = engine.get_available_agents()
        assert "Librarian" in agents
        assert "Scholar" in agents
        assert "Critic" in agents
        assert "Writer" in agents

    def test_dispatch_agent_bypasses_policy_when_check_disabled(
        self, mock_dispatcher, mock_a2a, mock_workflow_executor, mock_policy_engine
    ):
        """CollaborateEngine.dispatch_agent(check_policy=False) bypasses policy."""
        from saw.engines.collaborate.orchestrator import CollaborateEngine, CollaborateConfig
        from saw.domain.agent import AgentResult, AgentTask, AgentContext

        mock_dispatcher.dispatch.return_value = AgentResult(
            success=True, payload={}
        )

        config = CollaborateConfig(enable_policy_check=False)
        engine = CollaborateEngine(
            mock_dispatcher, mock_a2a, mock_workflow_executor, None, config
        )

        async def run_test():
            task = AgentTask(type="search", payload={})
            context = AgentContext(wiki_state={}, claims_context=[])
            result = await engine.dispatch_agent("Librarian", task, context, check_policy=False)
            assert result.success is True
            # Policy engine should not have been called
            mock_policy_engine.evaluate.assert_not_called()

        import asyncio

        asyncio.run(run_test())

    def test_check_policy_returns_true_when_no_engine_configured(
        self, mock_dispatcher, mock_a2a, mock_workflow_executor
    ):
        """CollaborateEngine.check_policy() returns allowed=True when no engine."""
        from saw.engines.collaborate.orchestrator import CollaborateEngine
        from saw.adapters.crypto.cedar_policy import PolicyDecision

        engine = CollaborateEngine(
            mock_dispatcher, mock_a2a, mock_workflow_executor, None
        )

        decision = engine.check_policy("Librarian", "saw_search", "wiki")
        assert decision.allowed is True
        assert "No policy engine" in decision.reason


class TestCollaborateInit:
    """Tests for module exports."""

    def test_import_all_from_collaborate(self):
        """All expected classes are exported from __init__."""
        from saw.engines.collaborate import (
            CollaborateEngine,
            CollaborateConfig,
            AgentDispatcher,
            ModelTier,
            WorkflowParser,
            WorkflowDefinition,
            WorkflowStep,
            WorkflowExecutor,
            WorkflowResult,
            A2AAdapter,
            A2AMessage,
            A2AResult,
            MessageType,
            BaseAgent,
            AgentProtocol,
            AgentTask,
            AgentContext,
            AgentResult,
            LibrarianAgent,
            WriterAgent,
            CriticAgent,
            LinkerAgent,
            ScholarAgent,
            GuardianAgent,
        )

        assert CollaborateEngine is not None
        assert CollaborateConfig is not None
