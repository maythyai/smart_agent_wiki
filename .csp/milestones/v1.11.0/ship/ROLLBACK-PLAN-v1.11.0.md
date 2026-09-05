# Rollback Plan — v1.11.0: 债务收口 IV / bug fix

**Tag**: v1.11.0
**Date**: 2026-09-05

## 触发条件

- semantic cache 返回错误结果或缓存失效逻辑错误
- compile/compiler 深覆盖测试引入的 mock 导致假绿
- workflow REST 读 DB 合并逻辑导致列表错误或崩溃
- Spec 命名回更导致 CLI 命令名不一致
- 安全漏洞

## 回滚步骤

1. **快速降级（<1min）**：semantic cache 是 additive 缓存层，cache miss 自动 fallback 到原查询路径。若 cache 逻辑出错，cache 自动失效后走原 semantic/keyword 路径。
2. **代码回滚（<5min）**：`git revert v1.11.0..v1.10.0` 或 `git reset --hard v1.10.0`（本地 trunk，未 push 远端）。
3. **DB rollback**：本版本无 migration 变更（F-O-1..4 均为代码/测试/Spec 变更，无 schema 改动）。无需 DB 回滚。
4. **Wheel 回滚**：`pip install smart-agent-wiki==1.10.0` 替换 1.11.0。

## 影响评估

- semantic cache 是 additive 缓存层（复用 F-QS-07 单例），不影响原查询路径。
- compile/compiler 深覆盖仅为新增测试文件，不修改生产代码逻辑。
- workflow REST unify 修改了 `/workflows` 端点读 DB 逻辑——回滚后恢复原 in-memory only 行为。
- F-O-4 为 Spec/文档回更，不影响运行时行为。
- 无 DB migration、无 schema 变更、无新依赖。

## 回滚验证

- `saw smoke` 6/6 pass（无新依赖）
- `pytest tests/` 1993 passed（回滚到 v1.10.0 基线）
- `saw workflow list` 正常返回
- `saw query "test"` 返回结果正常
