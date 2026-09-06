---
id: PRD-e2e-tail-v1.13.0
title: E2E 收尾轮
version: 1.0
status: Approved
author: [TBD]
date: 2026-09-06
product_type: platform
feature_count: 5
mvp_scope: [ingest-dir-recursive, real-benchmark-vllm, rest-workflows-changelog, coverage-67, retro-q1-q3-close]
thin_sections: []
upstream_source: .csp/artifacts/retrospective-v1.12.0.md#Q2-O1-O3-O2 + E2E Bug A
roadmap_ref: docs/strategy/ROADMAP.md#v1.13.0
target_version: v1.13.0
related_pms: [.csp/product-spec/PMS-e2e-tail.md]
related_specs: [.csp/specs/SPEC-F-R-1.md, .csp/specs/SPEC-F-R-2.md, .csp/specs/SPEC-F-R-3.md, .csp/specs/SPEC-F-R-4.md, .csp/specs/SPEC-F-R-5.md]
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
---

# PRD: E2E 收尾轮

> 内部 milestone v4.3。承接 v1.12.0 真实 E2E 暴露的 bug + 复盘 findings。**additive**——bug fix + 真实 benchmark + 文档 + coverage 棘轮，无 breaking API 变更 → MINOR。fix `84e1776`（embedding httpx + 去 ST fallback，已合入 master）在本版本基线内。

## 1. 背景与目标

### 1.1 背景：为什么现在做？不做会怎样？做了会怎样？

v1.12.0 把 embedding provider 从本地重 SDK pivot 到 OpenAI 风格 API（httpx 直连 vLLM），E2E 已验证通（commit `84e1776`：httpx + 去 ST fallback）。但真实 E2E 暴露 **1 个真 bug** 且留下 **4 个尾巴**：

- **Bug A（真 bug）**：`saw ingest <dir>` 传目录时报 "Is a directory"。ingest 应递归遍历目录下文件，而非把目录当单文件交给 extractor。
- **Q2/O1**：v1.12.0 的 benchmark 是 mock 假向量（手工构造 topic-direction 向量），非真实 API 语义向量。现 vLLM `qwen_embedding@8001` 可真测 semantic vs BM25 召回率 + P99 延迟 + cache 命中率。
- **O3**：v1.11.0 改了 REST `/workflows` 行为（读 DB merge live），但项目无 CHANGELOG 文件，字段名变更未标注，老消费者无兼容别名。
- **O2**：coverage 66%（`fail_under=65`），余量 1pp 仍薄，需继续棘轮推进到 67。
- **Q1/Q3**：本次 E2E 已闭合（Q1 真实 API E2E 验证通、Q3 ST fallback 已删），retrospective 需补记关闭。

不做会怎样：embedding "E2E 验证通过" 但有已知 bug（ingest 目录不可用）+ benchmark 是假数据（无法量化质量是否优于 BM25）+ REST 行为变更无文档（消费者踩坑）。做了会怎样：ingest 目录可用、benchmark 有真实 baseline、REST 行为有 CHANGELOG、coverage 有余量——embedding 真正"上线可用"。

### 1.2 目标用户

| 用户角色 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|
| KW（知识工作者） | 用 SAW 编译知识库，ingest 大量文档 | 批量 ingest 目录不报错 | `saw ingest ./docs` 递归导入 |
| DEV（开发者） | 用 REST API 集成 SAW workflow | `/workflows` 字段稳定有文档 | 集成 workflow list 到下游 |
| OPS（运维） | 部署 SAW + vLLM，关注性能 | benchmark 有真实 P99 baseline | 评估 semantic 检索是否可上生产 |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| ingest 目录可用 | `saw ingest <dir>` 递归成功 | 0 "Is a directory" 报错 | E2E 测试 + 手动验证 |
| benchmark 真实 baseline | semantic vs BM25 召回率 | semantic 召回 ≥ BM25（同义查询集） | 真实 vLLM benchmark 脚本输出 |
| benchmark P99 | semantic search P99 延迟 | 优于或接近 BM25 P99 `[TBD]` ms | 真实 vLLM benchmark P99 统计 |
| cache 命中率 | semantic cache hit/miss | 命中率 `[TBD]`%（重复查询加速） | cache hit/miss 计数 |
| REST 有文档 | CHANGELOG 标注行为变更 | CHANGELOG 文件存在 + `/workflows` 字段有兼容别名 | 文件存在性检查 + REST 测试 |
| coverage 棘轮 | `fail_under` | 65 → 67 | pyproject.toml + CI coverage 报告 |
| 不回归 | pytest passed | ≥ 2076 | CI pytest |

