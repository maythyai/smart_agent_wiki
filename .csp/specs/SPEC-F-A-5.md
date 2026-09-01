---
id: SPEC-F-A-5
title: 离线 fallback 冒烟（无 LLM）
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-e2e-usability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-A-5
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [SHARED-SCHEMAS.md]
ac_coverage: 2/2
---

# SPEC-F-A-5: 离线 fallback 冒烟

## 实现 delta（源自 CMS §M04 + KEY-CHALLENGES §1）
- LLM 不可达（断网/mock 失败）跑冒烟，断言核心路径 PASS（规则 fallback）。
- 复用 agent `_classify_fallback`（`agents/librarian.py:78`）、query 关键词路径。
- 降级标记：`AgentResult.metadata.fallback=true`、NL query 返回降级标注。

## 后端逻辑
- 注入 LLM 不可达 → 跑 ingest/govern/learn（不依赖 LLM 的路径）+ NL query（走 fallback）→ 断言 PASS + 降级标记。

## 异常处理
| 场景 | 处理 |
|---|---|
| LLM 超时/不可达 | 走 fallback，标记 degraded |
| fallback 路径缺 | 冒烟 FAIL，逐项补（暴露缺口） |

## 测试映射
| AC | 用例 |
|---|---|
| AC-E2E-2（LLM 不可达→fallback PASS） | `test_smoke_offline_fallback` |
| NL query 离线降级标记 | `test_smoke_offline_nl_degraded` |

## 实现就绪度
- [x] AC 覆盖 2/2
- [TBD] fallback 路径缺口由冒烟暴露后补
