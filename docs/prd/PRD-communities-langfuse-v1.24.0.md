---
id: PRD-communities-langfuse-v1.24.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: Approved
roadmap_ref: ROADMAP
target_version: v1.24.0
see_also: docs/analysis/COMPETITIVE-REFERENCE.md (A2/C4/D1)
---

# PRD: claims 图社区检测 + Langfuse trace (v1.24.0)

> 竞品借鉴 A2（GraphRAG 社区检测）/ D1（WeKnora Langfuse trace）；C4 Agent File 已在 v1.19.0(T3) ship。

## 1. 背景
- **A2 communities**：GraphRAG 在 claims/entity 图上做层次社区检测 + 社区报告，支持"整个库在讲什么"全局问答。SAW 落地：Louvain 社区检测（networkx）+ `saw_communities`/`saw_community_of` MCP 工具。差异化：社区成员是**带 4 级置信的 entity/claim**（非无置信文本社区）。
- **D1 Langfuse trace**：WeKnora 用 Langfuse 做 ReAct loop/工具调用 trace。SAW 已有 request_id contextvar + Sentry；D1 加 optional Langfuse SDK（env-gated，无包/无 env 时 graceful no-op）+ `langfuse_span(name)` helper。
- **C4 Agent File**：已在 v1.19.0 ship（`saw agents export/import`），本周期标 done 无新工作。

## 2. AC
- **AC-A2-1**：`GraphTraverse.communities(min_size)` Louvain 检测，返回 `[{id,size,members}]`；connected-components fallback；空图→[]。
- **AC-A2-2**：`saw_communities` + `saw_community_of(entity)` MCP 工具。
- **AC-D1-1**：`langfuse_span(name)` context manager；无 langfuse client→no-op yield None；有 client→span + end。
- **AC-D1-2**：`observability` optional-dep（langfuse>=2.0）；init_observability env-gated 初始化。

## 3. 非目标
- 社区报告 LLM 摘要（A2 仅结构社区，报告留后续）。
- DRIFT global search（仅 community_of 局部）。
- Langfuse 实际服务端（需 LANGFUSE_* env + 账号，基建）。

## 4. 验收
- A2: 5 测试（two clusters / min_size filter / community_of locate / unknown / empty graph）✓
- D1: 1 测试（no-op path）✓
- 全量 gate 绿，零回归。
