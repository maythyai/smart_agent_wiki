---
id: ARCHIVE-MANIFEST-v1.32.1
milestone: v1.32.1
release_type: MINOR (feat)
tag: v1.32.1
commit: b25ba83
released: 2026-10-14
canonical_version: 1.32.1
---

# Archive Manifest — v1.32.1 (数据驻留 + 合规 profile)

## Release
- tag: `v1.32.1` (annotated, pushed origin)
- commit: `b25ba83 release: v1.32.1 — 数据驻留 + 合规配置 profile (feat MINOR)`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.32.1
- assets: wheel + sdist (1.32.1)

## Added (1)
- `saw_compliance_status` MCP + `GET /api/v1/compliance` REST: load `.saw/compliance.yaml` + on-prem assertion. New `src/saw/compliance/profile.py` (ComplianceProfile + load_compliance_profile + compliance_status).
- MCP 工具 38→39.

## Gate
- pytest 2420 pass / 7 skip / 0 fail (+6: 5 test_profile + 1 TestComplianceProfileRoute)
- coverage 68.42% (gate 67 ✓); ruff 0; tsc clean
- bump: 1.32.0 → 1.32.1 (MINOR, additive)

## Deferred → v1.39（附解除条件）
- 强制执行（block 非 on-prem 启动）+ per-workspace 存储后端物理绑定 → v1.39 多租户同批。解除条件: v1.39 workspace 物理隔离。

## 续留（折入后续版本）
- AUDIT-F-05/06 (saw web SPA + proxy) + AUDIT-F-08 (404→200) → v1.33.0（下一版，解 E2E-BLOCKED-01）
- AUDIT-F-01/04 (god-files + coverage 70) + stale-freshness contamination → v1.34.0
- CRITIC-F-01 (Dashboard 状态卡) → v1.35.0
- E2E-BLOCKED-01 → v1.33 saw web 挂 SPA 解除
