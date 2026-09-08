# 审计摘要 — smart_agent_wiki @ v1.18.0-audit

> 完整报告见 `.csp/audit/AUDIT-VERDICT-v1.18.0-audit.md`

## 裁决：放行 ✅

W1 关键 bug（sub-service contextvar 数据泄漏）已修复并验证：2284 测试全绿 0 回归，深度安全审查全部通过。

## 修复内容

| 文件 | 改动 |
|------|------|
| `src/saw/engines/query/tree_mode.py` | +effective_workspace_id property；3 处 _workspace_id → effective_workspace_id |
| `src/saw/engines/query/compiler.py` | +effective_workspace_id property；1 处替换 |
| `src/saw/engines/query/graph_traverse.py` | +effective_workspace_id property；+_loaded_workspace_id 懒重载；多处替换 |
| `tests/unit/engines/query/test_subservice_workspace_contextvar.py` | +7 测试（contextvar set/get/isolation/thread/async/middleware/sub-service） |

## 安全审查（全通过）

- .env 已 gitignore（非 git 跟踪）
- SQL 全参数化（无 injection）
- JWT key = secrets.token_hex(32)（32 bytes / 256 bit）
- write_queue threading.Lock()（并发安全）
- 密钥文件 0600 权限

## 版本 bump

`v1.18.1（fix: AUDIT-F-08/W1 sub-service effective_workspace_id + W2 E2E test）` — PATCH
