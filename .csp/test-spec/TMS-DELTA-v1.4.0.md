# TMS Delta — v1.4.0（2026-09-03）

> 03 测试规约 delta。platform-team 新域 + debt 续。增量用例（不重写存量）。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-SEC-4（role×capability 0 越权） | F-P-1 | `tests/unit/test_rbac_matrix_e2e.py`（新建）：viewer/editor/admin × CRUD parametrize | [TBD-impl] |
| AC-SEC-5（Cedar 策略热加载） | F-P-1 | `tests/unit/test_cedar_hot_reload.py`（新建）：策略文件变更后生效 | [TBD-impl] |
| AC-DEPLOY-1（docker-prod up + healthcheck） | F-P-2 | `tests/unit/test_compose_prod.py`（新建）：compose 文件结构 + healthcheck 字段 | [TBD-impl] |
| AC-DEPLOY-2（secrets 不入库） | F-P-2 | detect-private-key pre-commit（既有）+ compose env 注入断言 | [TBD-impl] |
| AC-OBS-3（saw health 巡检聚合） | F-P-3 | `tests/unit/test_health_cmd.py`（新建）：聚合 engines/db/redis/receipt | [TBD-impl] |
| AC-OBS-4（saw audit receipts --session） | F-P-3 | `tests/unit/test_audit_cmd.py`（新建）：复用 ReceiptStore.verify_chain | [TBD-impl] |
| AC-WS-1（workspace 数据隔离） | F-P-4 | `tests/unit/test_workspace_isolation.py`（新建）：A/B workspace 数据不互查 | [TBD-impl] |
| AC-WS-2（跨 workspace 拒） | F-P-4 | 同上：用户仅授权 A 访问 B 拒 | [TBD-impl] |
| AC-LINT-2（F401/F841 0 errors） | F-Z-4 | `tests/unit/test_lint_baseline.py`（扩 v1.3.0）：--select F401/F841 0 | [TBD-impl] |
| AC-LINT-3（heavy-SDK skip） | F-Z-5 | `tests/unit/engines/learn/test_*.py`：importorskip 后 SDK 缺则 skip | [TBD-impl] |

## 约定
- platform-team 新域无既有 TMS，本轮建增量用例。
- F-P-3 复用 v1.2.0 ReceiptStore + check_engines（不重写）。
- F-Z-4 扩 v1.3.0 test_lint_baseline（移除 F401/F841 from ignore 后断言 0）。
