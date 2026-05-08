"""
Anatomy Index - 文件索引与 Token 估算

基于 OpenWolf 的 anatomy.md 概念实现：
- 扫描项目目录结构
- 为每个文件生成描述和 Token 估算
- 支持增量更新
"""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import FileEntry


# Token 估算常数
CHARS_PER_TOKEN_CODE = 3.5  # 代码文件字符/token 比率
CHARS_PER_TOKEN_TEXT = 4.0  # 文本文件字符/token 比率
SAMPLE_SIZE = 1000  # 大文件采样大小


def estimate_tokens(content: str, is_code: bool = True) -> int:
    """
    估算文本的 Token 数量

    基于字符数的估算，精度约 15%

    Args:
        content: 文本内容
        is_code: 是否为代码文件

    Returns:
        估算的 Token 数量
    """
    if not content:
        return 0
    ratio = CHARS_PER_TOKEN_CODE if is_code else CHARS_PER_TOKEN_TEXT
    return max(1, int(len(content) / ratio))


def estimate_file_tokens(file_path: Path, sample: bool = False) -> int:
    """
    估算文件的 Token 数量

    Args:
        file_path: 文件路径
        sample: 是否采样估算（适用于大文件）

    Returns:
        估算的 Token 数量
    """
    try:
        stat = file_path.stat()
        size = stat.st_size

        # 空文件
        if size == 0:
            return 0

        # 小文件直接读取
        if size < 10000 or not sample:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                return estimate_tokens(content, is_code=file_path.suffix != ".md")
            except Exception:
                return 0

        # 大文件采样估算
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                sample_content = f.read(SAMPLE_SIZE)
            sample_tokens = estimate_tokens(sample_content, is_code=file_path.suffix != ".md")
            return int((size / len(sample_content)) * sample_tokens)
        except Exception:
            return 0

    except Exception:
        return 0


def get_file_checksum(file_path: Path) -> Optional[str]:
    """获取文件的 MD5 校验和"""
    try:
        content = file_path.read_bytes()
        return hashlib.md5(content, usedforsecurity=False).hexdigest()
    except Exception:
        return None


