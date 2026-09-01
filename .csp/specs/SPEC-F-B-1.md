---
id: SPEC-F-B-1
title: 宣称 diff 脚本
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-claim-alignment.md
cms_ref: .csp/code-spec/saw/entry-points.jsonl
feature_id: F-B-1
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
---

# SPEC-F-B-1: 宣称 diff 脚本

## 实现 delta（源自 CMS entry-points）
- 新增 `scripts/claim_diff.sh` [TBD]：grep README/docs 文本宣称（MCP 数/连接器数/agent 数/入口数）vs `entry-points.jsonl` + `knowledge-graph.json`（`cms_extract.sh` 产物）。
- 输出 added/changed/removed 宣称项；重跑至 0 diff = 一致。

## 接口契约
- CLI/脚本：`bash scripts/claim_diff.sh`；stdout diff 报告；退出码 0=一致/1=有 diff。

## 后端逻辑
- 解析 docs 文本宣称数 → 比对 entry-points 计数 → diff 报告。

## 测试映射
| AC | 用例 |
|---|---|
| AC-ALIGN-1（代码 61 MCP vs 宣称 diff） | `test_claim_diff_mcp` |
| 0 diff = 一致 | `test_claim_diff_clean` |

## 实现就绪度
- [x] AC 覆盖 2/2；纯 grep 可复现
