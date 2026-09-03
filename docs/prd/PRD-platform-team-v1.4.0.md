---
id: PRD-platform-team-v1.4.0
title: 平台化与团队协作
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-03"
product_type: platform
feature_count: 4
mvp_scope: [platform-team, deployment, observability, workspace-isolation]
thin_sections: [4]
upstream_source: "docs/strategy/ROADMAP.md#v1.4.0 + .csp/artifacts/retrospective-v1.3.0.md (findings G1-G5)"
target_version: v1.4.0
roadmap_ref: ROADMAP
related_pms:
  - .csp/product-spec/PMS-security-hardening.md   # RBAC 深化复用
  - .csp/product-spec/PMS-observability.md       # 可观测生产闭环
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
related_retrospective: .csp/artifacts/retrospective-v1.3.0.md
---

# PRD-platform-team-v1.4.0：平台化与团队协作

> v1.3.0 闭环后的新一轮 01。platform-team track：从单机 local-first 走向可自托管多用户平台。前置依赖 v1.3.0 硬化尾巴基线（✅）+ 技术债清理（部分——G1 ruff F401/F841 仍 defer，本轮携带）。

## 1. 背景与动机（roadmap v1.4.0 + 复盘 G1-G5）

v1.3.0 收口了硬化弧线（smoke 链/CI 门禁/ruff/trace/coverage 棘轮）。复盘（retrospective-v1.3.0.md）回流：
- **G1**：ruff F401（626 未用 import）+ F841（27 死赋值）整体 defer，本轮须做 import/re-export 审计收口。
- **G2**：coverage 棘轮在 60（非目标 80）；query 子模块（compare/related/tree）是覆盖率杠杆点。
- **G3**：heavy-SDK learn 测试 CI 排除；需 importorskip 优雅跳过。
- **G4**：graphql latent bug 未被测试覆盖。
本轮在开新 platform-team 能力的同时，携带 G1/G3 债务收口。

## 2. 范围（4 Feature 组）

### F-P-1：多用户与 RBAC 深化
team 模式已有 JWT + RBAC（viewer/editor/admin）+ Cedar（v1.2.0）。本轮：角色/权限生产级深化——Cedar 策略从 demo 走到可配置多租户策略文件；权限矩阵 e2e 测试覆盖每个 role×capability。
- **AC-SEC-4**：每个 role×capability 有 e2e 断言（0 越权）。
- **AC-SEC-5**：Cedar 策略文件可热加载（不重启）。

### F-P-2：团队部署形态收敛
docker-compose.prod 成熟：生产配置收敛（secrets 经 env 注入、持久化卷、healthcheck 接 v1.2.0 的 /health/ready）。
- **AC-DEPLOY-1**：`docker compose -f docker-compose.prod.yml up` 一键起 + healthcheck PASS。
- **AC-DEPLOY-2**：secrets 不入 image/git（detect-private-key 门禁）。

### F-P-3：可观测性生产闭环
v1.3.0 trace + JSON 日志 + /health/ready 已就绪。本轮：健康巡检（/health/ready 巡检脚本）+ 告警钩子（Sentry 已接，补 alert webhook）+ 审计面板（receipt chain v1.2.0 → 可视化查询）。
- **AC-OBS-3**：`saw health` 巡检命令聚合 engines/db/redis/receipt chain 状态。
- **AC-OBS-4**：receipt chain 可查询（`saw audit receipts --session`）。

### F-P-4：多工作空间隔离
多 vault/workspace 隔离：单实例多 wiki（path-based routing 或 workspace ID），用户授权绑定 workspace。
- **AC-WS-1**：不同 workspace 数据物理隔离（DB 分库或 schema 前缀）。
- **AC-WS-2**：用户授权范围绑定 workspace（跨 workspace 访问拒）。

### F-debt-carried（源自 G1/G3）
- **G1 ruff 收口续**：F401 import 审计（__init__ re-export 核验后启用）+ F841 27 死赋值手修。
- **G3 heavy-SDK**：learn 3 测试加 importorskip，CI 全量 test 步不再需 ignore。

## 3. 非目标
- 多代理 workflow 编排（留 v1.5.0 智能自适应）。
- F-P-4 多 workspace 的完整多租户 SaaS（本轮只做隔离基座 + 绑定，不做计费/配额）。
- coverage 提到 80%（G2 是渐进，本轮补 query 子模块测试为主，不设硬指标）。

## 4. 风险
- **F-P-1 Cedar 热加载**：策略文件变更的并发安全 [TBD]。
- **F-P-4 隔离**：DB 分库 vs schema 前缀的迁移成本——需 03 技术方案决策（migration v8）。
- **G1 import 审计**：626 处，盲删风险高，须逐文件核 re-export。

## 5. 下游衔接
- → 02 拆解：F-P-1..4 各拆 Feature + DAG；F-debt-carried 沿用 v1.3.0 Z 结构。
- → 03：F-P-4 隔离方案需 ADR（DB 分库 vs schema）；Cedar 热加载方案。
- → 04：F-P-1..4 + 2 debt Task；migration v8 串行（F-P-4 依赖）。
