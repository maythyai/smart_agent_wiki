# 复盘 — v1.6.0 债务收口（2026-09-03）

> 07 闭环校验。findings 回流下一轮 01（v1.7.0）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec/ADR | ✅ | PRD-debt-closure-v1.6.0 Approved；ADR-008 workspace 写入；4 SPEC 1:1 |
| ADR → Task | ✅ | WBS 4 Task（T-F-J-1..4）；ADR-008 驱动 T-F-J-2 |
| Task → commit | ✅ | WBS 逐 Task 标 commit；4 Task 全 done（Wave1 627957b / Wave2 895c948 + DEV-LOG d6f138d）|
| AC → 测试 | ✅ | AC-WS-4(tree/compile 隔离) / AC-WS-5(insert+ingest 写隔离) / AC-COV-2(query 深覆盖，65 部分——见 J1) / AC-SEC-6(admin reload) |
| commit → tag | ✅ | v1.6.0 annotated @ 62f36cc |
| 测试/lint | ✅ | 1959 passed/3 skipped；ruff src/+tests/ 0 errors；smoke 6/6 |
| 构建 | ✅ | wheel smart_agent_wiki-1.6.0 |

## v1.6.0 度量
- 4 Task done（4 债务收口，无新能力）
- 新增测试 ~30（workspace 扩 5 + admin 3 + engine 11 + compare 4 + tree_mode 6 + compiler mock 适配）
- query 子模块覆盖大幅提升：engine.py 14→94% / compare.py 23→91% / tree_mode.py 21→66%
- 全量 1959 passed（+30 vs v1.5.0 1929）；coverage 63.1→63.7%
- workspace 全路径闭环：读（search/get_by_id + tree/compile）+ 写（insert+ingest）双通

## Findings（回流 v1.7.0）

### J1 — coverage 65 未达 [中]
F-J-3 query 深覆盖完成（engine/compare/tree_mode 大幅提升），但全量仅 63.7%——gap 在非 query 模块：`compile/compiler.py` 17% / `synthesize/scheduler.py` 32% / `reconcile/engine.py` 36%。fail_under 持 63（硬约定 #10）。
- **回流 04/05**：v1.7.0 补 compile/compiler + synthesize/scheduler 深覆盖，ratchet 63→65。

### J2 — graph_traverse workspace 隔离未做 [低]
graph_traverse 查 `entity`/`entity_relation` 表，无 workspace_id 列（v8 只加在 claim）。entity 隔离需新 migration。
- **回流 03**：v1.7.0+ ADR（entity 表加 workspace_id 列 + graph 路由注入）。

### J3 — F-J-1 QueryEngine 同步子服务用 setattr 私有属性 [低]
QueryEngine.__init__ 用 `setattr(_sub, "_workspace_id", ws)` 同步 tree_mode/compiler。可用但耦合私有属性。
- **回流 03**：v1.7.0+ 可演进为 search/compile 显式 workspace_id 参数（更干净）。

## 下游衔接 → v1.7.0（新一轮 01）
- 下一版本主题待定。建议：**coverage 65 收口（J1）** 或 **graph workspace 隔离（J2）** 或 开新能力。
- 既有产物可复用：ADR-008、4 SPEC、workspace 全路径读+写闭环、query 覆盖骨架。
- workspace 路由本轮**读写双闭环**（v1.5.0 读 + v1.6.0 读全路径 + 写）。
