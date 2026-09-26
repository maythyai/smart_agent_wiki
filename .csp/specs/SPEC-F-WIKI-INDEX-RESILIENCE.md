---
id: SPEC-F-WIKI-INDEX-RESILIENCE
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: approved
prd_ref: PRD-wiki-index-resilience-v1.30.2
target_version: v1.30.2
---

# SPEC — WikiIndexer.index_all per-page 容错（AUDIT-F-03）

## 根因
`src/saw/engines/query/wiki_indexer.py:WikiIndexer.index_all()`：
```python
for slug in self._wiki_repo.list_pages():
    page = self._wiki_repo.read(slug)   # ← raise StorageError on bad YAML
    if page is None: continue
    self._index_page(...)
```
`wiki_repo.read()` (`src/saw/adapters/storage/wiki_repository.py:107`) 对坏 YAML raise `StorageError`。`index_all` 未 per-page catch → 单坏页致整库索引失败（app.py:573 仅 log warning，indexed=0）。

## 改动
`index_all()` per-page try/except：
```python
def index_all(self) -> int:
    count = 0
    skipped = 0
    for slug in self._wiki_repo.list_pages():
        try:
            page = self._wiki_repo.read(slug)
        except Exception as e:
            logger.warning("Skipping unparseable wiki page %s: %s", slug, e)
            skipped += 1
            continue
        if page is None:
            continue
        self._index_page(slug, page.title, page.content, page.tags)
        count += 1
    if skipped:
        logger.warning("Wiki indexing: %d page(s) skipped due to parse errors", skipped)
    return count
```

## AC
- 坏 YAML 页：`index_all` 不 raise，该页 skip + warn，好页正常索引。
- `index_page(slug)` 单页路径不变（仍由调用方处理 raise）。
- 新增测试：`tests/unit/engines/query/test_wiki_indexer.py::test_index_all_skips_unparseable_page`——构造 1 好页 + 1 坏 YAML 页，assert `index_all()` 返回 1 且不 raise。

## 测试
- 新增 `test_index_all_skips_unparseable_page`。
- `pytest tests/unit/engines/query/test_wiki_indexer.py -q` 全绿。
- 全量回归 + ruff 0 + coverage 不回归。