## 2. 需求概述

修复 ingest 目录递归 + 用 vLLM 真测 embedding benchmark + REST 兼容别名+CHANGELOG + coverage 棘轮 67 + 闭合 Q1/Q3 复盘补记。

## 3. 详细功能设计

### 3.1 ingest 目录递归（Bug A）

- **描述**：`saw ingest <dir>` 传入目录时，应递归遍历目录下所有支持的文件（markdown/pdf/code/json/table/audio/video），逐文件 ingest，而非把目录路径当单文件交给 extractor 导致 "Is a directory"。
- **用户故事**：作为 KW，我想 `saw ingest ./docs` 递归导入目录下所有文档，以便批量入库不报错。
- **优先级**：P0
- **业务规则**：
  1. 目录递归遍历所有子目录（深度不限），只处理 classify 能识别的文件格式（markdown/pdf/code/json/table/audio/video），跳过 UNKNOWN 格式文件（如 `.txt` 无扩展名二进制等）。
  2. 空目录（无任何可识别文件）→ 返回 IngestResult，errors 含 "No ingestible files found in directory: {dir}"，claim_count=0。
  3. 每个文件独立 ingest（独立 session_id 或共享 session_id 聚合结果——HOW 留 03），任一文件失败不中断其余文件（best-effort），失败的记入 errors 列表。
  4. 目录与单文件行为不冲突：传入单文件时走既有路径（classify → 单 extractor），不触发递归。
  5. 不递归 `.git/`、`.saw/`（SAW 内部目录）、`node_modules/` 等已知噪声目录——HOW（具体排除清单）留 03，PRD 只要求"排除 SAW 内部 + VCS 目录"。
  6. 递归结果聚合：返回的 IngestResult 汇总所有文件的 claim_count/entity_count/relation_count，errors 汇总所有失败文件，parser 标 "directory-batch"。
- **交互流程**：入口 `saw ingest <dir> --path <wiki>` → 检测 source 是目录 → 递归枚举文件 → 逐文件 classify+extract+fuse+validate+enqueue → 汇总结果 → 打印 Panel（含文件数 + 总 claims）→ 成功反馈；失败处理：若全部文件失败 → Exit 1 + errors 列表；部分失败 → warnings 含失败文件 + claims 打印成功部分。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 目录不存在 | classify 返回 UNKNOWN → pipeline 报 "Unknown format" | "Error: directory not found or no ingestible files" |
| 空目录（无可识别文件） | 返回 errors 列表 | "No ingestible files found in directory: {dir}" |
| 部分文件提取失败 | 记入 errors，继续其余文件 | "Warnings: N files failed (see errors)" + 成功部分 Panel |
| 目录含子目录 | 递归进入子目录 | 正常 Panel（含递归文件数） |

**验收标准**：

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-A-1 | 目录递归 ingest | 一个含 3 个 .md 文件的目录 | `saw ingest <dir>` | 3 文件全部入库，claim_count ≥ 3，0 "Is a directory" 错误 |
| AC-A-2 | 空目录 | 一个无任何可识别文件的目录 | `saw ingest <dir>` | 返回 "No ingestible files found"，Exit 1 |
| AC-A-3 | 部分失败 | 目录含 2 .md + 1 损坏 .pdf | `saw ingest <dir>` | 2 .md 成功入库，1 .pdf 记入 errors，不中断 |
| AC-A-4 | 子目录递归 | 目录含子目录，子目录内 1 .md | `saw ingest <dir>` | 子目录内文件也被 ingest，claim_count 含子目录文件 |
| AC-A-5 | 排除 SAW 内部目录 | 目录含 `.saw/` 子目录 | `saw ingest <dir>` | `.saw/` 内文件不被 ingest |

### 3.2 真实 embedding benchmark（Q2/O1）

