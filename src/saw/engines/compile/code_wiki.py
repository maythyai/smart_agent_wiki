"""Code Wiki engine.

Generates repository-level AI documentation from code analysis,
integrating with the existing code_graph and code intelligence capabilities.
"""

from __future__ import annotations

import subprocess
import time
from datetime import datetime
from pathlib import Path

from saw.domain.code_wiki import (
    CodeWikiConfig,
    CodeWikiPage,
    CodeWikiResult,
    CodeWikiStatus,
)
from saw.domain.utils import utcnow


class CodeWikiEngine:
    """Generates and maintains Code Wiki documentation.

    Code Wiki pages are type=reference wiki pages that document
    code modules, APIs, and data models at the repository level.
    They integrate with the wiki compile layer and are indexed
    alongside other wiki pages.
    """

    def __init__(self, wiki_root: Path, llm_router=None, code_graph_engine=None) -> None:
        self._wiki_root = wiki_root
        self._code_wiki_dir = wiki_root / "code"
        self._llm = llm_router
        self._code_graph = code_graph_engine

    async def generate(self, config: CodeWikiConfig) -> CodeWikiResult:
        """Generate or update Code Wiki for a repository."""
        start = time.time()
        self._code_wiki_dir.mkdir(parents=True, exist_ok=True)

        # Get current commit
        commit = self._get_commit_hash(config.repo_path)
        config.commit_hash = commit

        # Scan source files
        source_files = self._scan_sources(config)
        result = CodeWikiResult(total_source_files=len(source_files), commit_hash=commit)

        # Group by module (top-level directories)
        modules = self._group_by_module(source_files, config)

        # Generate overview page
        overview = self._generate_overview(config, modules)
        self._write_page(overview)
        result.pages_generated.append(overview.filename)

        # Generate per-module pages
        (self._code_wiki_dir / "modules").mkdir(parents=True, exist_ok=True)
        for module_name, files in modules.items():
            page_path = self._code_wiki_dir / "modules" / f"{module_name}.md"

            if config.skip_if_exists and page_path.exists():
                result.pages_skipped.append(f"code/modules/{module_name}.md")
                continue

            page = self._generate_module_page(module_name, files, config)
            self._write_page(page)

            if page_path.exists():
                result.pages_updated.append(page.filename)
            else:
                result.pages_generated.append(page.filename)

        result.duration_seconds = time.time() - start
        return result

    async def status(self, config: CodeWikiConfig) -> CodeWikiStatus:
        """Check Code Wiki status for a repository."""
        current_commit = self._get_commit_hash(config.repo_path)
        status_file = self._code_wiki_dir / ".status"

        status = CodeWikiStatus(current_commit=current_commit)

        if self._code_wiki_dir.exists():
            pages = list(self._code_wiki_dir.rglob("*.md"))
            status.pages_count = len(pages)
            status.exists = status.pages_count > 0

        if status_file.exists():
            parts = status_file.read_text().strip().split("\n")
            if parts:
                status.last_commit = parts[0]
                if len(parts) > 1:
                    # F-COMP-06: read the actual generation timestamp from
                    # the status file (was hardcoded to utcnow(), hiding the
                    # real last-generated time).
                    try:
                        status.last_generated = datetime.fromisoformat(parts[1])
                    except (ValueError, TypeError):
                        status.last_generated = utcnow()

        status.is_stale = status.exists and status.last_commit != current_commit
        return status

    async def diff_since_last(self, config: CodeWikiConfig) -> list[str]:
        """Return source files changed since last Code Wiki generation."""
        status_file = self._code_wiki_dir / ".status"
        if not status_file.exists():
            return []

        last_commit = status_file.read_text().strip().split("\n")[0]
        current_commit = self._get_commit_hash(config.repo_path)

        if last_commit == current_commit:
            return []

        return self._git_diff_files(config.repo_path, last_commit, current_commit)

    # ─── Private helpers ───────────────────────────────────────────────

    def _get_commit_hash(self, repo_path: Path) -> str:
        """Get current HEAD commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "unknown"

    def _scan_sources(self, config: CodeWikiConfig) -> list[Path]:
        """Scan repository for source files matching include patterns."""
        repo = config.repo_path / config.target_path if config.target_path else config.repo_path
        files = []
        for pattern in config.include_patterns:
            for f in repo.glob(pattern):
                # Check exclusions
                rel = str(f.relative_to(repo))
                excluded = any(
                    self._matches_pattern(rel, ep) for ep in config.exclude_patterns
                )
                if not excluded:
                    files.append(f)
        return sorted(set(files))

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple glob-like pattern matching."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern.lstrip("*").lstrip("/"))

    def _group_by_module(
        self, files: list[Path], config: CodeWikiConfig
    ) -> dict[str, list[Path]]:
        """Group source files by top-level module directory."""
        repo = config.repo_path / config.target_path if config.target_path else config.repo_path
        modules: dict[str, list[Path]] = {}
        for f in files:
            rel = f.relative_to(repo)
            parts = rel.parts
            if len(parts) > 1:
                module = parts[0]
            else:
                module = "_root"
            modules.setdefault(module, []).append(f)
        return modules

    def _generate_overview(
        self, config: CodeWikiConfig, modules: dict[str, list[Path]]
    ) -> CodeWikiPage:
        """Generate repository overview page.

        When a CodeGraphEngine is attached, enriches the overview with
        architecture and community-detection intelligence.
        """
        repo_name = config.repo_path.name
        module_list = "\n".join(
            f"- **{name}**: {len(files)} files" for name, files in sorted(modules.items())
        )

        content = f"""# {repo_name} — Code Overview

