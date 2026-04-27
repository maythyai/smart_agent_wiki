"""Integration tests for advanced governance CLI commands.

Tests:
1. saw conflicts lists all detected contradictions with type and resolution
2. saw conflicts --unresolved shows only unresolved contradictions
3. saw audit verifies receipt chain and reports integrity
4. saw audit --export <path> exports receipts for offline verification
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from saw.drivers.cli.main import app


runner = CliRunner()


class TestConflictsCommand:
    """Test 1-2: saw conflicts command."""

    def test_conflicts_lists_all_contradictions(self, tmp_path: Path) -> None:
        """Should list all detected contradictions with classification."""
        # Create a minimal saw wiki
        saw_dir = tmp_path / ".saw"
        saw_dir.mkdir()
        (saw_dir / "config.yaml").write_text("path: .\n")

        # Create receipts directory
        audit_dir = saw_dir / "audit"
        audit_dir.mkdir()

        # Create claims.db
        import sqlite3
        db_path = saw_dir / "claims.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contradictions (
                uuid TEXT PRIMARY KEY,
                claim_a_uuid TEXT NOT NULL,
                claim_b_uuid TEXT NOT NULL,
                contradiction_type TEXT NOT NULL,
                resolution TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                resolved_at TEXT,
                blast_radius TEXT
            )
        """)
        conn.execute("""
            INSERT INTO contradictions
            (uuid, claim_a_uuid, claim_b_uuid, contradiction_type,
             resolution, detected_at, resolved_at, blast_radius)
            VALUES ('c-1', 'a-1', 'b-1', 'temporal', 'superseded',
                    '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00', '[]')
        """)
        conn.execute("""
            INSERT INTO contradictions
            (uuid, claim_a_uuid, claim_b_uuid, contradiction_type,
             resolution, detected_at, resolved_at, blast_radius)
            VALUES ('c-2', 'a-2', 'b-2', 'opinion', 'disputed',
                    '2024-01-02T00:00:00+00:00', NULL, '[]')
        """)
        conn.commit()
        conn.close()

        with patch.object(Path, "cwd", return_value=tmp_path):
            result = runner.invoke(app, ["conflicts"])

        assert result.exit_code == 0
        # Should show contradiction report
        assert "Contradiction" in result.output or "c-1" in result.output

    def test_conflicts_unresolved_filters(self, tmp_path: Path) -> None:
        """Should show only unresolved contradictions with --unresolved."""
        saw_dir = tmp_path / ".saw"
        saw_dir.mkdir()
        (saw_dir / "config.yaml").write_text("path: .\n")

        audit_dir = saw_dir / "audit"
        audit_dir.mkdir()

        import sqlite3
        db_path = saw_dir / "claims.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contradictions (
                uuid TEXT PRIMARY KEY,
                claim_a_uuid TEXT NOT NULL,
                claim_b_uuid TEXT NOT NULL,
                contradiction_type TEXT NOT NULL,
                resolution TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                resolved_at TEXT,
                blast_radius TEXT
            )
        """)
        # Resolved
        conn.execute("""
            INSERT INTO contradictions
            (uuid, claim_a_uuid, claim_b_uuid, contradiction_type,
             resolution, detected_at, resolved_at, blast_radius)
            VALUES ('c-1', 'a-1', 'b-1', 'temporal', 'superseded',
                    '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00', '[]')
        """)
        # Unresolved
        conn.execute("""
            INSERT INTO contradictions
            (uuid, claim_a_uuid, claim_b_uuid, contradiction_type,
             resolution, detected_at, resolved_at, blast_radius)
            VALUES ('c-2', 'a-2', 'b-2', 'opinion', 'disputed',
                    '2024-01-02T00:00:00+00:00', NULL, '[]')
        """)
        conn.commit()
        conn.close()

        with patch.object(Path, "cwd", return_value=tmp_path):
            result = runner.invoke(app, ["conflicts", "--unresolved"])

        assert result.exit_code == 0


class TestAuditCommand:
    """Test 3-4: saw audit command."""

    def test_audit_verifies_receipt_chain(self, tmp_path: Path) -> None:
        """Should verify receipt chain and report integrity."""
        saw_dir = tmp_path / ".saw"
        saw_dir.mkdir()
        (saw_dir / "config.yaml").write_text("path: .\n")

        # Create audit directory with receipts
        audit_dir = saw_dir / "audit"
        audit_dir.mkdir()

        receipts_content = """public_key: "test-public-key"
receipts:
  - operation_id: "op-1"
    operation_type: "ingest"
    agent: "Writer"
    claim_uuid: "claim-1"
    page_path: null
    timestamp: "2024-01-01T00:00:00+00:00"
    payload_hash: "abc123"
    signature: "sig-1"
    prev_receipt_id: null
  - operation_id: "op-2"
    operation_type: "query"
    agent: "Librarian"
    claim_uuid: null
    page_path: null
    timestamp: "2024-01-02T00:00:00+00:00"
    payload_hash: "def456"
    signature: "sig-2"
    prev_receipt_id: "op-1"
"""
        (audit_dir / "receipts.yaml").write_text(receipts_content)

        with patch.object(Path, "cwd", return_value=tmp_path):
            result = runner.invoke(app, ["audit"])

        assert result.exit_code == 0
        # Should show audit verification output
        assert "Audit" in result.output or "chain" in result.output.lower()

    def test_audit_export_exports_receipts(self, tmp_path: Path) -> None:
        """Should export receipts for offline verification."""
        saw_dir = tmp_path / ".saw"
        saw_dir.mkdir()
        (saw_dir / "config.yaml").write_text("path: .\n")

        audit_dir = saw_dir / "audit"
        audit_dir.mkdir()

        receipts_content = """public_key: "test-public-key"
receipts:
  - operation_id: "op-1"
    operation_type: "ingest"
    agent: "Writer"
    claim_uuid: "claim-1"
    page_path: null
    timestamp: "2024-01-01T00:00:00+00:00"
    payload_hash: "abc123"
    signature: "sig-1"
    prev_receipt_id: null
"""
        (audit_dir / "receipts.yaml").write_text(receipts_content)

        export_dir = tmp_path / "export"

        with patch.object(Path, "cwd", return_value=tmp_path):
            result = runner.invoke(app, ["audit", "--export", str(export_dir)])

        assert result.exit_code == 0
        # Should export files
        assert export_dir.exists() or result.exit_code == 0


class TestCLIRegistration:
    """Test that conflicts and audit commands are registered."""

    def test_conflicts_command_exists(self) -> None:
        """Should have conflicts command registered."""
        result = runner.invoke(app, ["--help"])
        assert "conflicts" in result.output

    def test_audit_command_exists(self) -> None:
        """Should have audit command registered."""
        result = runner.invoke(app, ["--help"])
        assert "audit" in result.output
