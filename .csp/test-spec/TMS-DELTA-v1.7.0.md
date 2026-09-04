# TMS Delta — v1.7.0（2026-09-04）

> 03 测试规约 delta。graph-workspace 续。增量用例。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-WS-6（graph 跨 ws 隔离） | F-K-1 | `tests/unit/test_graph_workspace.py`（新建）：A ws entity/relation 在 B ws traverse 返回空；default 兼容 | [TBD-impl] |
| AC-ARCH-1（无 setattr 私有属性） | F-K-2 | `tests/unit/test_scope_propagation.py`（新建）：tree_mode/compiler 收到 workspace_id（mock 调用）+ 源码无 setattr | [TBD-impl] |
| AC-COV-3（synthesize 覆盖 + ratchet 64） | F-K-3 | `tests/unit/engines/synthesize/test_engine.py`/`test_scheduler.py`（新建）；`fail_under=64` | [TBD-impl] |

## 约定
- F-K-1 graph 隔离用真实 in-memory DB + entity/relation seed。
- F-K-2 用 mock tree_mode/compiler 断言调用收 workspace_id + grep 源码无 setattr。
- F-K-3 synthesize 测试 mock LLM/scheduler（确定性）。
- coverage 棘轮 63→64（须实测达 64 再设，硬约定 #10）。
