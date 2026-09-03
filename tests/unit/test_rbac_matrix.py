"""RBAC matrix + Cedar hot-reload — F-P-1 (AC-SEC-4, AC-SEC-5).

- AC-SEC-4: every role × permission maps to the documented allow/deny
  (0 privilege escalation). Pins the matrix so a drift regresses the test.
- AC-SEC-5: CedarPolicyEngine.reload() re-reads the policy file without
  restarting the process.
"""

from __future__ import annotations

import pytest

from saw.auth.permissions import Permission, has_permission, get_role_permissions


# ── AC-SEC-4: role × permission matrix ──────────────────────────────

# (role, permission, expected_allowed)
MATRIX = [
    # viewer: READ only
    ("viewer", Permission.READ, True),
    ("viewer", Permission.WRITE, False),
    ("viewer", Permission.ADMIN, False),
    # editor: READ + WRITE
    ("editor", Permission.READ, True),
    ("editor", Permission.WRITE, True),
    ("editor", Permission.ADMIN, False),
    # admin: all
    ("admin", Permission.READ, True),
    ("admin", Permission.WRITE, True),
    ("admin", Permission.ADMIN, True),
]


@pytest.mark.parametrize("role,perm,allowed", MATRIX)
def test_role_permission_matrix(role: str, perm: Permission, allowed: bool) -> None:
    """AC-SEC-4: each role×permission matches the documented matrix."""
    assert has_permission(role, perm) is allowed, (
        f"{role} should {'have' if allowed else 'lack'} {perm.name}"
    )


def test_unknown_role_defaults_read_only() -> None:
    """AC-SEC-4: an unknown role gets the least privilege (READ only)."""
    perms = get_role_permissions("nobody")
    assert perms == [Permission.READ]


def test_no_role_has_more_than_admin() -> None:
    """AC-SEC-4: admin is the maximal role; no role exceeds it."""
    admin_perms = set(get_role_permissions("admin"))
    for role in ("viewer", "editor"):
        assert set(get_role_permissions(role)) <= admin_perms, (
            f"{role} has a permission admin lacks"
        )


# ── AC-SEC-5: Cedar policy hot-reload ───────────────────────────────


def test_cedar_reload_recreates_python_adapter(tmp_path) -> None:
    """AC-SEC-5: reload() re-reads the policy file (no restart)."""
    from saw.adapters.crypto.cedar_policy import CedarPolicyEngine

    policy = tmp_path / "p.cedar"
    policy.write_text('// initial\npermit (principal == User::"a", action, resource);\n')

    engine = CedarPolicyEngine(policy)
    initial_adapter = engine._python_adapter

    # Rewrite the policy file (simulating an operator edit).
    policy.write_text('// edited\npermit (principal == User::"b", action, resource);\n')
    engine.reload()

    # reload() must instantiate a fresh python adapter (re-read the file),
    # distinct from the original — even when cedar-python is absent (the
    # adapter object identity changes; the file path is retained).
    assert engine._python_adapter is not initial_adapter, (
        "reload() did not recreate the python adapter"
    )
    assert engine._policy_path == policy, "reload() lost the policy path"


def test_cedar_reload_does_not_raise_without_backend(tmp_path) -> None:
    """AC-SEC-5: reload() is safe even when neither backend is installed."""
    from saw.adapters.crypto.cedar_policy import CedarPolicyEngine

    engine = CedarPolicyEngine(tmp_path / "absent.cedar")
    # Must not raise; falls back to CLI (hot per-call).
    result = engine.reload()
    assert isinstance(result, bool)
