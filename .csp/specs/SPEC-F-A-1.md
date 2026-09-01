---
id: SPEC-F-A-1
title: 冒烟命令骨架与 fresh 库初始化
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-e2e-usability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-A-1
complexity: S
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [SHARED-SCHEMAS.md, API-OVERVIEW.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-A-1-1]
---

# SPEC-F-A-1: 冒烟命令骨架

## 实现 delta（源自 CMS）
- 新增 CLI 冒烟命令（`drivers/cli/commands/smoke_cmd.py` [TBD 命令名]，经 `main.py` 注册）。
- fresh 库初始化复用 `init_cmd`（`commands/init_cmd.py:22`），临时库置 `.hub-run/smoke/`。
- 节点报告器：逐节点 PASS/FAIL+耗时，退出码 0/1。
- 不含各引擎断言（F-A-2..A-4），不含 CI（F-A-6）。

## 接口契约
- CLI: `saw smoke [--keep]`（[TBD] 命令名）；stdout 节点报告；退出码 0=全过/1=有失败。
- 无新增 HTTP/MCP 入口。

## UI/DB
- N/A（CLI 工具）。DB：fresh `saw.db`（复用 schema，源自 CMS §M09）。

## 后端逻辑
- 骨架：`init` → 注册节点 → 依次跑（节点实现在 F-A-2..A-4）→ 汇总 → 退出码。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-E2E-1（fresh→全 PASS 退出0） | `test_smoke_skeleton_pass`：fresh 库跑骨架，断言退出 0 + 节点报告 |
| 失败退出非0 | `test_smoke_skeleton_fail`：注入失败节点，断言退出 1 + 定位节点 |

## 实现就绪度
- [x] 命令接口可 mock（CLI 退出码可断言）
- [x] AC 覆盖 2/2
- [TBD] 命令名（避免与 `audit` 混淆）
