"""Code AST extractor for ingestion engine - zero LLM extraction.

Per INGE-04: Structured data (code) AST extraction with zero LLM calls.
Per D-08: Zero LLM for structured data (code, JSON, tables).
"""
from __future__ import annotations

import ast
import re
import uuid
from pathlib import Path

from saw.domain.claims import Claim
from saw.domain.entities import Entity
from saw.engines.ingest.extractors.markdown import ExtractionResult


class CodeASTExtractor:
    """Extract claims and entities from code files via AST - ZERO LLM."""

    def extract(self, file_path: Path, source_uuid: str) -> ExtractionResult:
        """Extract from a code file using AST (zero LLM calls).

        Args:
            file_path: Path to the code file.
            source_uuid: UUID of the source document in Vault.

        Returns:
            ExtractionResult with claims, entities, relations, and metadata.
        """
        ext = file_path.suffix.lower()
        content = file_path.read_text(encoding="utf-8", errors="replace")

        claims: list[Claim] = []
        entities: list[Entity] = []
        metadata = {
            "source_file": str(file_path),
            "language": self._detect_language(ext),
            "extraction_method": "ast",
        }

        if ext == ".py":
            claims, entities = self._extract_python(content, file_path, source_uuid)
        else:
            claims, entities = self._extract_generic(content, file_path, source_uuid, ext)

        return ExtractionResult(
            claims=claims,
            entities=entities,
            relations=[],  # Relations from code are implicit
            metadata=metadata,
        )

    def _extract_python(
        self,
        content: str,
        file_path: Path,
        source_uuid: str,
    ) -> tuple[list[Claim], list[Entity]]:
        """Extract from Python code using ast.parse."""
        claims: list[Claim] = []
        entities: list[Entity] = []
        seen_names: set[str] = set()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to regex extraction if AST fails
            return self._extract_generic(content, file_path, source_uuid, ".py")

        # Extract classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                name = node.name
                docstring = ast.get_docstring(node) or ""

                # Claim from class
                claim_content = f"Class {name}: {docstring[:200] if docstring else 'No docstring'}"
                claim = Claim(
                    uuid=str(uuid.uuid4()),
                    content=claim_content,
                    source_uuid=source_uuid,
                    content_hash=Claim.compute_hash(claim_content),
                    tags=["python", "class"],
                )
                claims.append(claim)

                # Entity from class name
                if name not in seen_names:
                    seen_names.add(name)
                    entity = Entity(
                        uuid=str(uuid.uuid4()),
                        name=name,
                        entity_type="class",
                        description=docstring[:100] if docstring else "",
                    )
                    entities.append(entity)

                # Extract methods as entities
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_name = f"{name}.{item.name}"
                        method_docstring = ast.get_docstring(item) or ""

                        if method_name not in seen_names:
                            seen_names.add(method_name)
                            entity = Entity(
                                uuid=str(uuid.uuid4()),
                                name=method_name,
                                entity_type="method",
                                description=method_docstring[:100] if method_docstring else "",
                            )
                            entities.append(entity)

            elif isinstance(node, ast.FunctionDef):
                # Skip if it's a method (already handled above)
                if not any(
                    isinstance(parent, ast.ClassDef)
                    for parent in ast.walk(tree)
                    if hasattr(parent, "body") and node in parent.body
                ):
                    name = node.name
                    docstring = ast.get_docstring(node) or ""

                    # Claim from function
                    args = [arg.arg for arg in node.args.args]
                    sig = f"{name}({', '.join(args)})"
                    claim_content = f"Function {sig}: {docstring[:200] if docstring else 'No docstring'}"
                    claim = Claim(
                        uuid=str(uuid.uuid4()),
                        content=claim_content,
                        source_uuid=source_uuid,
                        content_hash=Claim.compute_hash(claim_content),
                        tags=["python", "function"],
                    )
                    claims.append(claim)

                    if name not in seen_names:
                        seen_names.add(name)
                        entity = Entity(
                            uuid=str(uuid.uuid4()),
                            name=name,
                            entity_type="function",
                            description=docstring[:100] if docstring else "",
                        )
                        entities.append(entity)

        # Extract imports as entities
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name not in seen_names:
                        seen_names.add(name)
                        entity = Entity(
                            uuid=str(uuid.uuid4()),
                            name=name,
                            entity_type="module",
                        )
                        entities.append(entity)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module not in seen_names:
                    seen_names.add(module)
                    entity = Entity(
                        uuid=str(uuid.uuid4()),
                        name=module,
                        entity_type="module",
                    )
                    entities.append(entity)

        return claims, entities

    def _extract_generic(
        self,
        content: str,
        file_path: Path,
        source_uuid: str,
        ext: str,
    ) -> tuple[list[Claim], list[Entity]]:
        """Extract from non-Python code using regex patterns."""
        claims: list[Claim] = []
        entities: list[Entity] = []
        seen_names: set[str] = set()

        # Regex patterns for different languages
        patterns = {
            # JavaScript/TypeScript
            ".js": [
                r"(?:function|const|let|var)\s+(\w+)\s*(?:=|:|\()",
                r"class\s+(\w+)",
            ],
            ".ts": [
                r"(?:function|const|let|var)\s+(\w+)\s*(?:=|:|\()",
                r"class\s+(\w+)",
                r"interface\s+(\w+)",
            ],
            # Go
            ".go": [
                r"func\s+(\w+)",
                r"type\s+(\w+)\s+struct",
            ],
            # Rust
            ".rs": [
                r"fn\s+(\w+)",
                r"struct\s+(\w+)",
                r"enum\s+(\w+)",
            ],
            # Java
            ".java": [
                r"class\s+(\w+)",
                r"(?:public|private|protected)?\s+(?:static)?\s+\w+\s+(\w+)\s*\(",
            ],
        }

        lang_patterns = patterns.get(ext, [])

        for pattern in lang_patterns:
            for match in re.finditer(pattern, content):
                name = match.group(1)
                if name and name not in seen_names:
                    seen_names.add(name)

                    # Create claim
                    claim_content = f"Definition: {name} in {file_path.name}"
                    claim = Claim(
                        uuid=str(uuid.uuid4()),
                        content=claim_content,
                        source_uuid=source_uuid,
                        content_hash=Claim.compute_hash(claim_content),
                        tags=["code", self._detect_language(ext)],
                    )
                    claims.append(claim)

                    # Create entity
                    entity_type = "function" if "func" in pattern or "fn" in pattern else "class"
                    entity = Entity(
                        uuid=str(uuid.uuid4()),
                        name=name,
                        entity_type=entity_type,
                    )
                    entities.append(entity)

        return claims, entities

    def _detect_language(self, ext: str) -> str:
        """Detect programming language from extension."""
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }
        return lang_map.get(ext, "unknown")