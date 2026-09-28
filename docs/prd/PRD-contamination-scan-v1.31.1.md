---
id: PRD-contamination-scan-v1.31.1
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: approved
roadmap_ref: ROADMAP
target_version: v1.31.1
type: feature
see_also: PRD-provenance-activity-v1.31.0 (deferred 项)
---

# PRD — v1.31.1 contamination scan (feat MINOR)

> v1.31.0 deferred 项（解除条件：v1.31.0 released ✓，已满足）。feat MINOR（additive）。

## 背景
跨 agent 知识污染（审计调研：97% 多 agent 系统从不做溯源验证）的核心场景之一：一条 claim 衍生自一个**已被取代（superseded）的源 claim**——源被矛盾解决判定过时，但衍生 claim 仍被检索/推理使用，污染下游。

## 范围（1 feat）
- **`saw_contamination_scan` MCP + `GET /api/v1/contamination` REST**：扫描 claim 库，返回衍生自已解决 SUPERSEDED 矛盾源 claim 的 claim 列表（contaminated），附源 claim uuid + 矛盾 id + reason="superseded_source"。

## 非目标（deferred / 后续）
- **stale-freshness contamination**（源 freshness 过期）：需 FreshnessTracker 集成 + freshness threshold 配置 → v1.34 perf 硬化同批（与 D3 heartbeat stale 巡检协同）。解除条件：v1.34 freshness threshold 可配。
- 自动降级 contaminated claim 置信：→ v1.31.2（如需要）。

## 成功指标
- 无 SUPERSEDED 矛盾 → 返回空列表。
- 有 SUPERSEDED 矛盾（claim_a/b）+ 衍生 claim（source_uuid 指向其中之一）→ 返回该衍生 claim，reason=superseded_source。
- 不返回源 claim 自身。

## 留尾
- stale-freshness contamination → deferred v1.34（附解除条件，计入 v1.34 入口）。
