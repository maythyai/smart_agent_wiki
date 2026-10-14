---
id: PRD-compliance-profile-v1.32.1
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-14
status: approved
roadmap_ref: ROADMAP
target_version: v1.32.1
type: feature
see_also: PRD-compliance-audit-v1.32.0 (deferred 项)
---

# PRD — v1.32.1 数据驻留 + 合规配置 profile (feat MINOR)

> v1.32.0 deferred 项（解除条件：v1.32.0 released ✓）。feat MINOR（additive）。

## 背景
企业（医疗/金融/政务）合规准入需声明性配置：① 数据驻留（on-prem/region）；② 审计 receipt 强制；③ 留存策略。既有 `.saw/config.yaml` 仅支持 path/auth_mode，无合规 profile。

## 范围（1 feat）
- **合规 profile 加载 + 状态查询**: `.saw/compliance.yaml`（或 config.yaml `compliance` 节）声明 `profile`(hipaa/sox/gdpr/default) + `data_residency`(on_prem, region) + `require_audit_receipts` + `retention_days`。`saw_compliance_status` MCP + `GET /api/v1/compliance` REST 返回 active profile + on-prem 断言（host 非 networked → on_prem_satisfied）。

## 非目标
- 强制执行（block 非 on-prem 启动）→ 后续（v1.39 多租户同批）。
- per-workspace 存储后端物理绑定 → v1.39。

## 成功指标
- 无 compliance.yaml → status 返回 `{profile: "default", on_prem_satisfied: <bool>}`。
- 有 compliance.yaml → status 返回声明 profile + on_prem 断言。
- on-prem 断言：host∈loopback 或 SAW_ALLOW_UNAUTH_NETWORK 未设 → on_prem_satisfied=True。

## 留尾
- 强制执行 + per-workspace 物理绑定 → deferred v1.39（附解除条件）。
