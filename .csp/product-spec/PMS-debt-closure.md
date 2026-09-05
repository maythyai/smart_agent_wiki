---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-debt-closure-v1.11.0.md]]"
  - "[[docs/prd/PRD-debt-closure-v1.6.0.md]]"
  - "[[.csp/artifacts/retrospective-v1.10.0.md]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]] §M07(query)/§M08(compile)"
created: "2026-09-03"
updated: "2026-09-05"
---

# PMS: debt-closure（债务收口模块，living baseline）

> v1.11.0 债务收口 IV（delta）。延续 v1.6.0（workspace 全路径 II）→ 本轮收敛 v1.10.0 及累积的 5 项可修缺陷（N7 cache / N2·K1 coverage / M3 workflow REST / N5 Spec / N6 hash）。不引入新能力、不需 SDK。

## 模块边界
- **做什么（v1.11.0 delta）**：
  - semantic search 走 query cache（复用 F-QS-07，query-text→embedding→results，TTL + 索引变更失效）；
  - compile/compiler.py 深覆盖（30 函数，17%→[TBD]，拖动全量 coverage ≥65，fail_under 64→65）；
  - workflow REST `GET /api/v1/workflows` 统一读 DB（merge live + durable，消歧 CLI vs REST 语义双重）；
  - SPEC-F-N-1 CLI 命名回更（`saw search rebuild-embeddings` → `saw rebuild-embeddings`）；
  - v1.10.0 tag hash 一致性复核（@3865c75 三处一致）。
- **不做什么**：embedding E2E 验证（N1，须 SDK）；per-request workspace 注入（N3/K2，v2.0）；向量检索 benchmark（N4，须 SDK）；agent 活动聚合（M2）；链接自动 apply（L2）；新能力。
- **PMS 边界 = PRD §2（5 模块）**。复用 v1.10.0 既有 F-QS-07 cache 路径 + `workflow_executions` DB 表。

## 验收形态
- semantic cache 命中后跳过全量 cosine（AC-CACHE-1）。
- 全量 coverage ≥65%，fail_under=65（AC-COV-2）。
- REST `/workflows` 读 `workflow_executions` 表 + merge live（AC-WF-1/2/3）。
- SPEC-F-N-1 命名与实现一致（AC-SPEC-1）。
- tag hash 三处 = @3865c75（AC-HASH-1）。

## 接口契约摘要（ground 自源码）
- semantic cache 插入点：`engines/query/engine.py` `_semantic_search`（无 cache），参照同文件 `_keyword_search`（L223–237 cache.get / L299–300 cache.set）。
- compile/compiler：`engines/compile/compiler.py:67–658`（30 def）；测试目录 `tests/unit/engines/compile/` 不存在（新建）。
- workflow REST：`api/routes/collaborate.py:33` `_workflows: dict = {}`（L328–335 `list_workflows` 读内存）；CLI `drivers/cli/commands/workflow_cmd.py` `list_recent` 读 `workflow_executions` 表。
- Spec 命名：`.csp/specs/SPEC-F-N-1.md` CLI 节 vs `drivers/cli/main.py:73` `app.command(name="rebuild-embeddings")`。

## 关联
- PRD: `docs/prd/PRD-debt-closure-v1.11.0.md`（当前）；`docs/prd/PRD-debt-closure-v1.6.0.md`（历史）
- 上游复盘: `.csp/artifacts/retrospective-v1.10.0.md`（N7/N2·K1/M3/N5/N6）
- 复用 PMS: `PMS-embedding.md`（cache 插入点）、`PMS-agent-viz.md`（workflow REST/CLI）
- 下游 Spec: [.csp/specs/SPEC-F-O-1.md, .csp/specs/SPEC-F-O-2.md, .csp/specs/SPEC-F-O-3.md, .csp/specs/SPEC-F-O-4.md]
