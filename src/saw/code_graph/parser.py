"""Tree-sitter 多语言代码解析器 — 源码 → CodeNode/CodeEdge

支持语言: Python, TypeScript/JavaScript (渐进扩展)
零 LLM 依赖，纯 AST 结构提取。
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from saw.code_graph.models import (
    CodeNode,
    CodeEdge,
    NodeKind,
    EdgeType,
    ConfidenceTier,
    ParseResult,
    content_hash,
    make_uid,
)

logger = logging.getLogger(__name__)

# 支持的文件扩展名 → 语言标识
EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
}

# 跳过的目录
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".next", ".nuxt", "coverage", ".saw",
}

# 跳过的文件模式
SKIP_PATTERNS = {
    ".min.js", ".bundle.js", ".map", ".d.ts",
    "package-lock.json", "yarn.lock", "uv.lock", "poetry.lock",
}


def detect_language(file_path: str | Path) -> Optional[str]:
    """根据文件扩展名检测语言"""
    suffix = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(suffix)


def should_skip(path: Path) -> bool:
    """判断是否应跳过该路径"""
    parts = path.parts
    if any(d in parts for d in SKIP_DIRS):
        return True
    name = path.name
    if any(name.endswith(p) for p in SKIP_PATTERNS):
        return True
    return False


def _is_test_path(rel_path: str) -> bool:
    """路径段感知的测试文件检测 (避免 'latest.py'/'contest.ts' 误判)"""
    lower = rel_path.lower()
    parts = lower.replace("\\", "/").split("/")
    filename = parts[-1] if parts else lower
    # 目录段: tests/, test/, __tests__/
    if any(seg in ("tests", "test", "__tests__") for seg in parts[:-1]):
        return True
    # 文件名: test_*.py, *_test.py, *.test.ts, *.spec.ts
    if filename.startswith("test_") or filename.startswith("test-"):
        return True
    if "_test." in filename or ".test." in filename or ".spec." in filename:
        return True
    return False


def discover_files(root: str | Path, languages: Optional[list[str]] = None) -> list[Path]:
    """发现根目录下所有可解析的源码文件 (不跟随符号链接，防止循环)"""
    import os

    root = Path(root)
    files = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # 跳过排除目录 (就地修改 dirnames 阻止递归)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in sorted(filenames):
            path = Path(dirpath) / fname
            if should_skip(path):
                continue
            lang = detect_language(path)
            if lang is None:
                continue
            if languages and lang not in languages:
                continue
            files.append(path)
    return sorted(files)


class CodeParser:
    """多语言代码解析器

    当前实现: 基于 AST 正则/启发式的轻量解析（无需 tree-sitter 二进制依赖）
    未来升级: 接入 tree-sitter 精确解析

    设计原则:
    - 单文件解析失败不影响整体构建（错误隔离）
    - 返回 ParseResult 包含 nodes + edges + errors
    - 确定性 UID: file_path::qualified_name
    """

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()

    def parse_file(self, file_path: str | Path) -> ParseResult:
        """解析单个文件，提取符号节点和关系边"""
        file_path = Path(file_path)
        language = detect_language(file_path)
        if language is None:
            return ParseResult(
                file_path=str(file_path),
                language="unknown",
                errors=[f"Unsupported file type: {file_path.suffix}"],
            )

        start = time.time()
        try:
            # 文件大小保护: 跳过超大文件 (防止生成的代码导致 OOM)
            file_size = file_path.stat().st_size
            if file_size > 2 * 1024 * 1024:  # 2MB
                return ParseResult(
                    file_path=str(file_path),
                    language=language,
                    errors=[f"File too large: {file_size} bytes (limit: 2MB)"],
                )
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as e:
            return ParseResult(
                file_path=str(file_path),
                language=language,
                errors=[f"Read error: {e}"],
            )

        rel_path = str(file_path.relative_to(self.root_path)) if file_path.is_relative_to(self.root_path) else str(file_path)
        file_hash = content_hash(source)

        if language == "python":
            result = self._parse_python(rel_path, source, file_hash)
        elif language in ("typescript", "javascript"):
            result = self._parse_typescript(rel_path, source, file_hash)
        else:
            result = ParseResult(file_path=rel_path, language=language)

        result.parse_time_ms = (time.time() - start) * 1000
        return result

    def parse_files(self, file_paths: list[Path]) -> list[ParseResult]:
        """批量解析文件"""
        results = []
        for fp in file_paths:
            results.append(self.parse_file(fp))
        return results

    # ─── Python 解析 ──────────────────────────────────────────────

    def _parse_python(self, rel_path: str, source: str, file_hash: str) -> ParseResult:
        """Python AST 解析 — 使用标准库 ast 模块"""
        import ast

        result = ParseResult(file_path=rel_path, language="python")

        # 文件级节点
        file_uid = make_uid(rel_path, "<module>")
        file_node = CodeNode(
            uid=file_uid,
            name=Path(rel_path).stem,
            kind=NodeKind.FILE,
            file_path=rel_path,
            language="python",
            start_line=1,
            end_line=source.count("\n") + 1,
            content_hash=file_hash,
        )
        result.nodes.append(file_node)

        try:
            tree = ast.parse(source, filename=rel_path)
        except SyntaxError as e:
            result.errors.append(f"SyntaxError: {e}")
            return result

        # 收集导入
        imports: list[tuple[str, int]] = []  # (module_name, line)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append((module, node.lineno))

        # 提取顶层和嵌套定义
        self._extract_python_definitions(
            tree, rel_path, file_hash, file_uid, result, parent_qualifier=""
        )

        # 生成 IMPORTS 边
        for module_name, _line in imports:
            if module_name:
                # 尝试解析为项目内文件
                target_path = self._resolve_python_module(module_name)
                if target_path:
                    target_uid = make_uid(target_path, "<module>")
                    result.edges.append(CodeEdge(
                        source=file_uid,
                        target=target_uid,
                        edge_type=EdgeType.IMPORTS,
                        confidence=0.9,
                        confidence_tier=ConfidenceTier.RESOLVED,
                    ))

        return result

    def _extract_python_definitions(
        self,
        tree: ast.AST,
        rel_path: str,
        file_hash: str,
        parent_uid: str,
        result: ParseResult,
        parent_qualifier: str,
    ) -> None:
        """递归提取 Python 定义（类、函数、方法）"""
        import ast

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                qualified = f"{parent_qualifier}{node.name}" if not parent_qualifier else f"{parent_qualifier}.{node.name}"
                uid = make_uid(rel_path, qualified)

                # 检测是否为测试类 (路径段匹配，避免 "latest.py" 等误判)
                is_test = node.name.startswith("Test") or _is_test_path(rel_path)
                kind = NodeKind.TEST if is_test else NodeKind.CLASS

                # 提取 docstring
                docstring = ast.get_docstring(node) or ""

                # 提取方法签名
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

                class_node = CodeNode(
                    uid=uid,
                    name=node.name,
                    kind=kind,
                    file_path=rel_path,
                    language="python",
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature=f"class {node.name}",
                    parameters=[],
                    docstring=docstring[:500] if docstring else None,
                    content_hash=file_hash,
                    metadata={"methods": methods},
                )
                result.nodes.append(class_node)

                # CONTAINS 边: parent → class
                result.edges.append(CodeEdge(
                    source=parent_uid,
                    target=uid,
                    edge_type=EdgeType.CONTAINS,
                ))

                # INHERITS 边
                for base in node.bases:
                    base_name = self._get_name_from_node(base)
                    if base_name:
                        # 暂时用裸名，PostProcess 阶段解析
                        result.edges.append(CodeEdge(
                            source=uid,
                            target=base_name,
                            edge_type=EdgeType.INHERITS,
                            confidence=0.85,
                            confidence_tier=ConfidenceTier.EXTRACTED,
                            metadata={"bare_name": True},
                        ))

                # 递归提取方法
                self._extract_python_methods(
                    node, rel_path, file_hash, uid, qualified, result
                )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = f"{parent_qualifier}{node.name}" if not parent_qualifier else f"{parent_qualifier}.{node.name}"
                uid = make_uid(rel_path, qualified)

                is_test = node.name.startswith("test_") or _is_test_path(rel_path)
                is_endpoint = self._has_decorator(node, ("route", "get", "post", "put", "delete", "patch", "api_view"))

                if is_test:
                    kind = NodeKind.TEST
                elif is_endpoint:
                    kind = NodeKind.ENDPOINT
                else:
                    kind = NodeKind.FUNCTION

                # 签名
                params = self._extract_python_params(node)
                sig = f"{'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}def {node.name}({', '.join(params)})"
                if node.returns:
                    ret = self._get_name_from_node(node.returns)
                    if ret:
                        sig += f" -> {ret}"

                docstring = ast.get_docstring(node) or ""

                func_node = CodeNode(
                    uid=uid,
                    name=node.name,
                    kind=kind,
                    file_path=rel_path,
                    language="python",
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature=sig,
                    parameters=params,
                    docstring=docstring[:500] if docstring else None,
                    content_hash=file_hash,
                )
                result.nodes.append(func_node)

                # CONTAINS 边
                result.edges.append(CodeEdge(
                    source=parent_uid,
                    target=uid,
                    edge_type=EdgeType.CONTAINS,
                ))

                # CALLS 边: 提取函数体内的调用
                self._extract_python_calls(node, uid, rel_path, result)

    def _extract_python_methods(
        self,
        class_node: ast.ClassDef,
        rel_path: str,
        file_hash: str,
        class_uid: str,
        class_qualifier: str,
        result: ParseResult,
    ) -> None:
        """提取类方法"""
        import ast

        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = f"{class_qualifier}.{node.name}"
                uid = make_uid(rel_path, qualified)

                is_test = node.name.startswith("test_")
                kind = NodeKind.TEST if is_test else NodeKind.METHOD

                params = self._extract_python_params(node)
                sig = f"def {node.name}({', '.join(params)})"
                docstring = ast.get_docstring(node) or ""

                method_node = CodeNode(
                    uid=uid,
                    name=node.name,
                    kind=kind,
                    file_path=rel_path,
                    language="python",
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature=sig,
                    parameters=params,
                    docstring=docstring[:500] if docstring else None,
                    content_hash=file_hash,
                )
                result.nodes.append(method_node)

                # CONTAINS 边: class → method
                result.edges.append(CodeEdge(
                    source=class_uid,
                    target=uid,
                    edge_type=EdgeType.CONTAINS,
                ))

                # CALLS 边
                self._extract_python_calls(node, uid, rel_path, result)

    def _extract_python_calls(
        self, func_node: ast.AST, caller_uid: str, rel_path: str, result: ParseResult
    ) -> None:
        """提取函数体内的函数调用"""
        import ast

        seen_calls: set[str] = set()
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                callee = self._get_call_name(node)
                if callee and callee not in seen_calls:
                    seen_calls.add(callee)
                    # 裸名边，PostProcess 阶段解析为完整 UID
                    result.edges.append(CodeEdge(
                        source=caller_uid,
                        target=callee,
                        edge_type=EdgeType.CALLS,
                        confidence=0.7,
                        confidence_tier=ConfidenceTier.EXTRACTED,
                        metadata={"bare_name": True},
                    ))

    def _extract_python_params(self, node) -> list[str]:
        """提取函数参数列表"""
        import ast

        params = []
        for arg in node.args.args:
            if arg.arg != "self" and arg.arg != "cls":
                params.append(arg.arg)
        for arg in node.args.kwonlyargs:
            params.append(arg.arg)
        if node.args.vararg:
            params.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            params.append(f"**{node.args.kwarg.arg}")
        return params

    def _has_decorator(self, node, names: tuple[str, ...]) -> bool:
        """检查函数是否有指定装饰器 (精确匹配末尾组件)"""
        import ast

        for dec in node.decorator_list:
            dec_name = self._get_name_from_node(dec)
            if dec_name:
                # 取最后一个点分组件做精确匹配，避免子串误匹配
                tail = dec_name.split(".")[-1]
                if tail in names:
                    return True
        return False

    # ─── TypeScript/JavaScript 解析 ───────────────────────────────

    def _parse_typescript(self, rel_path: str, source: str, file_hash: str) -> ParseResult:
        """TypeScript/JavaScript 启发式解析

        当前使用正则启发式（无需 tree-sitter 二进制），
        未来可升级为 tree-sitter 精确解析。
        """
        import re

        result = ParseResult(file_path=rel_path, language="typescript")

        file_uid = make_uid(rel_path, "<module>")
        file_node = CodeNode(
            uid=file_uid,
            name=Path(rel_path).stem,
            kind=NodeKind.FILE,
            file_path=rel_path,
            language="typescript",
            start_line=1,
            end_line=source.count("\n") + 1,
            content_hash=file_hash,
        )
        result.nodes.append(file_node)

        lines = source.split("\n")

        # 提取 import 语句
        import_pattern = re.compile(
            r"""(?:import\s+.*?\s+from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))"""
        )
        for match in import_pattern.finditer(source):
            module = match.group(1) or match.group(2)
            if module and module.startswith("."):
                target_path = self._resolve_relative_import(rel_path, module)
                if target_path:
                    target_uid = make_uid(target_path, "<module>")
                    result.edges.append(CodeEdge(
                        source=file_uid,
                        target=target_uid,
                        edge_type=EdgeType.IMPORTS,
                        confidence=0.9,
                        confidence_tier=ConfidenceTier.RESOLVED,
                    ))

        # 提取 class 定义
        class_pattern = re.compile(
            r"^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?",
            re.MULTILINE,
        )
        for match in class_pattern.finditer(source):
            class_name = match.group(1)
            extends = match.group(2)
            line_no = source[: match.start()].count("\n") + 1
            uid = make_uid(rel_path, class_name)

            is_test = _is_test_path(rel_path)
            kind = NodeKind.TEST if is_test else NodeKind.CLASS

            class_node = CodeNode(
                uid=uid,
                name=class_name,
                kind=kind,
                file_path=rel_path,
                language="typescript",
                start_line=line_no,
                end_line=line_no,  # 启发式无法精确获取结束行
                signature=f"class {class_name}" + (f" extends {extends}" if extends else ""),
                content_hash=file_hash,
            )
            result.nodes.append(class_node)

            result.edges.append(CodeEdge(
                source=file_uid, target=uid, edge_type=EdgeType.CONTAINS
            ))

            if extends:
                result.edges.append(CodeEdge(
                    source=uid,
                    target=extends,
                    edge_type=EdgeType.INHERITS,
                    confidence=0.85,
                    confidence_tier=ConfidenceTier.EXTRACTED,
                    metadata={"bare_name": True},
                ))

        # 提取 function/const arrow 定义
        func_patterns = [
            re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE),
            re.compile(r"^(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*\S+\s*)?=>", re.MULTILINE),
        ]
        for pattern in func_patterns:
            for match in pattern.finditer(source):
                func_name = match.group(1)
                params_str = match.group(2)
                line_no = source[: match.start()].count("\n") + 1
                uid = make_uid(rel_path, func_name)

                is_test = func_name.startswith("test") or _is_test_path(rel_path)
                kind = NodeKind.TEST if is_test else NodeKind.FUNCTION

                params = [p.strip().split(":")[0].strip() for p in params_str.split(",") if p.strip()]

                func_node = CodeNode(
                    uid=uid,
                    name=func_name,
                    kind=kind,
                    file_path=rel_path,
                    language="typescript",
                    start_line=line_no,
                    end_line=line_no,
                    signature=f"function {func_name}({params_str.strip()})",
                    parameters=params,
                    content_hash=file_hash,
                )
                result.nodes.append(func_node)

                result.edges.append(CodeEdge(
                    source=file_uid, target=uid, edge_type=EdgeType.CONTAINS
                ))

        # 提取 interface/type 定义
        type_pattern = re.compile(
            r"^(?:export\s+)?(?:interface|type)\s+(\w+)", re.MULTILINE
        )
        for match in type_pattern.finditer(source):
            type_name = match.group(1)
            line_no = source[: match.start()].count("\n") + 1
            uid = make_uid(rel_path, type_name)

            type_node = CodeNode(
                uid=uid,
                name=type_name,
                kind=NodeKind.TYPE,
                file_path=rel_path,
                language="typescript",
                start_line=line_no,
                end_line=line_no,
                signature=f"type {type_name}",
                content_hash=file_hash,
            )
            result.nodes.append(type_node)

            result.edges.append(CodeEdge(
                source=file_uid, target=uid, edge_type=EdgeType.CONTAINS
            ))

        return result

    # ─── 工具方法 ─────────────────────────────────────────────────

    def _get_name_from_node(self, node) -> Optional[str]:
        """从 AST 节点提取名称"""
        import ast

        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name_from_node(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self._get_name_from_node(node.value)
        elif isinstance(node, ast.Call):
            return self._get_name_from_node(node.func)
        return None

    def _get_call_name(self, node) -> Optional[str]:
        """从 Call 节点提取被调用函数名"""
        import ast

        if isinstance(node.func, ast.Name):
            # 跳过内置函数
            builtins = {"print", "len", "range", "str", "int", "float", "list", "dict", "set", "tuple", "type", "isinstance", "hasattr", "getattr", "setattr", "super"}
            if node.func.id in builtins:
                return None
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # obj.method() → 只取 method 名（裸名）
            return node.func.attr
        return None

    def _resolve_python_module(self, module_name: str) -> Optional[str]:
        """将 Python 模块名解析为项目内相对路径"""
        # 尝试将 module.path 转为 module/path.py
        parts = module_name.split(".")
        candidate = Path("/".join(parts) + ".py")
        full = self.root_path / candidate
        if full.exists():
            return str(candidate)

        # 尝试 package __init__.py
        candidate = Path("/".join(parts)) / "__init__.py"
        full = self.root_path / candidate
        if full.exists():
            return str(candidate)

        # 尝试 src/ 前缀
        candidate = Path("src") / Path("/".join(parts) + ".py")
        full = self.root_path / candidate
        if full.exists():
            return str(candidate)

        return None

    def _resolve_relative_import(self, current_file: str, module: str) -> Optional[str]:
        """解析相对导入路径 (正确处理 ../ 父目录导入, 含路径遍历防护)"""
        current_dir = Path(current_file).parent
        # 计算前导点数量确定向上层级: "./" → 0, "../" → 1, "../../" → 2
        dots = len(module) - len(module.lstrip("."))
        base = current_dir
        for _ in range(max(0, dots - 1)):
            base = base.parent
        # 去掉前导点和斜杠得到模块路径
        clean = module.lstrip(".").lstrip("/")
        if not clean or ".." in clean:
            return None
        candidates = [
            base / f"{clean}.ts",
            base / f"{clean}.tsx",
            base / f"{clean}.js",
            base / f"{clean}.jsx",
            base / f"{clean}/index.ts",
            base / f"{clean}/index.js",
        ]
        root_resolved = self.root_path.resolve()
        for c in candidates:
            full = (self.root_path / c).resolve()
            # 路径遍历防护: 确保解析后的路径仍在项目根目录内
            if full.is_relative_to(root_resolved) and full.exists():
                return str(c)
        return None
