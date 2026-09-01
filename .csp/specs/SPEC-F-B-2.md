---
id: SPEC-F-B-2
title: 能力清单生成（CAPABILITIES.md）
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-claim-alignment.md
cms_ref: .csp/code-spec/saw/entry-points.jsonl
feature_id: F-B-2
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-B-2-1]
---

# SPEC-F-B-2: 能力清单生成

## 实现 delta
- 新增 `scripts/gen_capabilities.sh` [TBD]：消费 `entry-points.jsonl` + `knowledge-graph.json` → 生成 `docs/CAPABILITIES.md`，每条带 file:line。
- 宣称无代码对应 → 标 `[unverified]`，不写"已支持"。

## 接口契约
- 产物 `docs/CAPABILITIES.md`（人/agent 可读）；条目格式：`| capability | entry | file:line | verified |`。

## 测试映射
| AC | 用例 |
|---|---|
| 每条带 file:line（AC-ALIGN-2 辅） | `test_capabilities_has_file_line` |
| 无对应标 [unverified]（AC-ALIGN-2） | `test_capabilities_unverified_marked` |

## 实现就绪度
- [x] AC 覆盖 2/2；依赖 F-B-1
