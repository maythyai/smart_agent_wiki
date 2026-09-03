# 复盘 — v1.2.0 Wave 1 安全/可观测硬化（2026-09-03）

> 07 闭环校验。findings 回流 roadmap 与下一轮 01。

## 闭环校验结论：✅ 通过

| 链路环节 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-product-hardening-v1.md → SPEC-F-{A1,B1,C1-5,D1,D3,E1}.md（10 Spec 1:1 Task）|
| Spec → Task | ✅ | WBS.md 10 Task，spec_ref 列 1:1 |
| Task → commit | ✅ | 10/10 Task ID 均在 master 历史有 commit（d9f64c5 切片含 A1/B1/C3/C4；本轮 cherry-pick C1/C2/C5/D1/D3 + E-1）|
| AC → 测试 | ✅ | AC-SEC-1(security_matrix 23t)/AC-SEC-2(receipt 11t)/AC-OBS-2(observability 9t)/AC-E2E-1(smoke)/AC-ALIGN-1(claim_diff) |
| commit → tag | ✅ | v1.2.0 annotated tag @ 532710f |
| 测试 | ✅ | 1853 passed / 3 skipped / 0 失败 |
| 构建 | ✅ | wheel = smart_agent_wiki-1.2.0 |

## Findings（回流）

### F1 — 工具：subagent 静默写入失败 [高]
4 个 subagent 的 write_file/edit_file 返回 "completed with no output" 但实际未落盘——C-2 核心（dispatcher+receipt_store）、D-3 编辑（observability+health）全丢，仅 migrations+test 幸存。Lead 以幸存 test 为 TDD 契约重建。
- **回流下一轮 05**：Lead 在 spawn 后、commit 前必须 `git status` 逐 worktree 核验落盘，不信任 subagent 的"completed"无输出回报。考虑给子 agent 加"写后立即 read 回读校验"硬约束。
- **回流 03/工具链**：上报工具执行层故障（MCP local tools 间歇性空返回）。

### F2 — 技术债：ruff baseline 未绿 [中]
项目无 ruff 配置文件，默认值下未修改的 master queue.py 报 7 个 UP017。`timezone.utc`/`except Exception` 是全代码库既有 pattern（queue/dispatcher/ed25519/health/observability）。本轮决策：新代码匹配 pattern，不顺手重构。
- **回流下一轮 01/04**：建独立 task「ruff 配置 + baseline 修」（加 `pyproject [tool.ruff]` 显式 select/noqa 策略，或统一 `timezone.utc`→`UTC` 全量修）。不应在功能 Wave 内混入。

### F3 — roadmap 现实漂移 [中]
ROADMAP v1.1.0 narrative 标"产品加固 in-progress"，但 v1.1.0 实际发布的是 MCP 思考工具/breadcrumb 等（不同主题）；产品加固（Wave 1）实际落地为 v1.2.0。本轮仅修了 canonical 版本行 + status 表（v1.1.0/v1.2.0 → released），narrative 段未重写。
- **回流下一轮 01**：重写 ROADMAP v1.1.0/v1.2.0 narrative 使主题与实际发布对齐；重定义 v1.3.0 主题。

### F4 — 行为变更（须入 release notes / 迁移指南）[中]
v1.2.0 含 2 处行为变更（非 API break，但影响运维）：
- **JSON 日志默认 ON**：team/prod 部署无需配 `SAW_JSON_LOGS=1` 即得结构化日志；本地 dev 需 `SAW_PRETTY_LOGS=1` 切回可读文本。
- **/health/ready engine-aware**：engine 未初始化 → 503（此前恒 200，只要 db/redis 通）。K8s readiness 行为变严。
- **回流 06/文档**：QUICKSTART/MIGRATION 补"v1.2.0 行为变更"段（本轮未补，标 [TBD] 给下一轮）。

### F5 — CMS re-align [完成]
- drift D1（6 agent execute() 疑空实现）→ **更正为不成立**：6 agent 均有真实 execute()（writer:56/librarian:53/critic:56/linker:51/scholar:56/guardian:80），仅 BaseAgent.execute(base.py:56) stub。
- drift D3（前后端认证独立）→ **消解**：前端 token 拦截链完整同源。
- 行漂移记录：auth_dep 实际 app.py:275（CMS 标 267）；observability 实际在 drivers/web/middleware/。
- 新增调用链：dispatcher→_produce_receipt→ReceiptSigner→ReceiptStore.store/verify_chain；health→check_engines。

### F6 — 范围：Wave 2/3 延后 [计划]
Wave 2（7 Task：A2/A3/A4 冒烟 + B2/B3 宣称一致 + D2 trace 贯穿 + E2 coverage 门禁）、Wave 3（3 Task：A5 离线 fallback + A6 CI smoke + E3 CI 集成）未在本周期实施。
- **回流下一轮 01**：评估是否将 Wave 2/3 纳入下一周期 PRD，或插入新优先级（如 F2 ruff 修、F4 文档补）。

## 度量
- 本轮 commit：11（5 feature/test + 1 csp docs + 1 release + 4 worktree 原子）
- 新增测试：59（16+23+11+9）+ E-1 基线
- 全量：1853 passed / 3 skipped
- 覆盖率基线：62% total / 64% core（E-1 实测）
- 团队：4 并行 subagent（worktree 隔离）+ Lead 集成；max_workers=4
