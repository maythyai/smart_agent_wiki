# TMS Delta — v1.6.0（2026-09-03）

> 03 测试规约 delta。debt-closure 续。增量用例。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-WS-4（tree/compile 跨 ws 隔离） | F-J-1 | `tests/unit/test_workspace_routing.py`（扩）：tree_mode + compiler 在 ws B 不返 ws A claim | [TBD-impl] |
| AC-WS-5（ingest 写入 ws 隔离） | F-J-2 | `tests/unit/test_workspace_routing.py`（扩）：ingest(workspace_id="alpha") → claim 落 alpha + B ws 不可见 | [TBD-impl] |
| AC-COV-2（query 覆盖→65） | F-J-3 | `tests/unit/engines/query/test_engine_modes.py`（新建）/ `test_compare.py`（扩）/ `test_tree_mode.py`（扩）；`fail_under=65` | [TBD-impl] |
| AC-SEC-6（admin reload Web，非 admin 403） | F-J-4 | `tests/unit/test_admin_policy_reload.py`（新建）：admin 200 + 非 admin 403 + cedar.reload 调用 | [TBD-impl] |

## 约定
- F-J-1/J-2 扩 v1.5.0 `test_workspace_routing.py`（加 tree/compile/write 用例）。
- F-J-3 query 深覆盖：engine mode 分发 + compare + tree_mode 主分支。
- F-J-4 Web 端点用 TestClient（FastAPI）+ mock cedar。
- coverage 棘轮 63→65（须实测达 65 再设，硬约定 #10）。
