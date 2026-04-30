"""Bulk import/export operations for API platform.

Phase 6: API Platform — Bulk operations.
Per APIP-06: Bulk import/export via API.

Supports JSON, CSV, and Markdown formats.
"""
from __future__ import annotations

import csv
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from io import StringIO
from typing import Any, List, Optional


class ImportFormat(str, Enum):
    """Import format types."""
    JSON = "json"
    CSV = "csv"


class ExportFormat(str, Enum):
    """Export format types."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    NDJSON = "ndjson"


@dataclass
class ImportResult:
    """Result of import operation."""
    task_id: str
    status: str  # pending, processing, completed, failed
    format: ImportFormat
    vaults_created: int = 0
    claims_created: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "format": self.format.value,
            "vaults_created": self.vaults_created,
            "claims_created": self.claims_created,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class BulkVaultImport:
    """Bulk vault import data."""
    name: str
    description: Optional[str] = None
    entries: List[dict] = field(default_factory=list)


@dataclass
class BulkClaimImport:
    """Bulk claim import data."""
    content: str
    source: Optional[str] = None
    confidence: Optional[float] = None
    tags: Optional[List[str]] = None


class BulkImportService:
    """Service for bulk import operations."""

    def __init__(self, session=None):
        self.session = session
        self._tasks: dict[str, ImportResult] = {}

    def parse_json_vaults(self, content: str) -> List[BulkVaultImport]:
        """Parse JSON vault import data."""
        data = json.loads(content)
        vaults = []

        for item in data:
            vault = BulkVaultImport(
                name=item.get("name", "Untitled"),
                description=item.get("description"),
                entries=item.get("entries", []),
            )
            vaults.append(vault)

        return vaults

    def parse_csv_claims(self, content: str) -> List[BulkClaimImport]:
        """Parse CSV claim import data."""
        claims = []
        reader = csv.DictReader(StringIO(content))

        for row in reader:
            claim = BulkClaimImport(
                content=row.get("content", ""),
                source=row.get("source"),
                confidence=float(row.get("confidence", 1.0)),
                tags=row.get("tags", "").split(",") if row.get("tags") else None,
            )
            claims.append(claim)

        return claims

    def import_vaults(
        self,
        user_id: str,
        content: str,
        format: ImportFormat,
    ) -> ImportResult:
        """Import vaults from content."""
        task_id = str(uuid.uuid4())
        result = ImportResult(
            task_id=task_id,
            status="pending",
            format=format,
            started_at=datetime.now(timezone.utc),
        )

        try:
            if format == ImportFormat.JSON:
                vaults = self.parse_json_vaults(content)

                for vault_data in vaults:
                    # Create vault (placeholder)
                    result.vaults_created += 1

                    # Create claims for entries
                    for entry in vault_data.entries:
                        result.claims_created += 1

                result.status = "completed"
                result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            result.completed_at = datetime.now(timezone.utc)

        self._tasks[task_id] = result
        return result

    def import_claims(
        self,
        vault_id: str,
        content: str,
        format: ImportFormat,
    ) -> ImportResult:
        """Import claims to a vault from content."""
        task_id = str(uuid.uuid4())
        result = ImportResult(
            task_id=task_id,
            status="pending",
            format=format,
            started_at=datetime.now(timezone.utc),
        )

        try:
            claims = []

            if format == ImportFormat.JSON:
                data = json.loads(content)
                for item in data:
                    claims.append(BulkClaimImport(
                        content=item.get("content", ""),
                        source=item.get("source"),
                        confidence=item.get("confidence"),
                        tags=item.get("tags"),
                    ))

            elif format == ImportFormat.CSV:
                claims = self.parse_csv_claims(content)

            # Create claims (placeholder)
            result.claims_created = len(claims)
            result.status = "completed"
            result.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            result.completed_at = datetime.now(timezone.utc)

        self._tasks[task_id] = result
        return result

    def get_task_status(self, task_id: str) -> Optional[ImportResult]:
        """Get import task status."""
        return self._tasks.get(task_id)


class BulkExportService:
    """Service for bulk export operations."""

    def __init__(self, session=None):
        self.session = session

    def export_vaults_json(
        self,
        vaults: List[dict],
        include_claims: bool = True,
    ) -> str:
        """Export vaults as JSON."""
        data = []

        for vault in vaults:
            vault_data = {
                "id": vault.get("id"),
                "name": vault.get("name"),
                "description": vault.get("description"),
                "created_at": vault.get("created_at"),
            }

            if include_claims:
                vault_data["claims"] = vault.get("claims", [])

            data.append(vault_data)

        return json.dumps(data, indent=2)

    def export_vaults_csv(
        self,
        vaults: List[dict],
    ) -> str:
        """Export vaults as CSV."""
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["id", "name", "description", "created_at"])

        # Data
        for vault in vaults:
            writer.writerow([
                vault.get("id"),
                vault.get("name"),
                vault.get("description"),
                vault.get("created_at"),
            ])

        return output.getvalue()

    def export_vaults_markdown(
        self,
        vaults: List[dict],
        include_claims: bool = True,
    ) -> str:
        """Export vaults as Markdown."""
        lines = []

        for vault in vaults:
            lines.append(f"# {vault.get('name', 'Untitled')}")
            lines.append("")
            lines.append(f"ID: {vault.get('id')}")
            lines.append(f"Created: {vault.get('created_at')}")
            lines.append("")

            if vault.get("description"):
                lines.append(f"**Description:** {vault['description']}")
                lines.append("")

            if include_claims and vault.get("claims"):
                lines.append("## Claims")
                lines.append("")

                for claim in vault["claims"]:
                    lines.append(f"- {claim.get('content', '')}")
                    lines.append(f"  - Confidence: {claim.get('confidence', 'N/A')}")

        return "\n".join(lines)

    def export_claims_ndjson(
        self,
        claims: List[dict],
    ) -> str:
        """Export claims as NDJSON (newline-delimited JSON)."""
        lines = []

        for claim in claims:
            lines.append(json.dumps(claim))

        return "\n".join(lines)

    def export(
        self,
        data: List[dict],
        format: ExportFormat,
        data_type: str = "vaults",
        include_claims: bool = True,
    ) -> str:
        """Export data in specified format."""
        if data_type == "vaults":
            if format == ExportFormat.JSON:
                return self.export_vaults_json(data, include_claims)
            elif format == ExportFormat.CSV:
                return self.export_vaults_csv(data)
            elif format == ExportFormat.MARKDOWN:
                return self.export_vaults_markdown(data, include_claims)

        elif data_type == "claims":
            if format == ExportFormat.JSON:
                return json.dumps(data, indent=2)
            elif format == ExportFormat.CSV:
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=["id", "content", "confidence", "created_at"])
                writer.writeheader()
                for claim in data:
                    writer.writerow(claim)
                return output.getvalue()
            elif format == ExportFormat.NDJSON:
                return self.export_claims_ndjson(data)

        return json.dumps(data)