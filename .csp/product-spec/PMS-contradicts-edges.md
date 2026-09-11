---
id: PMS-contradicts-edges
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: built
roadmap_ref: ROADMAP
target_version: v1.21.0
prd_ref: docs/prd/PRD-contradicts-edges-v1.21.0.md
---

# PMS: contradicts 矛盾边+置信 (B1, v1.21.0)

## 模块边界
把检测到的矛盾建模为**带置信的 `contradicts` 图边**（claim_a↔claim_b + 双 4 级置信 + 可选 receipt），而非仅独立 contradictions 表记录。强化治理护城河（溯源+治理耦合）。

## 对外接口
- `ContradictionRecord`（dataclass）：+ `claim_a_confidence`/`claim_b_confidence`/`receipt`
- `ContradictionDetector.get_contradiction_edges()` → `list[dict]`（图边：source/target/edge_type="contradicts"/双置信/receipt/resolved）
- `saw_conflicts` MCP 工具：输出含双置信 + receipt
- migration v11：`contradictions` 表 +3 列

## 内部接口
- `store_contradiction` / `ContradictionsSink.write` / `record_to_payload`：写 11 列
- `_row_to_record`：按列名读（robust to ALTER）
- `_create_record`：从 claim_a/b.confidence 捕获

## 依赖
- `saw.engines.govern.contradiction`（ContradictionDetector）
- `saw.write_queue.sinks.contradictions_sink`
- `saw.db.migrations` v11
- `saw.domain.value_objects.ConfidenceLevel`（4 级）

## 状态
- built（v1.21.0）：migration v11 + record/sink/edges/MCP + 测试，gate 绿。
- 待补位：Ed25519 receipt 签名 wiring（detector 注入 signer）；图遍历器消费 contradicts 边。
