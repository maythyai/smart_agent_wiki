---
id: SPEC-F-C-4
title: 输入消毒/URL 守卫全覆盖
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-security-hardening.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-C-4
complexity: S
tdd_ref: .csp/tech-design/SECURITY-ARCHITECTURE.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-C-4-1]
---

# SPEC-F-C-4: URL 守卫全覆盖

## 实现 delta（源自 CMS §M08）
- 复用 `adapters/url_guard.py`；审计所有外部 URL 入口（ingest url/连接器 OAuth/webhook）经守卫。
- 阻断内网地址 + 非常规协议（防 SSRF/协议混淆）。

## 测试映射
| AC | 用例 |
|---|---|
| 外部 URL 入口经 url_guard | `test_url_guard_coverage` |
| 内网/非常规协议被阻断 | `test_url_guard_block_internal` |

## 实现就绪度
- [x] AC 覆盖 2/2
