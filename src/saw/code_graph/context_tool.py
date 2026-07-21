"""saw_code_context MCP 工具 — token 预算感知的上下文组装

多分辨率上下文交付:
- minimal: 仅名称+类型 (token 最省)
- standard: 签名+关系+风险等级
- verbose: 完整源码片段+docstring

每次查询返回 context_savings 元数据。
"""

from __future__ import annotations

import logging
from typing import Optional

from saw.code_graph.models import CodeNode, NodeKind

logger = logging.getLogger(__name__)

# Token 估算: 平均 4 字符 ≈ 1 token
CHARS_PER_TOKEN = 4


def get_code_context_tool_definition() -> dict:
    """saw_code_context 工具定义"""
    return {
        "name": "saw_code_context",
        "description": """Get token-efficient code context for a symbol.

Assembles a compact context package around a target symbol, respecting
a token budget. Three detail levels:
- minimal: name + kind + file (cheapest)
- standard: + signature + direct relationships + risk level
- verbose: + source snippet + docstring + transitive relationships

Returns context_savings metadata showing tokens saved vs reading all files.

Use this instead of reading entire files when you need to understand a symbol.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Symbol name or UID",
                },
                "detail_level": {
                    "type": "string",
                    "enum": ["minimal", "standard", "verbose"],
                    "default": "standard",
                    "description": "How much context to include",
                },
                "token_budget": {
                    "type": "integer",
                    "default": 2000,
                    "description": "Maximum tokens to use for context",
                },
                "include_callers": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include who calls this symbol",
                },
                "include_callees": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include what this symbol calls",
                },
            },
            "required": ["target"],
        },
    }


async def handle_code_context(
    target: str,
    detail_level: str = "standard",
    token_budget: int = 2000,
    include_callers: bool = True,
    include_callees: bool = True,
    engine=None,
) -> dict:
    """Handle saw_code_context tool call.

    Assembles context within token budget, prioritizing:
    1. Target symbol info
    2. Direct relationships (callers/callees)
    3. Source snippet (verbose only)
    4. Transitive relationships (if budget allows)
    """
    if engine is None:
        return {"error": "engine_not_available", "message": "Code graph engine not initialized"}

    try:
        # Resolve target
        node = engine._resolve_target(target)
        if not node:
            suggestions = [n.name for n in engine.search(target, limit=5)]
            return {
                "error": "node_not_found",
                "message": f"Symbol '{target}' not found",
                "suggestions": suggestions,
            }

        budget_chars = token_budget * CHARS_PER_TOKEN
        used_chars = 0
        context_parts = []

        # 1. Target symbol info
        target_info = _format_node(node, detail_level)
        used_chars += len(target_info)
        context_parts.append(target_info)

        # 2. Direct relationships
        if include_callers and used_chars < budget_chars:
            callers = engine.callers_of(node.uid)
            callers_text = _format_relationships("Called by", callers, detail_level)
            if used_chars + len(callers_text) <= budget_chars:
                context_parts.append(callers_text)
                used_chars += len(callers_text)

        if include_callees and used_chars < budget_chars:
            callees = engine.callees_of(node.uid)
            callees_text = _format_relationships("Calls", callees, detail_level)
            if used_chars + len(callees_text) <= budget_chars:
                context_parts.append(callees_text)
                used_chars += len(callees_text)

        # 3. Impact summary (standard+)
        if detail_level in ("standard", "verbose") and used_chars < budget_chars:
            impacts = engine.impact_analysis(node.uid, max_depth=2)
            if impacts:
                impact_text = _format_impacts(impacts)
                if used_chars + len(impact_text) <= budget_chars:
                    context_parts.append(impact_text)
                    used_chars += len(impact_text)

        # 4. Source snippet (verbose only)
        if detail_level == "verbose" and used_chars < budget_chars:
            snippet = _get_source_snippet(node, engine)
            if snippet and used_chars + len(snippet) <= budget_chars:
                context_parts.append(snippet)
                used_chars += len(snippet)

        # Compute savings
        total_related_files = _count_related_files(node, engine)
        estimated_full_read = total_related_files * 2000  # ~2000 chars per file avg
        savings_pct = max(0, (1 - used_chars / max(estimated_full_read, 1)) * 100)

        return {
            "target": {
                "uid": node.uid,
                "name": node.name,
                "kind": node.kind.value,
                "file_path": node.file_path,
            },
            "detail_level": detail_level,
            "context": "\n\n".join(context_parts),
            "tokens_used": used_chars // CHARS_PER_TOKEN,
            "token_budget": token_budget,
            "context_savings": {
                "tokens_returned": used_chars // CHARS_PER_TOKEN,
                "estimated_full_read_tokens": estimated_full_read // CHARS_PER_TOKEN,
                "savings_percent": round(savings_pct, 1),
                "files_summarized": total_related_files,
            },
        }

    except Exception as e:
        logger.exception(f"Error in code_context: {e}")
        return {"error": "context_error", "message": str(e)}


# ─── Formatting helpers ───────────────────────────────────────────


def _format_node(node: CodeNode, detail: str) -> str:
    """格式化节点信息"""
    if detail == "minimal":
        return f"[{node.kind.value}] {node.name} @ {node.file_path}:{node.start_line}"

    lines = [f"## {node.name} ({node.kind.value})"]
    lines.append(f"File: {node.file_path}:{node.start_line}-{node.end_line}")
    if node.signature:
        lines.append(f"Signature: {node.signature}")
    if detail == "verbose" and node.docstring:
        lines.append(f"Doc: {node.docstring[:300]}")
    return "\n".join(lines)


def _format_relationships(label: str, nodes: list[CodeNode], detail: str) -> str:
    """格式化关系列表"""
    if not nodes:
        return ""

    lines = [f"### {label} ({len(nodes)})"]
    for n in nodes[:10]:  # 最多 10 个
        if detail == "minimal":
            lines.append(f"  - {n.name} ({n.kind.value})")
        else:
            lines.append(f"  - {n.name} ({n.kind.value}) @ {n.file_path}:{n.start_line}")
    if len(nodes) > 10:
        lines.append(f"  ... and {len(nodes) - 10} more")
    return "\n".join(lines)


def _format_impacts(impacts) -> str:
    """格式化影响分析"""
    if not impacts:
        return ""
    lines = [f"### Impact Radius ({len(impacts)} affected)"]
    for imp in impacts[:8]:
        lines.append(f"  - [{imp.risk_level}] {imp.name} (depth={imp.depth}, score={imp.score:.2f})")
    return "\n".join(lines)


def _get_source_snippet(node: CodeNode, engine) -> str:
    """获取源码片段 (verbose 模式)"""
    try:
        from pathlib import Path
        file_path = Path(engine.root_path) / node.file_path
        if not file_path.exists():
            return ""
        lines = file_path.read_text(encoding="utf-8").split("\n")
        start = max(0, node.start_line - 1)
        end = min(len(lines), node.end_line)
        # 限制 50 行
        if end - start > 50:
            end = start + 50
        snippet = "\n".join(lines[start:end])
        return f"### Source ({node.file_path}:{node.start_line}-{end})\n```\n{snippet}\n```"
    except Exception:
        return ""


def _count_related_files(node: CodeNode, engine) -> int:
    """估算相关文件数"""
    files = {node.file_path}
    for e in engine.get_outgoing_edges(node.uid):
        target = engine.get_node(e.target)
        if target:
            files.add(target.file_path)
    for e in engine.get_incoming_edges(node.uid):
        source = engine.get_node(e.source)
        if source:
            files.add(source.file_path)
    return len(files)


__all__ = ["get_code_context_tool_definition", "handle_code_context"]
