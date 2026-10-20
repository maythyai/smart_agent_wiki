---
id: PRD-v1.37-governed-code-intelligence
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-20
status: Draft
prd_depth: planning
upstream_source: docs/strategy/ROADMAP.md#v1.37.0
roadmap_ref: ROADMAP
target_version: v1.37.0
type: feature
tracks: [core-trust, intelligence-adaptation]
---

# PRD — v1.37.0 Governed Code Intelligence + Token Optimizer（规划级, v1.43+v1.44 合并）

## §1 背景与目标
CodeGraph(29k★)/Graphify(55k★) 拥挤但 code-only——无治理/溯源。SAW 差异化：impact+staleness+provenance = "governed code intelligence"。Token Optimizer(65% 理论节省)产品化直击 OpenClaw $47k 跑飞/月$3600 成本痛点。本版合并原 v1.43(coding-harness+governed code intel) + v1.44(token optimizer)——同 DEV 用户价值（cost+code governance）。

**目标**：governed code intelligence 楔子 + Token Optimizer 产品化为 cost layer。

## §3 功能设计

### F1: tree-sitter AST zero-LLM 解析
- **用户故事**：开发者查 code impact 时，AST 解析不经 LLM（快+省 token）。
- **优先级**：P0
- **关键规则要点**：① tree-sitter 增量解析（多语言）；② AST→claims 零 LLM 调用；③ code↔doc anchoring（claims 锚定 code symbol）。
- **主流程**：code-graph build → tree-sitter parse → claims（零 LLM）→ impact/staleness。

### F2: coding-harness skills 全平台
- **用户故事**：Codex/Cursor/OpenCode 用户装 SAW skills 获 governed code intelligence。
- **优先级**：P1
- **关键规则要点**：① C3 续（v1.20 已有 Claude Code skills）；② "governed" 楔子：impact+staleness+provenance（vs CodeGraph code-only）；③ skills 包教 harness 何时调 saw_resolve/saw_impact/saw_staleness。

### F3: Token ledger 产品化
- **用户故事**：开发者经 `/api/v1/tokens` + `saw_tokens` MCP 查 token 消耗+节省。
- **优先级**：P1
- **关键规则要点**：① Anatomy/Cerebrum/BugLog/Tracker 暴露为 served 层；② cost dashboard（per-session/workspace/agent）；③ 重复读检测+提示（Session Tracker 升级，直击 OpenClaw 底噪）。

### F4: context-compaction
- **用户故事**：agent context 膨胀时，SAW 自动蒸馏过期/低价值 context。
- **优先级**：P2
- **关键规则要点**：① compaction 锚定可信 claims（非无差别压缩）；② 压缩后仍可溯源。

## §6 验收标准
- **AC-F1**：AST 解析 zero-LLM（无 LLM API 调用）；impact 锚 claims。
- **AC-F3**：`/api/v1/tokens` 返回 per-session token 消耗+理论节省。
- **AC-F4**：context-compaction 后 token 下降 `[TBD]`，压缩内容可溯源。

## §8 风险与依赖
- 前置：v1.36.0（reasoner 提供 context 层）。
- R1: tree-sitter 多语言 AST 复杂 → 先 Python+TS，其他语言后续补。
- thin_sections: tree-sitter grammar 配置、token ledger schema → 01 升级补全。
