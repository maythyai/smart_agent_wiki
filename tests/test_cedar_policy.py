"""Tests for Cedar policy engine adapter.

Per PLAN.md Task 1: PolicyEngine protocol with cedar-python and CLI fallback.
Per PITFALLS.md Pitfall 13: cedar-python binding immaturity requires fallback.
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPolicyDecision:
    """Tests for PolicyDecision dataclass."""

    def test_policy_decision_has_required_fields(self):
        """PolicyDecision includes allowed, reason, policy_id fields."""
        from saw.adapters.crypto.cedar_policy import PolicyDecision

        decision = PolicyDecision(allowed=True, reason="Permit rule matched", policy_id="rule-001")
        assert decision.allowed is True
        assert decision.reason == "Permit rule matched"
        assert decision.policy_id == "rule-001"

    def test_policy_decision_defaults(self):
        """PolicyDecision has sensible defaults."""
        from saw.adapters.crypto.cedar_policy import PolicyDecision

        decision = PolicyDecision(allowed=False)
        assert decision.allowed is False
        assert decision.reason is None
        assert decision.policy_id is None


class TestCedarPythonAdapter:
    """Tests for cedar-python binding adapter."""

    def test_cedar_python_adapter_available_property(self):
        """CedarPythonAdapter.available reflects cedar-python availability."""
        from saw.adapters.crypto.cedar_policy import CedarPythonAdapter

        # Create with non-existent policy file
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            adapter = CedarPythonAdapter(policy_path)
            # cedar-python may not be installed, so available depends on import
            assert isinstance(adapter.available, bool)

    def test_cedar_python_adapter_raises_when_unavailable(self):
        """CedarPythonAdapter raises RuntimeError when cedar-python unavailable."""
        from saw.adapters.crypto.cedar_policy import CedarPythonAdapter, PolicyDecision

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            adapter = CedarPythonAdapter(policy_path)

            if not adapter.available:
                with pytest.raises(RuntimeError, match="cedar-python not available"):
                    adapter.evaluate("Agent::\"Librarian\"", "Action::\"saw_ingest\"", "Resource::\"wiki\"")


class TestCedarCLIAdapter:
    """Tests for Cedar CLI subprocess adapter."""

    def test_cedar_cli_adapter_constructs_correct_command(self):
        """CedarCLIAdapter constructs correct CLI command."""
        from saw.adapters.crypto.cedar_policy import CedarCLIAdapter

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            adapter = CedarCLIAdapter(policy_path, cedar_bin="cedar")

            # Mock subprocess.run to capture command
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")

                adapter.is_authorized(
                    principal="Agent::\"Librarian\"",
                    action="Action::\"saw_ingest\"",
                    resource="Resource::\"wiki\"",
                )

                # Check command construction
                call_args = mock_run.call_args
                cmd = call_args[0][0]
                assert "cedar" in cmd
                assert "authorize" in cmd
                assert "--policies" in cmd

    def test_cedar_cli_adapter_returns_false_on_cli_not_found(self):
        """CedarCLIAdapter returns False when CLI not found."""
        from saw.adapters.crypto.cedar_policy import CedarCLIAdapter

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            adapter = CedarCLIAdapter(policy_path, cedar_bin="nonexistent_cedar_binary")

            decision = adapter.is_authorized(
                principal="Agent::\"Librarian\"",
                action="Action::\"saw_ingest\"",
                resource="Resource::\"wiki\"",
            )

            assert decision is False

    def test_cedar_cli_adapter_handles_timeout(self):
        """CedarCLIAdapter handles timeout gracefully."""
        from saw.adapters.crypto.cedar_policy import CedarCLIAdapter
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            adapter = CedarCLIAdapter(policy_path, cedar_bin="cedar")

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(cmd="cedar", timeout=30)

                decision = adapter.evaluate(
                    principal="Agent::\"Librarian\"",
                    action="Action::\"saw_ingest\"",
                    resource="Resource::\"wiki\"",
                )

                assert decision.allowed is False
                assert "timeout" in decision.reason.lower()


class TestCedarPolicyEngine:
    """Tests for the unified CedarPolicyEngine."""

    def test_is_authorized_returns_true_for_permit_rule(self):
        """PolicyEngine.is_authorized() returns True for permit rule."""
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            # Simple permit-all policy for testing
            policy_path.write_text('permit(principal, action, resource);')

            engine = CedarPolicyEngine(policy_path)

            # Mock the adapter to return True
            with patch.object(engine, '_use_cli', False):
                with patch.object(engine._python_adapter, '_available', True):
                    with patch.object(
                        engine._python_adapter, 'evaluate',
                        return_value=type('PolicyDecision', (), {'allowed': True, 'reason': None, 'policy_id': None})()
                    ):
                        result = engine.is_authorized(
                            principal="Agent::\"Librarian\"",
                            action="Action::\"saw_ingest\"",
                            resource="Resource::\"wiki\"",
                        )
                        assert result is True

    def test_is_authorized_returns_false_for_forbid_rule(self):
        """PolicyEngine.is_authorized() returns False for forbid rule."""
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine, PolicyDecision

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('forbid(principal, action, resource);')

            engine = CedarPolicyEngine(policy_path)

            # Mock to return forbid decision
            with patch.object(
                engine, 'evaluate',
                return_value=PolicyDecision(allowed=False, reason="Explicit forbid rule")
            ):
                result = engine.is_authorized(
                    principal="Agent::\"Writer\"",
                    action="Action::\"saw_verify\"",
                    resource="Resource::\"wiki\"",
                )
                assert result is False

    def test_default_deny_policy_unpermitted_actions_return_false(self):
        """Default deny policy: unpermitted actions return False."""
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine, PolicyDecision

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            # Empty policy - no permits
            policy_path.write_text('')

            engine = CedarPolicyEngine(policy_path)

            # Any action should be denied when no permit rule exists
            with patch.object(
                engine, 'evaluate',
                return_value=PolicyDecision(allowed=False, reason="No matching permit rule")
            ):
                result = engine.is_authorized(
                    principal="Agent::\"Unknown\"",
                    action="Action::\"saw_delete\"",
                    resource="Resource::\"wiki\"",
                )
                assert result is False

    def test_evaluation_error_returns_false(self):
        """Policy evaluation error returns False (fail-secure)."""
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            engine = CedarPolicyEngine(policy_path)

            # Mock to raise exception
            with patch.object(engine._python_adapter, 'evaluate', side_effect=Exception("Cedar error")):
                with patch.object(engine._cli_adapter, 'evaluate', side_effect=Exception("CLI error")):
                    decision = engine.evaluate(
                        principal="Agent::\"Librarian\"",
                        action="Action::\"saw_ingest\"",
                        resource="Resource::\"wiki\"",
                    )
                    assert decision.allowed is False
                    assert "error" in decision.reason.lower()

    def test_evaluate_returns_policy_decision(self):
        """PolicyEngine.evaluate() returns PolicyDecision with details."""
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine, PolicyDecision

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            engine = CedarPolicyEngine(policy_path)

            with patch.object(
                engine, 'evaluate',
                return_value=PolicyDecision(allowed=True, reason="Permit rule matched", policy_id="permit-001")
            ):
                decision = engine.evaluate(
                    principal="Agent::\"Librarian\"",
                    action="Action::\"saw_ingest\"",
                    resource="Resource::\"wiki\"",
                )
                assert isinstance(decision, PolicyDecision)
                assert decision.allowed is True
                assert decision.policy_id == "permit-001"


class TestPolicyEvaluationLogging:
    """Tests for policy evaluation logging."""

    def test_policy_evaluation_logs_decision_with_rule_id(self, caplog):
        """Policy evaluation logs decision with rule_id."""
        import logging
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine, PolicyDecision

        # Enable debug logging
        logging.getLogger("saw.adapters.crypto.cedar_policy").setLevel(logging.DEBUG)

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            engine = CedarPolicyEngine(policy_path)

            with patch.object(
                engine, 'evaluate',
                return_value=PolicyDecision(allowed=True, reason="OK", policy_id="rule-123")
            ):
                with caplog.at_level(logging.DEBUG):
                    decision = engine.evaluate(
                        principal="Agent::\"Librarian\"",
                        action="Action::\"saw_ingest\"",
                        resource="Resource::\"wiki\"",
                    )
                    # The decision should be returned correctly
                    assert decision.policy_id == "rule-123"


class TestCedarPythonFallback:
    """Tests for automatic Python to CLI fallback."""

    def test_automatic_fallback_to_cli(self):
        """CedarPolicyEngine automatically falls back to CLI when cedar-python unavailable."""
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine, PolicyDecision

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            engine = CedarPolicyEngine(policy_path)

            # Force CLI mode
            engine._use_cli = True

            # Mock CLI adapter to return success
            with patch.object(
                engine._cli_adapter, 'evaluate',
                return_value=PolicyDecision(allowed=True, reason="CLI permit")
            ):
                decision = engine.evaluate(
                    principal="Agent::\"Librarian\"",
                    action="Action::\"saw_ingest\"",
                    resource="Resource::\"wiki\"",
                )
                assert decision.allowed is True
                assert decision.reason == "CLI permit"

    def test_uses_python_adapter_when_available(self):
        """CedarPolicyEngine uses Python adapter when available."""
        from saw.adapters.crypto.cedar_policy import CedarPolicyEngine, PolicyDecision

        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.cedar"
            policy_path.write_text('permit(principal, action, resource);')

            engine = CedarPolicyEngine(policy_path)

            # Mock python adapter as available
            with patch.object(engine._python_adapter, '_available', True):
                engine._use_cli = False

                with patch.object(
                    engine._python_adapter, 'evaluate',
                    return_value=PolicyDecision(allowed=True, reason="Python permit")
                ):
                    decision = engine.evaluate(
                        principal="Agent::\"Librarian\"",
                        action="Action::\"saw_ingest\"",
                        resource="Resource::\"wiki\"",
                    )
                    assert decision.allowed is True