- **描述**：用 vLLM `qwen_embedding@8001` 真实 API 跑 semantic vs BM25 召回率对比 + P99 延迟 + semantic cache 命中率，产出真实 baseline 数据（非 mock 假向量）。benchmark 是一个可执行脚本/命令，PRD 只描述目标与方法（WHAT），具体脚本实现留 03。
- **用户故事**：作为 OPS，我想跑真实 embedding benchmark 得到 P99 + 召回率 baseline，以便判断 semantic 检索是否可上生产。
- **优先级**：P0
- **业务规则**：
  1. benchmark 须用**真实 vLLM API**（`qwen_embedding@8001`，用户已起），不可用 mock 假向量。
  2. benchmark 须对比 semantic vs BM25 **召回率**：在同一查询集上，统计两种模式各自召回的相关文档数。查询集含**同义查询**（query 与文档无字面重叠但语义相关——BM25 会漏、semantic 应召回）。
  3. benchmark 须测 **P99 延迟**：对同一查询跑 N 次（N ≥ 100），统计 P99。semantic P99 须优于或接近 BM25 P99（目标 [TBD] ms，跑完填实际值）。
  4. benchmark 须测 **semantic cache 命中率**：对同一查询重复跑 2 次，第 2 次应命中 cache（延迟显著降低）；统计 hit/miss。
  5. benchmark 须可重复执行（脚本/命令），输出结构化结果（召回率/P99/命中率数值 + 查询集明细）。
  6. benchmark 不依赖本地 torch/SentenceTransformer（v1.12.0 已 pivot 到 API，benchmark 走 API 路径）。
  7. benchmark 数据集须覆盖 ≥ 3 主题域（如 ML/crypto/web），每主题 ≥ 5 文档，保证召回对比有区分度。
  8. 若 vLLM 8001 不可达 → benchmark 报清晰错误（"vLLM embedding endpoint at :8001 unreachable"），不静默退化到 mock。
- **交互流程**：入口（脚本/命令 `[TBD]`）→ 检测 vLLM 8001 可达 → 建测试数据集 → BM25 baseline 查询 → semantic 查询 → cache 命中率测试 → 统计召回/P99/命中率 → 输出报告 → 成功反馈；失败处理：vLLM 不可达 → 报错退出。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| vLLM 8001 不可达 | 报错退出，不跑 mock | "Error: vLLM embedding endpoint at :8001 unreachable. Start vLLM then re-run." |
| API 超时 | 记超时，跳过该查询，继续 | "Warning: query N timed out, skipped" |
| API 返回维度不匹配 | 报错退出 | "Error: embedding dim mismatch (expected X, got Y)" |

**验收标准**：

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-B-1 | 真实 API 召回 | vLLM 8001 可达，3 主题数据集 | 跑 benchmark | semantic 召回率 ≥ BM25 召回率（同义查询集） |
| AC-B-2 | P99 延迟 | vLLM 8001 可达，100 次查询 | 跑 benchmark P99 统计 | 输出 P99 数值，记录 baseline（目标值 [TBD] ms） |
| AC-B-3 | cache 命中率 | vLLM 8001 可达，同一查询跑 2 次 | 跑 benchmark cache 测试 | 第 2 次命中 cache，延迟显著低于第 1 次，输出 hit/miss |
| AC-B-4 | vLLM 不可达 | vLLM 8001 不可达 | 跑 benchmark | 报 "vLLM endpoint unreachable" 错误退出，不 mock |

### 3.3 REST `/workflows` 兼容别名 + CHANGELOG（O3）

