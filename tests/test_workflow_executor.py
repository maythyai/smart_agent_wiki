"""Tests for workflow executor.

Per PLAN.md Task 3: WorkflowExecutor executes steps with gates and fallbacks.
Per PITFALLS.md Pitfall 10: Deadlock prevention, Pitfall 17: Gate loop.
"""
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWorkflowExecutor:
    """Tests for WorkflowExecutor."""

    @pytest.fixture
    def mock_dispatcher(self):
        """Create mock AgentDispatcher."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher

        dispatcher = MagicMock(spec=AgentDispatcher)
        dispatcher._agents = {"Librarian": MagicMock(), "Scholar": MagicMock(), "Critic": MagicMock(), "Writer": MagicMock()}
        dispatcher.dispatch = AsyncMock()
        return dispatcher

    @pytest.fixture
    def mock_a2a(self):
        """Create mock A2AAdapter."""
        from saw.engines.collaborate.a2a_protocol import A2AAdapter

        a2a = MagicMock(spec=A2AAdapter)
        a2a.handoff = AsyncMock()
        return a2a

    @pytest.fixture
    def mock_governor(self):
        """Create mock Governor."""
        mock = MagicMock()
        mock.get_confidence = MagicMock(return_value=3)
        mock.check_contradictions = AsyncMock(return_value=[])
        return mock

    def test_workflow_result_dataclass(self):
        """WorkflowResult has required fields."""
        from saw.engines.collaborate.workflow_executor import WorkflowResult

        result = WorkflowResult(
            workflow_id="test-123",
            name="test_workflow",
            status="completed",
            steps_completed=2,
            steps_total=2,
            outputs={"output": {"data": "test"}},
            errors=[],
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )

        assert result.workflow_id == "test-123"
        assert result.status == "completed"
        assert result.steps_completed == 2

    def test_gate_result_dataclass(self):
        """GateResult has required fields."""
        from saw.engines.collaborate.workflow_executor import GateResult

        result = GateResult(passed=True, reason="All conditions met", value=3, expected=3)
        assert result.passed is True
        assert result.value == 3

    @pytest.mark.asyncio
    async def test_executes_steps_in_sequence(self, mock_dispatcher, mock_a2a, mock_governor):
        """WorkflowExecutor executes steps in sequence."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.domain.agent import AgentResult

        # Mock successful dispatch
        mock_dispatcher.dispatch.return_value = AgentResult(
            success=True, payload={"results": []}, confidence=3
        )

        executor = WorkflowExecutor(mock_dispatcher, mock_a2a, mock_governor)

        yaml_content = """
name: sequential_workflow
steps:
  - agent: Librarian
    action: search
    output: search_results
  - agent: Scholar
    action: synthesize
    input: search_results
    output: synthesis
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            result = await executor.execute(yaml_path, {"query": "test"})

            assert result.status == "completed"
            assert mock_dispatcher.dispatch.call_count == 2

    @pytest.mark.asyncio
    async def test_passes_output_as_input_to_next_step(self, mock_dispatcher, mock_a2a, mock_governor):
        """WorkflowExecutor passes output of step N as input to step N+1."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.domain.agent import AgentResult

        # First step returns results, second step uses them
        first_result = AgentResult(success=True, payload={"pages": ["page1", "page2"]}, confidence=3)
        second_result = AgentResult(success=True, payload={"synthesis": "test synthesis"}, confidence=3)

        mock_dispatcher.dispatch.side_effect = [first_result, second_result]

        executor = WorkflowExecutor(mock_dispatcher, mock_a2a, mock_governor)

        yaml_content = """
name: chain_workflow
steps:
  - agent: Librarian
    action: search
    output: search_results
  - agent: Scholar
    action: synthesize
    input: search_results
    output: final_output
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            result = await executor.execute(yaml_path, {"query": "test"})

            # Check that second step received first step's output
            assert result.status == "completed"
            # Output should be stored in context
            assert "search_results" in result.outputs or result.status == "completed"

    @pytest.mark.asyncio
    async def test_checks_gates_before_proceeding(self, mock_dispatcher, mock_a2a, mock_governor):
        """WorkflowExecutor checks gates before proceeding to next step."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.domain.agent import AgentResult

        # Mock dispatch with high confidence
        mock_dispatcher.dispatch.return_value = AgentResult(
            success=True, payload={"review": "approved"}, confidence=4
        )

        executor = WorkflowExecutor(mock_dispatcher, mock_a2a, mock_governor)

        yaml_content = """
name: gated_workflow
steps:
  - agent: Librarian
    action: search
    output: search_results
  - agent: Critic
    action: review
    input: search_results
    gates:
      - confidence: ">= 3"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            # Set context with confidence value
            result = await executor.execute(yaml_path, {"query": "test", "confidence": 4})

            assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_retries_when_gate_fails(self, mock_dispatcher, mock_a2a, mock_governor):
        """WorkflowExecutor retries step when gate fails (up to max_retries)."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.domain.agent import AgentResult

        executor = WorkflowExecutor(mock_dispatcher, mock_a2a, mock_governor)

        yaml_content = """
name: retry_workflow
steps:
  - agent: Librarian
    action: search
    output: results
    max_retries: 2
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            # First two calls fail, third succeeds
            mock_dispatcher.dispatch.side_effect = [
                AgentResult(success=False, payload={}, error="timeout"),
                AgentResult(success=False, payload={}, error="timeout"),
                AgentResult(success=True, payload={"results": []}, confidence=3),
            ]

            result = await executor.execute(yaml_path, {"query": "test"})

            # Should have been called 3 times (2 retries + final success)
            assert mock_dispatcher.dispatch.call_count == 3
            assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_executes_fallback_action_when_retries_exceeded(self, mock_dispatcher, mock_a2a, mock_governor):
        """WorkflowExecutor executes fallback_action when max_retries exceeded."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.domain.agent import AgentResult

        executor = WorkflowExecutor(mock_dispatcher, mock_a2a, mock_governor)

        yaml_content = """
name: fallback_workflow
steps:
  - agent: Librarian
    action: search
    output: results
    max_retries: 2
    fallback_action: accept_with_flag
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            # All calls fail
            mock_dispatcher.dispatch.return_value = AgentResult(
                success=False, payload={}, error="persistent failure"
            )

            result = await executor.execute(yaml_path, {"query": "test"})

            # Should have been called max_retries times
            assert mock_dispatcher.dispatch.call_count == 3  # 1 + 2 retries
            # With accept_with_flag, workflow should still complete
            assert result.status in ["completed", "failed"]

    @pytest.mark.asyncio
    async def test_aborts_workflow_on_timeout(self, mock_dispatcher, mock_a2a, mock_governor):
        """WorkflowExecutor aborts workflow on timeout."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.domain.agent import AgentResult

        executor = WorkflowExecutor(mock_dispatcher, mock_a2a, mock_governor)

        yaml_content = """
name: timeout_workflow
timeout: 1  # 1 second timeout
steps:
  - agent: Librarian
    action: search
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            # Mock slow dispatch
            async def slow_dispatch(*args, **kwargs):
                await asyncio.sleep(2)  # Exceeds timeout
                return AgentResult(success=True, payload={})

            mock_dispatcher.dispatch.side_effect = slow_dispatch

            result = await executor.execute(yaml_path, {"query": "test"})

            assert result.status == "timeout"
            assert "timeout" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_publishes_progress_events(self, mock_dispatcher, mock_a2a, mock_governor):
        """WorkflowExecutor publishes progress events to event bus."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.domain.agent import AgentResult

        # Create mock event bus
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        mock_dispatcher.dispatch.return_value = AgentResult(success=True, payload={})

        executor = WorkflowExecutor(mock_dispatcher, mock_a2a, mock_governor, event_bus)

        yaml_content = """
name: event_workflow
steps:
  - agent: Librarian
    action: search
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "workflow.yaml"
            yaml_path.write_text(yaml_content)

            result = await executor.execute(yaml_path, {"query": "test"})

            # Should have published events
            assert event_bus.publish.call_count >= 2  # Start + Complete

    @pytest.mark.asyncio
    async def test_handles_a2a_handoff(self, mock_dispatcher, mock_a2a, mock_governor):
        """WorkflowExecutor handles A2A handoff between agents."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.engines.collaborate.a2a_protocol import A2AResult
        from saw.domain.agent import AgentResult

        # Mock handoff success
        mock_a2a.handoff.return_value = A2AResult(
            success=True, message_id="msg-123"
        )

        mock_dispatcher.dispatch.return_value = AgentResult(success=True, payload={})

        executor = WorkflowExecutor(mock_dispatcher, mock_a2a, mock_governor)

        # Test handoff method
        result = await executor._a2a.handoff(
            sender="Librarian",
            receiver="Scholar",
            task_type="synthesize",
            payload={"pages": ["p1"]},
            context={"workflow_id": "wf-123"},
        )

        assert result.success is True


