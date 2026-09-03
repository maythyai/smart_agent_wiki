# 复盘 — v1.4.0 平台化与团队协作（2026-09-03）

> 07 闭环校验。findings 回流下一轮 01（v1.5.0）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec/ADR | ✅ | PRD-platform-team-v1.4.0；ADR-005 workspace 隔离；无新 spec（direct task）|
| ADR → Task | ✅ | WBS v1.4.0 表 6 Task（P-1..4 + Z-4/5），ADR-005 驱动 P-4 |
| Task → commit | ✅ | WBS 逐 Task 标 commit；6 Task 全 done |
| AC → 测试 | ✅ | AC-SEC-4/5(13 rbac)/AC-DEPLOY-1/2(3 compose)/AC-OBS-3/4(3 health-audit)/AC-WS-1/2(3 workspace)/AC-LINT-2(313 F401)/AC-LINT-3(importorskip) |
| commit → tag | ✅ | v1.4.0 annotated @ a05d6b7 |
| 测试/lint | ✅ | 1898 passed/3 skipped；smoke 6/6；ruff src/+tests 0 errors（F401 启用）|
| 构建 | ✅ | wheel smart_agent_wiki-1.4.0 |

## v1.4.0 度量
- 6 Task done（platform 4 + debt 2）
- 新增测试 ~25（rbac 13 + compose 3 + health/audit 3 + workspace 3 + ci 2 importorskip + smoke_harness with_receipts）
- ruff F401：313 auto-fix（156 文件），F401 从 ignore 移除→启用
- 全量 1898 passed；migration v8（workspace_id + user_workspace_auth）

## Findings（回流 v1.5.0）

### H1 — ruff F841 仍 defer [中]
Z-4 收口了 F401（313 修，启用），但 F841（27 死赋值，副作用 RHS）仍 ignore。需逐个手审（drop-assign vs delete no-op）。
- **回流 04/05**：建 Z-4b task（27 文件手修 F841）。本轮已记 pyproject ignore 注释。

### H2 — P-4 workspace 隔离仅 primitive 级 [中]
P-4 实现了隔离原语（repo list_by_workspace + user_workspace_auth 绑定）+ 测试验隔离，但**全查询路径路由**（每个 engine/repo 查询注入 workspace_id 过滤）未做。当前隔离在原语层验，生产级须全路径路由 + e2e 跨 ws 拒。
- **回流 03/05**：v1.5.0+ 建专项「workspace 全路径路由」task（QueryEngine/IngestPipeline 注入 workspace scope）；当前 AC-WS-1/2 在原语层满足，全路径留后续。

### H3 — P-2 deploy 仅结构验，未 runtime 验 [低]
docker-compose.prod.yml 经 YAML 结构 + healthcheck/secrets 断言，但未真跑 `docker compose up`（CI 无 docker）。AC-DEPLOY-1 是结构层满足。
- **回流 06/CI**：若上 CI docker job，加 runtime 验；当前 local-only 无 push，结构验够。

### H4 — P-1 Cedar 热加载无触发端点 [低]
reload() 方法 + 测试验，但无 admin API/CLI 触发（operator 须编程调用）。[TBD] `POST /api/admin/policy/reload` 或 `saw policy reload`。
- **回流 04/05**：v1.5.0+ 补 admin 触发端点（小 task）。

### H5 — coverage 棘轮仍 60（G2 未解）[中]
v1.3.0 G2（coverage 80% 目标）未推进；1898 测试但 % 未重测。核心引擎 64%（v1.3.0 基线），query 子模块仍是杠杆。
- **回流 04/05**：v1.5.0 补 query 子模块测试提覆盖，逐步上调 fail_under。

## 下游衔接 → v1.5.0（新一轮 01）
- roadmap（Z2 已重写）：v1.5.0 = 智能与自适应（multi-agent workflow 生产级、Learn 引擎落地、token 优化实测、agent 角色一致性）。
- 下一轮 01 须决策：开智能自适应新能力 OR 先清 H1/H2/H4 债（F841/workspace 全路由/Cedar 端点）。
