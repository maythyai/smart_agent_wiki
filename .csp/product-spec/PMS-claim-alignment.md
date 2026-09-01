---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-product-hardening-v1.md]]"
  - "[[.csp/code-spec/saw/entry-points.jsonl]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]]"
created: "2026-09-01"
updated: "2026-09-01"
---

# PMS: claim-alignment（实现-宣称一致性校准与能力清单）

## 模块边界
- **做什么**：以代码为单一事实源，自动比对 README/docs 能力宣称与实际实现（entry-points/knowledge-graph）；修正过时宣称；产出可信能力清单 `docs/CAPABILITIES.md`（每条带 file:line）。
- **不做什么**：不删历史文档（加"历史快照"标注）；不评价实现质量；不补功能（只校准宣称）。功能补全归 e2e-usability/security-hardening 等。
- **PMS 边界=PRD §3.2**。

## 验收形态
- diff 脚本输出 added/changed/removed 宣称项；重跑至 0 diff。
- 宣称无代码对应 → 标 `[unverified]`，不写"已支持"。
- 能力清单覆盖 MCP/连接器/agent/入口，带 file:line。

## 接口契约摘要
- 输入：`entry-points.jsonl` + `knowledge-graph.json` + README/docs 文本。
- 输出：diff 报告 + `docs/CAPABILITIES.md`。
- 校验源：`scripts/cms_extract.sh`（重生成 entry-points）。

## 关联
- PRD: `docs/prd/PRD-product-hardening-v1.md` §3.2
- CMS: `.csp/code-spec/saw/entry-points.jsonl`（215 入口）
- 历史审计: `docs/smart_agent_wiki_deep_audit.md`（过时，加标注不删）
- 下游 Spec: [待 03 回填]
