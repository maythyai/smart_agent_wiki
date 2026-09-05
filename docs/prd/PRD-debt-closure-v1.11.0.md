---
id: PRD-debt-closure-v1.11.0
title: 债务收口 IV / bug fix
version: 1.0
status: Released
author: lifecycle-orchestrator
date: 2026-09-05
product_type: platform
feature_count: 5
mvp_scope: [semantic-cache, compile-coverage, workflow-rest-unify, spec-naming-revert, hash-reverify]
thin_sections: [7]
upstream_source: .csp/artifacts/retrospective-v1.10.0.md#findings-N7-N2-M3-N5-N6
roadmap_ref: docs/strategy/ROADMAP.md#v1.11.0
target_version: v1.11.0
related_pms: [.csp/product-spec/PMS-debt-closure.md]
related_specs: [.csp/specs/SPEC-F-O-1.md, .csp/specs/SPEC-F-O-2.md, .csp/specs/SPEC-F-O-3.md, .csp/specs/SPEC-F-O-4.md, .csp/tech-decisions/ADR/ADR-011-semantic-search-cache.md]
related_decomposition: .csp/decomposition/DECOMPOSITION-DELTA-v1.11.0.md
---

# PRD: 债务收口 IV / bug fix

> 内部 milestone v4.1。additive MINOR——bug fix + 测试覆盖 + 行为统一，无 breaking API 变更。不引入新能力、不需 `[learn]` SDK。

## 1. 背景与目标

### 1.1 背景

v1.10.0（embedding 语义搜索）于 2026-09-04 发布（tag @3865c75），引入 embedding 索引 + 语义检索 + smart-linking 语义增强。07 复盘（`.csp/artifacts/retrospective-v1.10.0.md`）产出 findings N1–N7 + 续留 M2/M3/L2/K1/K2，其中 5 项可在本轮不引入新能力、不需 SDK 的前提下修复：

- **N7**（P3）：semantic search 不走 cache——`_semantic_search` 每次全量 cosine，不复用 `_keyword_search` 的 F-QS-07 cache 路径。v1.10.0 新引入的 perf bug。
- **N2/K1**（P2）：coverage 未增（~64.2%），`compile/compiler.py` 仍 17%（拖 6 轮的最后 coverage 洼地），fail_under=64 持。北极星 coverage 65 差 ~1pp。
- **M3**（续留）：CLI `saw workflow list` 读 durable DB（`workflow_executions` 表），REST `GET /api/v1/workflows` 读 in-memory `_workflows` dict——语义双重，用户混淆。
- **N5**（P3）：SPEC-F-N-1 写 `saw search rebuild-embeddings`（子命令），实际实现为顶层命令 `saw rebuild-embeddings`（`main.py:73`）。Spec→实现偏离。
- **N6**（P3）：ROADMAP/lifecycle tag hash 不一致——07 已更正为 @3865c75，本轮复核确认三处一致。

**不做会怎样**：semantic 重复查询慢、coverage 北极星不达 65、workflow list 语义矛盾、Spec 与实现不一致、hash 追溯混淆持续存在。
**做了会怎样**：semantic 重复查询走 cache 变快、coverage ≥65 达北极星、workflow list 语义统一、Spec 与实现一致、hash 三处一致复核完成。

### 1.2 目标用户

| 用户角色 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|
| 知识库运维者 | local-first SAW 部署，CLI 为主 | 语义检索重复查询变快；workflow list 语义一致 | 日常运维 `saw search --mode semantic` + `saw workflow list` |
| 平台开发者 | REST API 集成 SAW | REST `/workflows` 返回 durable 历史（与 CLI 一致） | 通过 REST 查询 workflow 运行态 |
| 项目维护者 | 追溯 PRD→Spec→Task→commit→tag 链路 | Spec 命名与实现一致；hash 追溯准确 | 07 复盘 / 发布校验 |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| semantic cache 命中 | 重复查询命中率 | `[TBD]`（须 benchmark 后定基线） | cache hit/miss 计数 |
| coverage 北极星 | 全量覆盖率 | ≥65%（fail_under=65） | `pytest --cov` CI step |
| 测试不回归 | passed 数 | ≥1993（v1.10.0 基线） | CI pytest |
| workflow 语义一致 | CLI vs REST 返回数据源 | 均读 `workflow_executions` DB | 端到端断言 |

