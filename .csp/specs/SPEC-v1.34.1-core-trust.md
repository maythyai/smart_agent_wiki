---
id: SPEC-v1.34.1-core-trust
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-27
status: approved
prd_ref: PRD-v1.34.1-core-trust-hardening
target_version: v1.34.1
---

# SPEC — v1.34.1 core-trust 硬化（轻量）

## F3: stale-freshness contamination（v1.31.1 deferred）
**文件**: `src/saw/adapters/storage/claims_repository.py:scan_contamination()` + `src/saw/api/routes/govern.py` + `src/saw/drivers/mcp/tools/govern.py`
**改动**: scan_contamination 新增 stale-source 检测——查 source claim 的 `last_accessed`，早于 `SAW_STALE_THRESHOLD_DAYS`（default 90）→ 返回 reason="stale_source"。
**AC**: test_scan_contamination_stale_source（unit test: insert source with old last_accessed → flag）。
**证据 file:line**: `claims_repository.py scan_contamination()` 当前仅 superseded_source 逻辑（line 428-460）。

## F4: Dashboard 状态卡（CRITIC-F-01）
**文件**: `web/src/pages/Dashboard.tsx`
**改动**: 移除 "View Graph"/"Search Pages"/"Manage Integrations" 按钮；新增 StatusCards（队列深度/agent 活动/矛盾数），接 `/api/v1/status`（既有）或 dashboard stats endpoint。
**AC**: test_dashboard_no_nav_buttons + test_dashboard_status_cards（vitest）。
**证据 file:line**: `Dashboard.tsx` button_sample 含 View Graph/Search Pages/Manage Integrations。

## F1: coverage push（AUDIT-F-04 partial）
**文件**: `tests/unit/engines/ingest/test_pipeline_phases.py`（扩）+ `tests/unit/engines/query/test_learn.py`（新）
**改动**: 补 extract.py helpers 测试 + learn.py 测试。fail_under 68→70。
**AC**: extract.py ≥40% coverage; total ≥69%（诚实地）。若未到 70%：标 gap defer v1.34.2。

## 测试
- pytest --cov-fail-under=70（目标）；ruff 0；tsc clean；vitest pass。
- 双闸门 exit 0（version_integrity + findings_closure with --baseline）。