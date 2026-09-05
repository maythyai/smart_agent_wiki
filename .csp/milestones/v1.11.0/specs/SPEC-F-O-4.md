---
id: SPEC-F-O-4
title: Spec 命名回更 + tag hash 复核（N5+N6，文档修复）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
prd_ref: docs/prd/PRD-debt-closure-v1.11.0.md
pms_ref: .csp/product-spec/PMS-debt-closure.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-O-4
complexity: S
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
ac_coverage: 3/3
related_tasks: [.csp/tasks/TASKS-DELTA-v1.11.0.md#T-F-O-4]
---

# SPEC-F-O-4: Spec 命名回更 + tag hash 复核

## 实现 delta（ground 自源码）

### N5: SPEC-F-N-1 CLI 命名回更

- **问题**：`.csp/specs/SPEC-F-N-1.md` 写 `saw search rebuild-embeddings`（子命令路径），实际实现为顶层命令 `saw rebuild-embeddings`（`src/saw/drivers/cli/main.py:73` `app.command(name="rebuild-embeddings")`）。
- **根因**：`search` 是独立函数注册（`main.py:78 app.command(name="search")(search)`），不是 Typer 子命令组，无法挂子命令。`rebuild-embeddings` 是独立顶层命令注册。
- **回更范围**（grep 确认共 3 处，均在 SPEC-F-N-1.md）：
  - L27：`- **重建命令**：\`saw search rebuild-embeddings\`（新增 CLI 子命令...` → 回更为 `saw rebuild-embeddings`（顶层命令）
  - L133：`### 重建命令（\`saw search rebuild-embeddings\`）` → 回更为 `### 重建命令（\`saw rebuild-embeddings\`）`
  - L189：`saw search rebuild-embeddings [--path DIR]` → 回更为 `saw rebuild-embeddings [--path DIR]`
- **不改实现**：实现是正确的（`main.py:73` 顶层命令），仅回更 Spec 文档。

### N6: tag hash 三处一致性复核

- **权威值**：`git rev-list -n1 v1.10.0` = `3865c75`（短 hash）。
- **复核三处**：

| 位置 | 当前值 | 复核结果 |
|---|---|---|
| `docs/strategy/ROADMAP.md` L170 | `@3865c75` | ✓ 一致（07 已更正） |
| `.csp/lifecycle-state.json` 06-ship progress | `@3865c75` | ✓ 一致（07 已更正） |
| `git rev-list -n1 v1.10.0` | `3865c75...` | ✓ 权威值 |

- **结论**：三处一致，本轮仅复核确认，无回更需要（若 05 实施时 `git rev-list` 确认一致则零改动）。

## 后端架构

无代码改动（文档修复 + 复核任务）。

## API 契约

无 API 变更。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-SPEC-1（Spec 命名回更） | `tests/unit/test_spec_naming.py`（新建）：grep `saw search rebuild-embeddings` 于 `.csp/specs/SPEC-F-N-1.md` → 0 匹配 | 旧命令名全部回更 |
| AC-SPEC-2（实现不变） | `tests/unit/test_spec_naming.py`（扩）：subprocess `saw rebuild-embeddings --help` → exit 0 | 顶层命令可用 |
| AC-HASH-1（hash 三处一致） | `tests/unit/test_hash_consistency.py`（新建）：`git rev-list -n1 v1.10.0` short hash → 对比 ROADMAP + lifecycle-state.json → 三处一致 | hash 一致 |

> 注：AC-SPEC-2 和 AC-HASH-1 依赖 git/CLI 环境，可用 `subprocess.run` 或 `shutil.which` 守卫；CI 有 git 可跑。AC-SPEC-1 纯文件 grep，CI 可跑。

## 安全考量

N/A（文档修复 + 复核任务）。

## 实现就绪度

- [x] 回更位置明确（SPEC-F-N-1.md L27/L133/L189，grep 确认 3 处）
- [x] 回更后命令名正确（`saw rebuild-embeddings`，与 `main.py:73` 一致）
- [x] hash 三处复核确认（@3865c75 一致）
- [x] AC 覆盖 3/3
- [x] 不改实现（仅文档回更 + 复核）
