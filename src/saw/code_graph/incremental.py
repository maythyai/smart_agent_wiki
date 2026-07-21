"""增量构建编排 — content-hash + git-diff 双模式

目标: 代码变更后 < 2s 完成图更新，无需全量重建。
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

from saw.code_graph.models import BuildResult, ParseResult, content_hash
from saw.code_graph.parser import CodeParser, discover_files
from saw.code_graph.store import CodeGraphStore

logger = logging.getLogger(__name__)


class IncrementalBuilder:
    """增量构建编排器

    双模式检测变更:
    1. Git 模式: git diff --name-only (有 .git 时优先)
    2. Hash 模式: SHA-256 content hash 比对 (file_tracking 表)

    增量重建流程:
    1. 检测变更文件集
    2. 仅重新解析变更文件
    3. 原子替换该文件的 nodes/edges (store_file_batch)
    4. 删除已移除文件的图数据
    5. 触发 PostProcess (由 Engine 调用)
    """

    def __init__(
        self,
        root_path: str | Path,
        store: CodeGraphStore,
        parser: Optional[CodeParser] = None,
    ):
        self.root_path = Path(root_path).resolve()
        self.store = store
        self.parser = parser or CodeParser(self.root_path)

    def full_build(self, languages: Optional[list[str]] = None) -> BuildResult:
        """全量构建 — 解析所有源码文件"""
        start = time.time()
        result = BuildResult()

        files = discover_files(self.root_path, languages)
        result.total_files = len(files)

        for fp in files:
            try:
                parse_result = self.parser.parse_file(fp)
                if parse_result.errors:
                    result.files_failed += 1
                    result.errors.extend(parse_result.errors)
                else:
                    # 应用语言特化 Resolver (框架语义增强)
                    parse_result = self._apply_resolvers(parse_result)
                    self.store.store_file_batch(parse_result)
                    result.files_parsed += 1
                    result.total_nodes += len(parse_result.nodes)
                    result.total_edges += len(parse_result.edges)
            except Exception as e:
                result.files_failed += 1
                result.errors.append(f"{fp}: {e}")
                logger.warning(f"Failed to parse {fp}: {e}")

        # 创建快照
        snapshot = self.store.create_snapshot("full_build", files_changed=result.files_parsed)
        result.snapshot_id = snapshot.snapshot_id
        result.build_time_ms = (time.time() - start) * 1000

        logger.info(
            f"Full build complete: {result.files_parsed}/{result.total_files} files, "
            f"{result.total_nodes} nodes, {result.total_edges} edges, "
            f"{result.build_time_ms:.0f}ms"
        )
        return result

    def incremental_update(self, languages: Optional[list[str]] = None) -> BuildResult:
        """增量更新 — 仅处理变更文件"""
        start = time.time()
        result = BuildResult()

        # 检测变更
        changed, removed = self._detect_changes()
        result.total_files = len(changed) + len(removed)

        # 处理删除的文件
        for file_path in removed:
            self.store.remove_file(file_path)
            logger.debug(f"Removed: {file_path}")

        # 处理变更的文件
        for file_path in changed:
            full_path = self.root_path / file_path
            if not full_path.exists():
                self.store.remove_file(file_path)
                continue

            try:
                parse_result = self.parser.parse_file(full_path)
                if parse_result.errors:
                    result.files_failed += 1
                    result.errors.extend(parse_result.errors)
                else:
                    parse_result = self._apply_resolvers(parse_result)
                    self.store.store_file_batch(parse_result)
                    result.files_parsed += 1
                    result.total_nodes += len(parse_result.nodes)
                    result.total_edges += len(parse_result.edges)
            except Exception as e:
                result.files_failed += 1
                result.errors.append(f"{file_path}: {e}")

        result.files_skipped = result.total_files - result.files_parsed - result.files_failed

        # 创建快照
        if result.files_parsed > 0 or removed:
            snapshot = self.store.create_snapshot(
                "incremental", files_changed=result.files_parsed + len(removed)
            )
            result.snapshot_id = snapshot.snapshot_id

        result.build_time_ms = (time.time() - start) * 1000

        logger.info(
            f"Incremental update: {result.files_parsed} parsed, "
            f"{len(removed)} removed, {result.files_skipped} skipped, "
            f"{result.build_time_ms:.0f}ms"
        )
        return result

    def _apply_resolvers(self, result) -> "ParseResult":
        """应用语言特化 Resolver 增强 ParseResult

        Resolver 在通用 AST 解析之后运行，负责:
        - 框架装饰器语义 (FastAPI route → ENDPOINT)
        - Depends() → DEPENDS_ON 边
        - 其他语言/框架特化逻辑
        """
        try:
            from saw.code_graph.resolvers.registry import get_resolver
            resolvers = get_resolver(result.language)
            for resolver in resolvers:
                result = resolver.resolve(result, {})
        except (ImportError, Exception) as e:
            logger.debug(f"Resolver skipped for {result.file_path}: {e}")
        return result

    def _detect_changes(self) -> tuple[list[str], list[str]]:
        """检测变更文件集

        Returns:
            (changed_files, removed_files) — 相对路径列表
        """
        # 优先尝试 git diff
        git_changes = self._detect_via_git()
        if git_changes is not None:
            return git_changes

        # 降级: content hash 比对
        return self._detect_via_hash()

    def _detect_via_git(self) -> Optional[tuple[list[str], list[str]]]:
        """通过 git diff 检测变更"""
        git_dir = self.root_path / ".git"
        if not git_dir.exists():
            # 可能是 worktree
            git_file = self.root_path / ".git"
            if not git_file.is_file():
                return None

        try:
            # 获取相对于 HEAD 的变更
            proc = subprocess.run(
                ["git", "diff", "--name-status", "HEAD"],
                cwd=str(self.root_path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0:
                return None

            changed = []
            removed = []
            for line in proc.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                status = parts[0]

                # 处理 rename/copy: R100\told.py\tnew.py
                if status.startswith(("R", "C")) and len(parts) >= 3:
                    old_path, new_path = parts[1], parts[2]
                    from saw.code_graph.parser import detect_language, should_skip
                    if detect_language(old_path) and not should_skip(Path(old_path)):
                        removed.append(old_path)
                    if detect_language(new_path) and not should_skip(Path(new_path)):
                        changed.append(new_path)
                    continue

                file_path = parts[1]

                # 只处理源码文件
                from saw.code_graph.parser import detect_language, should_skip
                if detect_language(file_path) is None:
                    continue
                if should_skip(Path(file_path)):
                    continue

                if status.startswith("D"):
                    removed.append(file_path)
                else:
                    changed.append(file_path)

            # 也检查未追踪的新文件
            proc2 = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=str(self.root_path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc2.returncode == 0:
                from saw.code_graph.parser import detect_language, should_skip
                for line in proc2.stdout.strip().split("\n"):
                    if line and detect_language(line) and not should_skip(Path(line)):
                        if line not in changed:
                            changed.append(line)

            return changed, removed

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _detect_via_hash(self) -> tuple[list[str], list[str]]:
        """通过 content hash 比对检测变更"""
        tracked = {ft.file_path: ft.content_hash for ft in self.store.get_tracked_files()}
        current_files = discover_files(self.root_path)

        changed = []
        removed = []
        seen = set()

        for fp in current_files:
            rel_path = str(fp.relative_to(self.root_path))
            seen.add(rel_path)

            try:
                source = fp.read_text(encoding="utf-8", errors="replace")
                current_hash = content_hash(source)
            except OSError:
                continue

            stored_hash = tracked.get(rel_path)
            if stored_hash != current_hash:
                changed.append(rel_path)

        # 检测已删除的文件
        for tracked_path in tracked:
            if tracked_path not in seen:
                removed.append(tracked_path)

        return changed, removed