- **描述**：v1.11.0 改了 REST `GET /workflows` 行为（读 durable DB `workflow_executions` 表 merge live in-memory），但无 CHANGELOG 标注行为变更，且响应字段名（如 `definition_name`）无兼容别名。本模块加字段别名 + 建 CHANGELOG 文件标注行为变更。
- **用户故事**：作为 DEV，我想 `/workflows` 响应有兼容别名且行为变更有 CHANGELOG，以便集成时不踩坑。
- **优先级**：P1
- **业务规则**：
  1. `GET /workflows` 响应增加兼容别名字段：每个 workflow item 除现有 `definition_name` 外，加 `name` 别名（同值），供老消费者兼容。
  2. `GET /workflows` 响应增加 `workflow` 别名（= `definition_name`），兼容 POST 响应的字段名。
  3. 建立 `CHANGELOG.md` 文件（项目根），标注 v1.11.0 `/workflows` 行为变更：从 in-memory only → durable DB + live merge；字段从 `name` → `definition_name`（加 `name` 别名兼容）。
  4. CHANGELOG 格式遵循 Keep a Changelog 约定（语义化版本 + 日期 + 变更类型 Added/Changed/Fixed/Deprecated）。
  5. CHANGELOG 须回溯标注 v1.10.0–v1.13.0 的关键行为变更（至少 v1.11.0 REST 行为 + v1.12.0 embedding provider pivot），v1.13.0 本轮变更（ingest dir fix + benchmark + coverage）。
  6. 别名不改变现有字段语义——`definition_name` 仍是主字段，别名是镜像值，未来 deprecated 时再移除。
  7. REST 测试须断言别名字段存在且等于主字段。
- **交互流程**：入口 `GET /api/v1/workflows` → 既有逻辑（DB merge live）→ 响应 body 每个 item 加 `name`/`workflow` 别名 → 返回；CHANGELOG：开发者读 `CHANGELOG.md` → 找到 v1.11.0 行为变更条目 → 知晓兼容方案。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 老消费者读 `name` 字段 | 别名返回同值 | 无感兼容 |
| 新消费者读 `definition_name` | 主字段返回 | 正常 |
| DB 无行（空 wiki） | 既有逻辑返回 `{"workflows": [], "total": 0}` | 正常空响应 |

**验收标准**：

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-C-1 | 别名兼容 | `GET /workflows` 返回非空列表 | 解析响应 | 每个 item 含 `name` 且 == `definition_name` |
| AC-C-2 | CHANGELOG 存在 | 项目根 | 读 `CHANGELOG.md` | 文件存在，含 v1.11.0 `/workflows` 行为变更条目 |
| AC-C-3 | CHANGELOG 回溯 | 读 `CHANGELOG.md` | 含 v1.12.0 embedding pivot 条目 + v1.13.0 本轮条目 |

### 3.4 coverage 棘轮 67（O2）

- **描述**：将 `pyproject.toml` `[tool.coverage.report] fail_under` 从 65 提升到 67，给余量。通过补测非核心模块边角提升实际覆盖率到 ≥ 67%。
- **用户故事**：作为 DEV，我想 coverage 门禁有 2pp 余量，以免新增测试波动就 break CI。
- **优先级**：P2
- **业务规则**：
  1. `pyproject.toml` `fail_under` 从 65 改为 67。
  2. 实际覆盖率须 ≥ 67%（当前 66%，需补测 ≥ 1pp 覆盖非核心边角模块——具体补哪些模块留 03 任务拆解定）。
  3. 补测不引入新功能代码，只加测试覆盖既有未覆盖路径。
  4. 补测须是真实测试（非 `pragma: no cover` 绕过），`pragma: no cover` 使用不增加。
  5. CI 须在 `fail_under=67` 下绿。
- **交互流程**：入口 CI `pytest --cov` → 覆盖率 ≥ 67% → pass；失败处理：< 67% → CI break，开发者补测。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 覆盖率 66% | break | CI 红色，须补测 |
| 补测后 67%+ | pass | CI 绿色 |

**验收标准**：

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-D-1 | fail_under 提升 | 读 `pyproject.toml` | `fail_under = 67` | 值为 67 |
| AC-D-2 | 实际覆盖率达标 | 跑 `pytest --cov` | coverage 报告 | ≥ 67%，CI 绿 |

### 3.5 闭合 Q1/Q3 复盘补记

- **描述**：v1.12.0 复盘的 Q1（真实 API E2E 未跑）和 Q3（ST fallback 路径未测）在本轮 E2E 中已闭合（Q1 真实 API E2E 验证通过 commit `84e1776`；Q3 ST fallback 已删——httpx 直连 vLLM，去 ST fallback）。在 retrospective 中补记关闭状态。
- **用户故事**：作为 DEV，我想复盘 findings Q1/Q3 标记为闭合，以便 backlog 准确。
- **优先级**：P2
- **业务规则**：
  1. Q1（真实 API E2E 未跑，High/P1）→ 标 `closed`：commit `84e1776` 用 httpx 直连 vLLM `qwen_embedding@8001`，真实 API E2E 验证通过（semantic 检索召回正常）。
  2. Q3（ST fallback 路径未测，Low/P3）→ 标 `closed`：commit `84e1776` 删除了 ST fallback 路径（`_st_available`/`_embed_via_st` 移除），provider 改为 API-only（httpx 直连），无 ST fallback 分支需测。
  3. 补记写在 `.csp/artifacts/retrospective-v1.12.0.md` 的 Q1/Q3 findings 下，加 `**v1.13.0 闭合**` 标注 + commit `84e1776` 证据。
  4. 不新建 retrospective 文件（Q1/Q3 是 v1.12.0 findings，在原文件补记）。
