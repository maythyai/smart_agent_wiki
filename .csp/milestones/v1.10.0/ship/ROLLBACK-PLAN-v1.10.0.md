# Rollback Plan — v1.10.0: embedding 语义搜索

**Tag**: v1.10.0
**Date**: 2026-09-04

## 触发条件

- embedding 索引重建导致数据损坏或性能严重退化
- 语义检索返回错误结果或崩溃
- smart-linking suggest 因 embedding 信号产生更差结果
- 安全漏洞

## 回滚步骤

1. **快速降级（<1min）**：query engine `--mode` 默认回退到 `keyword`（BM25），不依赖 embedding 索引。用户不传 `--mode semantic` 即走原有 BM25 路径。
2. **代码回滚（<5min）**：`git revert v1.10.0..v1.9.0` 或 `git reset --hard v1.9.0`（本地 trunk，未 push 远端）。
3. **DB migration rollback（<15min）**：migration v10 添加 embedding_store 表，down() 删除该表。不影响现有 claims/wiki/FTS5 数据。
4. **Wheel 回滚**：`pip install smart-agent-wiki==1.9.0` 替换 1.10.0。

## 影响评估

- embedding 索引是 additive 层，不影响 BM25/FTS5 原有路径。
- migration v10 仅添加表，不修改现有表结构。
- sentence_transformers 是 optional `[learn]` extra，不影响核心功能。

## 回滚验证

- `saw smoke` 6/6 pass（无 embedding 依赖）
- `pytest tests/` 1993 passed（embedding 测试 importorskip skip，不阻断）
- `saw query "test"` 返回 BM25 结果正常
