# 复盘 — v1.5.0 智能与自适应（2026-09-03）

> 07 闭环校验。findings 回流下一轮 01（v1.6.0）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec/ADR | ✅ | PRD-intelligence-adaptation-v1.5.0 Approved；ADR-006 resume 状态机；ADR-007 workspace scope；8 SPEC 1:1（SPEC-F-I-1..4 + SPEC-F-Z-6..9）|
| ADR → Task | ✅ | WBS 8 Task（T-F-I-1..4 + T-F-Z-6..9）；ADR-006 驱动 T-F-I-1；ADR-007 驱动 T-F-Z-7 |
| Task → commit | ✅ | WBS 逐 Task 标 commit；8 Task 全 done（Wave1 404c787 / Wave2 c6d6b10 / Z-9 616d929 / Z-6 4b45a61 + DEV-LOG 7e9a29a）|
| AC → 测试 | ✅ | AC-WF-1/2(resume+validate) / AC-LR-1/2(distill mock+gaps) / AC-TK-1(bench) / AC-AG-1(lint) / AC-LINT-2续(F401/F841=0) / AC-WS-3(workspace routing) / AC-SEC-5续(policy reload) / AC-COV-1(query coverage+fail_under 63) |
| commit → tag | ✅ | v1.5.0 annotated @ 89b284e |
| 测试/lint | ✅ | 1929 passed/3 skipped；ruff src/+tests/ 0 errors（F401+F841 启用）；smoke 6/6 |
| 构建 | ✅ | wheel smart_agent_wiki-1.5.0 |

## v1.5.0 度量
- 8 Task done（4 新能力 + 4 债务）
- 新增测试 ~31（workflow 4 + token 2 + learn 2 + policy 2 + workspace 3 + query coverage 10 + wiki_indexer 4 + lint_baseline 2 + coverage_gate 改）
- ruff F841：27 处手审（19 纯删 + 8 裸调用），F841 从 ignore 移除→启用
- 全量 1929 passed（+31 vs v1.4.0 1898）；coverage 63%（+1 vs 62%）；fail_under 60→63
- 新增 4 CLI 命令（workflow/learn/token/policy sub-app）；workflow_executor.resume() 延伸
- 既有引擎复用：M-16 状态机 / HI-9 持久化 / startup recovery / Distiller / TrendSenser / CedarPolicyEngine.reload / SessionTracker / WorkflowParser.validate 全未重造

## Findings（回流 v1.6.0）

### I1 — F-Z-7 workspace 路由仅搜索路径 [中]
本轮只做了 claims search/get_by_id + QueryEngine 搜索路径的 workspace scope 注入 + cache key 修复（AC-WS-3 在搜索数据路径满足）。**全路径**（graph_traverse / tree_mode / ContextCompiler / IngestPipeline 写入）未注入 workspace_id。诚实标注：非"全覆盖"。
- **回流 03/05**：v1.6.0 建专项"workspace 全路径路由 II"（graph/compiler/ingest-write 注入 + e2e 跨 ws 拒矩阵）。

### I2 — coverage 棘轮仅 63（未达 65）[中]
TMS-DELTA 原写 60→65，实测 63.1%，按硬约定 #10 设 fail_under=63（不高于实测）。query engine.py 14% / compare 23% / tree_mode 21% 仍是杠杆点。
- **回流 04/05**：v1.6.0 补 query engine.py / compare / tree_mode 深覆盖，ratchet 63→65+。

### I3 — F-I-1 resume 索引制（context 不持久化）[低]
resume 从 steps_completed index 续跑，但 context 不持久化→已 completed 步的 output 丢失则该步重跑。幂等靠 Write Queue outbox。
- **回流 03**：v2.0 演进全量 context 快照（需序列化 context dict，膨胀+耦合，本轮 thin defer）。

### I4 — F-Z-8 policy reload 仅 CLI [低]
`saw policy reload` 已落地；Web admin 端点 `POST /api/admin/policy/reload` defer（CLI 本地无鉴权，Web 端点需 RBAC admin 守）。
- **回流 04/05**：v1.6.0+ 补 Web admin 端点（小 task）。

### I5 — 工作区有遗留脏文件 [低]
master 有 pre-existing 未提交脏文件（`.planning/benchmarks/*.json` ×12、`CLAUDE.md`、`uv.lock`）——非本轮产物，本轮 commit 均未扫入。或为早期 benchmark 跑产物 / 本地 CLAUDE.md 草稿。
- **回流 00/治理**：下一周期 init 时 `git status` 核，决定 stash 或 commit（非功能性，不阻塞发布）。

## 下游衔接 → v1.6.0（新一轮 01）
- roadmap 下一版本主题待定（建议：**workspace 全路径路由 II + 深覆盖** 或 智能自适应续（自定义 agent / workflow 可视化））。
- 下一轮 01 须决策：开新能力 OR 先清 I1/I2 债（workspace 全路径 / coverage 65）。
- 既有产物可复用：本轮 ADR-006/007、8 SPEC、workspace_id 原语（v8）、CLI 命令骨架。
