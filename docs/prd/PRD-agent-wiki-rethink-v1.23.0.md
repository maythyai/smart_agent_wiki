---
id: PRD-agent-wiki-rethink-v1.23.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: Approved
roadmap_ref: ROADMAP
target_version: v1.23.0
see_also: docs/analysis/COMPETITIVE-REFERENCE.md (A1/B2) | .csp/product-spec/PMS-agent-tools.md
---

# PRD: agent 自维护 Wiki + memory_rethink + saw_resolve 语义 (v1.23.0)

> 竞品借鉴 A1（WeKnora agent 自蒸馏 Wiki）/ B2（Letta memory_rethink）/ saw_resolve 语义升级。

## 1. 背景与价值
- **A1 saw_wiki_distill(topic)**：Writer agent 从搜索排序的高置信 claims 起草 wiki 综合页 + 经 WikiRepository 写入（真页 frontmatter，可被 saw links suggest 互链）。WeKnora "agents distill docs→wiki" 的 SAW 落地。
- **B2 rethink_contradiction(uuid)**：Detector 重评既有矛盾（re-classify+re-resolve+persist）——Letta "agent 遇新信息冲突时重评记忆"。建在 B1 contradicts 边之上。
- **saw_resolve 语义升级**：embeddings 可用时用 `query(mode=semantic)`（cosine）召回，找到关键词漏的同义 claims；无 embeddings 自动回退 FTS5/BM25。

## 2. 需求（AC）
- **AC-A1-1**：`saw_wiki_distill(topic, limit, path_prefix)` 搜 claims → Writer template 起草 → WikiRepository.write。无 claims→distilled=False；无 query_engine/wiki_repo→error。
- **AC-B2-1**：`ContradictionDetector.rethink_contradiction(uuid)`（async）re-classify（LLM 不可用走 heuristic）+ re-resolve + UPDATE contradictions 行；未知 uuid→None。
- **AC-SEM-1**：saw_resolve 当 `embeddings_available()` 用 `query(mode=semantic)` 召回（带 confidence/score），否则 FTS5；既有 FTS5 测试不破。

## 3. 非目标
- A1 自动触发（on ingest）——本周期为 invocable 工具；自动触发留后续。
- B2 receipt 直签——rethink 经既有行 UPDATE，receipt 留后续。
- saw_resolve 语义的 semantic-cache 复用。

## 4. 验收
- A1: 3 测试（writes page / no_claims / no_wiki_repo）✓
- B2: 2 测试（rethink updates / unknown uuid→None）✓
- 既有 saw_resolve 测试（FTS5 路径）不破 ✓
- 全量 gate 绿，零回归。