> Auto-generated from code analysis. Source: `{config.repo_path}`
> Last analyzed: {utcnow().strftime('%Y-%m-%d')} | Commit: {config.commit_hash}

## Modules

{module_list}

## Statistics

- Total source files: {sum(len(f) for f in modules.values())}
- Module count: {len(modules)}
- Branch: {config.branch}
"""
        # Enrich with code graph intelligence (best-effort)
        graph_section = self._code_graph_overview_section()
        if graph_section:
            content += "\n" + graph_section

        return CodeWikiPage(
            filename="code/README.md",
            title=f"{repo_name} — Code Overview",
            content=content,
            source_files=[],
            commit_hash=config.commit_hash,
        )

    def _code_graph_overview_section(self) -> str:
        """Build architecture/communities sections from the code graph.

        Returns an empty string when no code graph is attached or any error
        occurs (code wiki generation must never fail because of graph issues).
        """
        if self._code_graph is None:
            return ""
        sections: list[str] = []
        try:
            stats = self._code_graph.stats()
            if stats:
                sections.append("## Code Graph")
                sections.append("")
                sections.append(f"- Nodes: {stats.get('nodes', 0)}")
                sections.append(f"- Edges: {stats.get('edges', 0)}")
                sections.append(f"- Files: {stats.get('files', 0)}")
                sections.append("")
        except Exception:  # noqa: BLE001
            pass

        try:
            communities = self._code_graph.detect_communities()
            if communities:
                sections.append("## Detected Communities")
                sections.append("")
                for i, comm in enumerate(communities[:10], 1):
                    label = getattr(comm, "label", None) or getattr(comm, "name", f"Cluster {i}")
                    size = getattr(comm, "size", None)
                    if size is None:
                        members = getattr(comm, "members", None)
                        size = len(members) if members else "?"
                    sections.append(f"- **{label}** ({size} symbols)")
                sections.append("")
        except Exception:  # noqa: BLE001
            pass

        return "\n".join(sections)

    def _generate_module_page(
        self, module_name: str, files: list[Path], config: CodeWikiConfig
    ) -> CodeWikiPage:
        """Generate documentation for a single module."""
        repo = config.repo_path / config.target_path if config.target_path else config.repo_path
        rel_files = [str(f.relative_to(repo)) for f in files]

        # Analyze file types
        extensions = {}
        for f in files:
            ext = f.suffix
            extensions[ext] = extensions.get(ext, 0) + 1

        ext_summary = ", ".join(f"{ext}: {count}" for ext, count in sorted(extensions.items()))

        # Extract key classes/functions (simple heuristic)
        key_symbols = self._extract_key_symbols(files)

        content = f"""# {module_name}

> Auto-generated from code analysis. Source: `{module_name}/`
> Last analyzed: {utcnow().strftime('%Y-%m-%d')} | Commit: {config.commit_hash}

## Overview

Module `{module_name}` contains {len(files)} source files ({ext_summary}).

## Key Components

{key_symbols}

## Files

"""
        for rf in rel_files[:30]:  # Limit listing
            content += f"- `{rf}`\n"
        if len(rel_files) > 30:
            content += f"- ... and {len(rel_files) - 30} more files\n"

        return CodeWikiPage(
            filename=f"code/modules/{module_name}.md",
            title=module_name,
            content=content,
            source_files=rel_files,
            commit_hash=config.commit_hash,
        )

    def _extract_key_symbols(self, files: list[Path]) -> str:
        """Extract key class/function names from source files (heuristic)."""
        import re
        symbols = []
        for f in files[:10]:  # Limit to first 10 files
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                # Python classes and functions
                for match in re.finditer(r"^(?:class|def|async def)\s+(\w+)", content, re.MULTILINE):
                    symbols.append(f"- `{match.group(1)}` ({f.name})")
                # TypeScript/JavaScript exports
                for match in re.finditer(r"^export\s+(?:class|function|const)\s+(\w+)", content, re.MULTILINE):
                    symbols.append(f"- `{match.group(1)}` ({f.name})")
            except OSError:
                continue
        if not symbols:
            return "_No key symbols detected._"
        return "\n".join(symbols[:20])

    def _git_diff_files(self, repo_path: Path, from_commit: str, to_commit: str) -> list[str]:
        """Get list of files changed between two commits."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", from_commit, to_commit],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return [f for f in result.stdout.strip().split("\n") if f]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return []

    def _write_page(self, page: CodeWikiPage) -> None:
        """Write a Code Wiki page to disk."""
        page_path = self._wiki_root / page.filename
        page_path.parent.mkdir(parents=True, exist_ok=True)

        output = page.content.rstrip() + "\n\n"
        output += "<!-- metadata:\n"
        output += "type: reference\n"
        output += "confidence: high\n"
        output += "stability: fresh\n"
        output += f"commit: {page.commit_hash}\n"
        output += f"generated: {page.generated_at.isoformat()}\n"
        output += "-->\n"

        page_path.write_text(output, encoding="utf-8")

        # Update status file
        status_file = self._code_wiki_dir / ".status"
        status_file.write_text(f"{page.commit_hash}\n{page.generated_at.isoformat()}\n")