- **交互流程**：读 `retrospective-v1.12.0.md` → 在 Q1/Q3 finding 下追加闭合标注 → 保存。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| Q1/Q3 已标闭合 | 不重复标注 | 跳过 |

**验收标准**：

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-E-1 | Q1 闭合标注 | 读 `retrospective-v1.12.0.md` Q1 | 查找闭合标注 | 含 `**v1.13.0 闭合**` + commit `84e1776` |
| AC-E-2 | Q3 闭合标注 | 读 `retrospective-v1.12.0.md` Q3 | 查找闭合标注 | 含 `**v1.13.0 闭合**` + ST fallback 已删 |

## 4. 非功能要求

| 类别 | 要求 | 验收标准 |
|---|---|---|
| 性能 | benchmark 不 OOM | benchmark 脚本在 vLLM 8001 可达时跑完不超时（单次 < 5 min） |
| 性能 | ingest 递归不阻塞 | 100 文件目录 ingest 在 60s 内完成（无 LLM 模式） |
| 兼容 | 2076+ passed 不回归 | CI pytest ≥ 2076 passed，0 failed |
| 兼容 | ruff 0 | CI ruff check src/ tests/ 0 errors |
| 兼容 | smoke 6/6 | `saw smoke` 6/6 pass |
| 兼容 | REST 别名不破坏现有契约 | `/workflows` 既有字段（`definition_name`/`status`/`steps_completed`/`steps_total`/`updated_at`/`finished_at`）值不变 |
| 可维护 | CHANGELOG 可追溯 | CHANGELOG 每条变更带版本号 + 日期 |

## 5. 数据需求（埋点/事件）

| 事件名 | 触发条件 | 关键属性 | 用途 |
|---|---|---|---|
| ingest_dir_batch | `saw ingest <dir>` 递归完成 | file_count, success_count, fail_count, total_claims | 监控批量 ingest 健康度 |
| benchmark_run | benchmark 脚本执行完 | recall_semantic, recall_bm25, p99_ms, cache_hit_rate | 记录 baseline 数据 |
| rest_workflows_alias_hit | `/workflows` 响应被读 `name` 别名字段 | consumer_id (若可识别) | 监控别名使用率（未来 deprecated 决策依据） |

## 6. 验收标准（汇总）

见 Section 3 各模块 AC 表（AC-A-1..5 / AC-B-1..4 / AC-C-1..3 / AC-D-1..2 / AC-E-1..2），共 16 条 Given-When-Then。每功能模块 ≥ 2 条 AC。

## 7. 排期估算

| 阶段 | 预估工作量 | 依赖 | 风险 |
|---|---|---|---|
| 02 需求拆解 | [TBD] | 本 PRD Approved | 无 |
| 03 技术方案 | [TBD] | 02 done | benchmark 脚本设计须定 vLLM 接入方式 |
| 04 任务拆解 | [TBD] | 03 done | 无 |
| 05 实施 | [TBD] | 04 done | vLLM 8001 需用户保持运行；ingest 递归改动面 |
| 06 发布 | [TBD] | 05 done + verify 全绿 | 无 |
| 07 复盘 | [TBD] | 06 done | 无 |

