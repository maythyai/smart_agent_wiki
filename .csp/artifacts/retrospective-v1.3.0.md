# 复盘 — v1.3.0 硬化尾巴 + 技术债清理（2026-09-03）

> 07 闭环校验。findings 回流下一轮 01（v1.4.0）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-hardening-tail-v1.3.0；Wave 2/3 沿用 v1 spec（1:1），F-debt 无 spec（direct task）|
| Spec → Task | ✅ | WBS v1.3.0 表 13 Task（A2-6/B2-3/D2/E2-3/Z1-3）|
| Task → commit | ✅ | WBS 表逐 Task 标 commit；提交用 Feature ID（F-A-x），WBS 映射 Task→commit→Feature |
| AC → 测试 | ✅ | AC-E2E-1(8 smoke)/AC-E2E-2(3 offline)/AC-OBS-1(2 trace)/AC-TEST-1(2 cov)/AC-TEST-2(3 ci)/AC-LINT-1(ruff 0)/AC-ALIGN-2(3 capabilities)/AC-DOC-1/2 |
| commit → tag | ✅ | v1.3.0 annotated @ a82f0e3 |
| 测试 | ✅ | 1874 passed / 3 skipped |
| 构建/lint | ✅ | wheel 1.3.0；ruff src/+tests 0 errors；saw smoke 6/6 |

## v1.3.0 度量
- 13 Task done（Wave 2: 9 含 debt docs；Wave 3: 4 含 ruff 串行）
- 新增测试 ~30（smoke 11 + trace 2 + coverage 2 + ci 3 + capabilities 3）
- 全量 1874 passed；ruff baseline 从 ~3165 errors → 0（config + 2 F823 修 + 21 auto-fix）
- 团队：2 subagent（Z2/Z3 纯文档，稳定提交）+ Lead 串行核心；工具本周期无静默写入故障

## Findings（回流 v1.4.0）

### G1 — ruff 收口部分 defer [中]
F-Z-1 建了 config + 修 2 F823 真 bug + 21 auto-fix，但 F401（626 未用 import）+ F811（25）+ F841（27 死赋值）整体 defer（ignore）。这些规则未启用=未捕获。
- **回流 01/04**：建专项 task T-F-Z-1b（F401 import 审计，需 __init__ re-export 核验）+ T-F-Z-1c（F841 27 死赋值手修）。本轮已记入 pyproject ignore 注释。

### G2 — coverage 棘轮在 60 非目标 80 [中]
E-2 设 fail_under=60（current 62% 的回归底线），目标 80% 未达。严格 80% 会立即 block 全部合并（反模式）。
- **回流 04/05**：随测试增长逐步上调 fail_under（62→65→...→80）。核心引擎 64%，主要缺口 query(compare 30/related 23/tree 24)。补 query 子模块测试是提覆盖率的杠杆点。

### G3 — heavy-SDK learn 测试 CI 排除 [中]
test_distiller/test_fsrs/test_trends 需 sentence-transformers，非 dev dep；CI coverage 步 ignore 它们。CI 全量 test 步（pytest tests/ -x）若 dev 装不含该 SDK 会挂。
- **回流 03/04**：要么把 sentence-transformers 入 dev deps（重），要么给这 3 测试加 importorskip 优雅跳过（轻，推荐）。

### G4 — F823 graphql 真 bug 未被测试捕获 [低]
api/graphql.py 2 处 UnboundLocalError（global 遮蔽）是 latent bug，1853→1874 测试全过却未触发——说明 graphql 模块无测试覆盖或未在主路径 import。
- **回流 04/05**：给 graphql 加 smoke/单测，或确认其是否 dead code 待移除。

### G5 — subagent 稳定性 [低]
本周期 2 文档 subagent（Z2/Z3）干净提交，无静默写入故障（对比 v1.2.0 的 4 subagent 全故障）。工具层间歇性。
- **回流流程**：Lead 仍须每 worktree `git status` 核验落盘（不信任 subagent 回报）。

## 下游衔接 → v1.4.0（新一轮 01）
- roadmap（Z2 已重写）：v1.4.0 = 平台化与团队协作（platform-team）。
- 下一轮 01 须决策：是否先清 G1/G3 lint/SDK 债，再开 platform-team 新能力。
