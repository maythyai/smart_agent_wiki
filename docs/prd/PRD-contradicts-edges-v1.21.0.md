---
id: PRD-contradicts-edges-v1.21.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: Approved
roadmap_ref: ROADMAP
target_version: v1.21.0
see_also: docs/analysis/COMPETITIVE-REFERENCE.md (B1) | .csp/product-spec/PMS-contradicts-edges.md
---

# PRD: contradicts 矛盾边+置信 (v1.21.0, B1)

> 来源：竞品借鉴 Phase 0.5 B1（Cognee `contradicts` 图边+置信）。强化 SAW 治理护城河。

## 1. 背景与价值
SAW 已有矛盾检测（Govern engine）+ `contradictions` 表（claim_a/b + type + resolution + blast_radius）。但矛盾记录**不带双 claim 的置信、非图可遍历边**——读者/agent 无法判断"矛盾两边各可信多少"。B1 把矛盾建模为**带置信的 `contradicts` 图边**（Cognee 风格），与 Ed25519 receipt 闭环。

## 2. 需求（AC）
- **AC-B1-1**：`contradictions` 表加 `claim_a_confidence`/`claim_b_confidence`（4 级置信，默认 unverified）+ `receipt`（可选 Ed25519 receipt id）列。migration v11，幂等。
- **AC-B1-2**：`ContradictionRecord` 带 `claim_a_confidence`/`claim_b_confidence`/`receipt`；`_create_record` 从两 claim 的 `confidence` 捕获。
- **AC-B1-3**：`store_contradiction`/`ContradictionsSink` 写新列；`_row_to_record` 按列名读（robust to ALTER）。
- **AC-B1-4**：`get_contradiction_edges()` 暴露矛盾为 `contradicts` 图边（source/target/edge_type/confidence_a/confidence_b/receipt/resolved），供 saw_graph/saw_blast_radius/saw_navigate 遍历。
- **AC-B1-5**：`saw_conflicts` MCP 工具修复（原访问不存在的 `c.resolved`/`c.resolution_strategy` → AttributeError 被吞成 error）+ 输出双置信 + receipt。
- **AC-B1-6**：默认值 `unverified` 保证向后兼容（旧记录无置信→读 unverified，不报错）。

## 3. 非目标
- Ed25519 receipt 签名 wiring（receipt 列就位，签名注入留后续——detector 无 signer 注入点，best-effort）。
- 图遍历器内部集成 contradicts 边（仅暴露 `get_contradiction_edges()` + MCP；遍历器消费留后续）。

## 4. 差异化
- Cognee 把矛盾作图边带置信——SAW 落地为 `contradicts` 边 + **4 级置信**（非 Cognee 的连续分）+ **Ed25519 receipt 闭环**（Cognee 无审计凭证）。强化"可信知识"护城河。

## 5. 验收
- migration v11 fresh DB 加列 ✓（apply_migrations → version 11，cols present）
- 单元：_create_record 捕获置信 + store/read round-trip + get_contradiction_edges 带置信 ✓（+2 测试）
- saw_conflicts 输出双置信 ✓
- 全量 gate 绿，零回归 ✓
