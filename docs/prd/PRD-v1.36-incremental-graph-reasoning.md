---
id: PRD-v1.36-incremental-graph-reasoning
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-20
status: Draft
prd_depth: planning
upstream_source: docs/strategy/ROADMAP.md#v1.36.0
roadmap_ref: ROADMAP
target_version: v1.36.0
type: feature
tracks: [intelligence-adaptation]
---

# PRD — v1.36.0 Incremental Graph + Reasoning + Deep Research v2（规划级, v1.36+v1.45 合并）

## §1 背景与目标
GraphRAG 维护模式留真空；LightRAG(22.9k★) 有 graph+增量无治理；KAG 有 ontology+逻辑推理无 local-first/code。SAW 差异化：结论锚定可信 claims+置信+receipts。本版合并原 v1.36(incremental graph+reasoning) + v1.45(deep research v2)——同 intelligence track，都是"更智能的检索"。

**目标**：claims 图增量更新 + logical-symbolic reasoner + deep research 多步编排。

## §3 功能设计

### F1: claims 图增量更新（delta-merge）
- **用户故事**：新文档摄入后，claims 图只更新受影响子图，不全量重建。
- **优先级**：P0
- **关键规则要点**：① delta-merge 算法（新文档→受影响子图 merge）；② 增量走 Write Queue+receipt；③ 全量重建保留为 fallback。
- **主流程**：ingest → delta-merge → claims graph updated（只影响子图）。

### F2: logical-symbolic reasoner
- **用户故事**：agent 查询多跳推理问题时，reasoner 编排图谱推理+chunk 检索+LLM 推理。
- **优先级**：P0
- **关键规则要点**：① plan/retrieve/reason 三算子（借鉴 KAG）；② 自然语言→逻辑表达式→图谱推理+chunk 检索混合；③ 结论锚定可信 claims+置信+receipt（非 KAG 云优先）。
- **主流程**：query → plan → retrieve(reasoner+graph+chunk) → reason → 锚定 claims 的结论。

### F3: hierarchical community report v2
- **优先级**：P1
- **关键规则要点**：① 社区报告锚定 claims+置信（每社区可溯源）；② B3 status 轴续（TRUE/FALSE/SUSPECTED）。

### F4: Deep Research v2（原 v1.45 合并）
- **用户故事**：Scholar 编排多步 web 搜索+库内 claims+logical-symbolic reasoner→可溯源研究报告。
- **优先级**：P1
- **关键规则要点**：① web-grounded claim 摄入（URL→claim 带 freshness timer+source authority）；② 研究报告 provenance 导出。

## §6 验收标准
- **AC-F1**：ingest 新文档后 claims 图 delta-merge（不全量重建），增量走 Write Queue+receipt。
- **AC-F2**：logical-symbolic reasoner 对多跳问题返回结论锚定 claims（可溯源）。
- **AC-F4**：deep research 产报告带 ≥N 可溯源 claims `[TBD]`。

## §8 风险与依赖
- 前置：v1.35.0（Structured Context API，reasoner 依赖统一 context 层）。
- R1: logical-symbolic reasoner 实现复杂 → 先 plan/retrieve 两算子, reason 算子可后续补。
- thin_sections: delta-merge 算法细节、reasoner 算子 spec → 01 升级补全。
