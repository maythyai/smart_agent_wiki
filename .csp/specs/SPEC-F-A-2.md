---
id: SPEC-F-A-2
title: ingest+compile 链路冒烟
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-e2e-usability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-A-2
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [SHARED-SCHEMAS.md]
ac_coverage: 2/2
---

# SPEC-F-A-2: ingest+compile 冒烟

## 实现 delta（源自 CMS §M01/M05）
- 冒烟节点：ingest markdown fixture + url fixture（本地 fixture 避免网络）→ compile wiki 增量。
- 复用 `IngestPipeline.ingest`（`engines/ingest/pipeline.py:102`）、`extractors/markdown.py`/`url.py`、`engines/compile/compiler.py`。
- 断言：每条 claim 有 `anchor`（溯源原文位置）；wiki 页生成 + FTS5 索引更新。
- 提取器失败 → 跳过计数不中断（异常处理）。

## 接口契约
- 冒烟节点（被 F-A-1 骨架调用），无独立 HTTP。

## UI/DB
- N/A。DB：经 Write Queue → sinks（vault/claims/wiki/fts5），源自 CMS §M09。

## 后端逻辑
- ingest(md, url fixture) → `_build_write_ops`（pipeline.py:310）→ Dispatcher → compile 增量 → 断言 claim.anchor 非空 + wiki 页存在。

## 异常处理
| 场景 | 处理 |
|---|---|
| 提取器失败 | 跳过+计数，节点不中断 |
| 溯源断裂（claim 无 anchor） | 节点 FAIL，列 claim uuid |

## 测试映射
| AC | 用例 |
|---|---|
| ingest md+url 产 claim 可溯源 | `test_smoke_ingest_provenance` |
| compile wiki 增量生成 | `test_smoke_compile_incremental` |

## 实现就绪度
- [x] AC 覆盖 2/2；fixture 本地化可复现
