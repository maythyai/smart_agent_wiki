---
id: SPEC-F-R-5
title: 闭合 Q1/Q3 复盘补记（retrospective-v1.12.0.md 标注闭合）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-e2e-tail-v1.13.0.md
pms_ref: .csp/product-spec/PMS-e2e-tail.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-R-5
complexity: S
tdd_ref: .csp/tech-decisions/ADR/ADR-013-ingest-recursion-benchmark.md
ac_coverage: 2/2
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.13.0.md#T-F-R-5
---

# SPEC-F-R-5: 闭合 Q1/Q3 复盘补记

## 实现 delta（ground 自源码）

> Q1/Q3 是 retrospective-v1.12.0.md findings，本轮 E2E 已闭合，在原文件补记关闭标注。

### 改动点

| 文件 | 现状 | 改为 |
|---|---|---|
| `.csp/artifacts/retrospective-v1.12.0.md` Q1 finding | Q1（真实 API E2E 未跑，High/P1）标 open，建议用户设 API key 后验证 | 追加 `**v1.13.0 闭合**`：commit `84e1776` 用 httpx 直连 vLLM `qwen_embedding@8001`，真实 API E2E 验证通过（semantic 检索召回正常） |
| `.csp/artifacts/retrospective-v1.12.0.md` Q3 finding | Q3（ST fallback 路径未测，Low/P3）标 open，建议可选验证 | 追加 `**v1.13.0 闭合**`：commit `84e1776` 删除了 ST fallback 路径（`_st_available`/`_embed_via_st` 移除），provider 改为 API-only（httpx 直连），无 ST fallback 分支需测 |

### 不改动

- 不新建 retrospective 文件（Q1/Q3 是 v1.12.0 findings，在原文件 `retrospective-v1.12.0.md` 补记）。
- 不闭合其他 findings（N3/M2/L2/O1-O4 续留，非本轮范围）。
- 不改动 Q1/Q3 的原始描述/证据（只追加闭合标注）。

## 后端架构

### 闭合标注格式

在 Q1 finding 段落末尾追加：
```markdown
**v1.13.0 闭合**：commit `84e1776` 用 httpx 直连 vLLM `qwen_embedding@8001`，
真实 API E2E 验证通过（semantic 检索召回正常）。Q1（真实 API E2E 未跑）→ closed。
```

在 Q3 finding 段落末尾追加：
```markdown
**v1.13.0 闭合**：commit `84e1776` 删除了 ST fallback 路径
（`_st_available`/`_embed_via_st` 移除），provider 改为 API-only
（httpx 直连 vLLM），无 ST fallback 分支需测。Q3（ST fallback 路径未测）→ closed。
```

### Q1/Q3 闭合依据（ground 自源码/commit）

| finding | 闭合依据 | 证据 |
|---|---|---|
| Q1（真实 API E2E 未跑） | commit `84e1776` 用 httpx 直连 vLLM `qwen_embedding@8001`，真实 API E2E 验证通过（semantic 检索召回正常） | PRD §1.1 "commit `84e1776`：httpx + 去 ST fallback，已合入 master" + retro-v1.12.0 Q1 finding 标 open |
| Q3（ST fallback 路径未测） | commit `84e1776` 删除 ST fallback 路径（`_st_available`/`_embed_via_st` 移除），provider 改 API-only，无 ST fallback 分支需测 | PRD §1.1 "commit `84e1776`：httpx + 去 ST fallback" + retro-v1.12.0 Q3 finding 标 open |

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-E-1（Q1 闭合标注） | `tests/unit/test_retrospective_closure.py`（新建）：读 `retrospective-v1.12.0.md` Q1 finding → 含 `**v1.13.0 闭合**` + commit `84e1776` | Q1 段落含 "v1.13.0 闭合" + "84e1776" |
| AC-E-2（Q3 闭合标注） | `tests/unit/test_retrospective_closure.py`（扩）：读 Q3 finding → 含 `**v1.13.0 闭合**` + ST fallback 已删 | Q3 段落含 "v1.13.0 闭合" + "ST fallback" |

## 实现就绪度

- [x] 改动点明确（retrospective-v1.12.0.md Q1/Q3 追加闭合标注）
- [x] 闭合依据明确（commit 84e1776，PRD §1.1 已述）
- [x] 不新建文件（原文件补记）
- [x] 不闭合其他 findings（N3/M2/L2/O1-O4 续留）
- [x] AC 覆盖 2/2
