---
id: PRD-v1.35-structured-context-api
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-20
status: Draft
prd_depth: planning
upstream_source: docs/strategy/ROADMAP.md#v1.35.0
roadmap_ref: ROADMAP
target_version: v1.35.0
type: feature
tracks: [intelligence-adaptation]
---

# PRD — v1.35.0 Structured Context API v1（规划级, ★品类定位）

## §1 背景与目标
2026.09 行业论点收敛于 "Structured Context Infrastructure"——agent 需 context = vector(找相似)+graph(关系)+ontology(什么算什么)+state(现实此刻)+permission(谁能知)+action(可改什么)。SAW 架构本就覆盖六要素，但未统一暴露。本版**品类定位**：把分散的检索模式统一到一个 `saw_context` API，抢占"agent 可信编译知识层"品类。

**目标**：统一检索路由 + ontology 层 + state 层 + 自适应查询路由 + permission 维度。无单一竞品同时覆盖六要素（LightRAG 无治理/permission，KAG 无 local-first/code）。

## §3 功能设计

### F1: `saw_context` 统一 MCP+REST 接口
- **用户故事**：agent 经单一 `saw_context(query, mode, filters)` 获取结构化 context。
- **优先级**：P0
- **关键规则要点**：① mode = semantic|graph|drift|hybrid|logical；② filters = workspace/freshness/confidence/permission；③ 返回 unified context bundle（claims+graph+metadata+receipts）。
- **主流程**：agent 调 saw_context → 路由到对应检索 → 统一 bundle 返回。

### F2: ontology 层（concept type/relations）
- **用户故事**：agent 查询时能按 concept/type 过滤。
- **优先级**：P1
- **关键规则要点**：① claim→concept 归纳（复用既有 entity 模型）；② concept type/relation type 注册；③ 锚定 claims+receipts（可溯源到原文，非黑盒 ontology）。
- **主流程**：ingest 时抽取 concept → 查询时按 concept 过滤。

### F3: state 层（freshness/confidence/矛盾态作查询维度）
- **用户故事**：agent 查询时能过滤"仅 fresh/置信≥X/排除 contradicted"。
- **优先级**：P1
- **关键规则要点**：① freshness（9 级）作 query filter；② confidence（4 级）作 filter；③ contradicted claim 默认排除（可 opt-in）。

### F4: 自适应查询路由（confidence 门控）
- **优先级**：P2
- **关键规则要点**：① 低置信 claim 触发扩展检索/多跳；② 复用 BeyondUncertainty 启发式；③ SAW 4 级置信作门控。

### F5: permission 维度（RBAC workspace 过滤）
- **优先级**：P2
- **关键规则要点**：① query 按 workspace 过滤可见 claim；② permission 作 context 第六要素。

## §6 验收标准
- **AC-F1**：`saw_context(query, mode=hybrid)` 返回 claims+graph+metadata+receipts bundle。
- **AC-F2**：query filter `freshness>=3` 排除低新鲜度 claim。
- **AC-F3**：query filter `confidence>=cross_validated` 仅返回高置信 claim。

## §8 风险与依赖
- 前置：v1.34.1 ✓。
- R1: 统一 API 可能与既有 saw_query/saw_search MCP 工具重叠 → 保留既有工具 + saw_context 为上层封装。
- thin_sections: ontology schema 设计、adaptive routing 算法 → 01 升级补全。
