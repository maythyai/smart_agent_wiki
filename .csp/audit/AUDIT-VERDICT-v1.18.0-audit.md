# 裁决报告 — smart_agent_wiki @ v1.18.0-audit

> 生成时间：2026-09-08
> 审计模式：全量代码级审计（工具恢复后补齐）
> 证据来源：ls/git log/git status + 源码 file:line 读取 + 测试运行 + ruff + grep

## Executive Summary

```
裁决：[放行] — W1 关键 bug 已修复并验证（2284 passed 0 回归），深度安全审查无额外 Critical/High
致命 0 / 严重 1（W1 已修复） / 一般 0 / 提示 2 / 缺口 0
一句话依据：W1 sub-service contextvar 数据泄漏已修复（3 文件 effective_workspace_id 改造 + 7 新测试），
全量 2284 测试绿 0 回归，安全审查（.env/SQL/JWT/并发/密钥权限）全部通过。
```

## 1. 项目目标 vs 现状对照

| 需求 ID | 需求 | 风险级 | 现状 | 依据 |
|---------|------|--------|------|------|
| R1 | per-request workspace 隔离 | P0 | ✅ 已修复（W1 闭环） | tree_mode.py/compiler.py/graph_traverse.py effective_workspace_id + 7 测试 |
| R2 | tag flow O4 修复 | P2 | ✅ 已实现 | git log e4cf22d release commit |
| R3 | Desktop .app/.dmg | P1 | ✅ 已实现 | v1.17.0 tauri build |
| R4 | Web Dashboard 集成 | P1 | ✅ 已验证 | v1.17.0 F-V-2 |
| R5 | 端口收敛 8000 | P1 | ✅ 已修复 | v1.17.0 F-V-4 |
| R6 | rate limiter/backpressure | P1 | ✅ 有基准+实现 | .planning/benchmarks/ |
| R7 | 覆盖率门槛 67% | P2 | ✅ 达标 | pyproject.toml fail_under=67, coverage 67.42% |

## 2. 深度安全审查结果

| 审查项 | 结果 | 证据（file:line） |
|--------|------|------------------|
| .env 凭据泄露 | ✅ 安全 | `git check-ignore .env` → exit=0（已 gitignore） |
| SQL injection | ✅ 安全 | 全部 placeholders 参数化（pipeline.py:402, store.py:274,289,381,399,429,433,532,536） |
| JWT key 长度 | ✅ 安全 | jwt_auth.py:52 `secrets.token_hex(32)` = 32 bytes（256 bit） |
| write_queue 并发 | ✅ 安全 | queue.py:__init__ `threading.Lock()` + `check_same_thread=False` |
| 密钥文件权限 | ✅ 安全 | _keyfiles.py: `write_key_file` 0600, `ensure_keys_dir` 0700 |
| swallowed exceptions | ✅ 可接受 | health.py 降级容错；app.py:112 死信恢复先 log 再 catch |
| Ed25519 签名 | ✅ 有实现 | ed25519.py ReceiptSigner + receipt chain（AC-SEC-2） |

## 3. 技术模块缺陷清单

| 缺陷 ID | 级别 | 描述 | 状态 | 修复证据 |
|---------|------|------|------|---------|
| AUDIT-F-08/W1 | 严重 | sub-service 用实例级 _workspace_id 未读 contextvar | ✅ 已修复 | 3 文件 effective_workspace_id + 7 测试 |
| AUDIT-F-01 | — | .env 疑似凭据泄露 | ✅ 已排除 | git check-ignore 确认 |
| AUDIT-F-02 | 提示 | v2.0 MAJOR 两次推迟 | ℹ️ 信息项 | roadmap §1.1 已明确推迟条件 |
| AUDIT-F-03 | 提示 | 发布后未提交变更 | ℹ️ 正常 | retro + benchmark 增量 |

## 4. 联动测试结果

| 写路径 | UI/API | DB | 回路 | 结果 |
|--------|--------|-----|------|------|
| per-request workspace (W1 fix) | ✅ 7 测试 contextvar set/get/isolation/thread/async/middleware/sub-service | ✅ workspace A/B 隔离断言 | ✅ fallback to _workspace_id | **PASS** |
| Desktop→Web→API | ✅ vitest 64 | ✅ pytest 2284 | ✅ smoke 6/6 | **PASS** |

## 5. 测试验证

```
pytest: 2284 passed, 7 skipped, 0 failed (187.79s) — 含 7 新测试 0 回归
ruff: All checks passed!
coverage: fail_under=67（达标 67.42%）
smoke: 6/6
```

## 6. 版本 bump 建议

| findings 性质 | bump | roadmap 写入 |
|-------------|------|-------------|
| W1 sub-service contextvar 修复 + W2 E2E 测试 | **PATCH** | `v1.18.1（fix: AUDIT-F-08/W1 sub-service effective_workspace_id + W2 E2E test）` |

## 7. 裁决

**放行**。W1 关键 bug 已修复验证（2284 测试绿 0 回归），深度安全审查全部通过（.env/SQL/JWT/并发/密钥权限），无额外 Critical/High 发现。建议 bump v1.18.1 PATCH 发布。
