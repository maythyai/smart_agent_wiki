---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-debt-closure-v1.6.0.md]]"
  - "[[.csp/artifacts/retrospective-v1.5.0.md]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]] §M09(query)/§M13(ingest)"
created: "2026-09-03"
updated: "2026-09-03"
---

# PMS: debt-closure（workspace 全路径 II + 深覆盖）

> v1.6.0 债务收口模块。延续 v1.5.0：把 workspace scope 从搜索路径扩到 tree/compile 读取 + ingest 写入；query 深覆盖到 65；policy Web admin 端点。

## 模块边界
- **做什么**：
  - workspace 读取路径全路由（tree_mode + ContextCompiler 注入 workspace scope）；
  - workspace 写入路径（insert 持久化 workspace_id + IngestPipeline 透传）；
  - query 深覆盖（engine/compare/tree_mode 测试 → 65%）；
  - policy reload Web admin 端点（admin-only）。
- **不做什么**：graph_traverse workspace 隔离（entity 表无 ws 列，需 migration，defer v1.7.0）；resume 快照（v2.0）；新能力。
- **PMS 边界=PRD §2 F-J-1..4**。复用 v1.5.0 既有 workspace_id 原语（v8）+ QueryEngine workspace_id。

## 验收形态
- tree_mode + compiler 跨 ws 隔离（AC-WS-4）。
- ingest 写入 workspace "alpha" 的 claim 落 alpha，B ws 不可见（AC-WS-5）。
- 全量 coverage ≥ 65%，fail_under=65（AC-COV-2）。
- `POST /api/admin/policy/reload` admin 触发，非 admin 403（AC-SEC-6）。

## 接口契约摘要（ground 自源码）
- tree_mode：`engines/query/tree_mode.py:TreeModeSearch.__init__` + `search`（调 `claims_repo.get_by_id` line 108/243/250）。
- compiler：`engines/query/compiler.py:ContextCompiler.__init__` + `compile`（调 `claims_repo.get_by_id` line 88）。
- insert：`adapters/storage/claims_repository.py:SQLiteClaimsRepository.insert`（SQL 丢 workspace_id）。
- ingest：`engines/ingest/pipeline.py:_build_write_ops`（line 308）。
- policy：`adapters/crypto/cedar_policy.py:CedarPolicyEngine.reload`；Web 守卫 `drivers/web/middleware/security.py:require_role`。
- RBAC：`auth/permissions.py` + `drivers/web/middleware/security.py:get_current_user`。

## 关联
- PRD: `docs/prd/PRD-debt-closure-v1.6.0.md`
- 上游复盘: `.csp/artifacts/retrospective-v1.5.0.md`（I1/I2/I4）
- 复用 PMS: `PMS-intelligence-adaptation.md`（workspace scope 续）、`PMS-security-hardening.md`（RBAC）、`PMS-test-gate.md`（coverage）
- 下游 Spec: [待 03 回填] —— F-J-1..4 各 1 Spec