@dataclass
class AnatomyIndex:
    """
    文件索引管理器

    管理项目的文件结构索引，包括描述和 Token 估算
    """

    project_root: Path
    entries: dict[str, FileEntry] = None  # type: ignore

    def __post_init__(self):
        if self.entries is None:
            self.entries = {}
        self.project_root = Path(self.project_root)

    def scan_directory(
        self,
        directory: Optional[Path] = None,
        exclude_dirs: Optional[set[str]] = None,
        include_extensions: Optional[set[str]] = None,
    ) -> dict[str, FileEntry]:
        """
        扫描目录并生成索引

        Args:
            directory: 要扫描的目录，默认为项目根目录
            exclude_dirs: 排除的目录名
            include_extensions: 包含的文件扩展名

        Returns:
            文件路径到 FileEntry 的映射
        """
        if directory is None:
            directory = self.project_root

        exclude_dirs = exclude_dirs or {
            "__pycache__", ".git", ".venv", "node_modules",
            ".pytest_cache", ".benchmarks", "dist", "build",
            ".mypy_cache", ".ruff_cache", "*.egg-info",
        }

        # 默认包含常见代码和文档文件
        include_extensions = include_extensions or {
            ".py", ".js", ".ts", ".tsx", ".jsx",
            ".md", ".rst", ".txt",
            ".json", ".yaml", ".yml", ".toml",
            ".sh", ".bash",
            ".html", ".css", ".scss",
            ".sql",
        }

        entries: dict[str, FileEntry] = {}

        for root, dirs, files in os.walk(directory):
            # 排除指定目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]

            rel_root = Path(root).relative_to(self.project_root)

            # 添加目录条目
            if str(rel_root) != ".":
                dir_path = str(rel_root)
                entries[dir_path] = FileEntry(
                    path=dir_path,
                    description="",
                    estimated_tokens=0,
                    is_directory=True,
                )

            # 添加文件条目
            for file in files:
                file_path = Path(root) / file

                # 检查扩展名
                if file_path.suffix not in include_extensions:
                    continue

                rel_path = str(file_path.relative_to(self.project_root))

                # 生成文件描述（简单实现）
                description = self._generate_description(file_path)

                # 估算 Token
                tokens = estimate_file_tokens(file_path, sample=True)

                # 获取校验和
                checksum = get_file_checksum(file_path)

                # 获取修改时间
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                except Exception:
                    mtime = None

                entries[rel_path] = FileEntry(
                    path=rel_path,
                    description=description,
                    estimated_tokens=tokens,
                    last_modified=mtime,
                    checksum=checksum,
                    is_directory=False,
                    language=self._detect_language(file_path),
                )

        self.entries = entries
        return entries

    def _generate_description(self, file_path: Path) -> str:
        """
        为文件生成简单描述

        实际应用中可以使用 LLM 生成更详细的描述
        """
        name = file_path.name
        suffix = file_path.suffix

        # 基于文件名和类型的简单描述
        if suffix == ".py":
            if name.startswith("test_"):
                return f"Test file for {name[5:-3]}"
            elif name == "__init__.py":
                return "Package initialization"
            return f"Python module: {name[:-3]}"
        elif suffix == ".md":
            return f"Documentation: {name[:-3]}"
        elif suffix == ".json":
            return f"JSON config/data: {name[:-5]}"
        elif suffix in (".yaml", ".yml"):
            return f"YAML config: {name}"
        elif suffix in (".ts", ".tsx"):
            return f"TypeScript: {name}"
        elif suffix in (".js", ".jsx"):
            return f"JavaScript: {name}"

        return f"File: {name}"

    def _detect_language(self, file_path: Path) -> str:
        """检测文件语言"""
        suffix_to_lang = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".sh": "shell",
            ".bash": "shell",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
        }
        return suffix_to_lang.get(file_path.suffix, "unknown")

    def get_entry(self, file_path: str) -> Optional[FileEntry]:
        """获取文件条目"""
        return self.entries.get(file_path)

    def update_entry(self, file_path: str, entry: FileEntry) -> None:
        """更新文件条目"""
        self.entries[file_path] = entry

    def remove_entry(self, file_path: str) -> None:
        """移除文件条目"""
        self.entries.pop(file_path, None)

    def to_markdown(self) -> str:
        """
        转换为 markdown 格式

        格式与 OpenWolf 的 anatomy.md 兼容
        """
        lines = [
            "# anatomy.md",
            "",
            "> Project structure index. Auto-maintained by Smart Agent Wiki.",
            "> Run `saw anatomy scan` to regenerate.",
            "",
        ]

        # 按目录分组
        current_dir = ""

        for path in sorted(self.entries.keys()):
            entry = self.entries[path]

            if entry.is_directory:
                # 目录标题
                if path != current_dir:
                    lines.append(f"\n## {path}/\n")
                    current_dir = path
            else:
                # 文件条目
                parent = str(Path(path).parent)
                if parent != current_dir and parent != ".":
                    lines.append(f"\n## {parent}/\n")
                    current_dir = parent

                lines.append(entry.to_markdown_line())

        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, content: str, project_root: Path) -> "AnatomyIndex":
        """
        从 markdown 内容解析索引

        Args:
            content: markdown 内容
            project_root: 项目根目录

        Returns:
            AnatomyIndex 实例
        """
        import re

        entries: dict[str, FileEntry] = {}
        current_dir = ""

        for line in content.split("\n"):
            # 解析目录标题
            dir_match = re.match(r"^## (.+)/$", line)
            if dir_match:
                current_dir = dir_match.group(1)
                entries[current_dir] = FileEntry(
                    path=current_dir,
                    description="",
                    estimated_tokens=0,
                    is_directory=True,
                )
                continue

            # 解析文件条目
            # 格式: - `filename` - description (~N tok)
            file_match = re.match(r"^- `(.+?)` - (.+?) \(~(\d+) tok\)$", line)
            if file_match:
                filename = file_match.group(1)
                description = file_match.group(2)
                tokens = int(file_match.group(3))

                # 构建完整路径
                if current_dir:
                    full_path = f"{current_dir}/{filename}"
                else:
                    full_path = filename

                entries[full_path] = FileEntry(
                    path=full_path,
                    description=description,
                    estimated_tokens=tokens,
                    is_directory=False,
                )

        return cls(project_root=project_root, entries=entries)

    def get_total_tokens(self) -> int:
        """获取所有文件的总 Token 估算"""
        return sum(e.estimated_tokens for e in self.entries.values() if not e.is_directory)

    def get_file_count(self) -> int:
        """获取文件数量"""
        return sum(1 for e in self.entries.values() if not e.is_directory)

    def find_by_pattern(self, pattern: str) -> list[FileEntry]:
        """
        按模式搜索文件

        Args:
            pattern: 搜索模式（支持 glob 风格）

        Returns:
            匹配的文件条目列表
        """
        import fnmatch

        results = []
        for path, entry in self.entries.items():
            if entry.is_directory:
                continue
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(entry.path, pattern):
                results.append(entry)

        return results