## 2. 需求概述

收敛 v1.10.0 及累积的 5 项可修缺陷（semantic cache / compile 深覆盖 / workflow REST 统一读 DB / Spec 命名回更 / hash 复核），不引入新能力、不需 SDK。

## 3. 详细功能设计

### 3.1 semantic search 走 query cache（N7）

- **描述**：`_semantic_search` 复用 F-QS-07 cache 路径（query-text→embedding→results），TTL + 索引变更失效，与 `_keyword_search` cache 机制对称。
- **用户故事**：作为知识库运维者，我想重复语义查询走 cache 变快，以便大规模库下 semantic 检索不因全量 cosine 慢于 BM25。
- **优先级**：P0
- **业务规则**：
  1. cache key 须含 `mode="semantic"` + `workspace_id`（与 `_keyword_search` 的 `workspace_id` 隔离对称），防跨 workspace 泄漏。
  2. cache 命中时直接返回缓存结果，跳过 `embed_texts()` + 全量 cosine。
  3. cache 失效条件同 F-QS-07：TTL 过期 + 内容写入（claim/wiki ingest 触发 cache clear）+ embedding 索引重建（`rebuild-embeddings` 触发 cache clear）。
  4. `semantic_fallback`（降级到 BM25）的结果**不缓存**——降级结果已走 `_keyword_search` 自身 cache，不重复缓存。
  5. `index_empty` 的空结果**不缓存**——避免空索引状态被缓存阻塞后续重建。
- **交互流程**：入口 `saw search --mode semantic` / `GET /api/v1/search?mode=semantic` → cache.get(question, {mode:semantic, workspace_id, limit, offset}) → 命中→返回缓存；未命中→embed + cosine + 排序 → cache.set → 返回。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| cache 写入失败（DB 锁/异常） | catch + 日志 warning，不阻塞查询返回 | 无（降级为无 cache，查询正常） |
| TTL 过期后首次查询 | cache miss → 正常计算 + 重写 cache | 无（用户无感） |

### 3.2 compile/compiler.py 深覆盖（N2/K1）

- **描述**：对 `engines/compile/compiler.py`（30 个 def，当前 17% 覆盖）专项深覆盖，拖动全量 coverage 从 ~64.2% 到 ≥65%，fail_under 从 64 提升到 65。
- **用户故事**：作为项目维护者，我想 compile/compiler.py 的 30 个函数有测试覆盖，以便 coverage 北极星 65 达成、最后洼地填平。
- **优先级**：P0
- **业务规则**：
  1. 覆盖目标函数（ground 自源码，`compiler.py:67-658`）：`_content_hash`(L282)、`_scan_vault_sources`(L297)、`_classify_sources_by_topic`(L316)、`_infer_topic`(L324)、`_ensure_topic_directories`(L337)、`_detect_page_type`(L393)、`_assess_confidence`(L407)、`_compile_content`(L419)、`_rule_based_compile`(L443)、`_llm_synthesize`(L461)、`_extract_title`(L497)、`_slugify`(L504)、`_write_page`(L511)、`_update_index_entry`(L534)、`_update_index_header`(L555)、`_cascade_update`(L570)、`_append_log`(L600)、`_parse_index`(L608)、`_parse_index_row`(L614)、`_parse_page`(L620)、`_parse_log`(L626)、`_render_empty_index`(L632)、`_render_index`(L638)、`_render_log_header`(L658)。
  2. `tests/unit/engines/compile/` 目录当前不存在——本轮新建测试目录 + 测试文件。
  3. `fail_under` 从 64 → 65（`pyproject.toml` `[tool.coverage.report]`）。
  4. 测试不依赖 `[learn]` extra（compiler 不涉及 embedding）。
- **交互流程**：N/A（测试基础设施，无用户交互）。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| compiler 依赖 LLM 的 `_llm_synthesize` | mock LLM 返回，测规则路径 + LLM 路径降级 | N/A |
| `_cascade_update` 递归更新 | seed 多页 + 触发级联 → 断言索引更新 | N/A |

### 3.3 workflow REST 统一读 DB（M3）

