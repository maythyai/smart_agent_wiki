"""Unit tests for DAG pipeline components."""
import pytest
import asyncio
from saw.ingest.pipeline import (
    PipelinePhase, PipelineContext, PipelineRunner,
    validate_dag, CycleDetectedError, MissingDependencyError,
    PhaseResults, PhaseResult
)
from saw.ingest.pipeline.validator import ValidationResult


class TestDAGValidation:
    """Tests for DAG validation."""

    def test_valid_simple_chain(self):
        """Test simple linear dependency chain."""
        phases = [
            PipelinePhase(name="a", deps=[], execute=lambda c, d: 1),
            PipelinePhase(name="b", deps=["a"], execute=lambda c, d: 2),
            PipelinePhase(name="c", deps=["b"], execute=lambda c, d: 3),
        ]
        result = validate_dag(phases)
        assert result.valid
        assert result.sorted_order == ["a", "b", "c"]

    def test_valid_diamond(self):
        """Test diamond-shaped dependency."""
        phases = [
            PipelinePhase(name="root", deps=[], execute=lambda c, d: 1),
            PipelinePhase(name="left", deps=["root"], execute=lambda c, d: 2),
            PipelinePhase(name="right", deps=["root"], execute=lambda c, d: 3),
            PipelinePhase(name="bottom", deps=["left", "right"], execute=lambda c, d: 4),
        ]
        result = validate_dag(phases)
        assert result.valid
        assert result.sorted_order[0] == "root"
        assert result.sorted_order[-1] == "bottom"

    def test_cycle_detection(self):
        """Test cycle detection with exact path."""
        phases = [
            PipelinePhase(name="a", deps=["c"], execute=lambda c, d: 1),
            PipelinePhase(name="b", deps=["a"], execute=lambda c, d: 2),
            PipelinePhase(name="c", deps=["b"], execute=lambda c, d: 3),
        ]
        result = validate_dag(phases)
        assert not result.valid
        assert result.cycle_path is not None
        # Should report the cycle path
        assert "a" in result.cycle_path
        assert "b" in result.cycle_path
        assert "c" in result.cycle_path

    def test_missing_dependency(self):
        """Test missing dependency detection."""
        phases = [
            PipelinePhase(name="a", deps=[], execute=lambda c, d: 1),
            PipelinePhase(name="b", deps=["nonexistent"], execute=lambda c, d: 2),
        ]
        result = validate_dag(phases)
        assert not result.valid
        assert result.missing_deps == [("b", "nonexistent")]

    def test_empty_phases(self):
        """Test empty phase list."""
        phases = []
        result = validate_dag(phases)
        assert result.valid
        assert result.sorted_order == []

    def test_single_phase(self):
        """Test single phase with no deps."""
        phases = [
            PipelinePhase(name="standalone", deps=[], execute=lambda c, d: 1),
        ]
        result = validate_dag(phases)
        assert result.valid
        assert result.sorted_order == ["standalone"]


class TestPipelineRunner:
    """Tests for pipeline execution."""

    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Test phases execute in order."""
        execution_order = []

        async def make_executor(name):
            async def executor(ctx, deps):
                execution_order.append(name)
                return {"name": name}
            return executor

        phases = [
            PipelinePhase(name="first", deps=[], execute=await make_executor("first")),
            PipelinePhase(name="second", deps=["first"], execute=await make_executor("second")),
        ]

        runner = PipelineRunner(phases)
        ctx = PipelineContext(graph=None, repo_path="/tmp")

        await runner.run(ctx)

        assert execution_order == ["first", "second"]

    @pytest.mark.asyncio
    async def test_deps_filtering(self):
        """Test that phases only see declared dependencies."""
        received_deps = []

        async def executor(ctx, deps):
            received_deps.append(set(deps.names()))
            return {}

        phases = [
            PipelinePhase(name="a", deps=[], execute=executor),
            PipelinePhase(name="b", deps=["a"], execute=executor),
            PipelinePhase(name="c", deps=["b"], execute=executor),  # Should NOT see 'a'
        ]

        runner = PipelineRunner(phases)
        ctx = PipelineContext(graph=None, repo_path="/tmp")

        await runner.run(ctx)

        assert received_deps[0] == set()  # a has no deps
        assert received_deps[1] == {"a"}  # b sees a
        assert received_deps[2] == {"b"}  # c sees only b (not a)

    @pytest.mark.asyncio
    async def test_output_preservation(self):
        """Test that phase outputs are preserved."""
        async def phase_a(ctx, deps):
            return {"value": 42}

        async def phase_b(ctx, deps):
            a_output = deps.get_output("a")
            return {"doubled": a_output["value"] * 2}

        phases = [
            PipelinePhase(name="a", deps=[], execute=phase_a),
            PipelinePhase(name="b", deps=["a"], execute=phase_b),
        ]

        runner = PipelineRunner(phases)
        ctx = PipelineContext(graph=None, repo_path="/tmp")

        results = await runner.run(ctx)

        assert results.get_output("a") == {"value": 42}
        assert results.get_output("b") == {"doubled": 84}

    def test_execution_order(self):
        """Test get_execution_order returns correct order."""
        phases = [
            PipelinePhase(name="c", deps=["b"], execute=lambda c, d: 3),
            PipelinePhase(name="a", deps=[], execute=lambda c, d: 1),
            PipelinePhase(name="b", deps=["a"], execute=lambda c, d: 2),
        ]

        runner = PipelineRunner(phases)
        order = runner.get_execution_order()

        assert order[0] == "a"
        assert order[1] == "b"
        assert order[2] == "c"


class TestPhaseResults:
    """Tests for PhaseResults collection."""

    def test_add_and_get(self):
        """Test adding and getting results."""
        results = PhaseResults()
        result = PhaseResult(name="test", output={"key": "value"}, duration_ms=100.0)

        results.add(result)
        retrieved = results.get("test")

        assert retrieved.name == "test"
        assert retrieved.output == {"key": "value"}

    def test_get_output_type_safe(self):
        """Test type-safe output access."""
        results = PhaseResults()
        results.add(PhaseResult(name="test", output={"value": 42}, duration_ms=100.0))

        output = results.get_output("test")
        assert output["value"] == 42

    def test_has_method(self):
        """Test checking if phase exists."""
        results = PhaseResults()

        assert not results.has("missing")

        results.add(PhaseResult(name="exists", output={}, duration_ms=100.0))
        assert results.has("exists")

    def test_names_method(self):
        """Test getting all phase names."""
        results = PhaseResults()
        results.add(PhaseResult(name="a", output={}, duration_ms=1.0))
        results.add(PhaseResult(name="b", output={}, duration_ms=2.0))

        names = results.names()
        assert set(names) == {"a", "b"}

    def test_get_nonexistent_raises(self):
        """Test that getting nonexistent phase raises error."""
        results = PhaseResults()

        from saw.ingest.pipeline.errors import PhaseNotFoundError
        with pytest.raises(PhaseNotFoundError):
            results.get("nonexistent")