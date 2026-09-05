# Rollback Plan — v1.12.0: embedding 改用 OpenAI 风格 API

**Tag**: v1.12.0
**Date**: 2026-09-05

## 触发条件

- litellm.embedding API 调用失败导致 embed_texts() 崩溃（API 不可达/key 无效/model 不存在）
- 维度配置变更导致 embedding_store dim 列与既有向量不兼容
- detect_tier() 误判 API 可用性导致降级路径错误
- embedding 测试 mock 与实际 API 行为不一致导致假绿
- 安全漏洞

## 回滚步骤

1. **快速降级（<1min）**：若 API embedding 失败，`detect_tier()` 自动检测 `_embeddings_available()` 返回 False → embedding 功能降级为 keyword-only 模式（同 v1.10.0 以前行为）。用户可装 `[learn]` extra 启用本地 ST fallback。
2. **代码回滚（<5min）**：`git revert v1.12.0..v1.11.0` 或 `git reset --hard v1.11.0`（本地 trunk，未 push 远端）。
3. **DB rollback**：本版本无 migration 变更（F-Q-1..4 为 provider 重构 + 配置 + 测试，无 schema 改动）。embedding_store dim 列已存在于 v1.10.0 migration。无需 DB 回滚。
4. **Wheel 回滚**：`pip install smart-agent-wiki==1.11.0` 替换 1.12.0。
5. **配置回滚**：移除 `EmbeddingSettings` 中的 API 配置（api_key/api_base/model），恢复纯本地 ST 模式。

## 影响评估

- embedding provider 重构是 additive 变更——API 不可用时自动 fallback 到 keyword-only（detect_tier 既有逻辑）。
- 维度可配是 additive 变更——dim 列已存在于 v1.10.0 schema，仅新增 dim 驱动逻辑。
- 本地 ST fallback 保持向后兼容——`[learn]` extra 仍可装，fallback 路径不变。
- 测试改 mock 不影响生产代码运行时行为。
- 无 DB migration、无 schema 变更、无新依赖（litellm 已在依赖）。

## 回滚验证

- `saw smoke` 6/6 pass（无新依赖）
- `pytest tests/` 2064 passed（回滚到 v1.11.0 基线）
- `saw query "test" --mode semantic` 降级为 keyword-only 正常返回
- embedding 索引重建功能正常（或降级跳过）