## 8. 风险与依赖

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| vLLM 8001 不稳定/用户关停 | Medium | benchmark 项无法跑 | benchmark 项标 "需 vLLM 可达"前置依赖；不可达时报错不 mock；其他 4 项不依赖 vLLM 可先行 |
| ingest 递归改动影响既有单文件路径 | Low | 单文件 ingest 回归 | AC-A-4 排除内部目录 + 单文件路径测试覆盖不回归 |
| REST 别名引入字段冗余 | Low | 响应体增大 | 别名是镜像值，未来 deprecated 时移除；监控 alias_hit 事件 |
| coverage 补测 ROI 低 | Medium | 花时间补边角模块 | 优先补 ingest/query 核心路径未覆盖分支，非边角 |
| 续留 findings 不收敛 | Low | backlog 堆积 | 本轮闭合 Q1/Q3；N3/M2/L2/O4 续留（非本轮范围） |

**续留 findings（非本轮范围）**：N3/K2（per-request workspace 注入，v2.0 架构候选）/ M2（agent 活动聚合）/ L2（链接自动 apply）/ O4（tag 指向 reconcile 非 release commit）。

## 附录

### ground 自源码

| claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|
| Bug A：`saw ingest <dir>` 报 "Is a directory" | `src/saw/engines/ingest/classifier.py:149` | `if source_path.is_dir():` 检测目录，从首个子文件推断格式，但返回 `ClassifiedSource(format=..., path=source_path)`——**返回目录路径本身**（非子文件） | TRUE |
| Bug A：extractor 收到目录路径报错 | `src/saw/engines/ingest/pipeline.py:120-130`（markdown 分支 `self._markdown_extractor.extract(classified.path, ...)`）+ `pipeline.py:211`（`except Exception as e: errors.append(f"Extraction failed for {source}: {e}...")`） | pipeline 把目录路径当单文件传给 extractor，extractor 尝试 open 目录 → OSError "Is a directory" → 被 pipeline.py:211 捕获记入 errors | TRUE |
| Bug A：pipeline 无目录递归逻辑 | `src/saw/engines/ingest/pipeline.py:ingest()`（全文） | `ingest()` 只处理单个 source（classify→单 extractor），无 `is_dir` 分支、无 `walk`/`rglob` 遍历子文件 | TRUE |
| Q2/O1：semantic 搜索 + cache 路径存在 | `src/saw/engines/query/engine.py:_semantic_search()`（约 L461-560） | `_semantic_search` 用 `get_cache()` + `mode="semantic"` key 隔离，cosine 排序；`_keyword_search` 是 BM25 baseline | TRUE |
| Q2/O1：既有 benchmark 是 mock 假向量 | `tests/unit/test_embedding_benchmark.py:10-12` + `:39`（`_topic_vec` 手工构造 topic-direction 向量） | benchmark 用 `_mock_embedding_response` 返回手工构造向量，非真实 API；注释标 "Real E2E benchmark requires real API key" | TRUE |
| O3：REST `/workflows` v1.11.0 改后读 DB merge live | `src/saw/api/routes/collaborate.py:327-411`（`list_workflows`） | 读 `workflow_executions` 表（durable）+ merge `_workflows` in-memory（live）；响应字段 `definition_name`（无 `name` 别名） | TRUE |
| O3：项目无 CHANGELOG 文件 | 项目根无 `CHANGELOG.md`（glob 确认不存在） | 无 CHANGELOG，v1.11.0 行为变更未标注 | TRUE |
| O2：coverage fail_under=65 | `pyproject.toml:127`（`fail_under = 65`） | 当前 66%，门禁 65；目标提升到 67 | TRUE |
| Q3：ST fallback 路径已删 | commit `84e1776`（httpx 直连 vLLM + 去 ST fallback，已合入 master） | provider 改 API-only（httpx 直连），`_st_available`/`_embed_via_st` 已移除——Q3 须标闭合 | TRUE |

### 下一步建议
- [ ] 进入需求拆解 → 把 5 功能模块翻成 Feature 清单 + 依赖图 + NFR，落 `.csp/decomposition/`
- [ ] 既有 PRD 解析 → 标准化中间表示落 `.csp/artifacts/`
- [ ] 进入 03 技术方案 → 读 PRD + decomposition + PMS，benchmark 脚本须定 vLLM httpx 接入方式 + 数据集构造
当前产物：`docs/prd/PRD-e2e-tail-v1.13.0.md`（status: Approved）+ `.csp/product-spec/PMS-e2e-tail.md`（ready）+ `docs/prd/PRD-INDEX.md` 已登记。已写 `.csp/lifecycle-state.json`：01 done，current_stage=02-decomposition。
