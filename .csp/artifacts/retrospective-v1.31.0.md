# 复盘 — v1.31.0 Provenance API + Activity 持久化（2026-09-18）

> 07 闭环校验。feat MINOR。前置：06-ship done（v1.31.0 tagged @532b3f4, pushed, Release 含 wheel+sdist）。

## 闭环校验：✅ 通过
| 链路 | 状态 | 证据 |
|---|---|---|
| PRD→Spec | ✅ | PRD-provenance-activity-v1.31.0 Approved；SPEC-F-PROVENANCE-ACTIVITY 3 feat 1:1 |
| Spec→Task | ✅ | v12 migration + activity_tracker conn/load/persist + app.py attach_conn + govern.py /provenance + saw_verify 增强 |
| AC→测试 | ✅ | test_activity_persistence_survives_restart + test_attach_conn_loads_existing + TestProvenanceRoute(4) |
| commit→tag | ✅ | v1.31.0 @532b3f4 (release commit, O4 fix 沿用) |
| 测试/lint | ✅ | pytest 2406/0 fail；ruff 0；cov 68.43%；tsc clean |
| 构建+Release | ✅ | wheel+sdist；https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.31.0 |

## 度量
- 3 feat done（activity 持久化 + provenance REST + saw_verify 增强）
- pytest 2406 passed（+6）
- coverage 68.43%（未回归）
- feat MINOR（additive，无 breaking）
- AUDIT-F-05 → closed（deferred-gate 闭合）

## Findings（回流）
- contamination scan → deferred v1.31.1（附解除条件：v1.31.0 released ✓，已并入 v1.31.1 入口清单）。
- 续留：AUDIT-F-01/04/06/08 + CRITIC-F-01 + E2E-BLOCKED-01（见 ARCHIVE-MANIFEST）。

## 教训
- v1.31.0 调研发现既有 `saw_verify` MCP 已返回 provenance chain——ROADMAP 原拟"新 saw_verify_provenance 工具"会重复。改为 REST 暴露既有链 + MCP 增强 receipt，避免重复造轮子。→ 01 PRD 阶段先 grep 既有能力再定 scope。
- AgentActivityTracker 持久化采用 write-through（每 event upsert）而非 batch flush——agent 活动低频，write-through 简单且无丢数据风险；高吞吐场景才需 batch。

## 下游衔接 → v1.31.1
- v1.31.1 (feat MINOR)：contamination scan（检测衍生自过期/被取代源的 claim）——需 freshness + contradiction resolution (superseded) 状态查询。入口清单：v1.31.0 deferred 项。
