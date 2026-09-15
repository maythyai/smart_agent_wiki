---
id: PRD-nlp-feedback-heartbeat-v1.26.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: Approved
roadmap_ref: ROADMAP
target_version: v1.26.0
see_also: docs/analysis/COMPETITIVE-REFERENCE.md (B4/B5/D3)
---

# PRD: NLP 降本层 + auto-feedback + heartbeat 巡检 (v1.26.0)

> 竞品借鉴 B4（FastGraphRAG NLP 降本）/ B5（Cognee provenance+auto-feedback）/ D3（Letta heartbeat）。

## 1. 内容
- **B4 `extract_noun_phrases(text)` + `saw_nlp_keywords` 工具**：FastGraphRAG 用 NLP 名词短语+共现作 ~1000x 便宜于 LLM 的索引层。SAW 落地：jieba（CJK）+ regex（Latin）名词短语提取，无 LLM 无网络，作 ingest 降本前置层 / OFFLINE tier 退化路径。
- **B5 `saw_record_feedback(claim_uuid, helpful)`**：Cognee auto-feedback 自调——用户/agent 标记 claim 是否有用，bump/lower 4 级置信（复用 claims_repo.update_confidence）。检索权重向"被标有用"的 claim 漂移，无需重摄入。
- **D3 `HeartbeatScheduler` + `saw_heartbeat_status`**：Letta heartbeat 定时跑 agent "大脑"。SAW 落地：apscheduler 后台定时跑 Governor freshness + Detector 未解矛盾巡检，让 stale claim / open contradiction 主动浮现（非等用户 `saw freshness`）。

## 2. AC
- **AC-B4**：`extract_noun_phrases(text, top_k)` Latin 过滤 stop-words；CJK jieba 名词；空→[]。`saw_nlp_keywords` 工具返回 `{keywords, count, mode:"nlp-no-llm"}`。
- **AC-B5**：`saw_record_feedback(uuid, helpful)` helpful→置信+1（cap HUMAN_VERIFIED），not helpful→-1（floor UNVERIFIED）；未知 uuid→error；无 governor→error。
- **AC-D3**：`HeartbeatScheduler(governor, detector, interval)` start()（apscheduler）；无 governor/interval≤0→disabled；_patrol 设 last_run（stale_count+unresolved_contradictions）；`saw_heartbeat_status` 返回 last_run。

## 3. 非目标
- B4 ingest 集成（仅 helper + 工具，ingest pre-filter 留后续）。
- B5 provenance lineage（saw_verify 已覆盖；B5 仅 auto-feedback 部分）。
- D3 实际 scheduler 运行测试（_patrol 直接调，不启 background scheduler）。

## 4. 验收
- B4: 4 测试 ✓ / B5: 4 测试 ✓ / D3: 5 测试 ✓
- 全量 gate 绿，零回归。
