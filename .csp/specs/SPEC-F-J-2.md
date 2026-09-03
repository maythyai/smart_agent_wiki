---
id: SPEC-F-J-2
title: workspace 写入路径（insert 持久化 + ingest 透传）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-debt-closure-v1.6.0.md
pms_ref: .csp/product-spec/PMS-debt-closure.md
feature_id: F-J-2
complexity: M
adr_ref: .csp/tech-decisions/ADR/ADR-008-workspace-write-strategy.md
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-J-2]
---

# SPEC-F-J-2: insert workspace_id 持久化 + ingest 透传

## 实现 delta（ground 自源码）
- `SQLiteClaimsRepository.insert`（`adapters/storage/claims_repository.py:155`）SQL 补 `workspace_id` 列 + 值 `claim.workspace_id`（ADR-008）。Claim 默认 'default' → backward compat。
- `upsert`（line 255）UPDATE 分支**不动** workspace_id（防覆盖）；INSERT 分支经 insert 写入。
- `IngestPipeline.ingest`（`engines/ingest/pipeline.py:100`）加 `workspace_id: str = "default"` 参数 → `_build_write_ops` 透传 → Claim 构建带 workspace_id（经 ClaimsSink 写入）。
- ClaimsSink 写 claim 时 claim.workspace_id 已设 → insert 落库正确。

## 接口契约
- 无新 CLI/HTTP；insert SQL + ingest 签名变更（默认 'default' backward compat）。
- ingest 到 ws "alpha" 的 claim 落 alpha（非 default）。

## 后端逻辑
- insert：`INSERT ... workspace_id VALUES (?, claim.workspace_id)`。
- ingest：workspace_id → Claim → WriteOp → ClaimsSink → insert。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-WS-5（ingest 写入 ws 隔离） | `tests/unit/test_workspace_routing.py` 扩：ingest(workspace_id="alpha") → claim 落 alpha + B ws 不可见 |

## 实现就绪度
- [x] Claim.workspace_id 字段就绪（domain）
- [x] AC 覆盖 1/1
- [TBD] ClaimsSink 是否透传 claim.workspace_id（05 核验）