- **描述**：REST `GET /api/v1/workflows`（`collaborate.py:328` `list_workflows`）当前读 in-memory `_workflows` dict（L33）；统一为读 `workflow_executions` DB 表（与 CLI `saw workflow list` 对称），merge live + durable 消歧。
- **用户故事**：作为平台开发者，我想 REST `/workflows` 返回 durable 历史（与 CLI 一致），以便 API 集成时 workflow 列表语义不矛盾。
- **优先级**：P0
- **业务规则**：
  1. `list_workflows` 改为读 `workflow_executions` DB 表（`SELECT ... ORDER BY COALESCE(updated_at, started_at) DESC LIMIT ?`），与 CLI `list_recent`（`workflow_cmd.py`）同源。
  2. live 运行中的 workflow（in-memory `_workflows` 中 status=running）须 merge 进 DB 结果——DB 中无记录或 status 未更新的 live run 须在返回中体现（live 覆盖 DB status）。
  3. 返回 schema 不变（`{"workflows": [...], "total": N}`），字段对齐 DB 列：`workflow_id` / `definition_name` / `status` / `steps_completed` / `steps_total` / `updated_at` / `finished_at`。
  4. `--limit` 默认 20（与既有 REST 行为一致）。
  5. **行为决策（WHAT）**：统一读 DB + merge live。**HOW（DB 查询方式/merge 策略）留 03 技术方案**——不指定框架。
- **交互流程**：入口 `GET /api/v1/workflows` → 查 `workflow_executions` 表 → merge live `_workflows` running 状态 → 返回 JSON 列表。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| DB 无 `workflow_executions` 表（migration 未跑） | apply_migrations 确保 v4 表存在；查询失败→500 | `{"error": "..."}` |
| live workflow 在 DB 无记录（刚启动未持久化） | merge in-memory live run 进结果，status=running | 列表含 live run |

### 3.4 Spec 命名回更（N5）

- **描述**：SPEC-F-N-1 CLI 节写 `saw search rebuild-embeddings`（子命令路径），实际实现为顶层命令 `saw rebuild-embeddings`（`main.py:73` `app.command(name="rebuild-embeddings")`）。Spec 是蓝图——实现偏离须回更 Spec。
- **用户故事**：作为项目维护者，我想 Spec 命名与实现一致，以便追溯链 PRD→Spec→Task→commit 不混淆。
- **优先级**：P1
- **业务规则**：
  1. SPEC-F-N-1.md CLI 节 `saw search rebuild-embeddings` → 回更为 `saw rebuild-embeddings`（顶层命令）。
  2. 回更范围：CLI 用法示例 + 重建命令描述段落 + API 契约 CLI 节。
  3. 不改实现（实现是正确的，`search` 是独立函数非 Typer 子命令组，无法挂子命令）。
  4. 回更后 Spec→实现一致（07 闭环校验不再标偏离）。
- **交互流程**：N/A（文档回更，无用户交互）。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| Spec 其他章节引用旧命令名 | grep 全 Spec 文件，全量回更 | N/A |

### 3.5 tag hash 一致性复核（N6）

- **描述**：07 复盘已更正 ROADMAP/lifecycle 的 v1.10.0 tag hash 为 @3865c75。本轮复核确认三处一致（ROADMAP / lifecycle / git tag 实际值）。
- **用户故事**：作为项目维护者，我想 tag hash 三处一致，以便追溯链 commit→tag 准确。
- **优先级**：P2
- **业务规则**：
  1. `git rev-list -n1 v1.10.0` = `3865c75`（权威值）。
  2. ROADMAP v1.10.0 行 = `@3865c75`（已更正，复核）。
  3. lifecycle-state.json 06-ship progress = `@3865c75`（已更正，复核）。
  4. 若发现不一致 → 回更至一致。
- **交互流程**：N/A（复核任务，无用户交互）。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 发现遗漏不一致处 | 回更 | N/A |

## 4. 非功能要求

