# 复盘 — v1.7.0 graph 隔离 + 清理 + 覆盖（2026-09-04）

> 07 闭环校验。findings 回流下一轮 01（v1.8.0）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec/ADR | ✅ | PRD-graph-workspace-v1.7.0 Approved；ADR-009 entity workspace 隔离；3 SPEC 1:1 |
| ADR → Task | ✅ | WBS 3 Task（T-F-K-1..3）；ADR-009 驱动 T-F-K-1 |
| Task → commit | ✅ | WBS 逐 Task 标 commit；3 Task 全 done（Wave1 ec22914 / Wave2 763e748 + DEV-LOG 8b1a67a）|
| AC → 测试 | ✅ | AC-WS-6(graph 隔离) / AC-ARCH-1(无 setattr) / AC-COV-3(synthesize 覆盖 + ratchet 64) |
| commit → tag | ✅ | v1.7.0 annotated @ 2c4a9d7 |
| 测试/lint | ✅ | 1977 passed/3 skipped；ruff src/+tests/ 0 errors；smoke 6/6 |
| 构建 | ✅ | wheel smart_agent_wiki-1.7.0 |

## v1.7.0 度量
- 3 Task done（graph 隔离 + scope 清理 + 覆盖，债务收口 III）
- 新增测试 ~18（graph_workspace 4 + scope 3 + synthesize 11）
- synthesize 子模块覆盖：engine.py 37→65% / scheduler.py 32→85%
- 全量 1977 passed（+18 vs v1.6.0）；coverage 63.7→64.2%；fail_under 63→64
- **workspace 三闭环完成**：读（claim search/get_by_id + tree/compile + graph）+ 写（claim insert/ingest + entity GraphSink）+ graph 隔离 全通

## Findings（回流 v1.8.0）

### K1 — coverage 65 未达 [中]
F-K-3 synthesize 覆盖完成（engine 65% / scheduler 85%），但全量 64.2%——最后 gap 在 `compile/compiler.py` 17%（复杂编译器）。fail_under=64（硬约定 #10）。
- **回流 04/05**：v1.8.0 补 compile/compiler.py 深覆盖，ratchet 64→65。

### K2 — per-request workspace 注入未做 [中]
workspace scope 仍引擎级（QueryEngine startup 单例 default ws）。graph/tree/compiler 的 scope 是引擎级，非请求级。Web 多 workspace 请求级注入（request context → engine）未做。
- **回流 03**：v1.8.0+ ADR（请求级 workspace context 注入，engine 工厂 per-request 或 contextvar）。

### K3 — entity_relation 用 JOIN 两端过滤（未加冗余列）[低]
graph 关系过滤用 JOIN entity 两端（非 entity_relation 加 workspace_id 列）。性能可接受（图规模小），但大图可能慢。
- **回流 03**：若性能问题，加 entity_relation.workspace_id 冗余列。

## 下游衔接 → v1.8.0（新一轮 01）
- 下一版本主题待定。建议：**coverage 65 收口（K1）** 或 **per-request workspace 注入（K2）** 或 开新能力。
- workspace 隔离本轮**三闭环完成**（v1.5.0 读 + v1.6.0 读全路径+写 + v1.7.0 graph）——workspace 故事告一段落，下一轮可转新能力。
- 既有产物：ADR-006/007/008/009、workspace 全套原语、3 轮覆盖骨架。
