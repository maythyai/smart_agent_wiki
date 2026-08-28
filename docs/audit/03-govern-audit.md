# Govern 治理与审计 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/engines/govern/*`、`src/saw/reconcile/*`、`src/saw/audit/*`、`src/saw/api/routes/govern.py`、`drivers/cli/commands/{conflicts,freshness,verify,review,audit,lint}_cmd.py`
> 覆盖说明: 全部范围内文件已读取；行号为代理估算，修复前以实际代码为准。

## 1. 执行摘要
- 检测、新鲜度、签名收据链、blast-radius 是真实实现，但置信度分布统计键名错误、FACTUAL 矛盾路径是死胡同、reconcile 引擎 auto_apply 不安全、两套矛盾子系统不整合。
- 核心功能完成度约 **70%**。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| 置信度/新鲜度检测 | 完整 | confidence/freshness.py |
| 置信度分布统计 | bug | F-GOV-01 |
| Ed25519 审计收据 | 完整 | audit.py |
| 矛盾解决（reconcile） | 不安全 | F-GOV-06 |
| FACTUAL 矛盾路径 | 死胡同 | F-GOV-04 |
| 矛盾子系统统一 | 缺失 | F-GOV-03 |

## 4. Findings 列表

### F-GOV-01 — Linter confidence_map 键名错误
- **P1** | 严重度 3 | 置信度 high | **原则** #1/#4
- **位置**: `engines/govern/linter.py`（confidence_map）
- **问题**: 使用 `{"unverified":1,"verified":2,"trusted":3,"authoritative":4}`，而 `ConfidenceLevel` 枚举名为 `single_source`/`cross_validated`/`human_verified`——除 unverified 外全归为 1 级。
- **后果**: lint/状态分布显示扭曲。

### F-GOV-02 — `saw conflicts` 在新库崩溃
- **P1** | 严重度 3 | **原则** #9
- **位置**: `drivers/cli/commands/conflicts_cmd.py`
- **问题**: 执行 `SELECT * FROM contradictions` 无 try/except，新库无表时 `sqlite3.OperationalError` 崩溃。

### F-GOV-03 — 两套矛盾子系统不整合
- **P1** | 严重度 2 | **原则** #4
- **位置**: `engines/govern/contradiction.py` vs `reconcile/`
- **问题**: 两个并行且不整合的矛盾子系统。

### F-GOV-04 — FACTUAL 矛盾死胡同
- **P1** | 严重度 3 | **原则** #1/#9
- **位置**: `engines/govern/contradiction.py`
- **问题**: FACTUAL 解析为 HISTORICAL 但不入队/通知，永远未解决；`blast_radius` 始终 `[]`（分析器从未调用）。

### F-GOV-05 — 无 CLI 矛盾解决路径
- **P1** | 严重度 2 | **原则** #3
- **问题**: 只有 API 能解决矛盾，CLI 用户无法操作。

### F-GOV-06 — ReconcileEngine 破坏性自动解决
- **P0** | 严重度 4 | 置信度 high | **原则** #3
- **位置**: `reconcile/engine.py`（`auto_apply=True` 默认 + `resolve_single`）
- **问题**: 默认 `auto_apply=True` 并将"失败者"设为 superseded；`resolve_single` 即使 MANUAL 策略也 supersede——破坏性自动解决，无确认、无撤销。
- **后果**: 用户数据被静默 supersede 且不可逆。

### F-GOV-07 — 置信度/新鲜度以原始整数展示
- **P1** | 严重度 2 | **原则** #2
- **问题**: 直接向用户展示原始整数而非可读标签。

### F-GOV-08 — get_stale_claims 忽略 last_accessed
- **P1** | 严重度 2 | **原则** #1
- **问题**: 与 D-13 和 `get_freshness_distribution` 矛盾。

### F-GOV-09 — 审计 COMPROMISED 无细节
- **P1** | 严重度 2 | **原则** #9
- **问题**: COMPROMISED 状态无细节说明。

### F-GOV-11 — /verify 仅检查存在性
- **P2** | 严重度 2 | **原则** #9

### F-GOV-12 — lint 隐藏分布
- **P2** | 严重度 2 | **原则** #1

### F-GOV-13 — 治理变更绕过写队列/回执链
- **P2** | 严重度 2 | **原则** #4

### F-GOV-14 — 存储错误被静默吞没
- **P2** | 严重度 2 | **原则** #1

### F-GOV-15 — 审计收据链断裂点
- **P3** | 严重度 1 | **原则** #9

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 1 |
| 3 | 4 |
| 2 | 7 |
| 1 | 3 |
| 优先级 | P0×1 P1×4 P2×7 P3×3 |

## 6. 修复优先级
- **Foundation**: F-GOV-06（破坏性自动解决加确认/撤销）
- **Core UI**: F-GOV-01/04（统计正确性 + 死胡同）
- **Interactions & States**: F-GOV-02/05/07/09
- **Polish**: F-GOV-11/12/13/14/15

## 7. 下一步建议
- 统一矛盾子系统；reconcile 默认 `auto_apply=False`；置信度/新鲜度用可读标签。