| 类别 | 要求 | 验收标准 |
|---|---|---|
| 性能 | semantic cache 命中后查询延迟 ≤ keyword cache 命中延迟（同量级） | `[TBD]`（须 benchmark 后定基线） |
| 测试覆盖 | 全量 coverage ≥65% | `pytest --cov --fail-under=65` CI step 通过 |
| 不回归 | 1993+ passed（v1.10.0 基线 1993） | CI pytest passed ≥1993 |
| Lint | ruff 0 errors | `ruff check src/ tests/` 0 errors |
| 冒烟 | smoke 6/6 | `saw smoke` 6/6 |
| 兼容 | 无 breaking API 变更（additive MINOR） | REST schema 不变；CLI 命令不变 |

## 5. 数据需求（埋点/事件）

| 事件名 | 触发条件 | 关键属性 | 用途 |
|---|---|---|---|
| semantic_cache_hit | `_semantic_search` cache.get 命中 | question_hash, workspace_id, mode | cache 命中率监控 |
| semantic_cache_miss | `_semantic_search` cache.get 未命中 → cache.set | question_hash, workspace_id, mode, result_count | cache 效率监控 |
| workflow_rest_list | REST `GET /api/v1/workflows` 调用 | source(dblive), limit, total | REST 语义统一验证 |

## 6. 验收标准

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-CACHE-1 | semantic cache 命中 | 同一 question + workspace_id + limit 的 semantic 查询已执行过一次（cache 已写入） | 再次执行 `saw search --mode semantic` 同查询 | 返回结果与首次一致，不调用 `embed_texts()` / 不执行全量 cosine |
| AC-CACHE-2 | semantic cache workspace 隔离 | workspace A 的 semantic 结果已缓存 | workspace B 执行同查询 | cache miss，独立计算（不泄漏 A 结果） |
| AC-CACHE-3 | semantic cache 索引变更失效 | semantic 结果已缓存 | 执行 `saw rebuild-embeddings`（或内容写入触发 cache clear） | cache 失效，下次查询重新计算 |
| AC-CACHE-4 | semantic fallback 不缓存 | embeddings unavailable，降级到 BM25（`semantic_fallback=True`） | 再次同查询 | 不读 semantic cache（降级结果走 `_keyword_search` 自身 cache） |
| AC-COV-1 | compile/compiler 深覆盖 | `tests/unit/engines/compile/` 测试目录新建 | 运行 `pytest --cov=saw.engines.compile.compiler` | compiler.py 覆盖率显著提升（17%→[TBD]），全量 coverage ≥65% |
| AC-COV-2 | fail_under 棘轮 | `pyproject.toml` `[tool.coverage.report]` | 检查 fail_under 值 | =65 |
| AC-WF-1 | REST 读 DB | `workflow_executions` 表有 3 条历史记录 | `GET /api/v1/workflows` | 返回 ≥3 条，字段含 workflow_id/status/steps |
| AC-WF-2 | REST merge live | in-memory `_workflows` 有 1 条 running（DB 无记录或 status 未更新） | `GET /api/v1/workflows` | 返回列表含该 live running workflow |
| AC-WF-3 | CLI/REST 语义一致 | 同一 wiki DB | CLI `saw workflow list` 与 REST `GET /api/v1/workflows` | 返回相同数据源（`workflow_executions` 表），结果集一致 |
| AC-SPEC-1 | Spec 命名回更 | SPEC-F-N-1.md 已回更 | grep `saw search rebuild-embeddings` 于 SPEC-F-N-1.md | 0 匹配（全部回更为 `saw rebuild-embeddings`） |
| AC-SPEC-2 | 实现不变 | 实现未改动 | `saw rebuild-embeddings --help` | 顶层命令可用（exit 0） |
| AC-HASH-1 | hash 三处一致 | git tag / ROADMAP / lifecycle-state | 对比 v1.10.0 tag hash | 三处均 = @3865c75 |

## 7. 排期估算

| 阶段 | 预估工作量 | 依赖 | 风险 |
|---|---|---|---|
| 02 需求拆解 | `[TBD]` | 本 PRD Approved | 无 |
| 03 技术方案 | `[TBD]` | 02 done | M3 REST merge 策略须设计 |
| 04 任务拆解 | `[TBD]` | 03 done | 无 |
| 05 实施 | `[TBD]` | 04 done | compile 深覆盖成本高（复杂编译器） |
| 06 发布 | `[TBD]` | 05 done | 无 |
| 07 复盘 | `[TBD]` | 06 done | 无 |

