---
id: SPEC-F-R-4
title: coverage 棘轮 fail_under 65→67 + 补测达 67%
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-e2e-tail-v1.13.0.md
pms_ref: .csp/product-spec/PMS-e2e-tail.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-R-4
complexity: S
tdd_ref: .csp/tech-decisions/ADR/ADR-013-ingest-recursion-benchmark.md
ac_coverage: 2/2
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.13.0.md#T-F-R-4
---

# SPEC-F-R-4: coverage 棘轮 fail_under 65→67 + 补测

## 实现 delta（ground 自源码）

> O2 闭合——coverage 66%（`fail_under=65`），余量 1pp 仍薄，棘轮推进到 67。

### 改动点

| 文件 | 行 | 现状 | 改为 |
|---|---|---|---|
| `pyproject.toml:127` | `fail_under = 65` | 当前 66%，门禁 65；余量 1pp | `fail_under = 67` |
| `tests/unit/engines/compile/test_coverage_config.py:9,14` | `test_fail_under_is_65()` 断言 `fail_under == 65` | 断言过严（硬编码 65），fail_under 提升到 67 后此测试会 break | 改为 `assert fail_under >= 65`（棘轮下限，不硬编码上限）或 `assert fail_under == 67` |
| `tests/unit/test_coverage_gate.py:32` | `assert 50 <= floor <= 65` | 上限 65 过严，fail_under=67 后 break | 改为 `assert 50 <= floor <= 80`（棘轮合理 band，不硬编码上限 65） |
| `tests/unit/test_coverage_gate.py:9`（`test_coverage_config.py` 注释） | 注释 "pyproject.toml fail_under=65 (AC-COV-2)" | 提升至 67 | 注释更新为 67 |

### 不改动

- `[tool.coverage.run]` source/omit 不变。
- `[tool.coverage.report]` exclude_lines 不变。
- 不引入 `pragma: no cover` 绕过（PRD 业务规则 4）。
- 不引入新功能代码（只加测试覆盖既有未覆盖路径）。

## 后端架构

### fail_under 提升（`pyproject.toml`）

```toml
[tool.coverage.report]
# ... comments ...
fail_under = 67
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

注释追加 v1.13.0 棘轮说明（65→67，coverage 66→≥67%）。

### 补测目标（HOW，本 Spec 定方向，04 任务拆解定具体）

当前 66%（v1.12.0 基线），须补 ≥1pp 达 67%。PRD 建议优先补 ingest/query 核心路径未覆盖分支。候选补测模块（04 任务拆解择优）：

| 模块 | 当前覆盖 | 补测方向 |
|---|---|---|
| `src/saw/engines/ingest/pipeline.py` | 未覆盖部分（递归分支新增 + 既有边界） | ingest 目录递归路径（F-R-1 新增）+ 边界（空 errors/None extraction） |
| `src/saw/engines/query/engine.py` | ~部分覆盖 | `_compare_query` / `_tree_query` / `_graph_query` 边界（空结果/解析） |
| `src/saw/api/routes/collaborate.py` | list_workflows 部分覆盖 | live merge 分支 + alias 字段（F-R-3 新增）+ conn is None fallback |
| `src/saw/drivers/cli/commands/` | 部分覆盖 | ingest 命令目录参数 + search 命令边界 |

**约束**：
- 补测须是真实测试（非 `pragma: no cover` 绕过），`pragma: no cover` 使用不增加。
- 补测不引入新功能代码。
- CI 须在 `fail_under=67` 下绿。

### 测试断言适配（ground 自源码）

`tests/unit/engines/compile/test_coverage_config.py:14`：
```python
# Before: assert fail_under == 65
# After:  assert fail_under >= 65  # ratchet floor, not hardcoded
```

`tests/unit/test_coverage_gate.py:32`：
```python
# Before: assert 50 <= floor <= 65
# After:  assert 50 <= floor <= 80  # reasonable ratchet band
```

**理由**：硬编码上限 65 会在棘轮提升时 break（每轮提升 fail_under 须改断言）。改为下限 `>= 65` + 合理 band `<= 80`（北极星 80%），避免每轮改断言。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-D-1（fail_under 提升） | `tests/unit/engines/compile/test_coverage_config.py`（改）：读 pyproject.toml → `fail_under == 67`（或 `>= 65` 棘轮） | `fail_under` 值为 67（或 ≥ 65） |
| AC-D-2（实际覆盖率达标） | CI `pytest --cov` → coverage 报告 ≥ 67% | coverage ≥ 67% + CI 绿 |

## 实现就绪度

- [x] fail_under 提升明确（65→67，pyproject.toml:127）
- [x] 测试断言适配明确（test_coverage_config.py + test_coverage_gate.py 去硬编码上限）
- [x] 补测方向定（ingest/query/collaborate 核心路径，04 择优）
- [x] 约束明确（不引入 pragma: no cover，不引入新功能代码）
- [x] AC 覆盖 2/2
- [ ] 具体补哪些模块 [TBD-04]（04 任务拆解定，PRD 建议优先 ingest/query）