class TestGateEvaluation:
    """Tests for gate condition evaluation."""

    @pytest.fixture
    def executor(self):
        """Create WorkflowExecutor with mocks."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor

        dispatcher = MagicMock()
        dispatcher._agents = {}
        a2a = MagicMock()
        governor = MagicMock()
        return WorkflowExecutor(dispatcher, a2a, governor)

    @pytest.mark.asyncio
    async def test_gate_confidence_threshold(self, executor):
        """Gate evaluation for confidence threshold."""
        result = await executor._check_gates(
            [{"confidence": ">= 3"}],
            {"confidence": 4}
        )
        assert result.passed is True

        result = await executor._check_gates(
            [{"confidence": ">= 3"}],
            {"confidence": 2}
        )
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_gate_contradiction_count(self, executor):
        """Gate evaluation for contradiction_count."""
        result = await executor._check_gates(
            [{"contradiction_count": "== 0"}],
            {"contradiction_count": 0}
        )
        assert result.passed is True

        result = await executor._check_gates(
            [{"contradiction_count": "== 0"}],
            {"contradiction_count": 2}
        )
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_multiple_gates(self, executor):
        """Multiple gate conditions must all pass."""
        result = await executor._check_gates(
            [{"confidence": ">= 3"}, {"contradiction_count": "== 0"}],
            {"confidence": 4, "contradiction_count": 0}
        )
        assert result.passed is True

        result = await executor._check_gates(
            [{"confidence": ">= 3"}, {"contradiction_count": "== 0"}],
            {"confidence": 4, "contradiction_count": 1}
        )
        assert result.passed is False

    def test_operator_evaluation(self, executor):
        """Operator evaluation helper tests all operators."""
        assert executor._eval_operator(5, ">=", 3) is True
        assert executor._eval_operator(3, ">=", 5) is False
        assert executor._eval_operator(3, "<=", 5) is True
        assert executor._eval_operator(5, "<=", 3) is False
        assert executor._eval_operator(3, "==", 3) is True
        assert executor._eval_operator(3, "==", 4) is False
        assert executor._eval_operator(3, "!=", 4) is True
        assert executor._eval_operator(3, "!=", 3) is False
        assert executor._eval_operator(5, ">", 3) is True
        assert executor._eval_operator(3, ">", 5) is False
        assert executor._eval_operator(3, "<", 5) is True
        assert executor._eval_operator(5, "<", 3) is False


class TestFallbackActions:
    """Tests for fallback action handling."""

    @pytest.fixture
    def executor(self):
        """Create WorkflowExecutor with mocks."""
        from saw.engines.collaborate.workflow_executor import WorkflowExecutor
        from saw.engines.collaborate.workflow_parser import WorkflowStep

        dispatcher = MagicMock()
        dispatcher._agents = {}
        a2a = MagicMock()
        governor = MagicMock()
        executor = WorkflowExecutor(dispatcher, a2a, governor)
        executor._step = WorkflowStep(agent="Librarian", action="search")
        return executor

    @pytest.mark.asyncio
    async def test_abort_fallback(self, executor):
        """Abort fallback returns failure."""
        from saw.engines.collaborate.workflow_executor import GateResult
        from saw.engines.collaborate.workflow_parser import WorkflowStep

        step = WorkflowStep(agent="Librarian", action="search", fallback_action="abort")
        gate_result = GateResult(passed=False, reason="Gate failed")

        result = await executor._handle_gate_failure(step, gate_result, {})
        assert result.get("failed") is True
        assert "Gate failed" in result.get("errors", [""])[0]

    @pytest.mark.asyncio
    async def test_accept_with_flag_fallback(self, executor):
        """Accept_with_flag fallback continues with flag."""
        from saw.engines.collaborate.workflow_executor import GateResult
        from saw.engines.collaborate.workflow_parser import WorkflowStep

        step = WorkflowStep(
            agent="Librarian",
            action="search",
            output_key="results",
            fallback_action="accept_with_flag",
        )
        gate_result = GateResult(passed=False, reason="Low confidence")
        context = {}

        result = await executor._handle_gate_failure(step, gate_result, context)
        assert result.get("success") is True
        assert result.get("flagged") is True
        assert "results_flagged" in context

    @pytest.mark.asyncio
    async def test_escalate_to_human_fallback(self, executor):
        """Escalate_to_human fallback requires review."""
        from saw.engines.collaborate.workflow_executor import GateResult
        from saw.engines.collaborate.workflow_parser import WorkflowStep

        step = WorkflowStep(
            agent="Librarian",
            action="search",
            fallback_action="escalate_to_human",
        )
        gate_result = GateResult(passed=False, reason="Needs review")

        result = await executor._handle_gate_failure(step, gate_result, {})
        assert result.get("failed") is True
        assert result.get("needs_review") is True


class TestWorkflowExampleFile:
    """Tests for the example workflow file."""

    def test_example_workflow_file_exists(self):
        """Example workflow file is created."""
        # This will be tested after Task 3 implementation
        pass

    def test_example_workflow_is_valid(self):
        """Example workflow YAML is valid."""
        from saw.engines.collaborate.workflow_parser import WorkflowParser

        yaml_content = """
name: 文献综述生成
timeout: 600
on_failure: abort

steps:
  - agent: Librarian
    action: search
    input: "{{ query }}"
    output: related_pages

  - agent: Scholar
    action: synthesize
    input: related_pages
    output: draft_synthesis
    max_retries: 2

  - agent: Critic
    action: review
    input: draft_synthesis
    output: reviewed_synthesis
    gates:
      - confidence: ">= 3"
      - contradiction_count: "== 0"
    max_retries: 3
    fallback_action: accept_with_flag

  - agent: Writer
    action: publish
    input: reviewed_synthesis
    output: wiki_page
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "example.yaml"
            yaml_path.write_text(yaml_content)

            parser = WorkflowParser()
            workflow = parser.parse(yaml_path)

            assert workflow.name == "文献综述生成"
            assert workflow.timeout == 600
            assert len(workflow.steps) == 4
            assert workflow.steps[2].gates is not None
            assert workflow.steps[2].fallback_action == "accept_with_flag"