## 8. 风险与依赖

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| compile/compiler.py 深覆盖成本高（复杂编译器，30 函数） | High | 测试投入大 | 优先覆盖高价值路径（`_compile_content`/`_cascade_update`/`_render_index`），剩余标 P2 续留 |
| M3 REST 改行为（in-memory→DB）须回归 | Medium | REST 调用方行为变化 | AC-WF-1/2/3 全覆盖；merge live 确保不丢运行态 |
| semantic cache 失效逻辑与 F-QS-07 不对称 | Low | cache stale | 复用 F-QS-07 cache 模块，失效条件同 keyword |
| 不需 `[learn]` SDK 的项才入本轮 | — | — | N1/N4（embedding E2E/benchmark）续留，须用户装 SDK |

**前置依赖**：v1.10.0 基线（@3865c75）。**不需** `[learn]` extra。

**非目标（续留）**：
- N1（embedding E2E 未验证，须用户装 SDK）— 续留
- N3/K2（per-request workspace 注入，v2.0 架构演进）— 续留
- N4（向量检索 P99 benchmark，须 SDK）— 续留
- M2（agent "最近活动" 聚合，须 event bus）— 续留
- L2（链接自动 apply 未做）— 续留

---

## 附录：ground 自源码

| claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|
| N7: `_semantic_search` 无 cache | `src/saw/engines/query/engine.py` `_semantic_search` 方法（L~330–420） | `_semantic_search` 无 `cache import/get/set`；`_keyword_search` 有 F-QS-07 cache（L223–237 `get_cache`/`_cache.get`，L299–300 `_cache.set`） | TRUE |
| N2/K1: compiler 17%，30 def 未深测 | `src/saw/engines/compile/compiler.py:67–658`（30 个 def，含 `_content_hash` L282 / `_cascade_update` L570 / `_render_index` L638 等） | `tests/unit/engines/compile/` 目录不存在（`ls` 确认）；coverage ~17%（07 复盘 N2 证据） | TRUE |
| M3: CLI list=durable DB，REST=in-memory | `src/saw/drivers/cli/commands/workflow_cmd.py` `list_recent`（SELECT FROM `workflow_executions`）；`src/saw/api/routes/collaborate.py:33` `_workflows: dict = {}`（L328–335 `list_workflows` 读 `_workflows.values()`） | CLI 读 DB 表；REST 读内存 dict——语义双重 | TRUE |
| N5: Spec 写 `saw search rebuild-embeddings`，实际顶层命令 | `.csp/specs/SPEC-F-N-1.md` CLI 节（`saw search rebuild-embeddings`）；`src/saw/drivers/cli/main.py:73` `app.command(name="rebuild-embeddings")` | Spec 写子命令路径；实现为顶层命令（`search` 是独立函数非 Typer 子命令组） | TRUE |
| N6: tag hash 3865c75，三处一致 | `git rev-list -n1 v1.10.0` = `3865c75`；`docs/strategy/ROADMAP.md` v1.10.0 行 `@3865c75`；`.csp/lifecycle-state.json` 06-ship progress `@3865c75` | 07 已更正，三处一致 | TRUE（已修，复核） |

### 下一步建议

- [ ] 进入需求拆解 → 把 5 个功能模块翻成 Feature 清单 + 依赖图 + NFR，落 `.csp/decomposition/`
- [ ] M3 REST 统一读 DB 是行为决策（HOW 留 03），02 拆解时须明确 merge live + durable 的 Feature 边界
- [ ] compile 深覆盖可按函数聚类拆多 Feature（rule-based 路径 / index 渲染 / cascade 级联）
- [ ] 进入 03 技术方案 → 读 PRD + decomposition + PMS，semantic cache 复用 F-QS-07 cache 模块（ADR-010 [TBD] 缓存优化落地）

当前产物：`docs/prd/PRD-debt-closure-v1.11.0.md`（status: Approved）+ `.csp/product-spec/PMS-debt-closure.md`（delta 更新）+ `docs/prd/PRD-INDEX.md` 已登记 + `.csp/manifest.json` 已回写。`.csp/lifecycle-state.json`：01 done，current_stage=02-decomposition。
