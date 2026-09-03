"""Workspace isolation — F-P-4 (AC-WS-1, AC-WS-2).

ADR-005 (schema-prefix isolation in a single DB): a ``workspace_id`` column
on claim + a ``user_workspace_auth`` binding. Verifies the isolation
primitive: claims are scoped by workspace, and a user can only reach the
workspaces they are granted.
"""

from __future__ import annotations

from saw.drivers.cli.commands.smoke_harness import build_smoke_context


def _ingest_and_get_claim_uuids() -> tuple:
    """Build a fresh context, ingest, return (ctx, [claim uuids])."""
    ctx = build_smoke_context()
    from saw.drivers.cli.commands.smoke_harness import _ingest_fixture

    _ingest_fixture(ctx)
    rows = ctx.conn.execute(
        "SELECT uuid FROM claim WHERE deleted_at IS NULL"
    ).fetchall()
    return ctx, [r[0] for r in rows]


def test_workspace_data_isolation() -> None:
    """AC-WS-1: claims in workspace A are not visible via workspace B."""
    ctx, uuids = _ingest_and_get_claim_uuids()
    try:
        assert len(uuids) >= 2
        repo = ctx.claims_repo
        # Assign claims to two workspaces.
        repo.set_workspace(uuids[0], "ws-A")
        repo.set_workspace(uuids[1], "ws-B")

        a_claims = repo.list_by_workspace("ws-A")
        b_claims = repo.list_by_workspace("ws-B")

        a_uuids = {c.uuid for c in a_claims}
        b_uuids = {c.uuid for c in b_claims}
        assert uuids[0] in a_uuids and uuids[0] not in b_uuids, (
            "ws-A claim leaked into ws-B"
        )
        assert uuids[1] in b_uuids and uuids[1] not in a_uuids, (
            "ws-B claim leaked into ws-A"
        )
        assert not (a_uuids & b_uuids), "workspaces share claims (no isolation)"
    finally:
        ctx.close()


def test_cross_workspace_access_denied() -> None:
    """AC-WS-2: a user granted only ws-A cannot reach ws-B."""
    ctx, _ = _ingest_and_get_claim_uuids()
    try:
        repo = ctx.claims_repo
        repo.grant_workspace_access("user-1", "ws-A", role="editor")
        # Another user gets ws-B.
        repo.grant_workspace_access("user-2", "ws-B", role="editor")

        authorized = repo.user_workspaces("user-1")
        assert authorized == ["ws-A"], f"user-1 authorized for unexpected ws: {authorized}"
        assert "ws-B" not in authorized, (
            "user-1 can reach ws-B (cross-workspace access not denied)"
        )
        # user-2 reaches only ws-B.
        assert repo.user_workspaces("user-2") == ["ws-B"]
    finally:
        ctx.close()


def test_existing_claims_default_workspace() -> None:
    """Backward compat: pre-isolation claims land in the 'default' workspace."""
    ctx, uuids = _ingest_and_get_claim_uuids()
    try:
        defaults = ctx.claims_repo.list_by_workspace("default")
        default_uuids = {c.uuid for c in defaults}
        # Freshly ingested claims (no explicit workspace) are in 'default'.
        assert set(uuids) <= default_uuids, "claims did not default to 'default' workspace"
    finally:
        ctx.close()
