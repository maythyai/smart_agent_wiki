"""Structured-data extractors (JSON / CSV / TSV) for ingestion.

F-INGEST-03: the classifier produced JSON/TABLE formats but no extractor
handled them, so .json/.csv/.tsv ingestion always errored with "no extractor".
These extractors create one claim per record/row (offline, rule-based — no
LLM required).
"""
from __future__ import annotations

import csv
import io
import json
import uuid
from pathlib import Path

from saw.domain.claims import Claim
from saw.domain.entities import Entity, EntityRelation
from saw.engines.ingest.extractors.markdown import ExtractionResult


class JSONExtractor:
    """Extract claims from JSON / JSONL files."""

    def extract(self, file_path: Path, source_uuid: str) -> ExtractionResult:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        stripped = text.strip()

        records: list = []
        if stripped and stripped[0] not in "[{":
            # JSONL: one value per line.
            for line in stripped.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        else:
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                data = None
            if isinstance(data, list):
                records = data
            elif data is not None:
                records = [data]

        claims: list[Claim] = []
        for rec in records:
            content = self._render(rec)
            if not content:
                continue
            claims.append(
                Claim(
                    uuid=str(uuid.uuid4()),
                    content=content,
                    source_uuid=source_uuid,
                    content_hash=Claim.compute_hash(content),
                )
            )

        return ExtractionResult(
            claims=claims,
            entities=[],
            relations=[],
            metadata={
                "source_file": str(file_path),
                "records_extracted": len(claims),
                "format": "json",
            },
        )

    @staticmethod
    def _render(rec) -> str:
        if isinstance(rec, dict):
            return "; ".join(f"{k}: {v}" for k, v in rec.items())
        return str(rec) if rec != "" else ""


class TableExtractor:
    """Extract claims from CSV / TSV files (one claim per row)."""

    def extract(self, file_path: Path, source_uuid: str) -> ExtractionResult:
        delimiter = "\t" if file_path.suffix == ".tsv" else ","
        text = file_path.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

        claims: list[Claim] = []
        for row in reader:
            content = "; ".join(f"{k}: {v}" for k, v in row.items() if v)
            if content:
                claims.append(
                    Claim(
                        uuid=str(uuid.uuid4()),
                        content=content,
                        source_uuid=source_uuid,
                        content_hash=Claim.compute_hash(content),
                    )
                )

        return ExtractionResult(
            claims=claims,
            entities=[],
            relations=[],
            metadata={
                "source_file": str(file_path),
                "rows_extracted": len(claims),
                "format": "table",
            },
        )
