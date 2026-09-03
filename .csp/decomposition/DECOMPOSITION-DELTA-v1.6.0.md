# Decomposition Delta — v1.6.0（2026-09-03）

> 新一轮 02 拆解 delta。源自 PRD-debt-closure-v1.6.0 + retrospective-v1.5.0.md findings I1/I2/I4。
> debt-closure track：4 Feature（F-J-1..4），延续 v1.5.0 workspace 增量 + 深覆盖 + policy web。无新引擎。

## 新增 Feature

| id | name | domain | priority | complexity | depends_on | wave | blocked_by | source | AC |
|---|---|---|---|---|---|---|---|---|---|
| F-J-1 | workspace 读取路径全路由（tree_mode + compiler） | debt-closure | P0 | M | — | 1 | — | retro I1 | AC-WS-4 |
| F-J-2 | workspace 写入路径（insert 持久化 + ingest 透传） | debt-closure | P0 | M | — | 1 | — | retro I1 | AC-WS-5 |
| F-J-3 | query 深覆盖（engine/compare/tree_mode → 65%） | debt-closure | P1 | M | F-J-1 | 2 | — | retro I2 | AC-COV-2 |
| F-J-4 | policy reload Web admin 端点 | debt-closure | P2 | S | — | 1 | — | retro I4 | AC-SEC-6 |

## 原子 Feature → Spec 映射（03 1:1）
- F-J-1 → SPEC-F-J-1（tree_mode + compiler workspace 注入）
- F-J-2 → SPEC-F-J-2（insert workspace_id 持久化 + ingest 透传）
- F-J-3 → SPEC-F-J-3（query 深覆盖 + 棘轮 63→65）
- F-J-4 → SPEC-F-J-4（policy web admin 端点）
> 4 原子 Feature = 4 Spec。

## DAG delta
```
F-J-1 ──▶ F-J-3   (J-3 tree_mode 测试覆盖 J-1 新代码)
F-J-2              (独立，与 J-1 不同文件：claims_repo.insert vs tree_mode/compiler/engine)
F-J-4              (独立，web route)
```
- J-1 → J-3（J-3 的 tree_mode 覆盖测试在 J-1 注入 workspace 后写）。
- J-1/J-2 文件不冲突（J-1: tree_mode.py/compiler.py/engine.py；J-2: claims_repository.py insert + pipeline.py）。
- 无新环。

## Wave 重排（v1.6.0）
- **Wave 1（并行，不同文件）**：F-J-1（tree_mode/compiler/engine）/ F-J-2（claims_repo insert + pipeline）/ F-J-4（web route）
- **Wave 2**：F-J-3（query 深覆盖测试 + fail_under 上调，在 J-1/J-2 代码落定后）

## 共享资源串行
- claims_repository.py：F-J-2 改 insert；F-J-1 不改此文件（仅调既有 workspace_id 参数）→ 不冲突。
- engine.py：F-J-1 透传 workspace_id 到 tree_mode/compiler；F-J-3 测试覆盖 → J-3 在 J-1 后。

## NFR delta
- **兼容**：F-J-2 insert 补 workspace_id 列须保 backward compat（Claim.workspace_id 默认 'default' → 既有调用行为不变）。
- **安全**：F-J-4 Web 端点 admin-only（require_role("admin")），勿裸暴露。
- **可测**：F-J-3 coverage 65 须实测达 65 再设 fail_under（硬约定 #10）。

## 下游消费
- → 03：F-J-2 insert 列变更需 ADR-008（workspace 写入策略）；4 Spec 1:1。
- → 04：~5-6 Task（J-1/J-2/J-3/J-4 + 测试）；J-3 串行 Wave 2。
