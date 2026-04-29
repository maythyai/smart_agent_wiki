"""Cedar Policy Engine with Python binding and CLI fallback.

Per PLAN.md Task 1: PolicyEngine protocol with cedar-python + CLI fallback.
Per PITFALLS.md Pitfall 13: cedar-python 0.1.4 is experimental.
Per D-14: Default deny policy - unpermitted actions return False.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@runtime_checkable
class PolicyEngine(Protocol):
    """Protocol for policy engine implementations.

    Supports multiple backends (cedar-python, Cedar CLI) with unified interface.
    """

    def is_authorized(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> bool:
        """Check if a principal is authorized to perform an action on a resource.

        Args:
            principal: Entity string (e.g., 'Agent::"Librarian"')
            action: Action string (e.g., 'Action::"saw_ingest"')
            resource: Resource string (e.g., 'Resource::"wiki"')
            context: Optional context for conditional policies

        Returns:
            True if authorized, False otherwise
        """
        ...

    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> "PolicyDecision":
        """Evaluate policy and return detailed decision.

        Args:
            principal: Entity string
            action: Action string
            resource: Resource string
            context: Optional context for conditional policies

        Returns:
            PolicyDecision with allowed status and details
        """
        ...


@dataclass
class PolicyDecision:
    """Result of a policy evaluation.

    Per D-14: Default deny - unpermitted actions return allowed=False.
    """

    allowed: bool
    reason: str | None = None
    policy_id: str | None = None


class CedarPythonAdapter:
    """cedar-python binding adapter (preferred when available).

    Per PITFALLS.md Pitfall 13: cedar-python is experimental.
    Falls back to CLI adapter if import fails.
    """

    def __init__(self, policy_path: Path, schema_path: Path | None = None) -> None:
        """Initialize cedar-python adapter.

        Args:
            policy_path: Path to Cedar policy file
            schema_path: Optional path to Cedar schema file
        """
        self._policy_path = policy_path
        self._schema_path = schema_path
        self._policy_set = None
        self._authorizer = None
        self._available = False

        # Try to load cedar-python
        try:
            from cedar import PolicySet, Authorizer

            self._policy_set = PolicySet.from_file(str(policy_path))
            self._authorizer = Authorizer()
            self._available = True
            logger.info(f"cedar-python loaded successfully from {policy_path}")
        except ImportError as e:
            logger.warning(f"cedar-python not available: {e}. Will use CLI fallback.")
        except Exception as e:
            logger.error(f"cedar-python initialization failed: {e}")

    @property
    def available(self) -> bool:
        """Check if cedar-python is available."""
        return self._available

    def is_authorized(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> bool:
        """Check authorization using cedar-python."""
        return self.evaluate(principal, action, resource, context).allowed

    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> PolicyDecision:
        """Evaluate policy using cedar-python.

        Raises:
            RuntimeError: If cedar-python is not available
        """
        if not self._available:
            raise RuntimeError("cedar-python not available, use CLI adapter")

        try:
            from cedar import Request, Entity

            request = Request(
                principal=Entity(principal),
                action=Entity(action),
                resource=Entity(resource),
                context=context or {},
            )
            decision = self._authorizer.is_authorized(request, self._policy_set)

            logger.debug(
                f"Cedar decision: {decision.decision} for {principal}/{action}/{resource}"
            )
            return PolicyDecision(
                allowed=decision.decision == "Allow",
                reason=decision.reason if hasattr(decision, "reason") else None,
                policy_id=decision.policy_id if hasattr(decision, "policy_id") else None,
            )
        except Exception as e:
            logger.error(f"cedar-python evaluation failed: {e}")
            raise


class CedarCLIAdapter:
    """Cedar CLI subprocess adapter (fallback).

    Per PITFALLS.md Pitfall 13: Use CLI subprocess as authoritative fallback.
    """

    def __init__(
        self,
        policy_path: Path,
        schema_path: Path | None = None,
        cedar_bin: str = "cedar",
        timeout: int = 30,
    ) -> None:
        """Initialize Cedar CLI adapter.

        Args:
            policy_path: Path to Cedar policy file
            schema_path: Optional path to Cedar schema file
            cedar_bin: Path to cedar CLI binary
            timeout: Timeout in seconds for CLI calls
        """
        self._policy_path = policy_path
        self._schema_path = schema_path
        self._cedar_bin = cedar_bin
        self._timeout = timeout

    def is_authorized(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> bool:
        """Check authorization using Cedar CLI."""
        return self.evaluate(principal, action, resource, context).allowed

    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> PolicyDecision:
        """Evaluate policy using Cedar CLI subprocess.

        Returns PolicyDecision with allowed=False on any error (fail-secure).
        """
        request_data = {
            "principal": principal,
            "action": action,
            "resource": resource,
            "context": context or {},
        }

        # Use TemporaryDirectory for atomic cleanup (fixes TOCTOU vulnerability)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                request_file = os.path.join(tmpdir, "request.json")
                # Set restrictive permissions
                os.chmod(tmpdir, 0o700)
                with open(request_file, "w", encoding="utf-8") as f:
                    os.chmod(request_file, 0o600)
                    json.dump(request_data, f)

                cmd = [
                    self._cedar_bin,
                    "authorize",
                    "--policies",
                    str(self._policy_path),
                    "--request-json",
                    request_file,
                ]
                if self._schema_path:
                    cmd.extend(["--schema", str(self._schema_path)])

                logger.debug(f"Running Cedar CLI: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                )

                allowed = result.returncode == 0
                reason = result.stderr.strip() if not allowed else None

                logger.info(
                    f"Cedar CLI decision: {'Allow' if allowed else 'Deny'} for {principal}/{action}/{resource}"
                )
                return PolicyDecision(allowed=allowed, reason=reason)
        except subprocess.TimeoutExpired:
            logger.error("Cedar CLI timeout")
            return PolicyDecision(allowed=False, reason="CLI timeout")
        except FileNotFoundError:
            logger.error(f"Cedar CLI not found at {self._cedar_bin}")
            return PolicyDecision(allowed=False, reason="CLI not found")
        except Exception as e:
            logger.error(f"Cedar CLI error: {e}")
            return PolicyDecision(allowed=False, reason=f"CLI error: {e}")


class CedarPolicyEngine:
    """Unified Cedar policy engine with automatic backend selection.

    Per D-14: Default deny policy - any evaluation failure returns False.
    Per PITFALLS.md Pitfall 13: Auto-fallback from cedar-python to CLI.
    """

    def __init__(self, policy_path: Path, schema_path: Path | None = None) -> None:
        """Initialize policy engine with automatic backend selection.

        Args:
            policy_path: Path to Cedar policy file
            schema_path: Optional path to Cedar schema file
        """
        self._python_adapter = CedarPythonAdapter(policy_path, schema_path)
        self._cli_adapter = CedarCLIAdapter(policy_path, schema_path)
        self._use_cli = not self._python_adapter.available

        if self._use_cli:
            logger.info("Using Cedar CLI adapter (cedar-python unavailable)")

    def is_authorized(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> bool:
        """Check if authorized (convenience method).

        Per D-14: Default deny - returns False on any error.
        """
        return self.evaluate(principal, action, resource, context).allowed

    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> PolicyDecision:
        """Evaluate policy with automatic backend selection.

        Per D-14: Default deny policy - any failure returns allowed=False.
        """
        try:
            if self._use_cli:
                return self._cli_adapter.evaluate(principal, action, resource, context)
            else:
                return self._python_adapter.evaluate(
                    principal, action, resource, context
                )
        except Exception as e:
            logger.error(f"Policy evaluation failed: {e}")
            # Per D-14: Fail-secure - return deny on any error
            return PolicyDecision(allowed=False, reason=f"Evaluation error: {e}")
