---
id: SPEC-F-L-2
title: 链接审计（saw links audit: 孤儿页 + 断链）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-smart-linking-v1.8.0.md
pms_ref: .csp/product-spec/PMS-smart-linking.md
feature_id: F-L-2
complexity: M
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-L-2]
---

# SPEC-F-L-2: links audit

## 实现 delta（ground 自源码）
- `links_cmd.py` 加 `audit` 子命令（与 suggest 同文件 bundle）。
- **孤儿页**：扫描 `list_pages()`，对每页计算反向链接数（扫描所有页 outlinks 反建 inbound map），inbound=0 → 孤儿。
- **断链**：扫描每页 `parse_wiki_links(content)`，target slug 不在 `list_pages()` 集合 → 断链。
- 复用 `wiki_repo.list_pages` + `read` + `wiki_links.parse_wiki_links` + `slugify`。镜像 web `get_backlinks` 反向逻辑。
- 性能：O(pages²) 反向扫描——限 top N 报告 + 跳过 .saw/ 目录。

## 接口契约
- `saw links audit [--path .]` → 输出孤儿页列表 + 断链列表（source→target）；exit 0（有/无均报告，无则 "no orphans"/"no broken links"）。

## 后端逻辑
- pages = list_pages()；inbound = {slug: count} 扫描 build；orphans = [p for p in pages if inbound[p]==0]；broken = [(src, target) for src in pages for link in parse_wiki_links(read(src)) if link.target not in pages_set]。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-LINK-2（孤儿页 + 断链） | `tests/unit/test_links_cmd.py`：page A 无入链→孤儿；page B [[missing]]→断链 |

## 实现就绪度
- [x] list_pages + parse_wiki_links + slugify 全就绪
- [x] AC 覆盖 1/1
- O(pages²) 限 top N
