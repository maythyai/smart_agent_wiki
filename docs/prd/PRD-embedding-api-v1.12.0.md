---
id: PRD-embedding-api-v1.12.0
title: embedding 改用 OpenAI 风格 API + E2E 验证
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
product_type: platform
feature_count: 4
mvp_scope: [embedding-provider-api, embedding-dim-configurable, local-st-optional-fallback, test-api-mock-e2e]
thin_sections: []
upstream_source: ".csp/artifacts/retrospective-v1.10.0.md#N1-N4 + 用户决策(pivot to API)"
roadmap_ref: docs/strategy/ROADMAP.md#v1.12.0
target_version: v1.12.0
related_pms:
  - .csp/product-spec/PMS-embedding-api.md
related_specs:
  - .csp/specs/SPEC-F-Q-1.md
  - .csp/specs/SPEC-F-Q-2.md
  - .csp/specs/SPEC-F-Q-3.md
  - .csp/specs/SPEC-F-Q-4.md   # 下游技术方案生成后回填
related_decomposition: .csp/decomposition/DECOMPOSITION-DELTA-v1.12.0.md
---

# PRD-embedding-api-v1.12.0：embedding 改用 OpenAI 风格 API + E2E 验证

> v1.11.0 闭环后新一轮 01。**用户决策 pivot**：不跑本地重 ML 服务（torch/sentence-transformers 本地模型——会打死 runner 且非生产形态），embedding 改用 **OpenAI 风格 API**（litellm，与既有 LLM 调用同范式）。闭合 v1.10.0 N1（High/P1）+ N4（Medium/P2）。**additive MINOR**——换 provider + E2E 验证 + benchmark，无 breaking API 变更 → 按 ROADMAP §1.1 规则发 MINOR，不强行 MAJOR。

## 1. 背景与目标

### 1.1 背景：为什么现在做？不做会怎样？做了会怎样？

**v1.10.0 引入了 embedding 语义搜索，但 provider 走本地 sentence-transformers，存在三个问题：**

1. **重 SDK 打死 runner**：`src/saw/adapters/embeddings.py::embed_texts()`（`embeddings.py:53,57`）直接调用 `SentenceTransformer("all-MiniLM-L6-v2").encode(texts, normalize_embeddings=True)`，底层依赖 torch + transformers（`pyproject.toml:64` `[learn]` extra 定义 `sentence-transformers>=2.2`）。torch 是 ~800MB 级重依赖，在 CI/runner 环境会因内存/OOM/模型下载超时而打死进程。v1.10.0 复盘 N1 证据：`sentence_transformers is NOT installed` → 7 个 importorskip 测试在 CI 全 skip。

2. **非生产形态**：本地模型推理（torch CPU 前向）在生产部署中不是合理形态——生产环境应走 API 服务（弹性、可观测、无本地模型下载）。项目已有的 LLM 调用（`src/saw/adapters/llm/router.py`）已用 litellm 做 OpenAI 风格 API 调用（`router.py:16` `import litellm`；`router.py:98,110` `_completion_with_retry` 调 `litellm.completion(**kwargs)`），embedding 走本地 ST 是范式不一致。

3. **E2E 未验证**：v1.10.0 的 12 条 AC 中 7 条以 `pytest.importorskip("sentence_transformers")` 落地（`tests/unit/test_embedding_index.py:6`、`tests/unit/test_semantic_search.py:6`、`tests/unit/test_related_pages_embedding.py:6`），CI 环境 ST 未装 → 全部 skip，真实语义检索路径**未经运行验证**（N1 High/P1）。仅降级路径（`tests/unit/test_embedding_degradation.py` 用 mock 通过 4 测试）经实测。

**不做会怎样**：embedding 语义搜索功能名义存在但实际不可用——CI 无法验证、生产部署需装 torch 打死 runner、语义检索形同虚设。N1（High/P1）持续悬空。

**做了会怎样**：embedding 从"本地重 SDK、未验证"到"API 轻接入、E2E 实测通过"——去掉本地 torch 重依赖，CI 用 API mock 跑通全部 embedding 测试（不再 importorskip skip），生产部署不依赖本地 torch/模型下载。闭合 N1 + N4。

### 1.2 目标用户

| 用户角色 | 简称 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|---|
| Knowledge Worker | KW | 使用 SAW 检索知识库的终端用户 | 语义查询不再漏同义结果 | `saw search "机器学习" --mode semantic` 召回内容用词不同但语义相同的 claim |
| Developer | DEV | 基于 SAW API 二次开发的工程师 | 可编程调用语义检索端点 + 配置 embedding provider | `GET /api/v1/search?mode=semantic`；通过 config 配置 embedding API base_url/key/model |
| Operator | OPS | 部署/运维 SAW 实例 | 无需安装 torch 即可启用 embedding 功能 | 生产部署走 API，runner 稳定不 OOM；API 失败时降级到 BM25 |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| embedding E2E 验证 | 测试全 pass（不 skip） | 7 个原 importorskip 测试改为 API mock 后全 pass | pytest CI |
| 无本地 torch 加载 | runner 进程无 torch import | 0 次 torch 加载 | CI 日志 + `pip show torch` 不存在 |
| 语义检索召回 | semantic vs BM25 召回率 | 优于纯 BM25 [TBD] | 同义查询集 benchmark |
| API 延迟 | semantic P99 | 优于或接近 BM25 毫秒级 [TBD] | benchmark |
| 不回归 | 全量 passed | ≥2064 passed | pytest CI |
| lint | ruff | 0 error | ruff check |

## 2. 需求概述

embedding provider 从本地 sentence-transformers 重构为 litellm OpenAI 风格 embedding API，维度可配置，本地 ST 降为可选 fallback，测试改 API mock + benchmark。

## 3. 详细功能设计

> **只描述 WHAT，不指定 HOW**（provider 选 litellm 是决策；具体调用参数/模型名归 03 技术方案）。不指定除 litellm 外的框架。

### 3.1 F-EA-1：embedding provider 重构为 litellm API

**WHAT**：`src/saw/adapters/embeddings.py::embed_texts()` 的 provider 从本地 `SentenceTransformer("all-MiniLM-L6-v2").encode()` 重构为 litellm OpenAI 风格 embedding API（`litellm.embedding`/`aembedding`）。base_url/api_key/model 走 config（复用既有 `LLMSettings` 的 `api_base`/`api_key` 范式，新增 embedding 专用配置项）。`embeddings_available()` 的检测逻辑从"检测 sentence_transformers 可 import"改为"检测 embedding API 配置可用"。调用方接口不变——`embed_texts(texts) -> list[list[float]] | None` 签名保持，下游 `_semantic_search`/`EmbeddingSink.write`/`compute_related_pages` 无需改动。

**用户故事**：作为 OPS，我想 embedding 走 API 而非本地模型，以便生产部署无需安装 torch 且 runner 稳定。

**优先级**：P0

**业务规则**：
1. provider 选 litellm（项目已用 litellm 做 LLM，`router.py:16` `import litellm`，`pyproject.toml:13` `litellm>=1.83.13` 已在核心依赖），不引入新框架。
2. embedding API 配置走 config（base_url/api_key/model），复用既有 LLM 同套 env 范式（`settings.py:19-26` `LLMSettings` 有 `api_base`/`api_key`；`router.py:133` `_MODEL_ENV_KEYS` 映射 model prefix → env var）。
3. `embed_texts()` 失败时返回 None（既有契约不变），调用方降级到非语义路径。
4. `embeddings_available()` 从检测 `sentence_transformers` 可 import（`settings.py:116-120` `_embeddings_available` 用 `importlib.import_module("sentence_transformers")`）改为检测 embedding API 配置可用（有 model + 有 api_key 或 api_base）。
5. `detect_tier()` 的 FULL 条件相应调整——不再以本地 ST 可 import 为前提，改为以 embedding API 配置可用为前提。

**交互流程**：入口 `saw ingest` / `saw search --mode semantic` / `saw links suggest` → 步骤：`embed_texts()` 调 litellm API 获取向量 → 成功返回 `list[list[float]]`；失败返回 None → 调用方降级。

**异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| API key 未配置 | `embeddings_available()` 返回 False，降级到 BM25 | tier=LIGHTWEIGHT，语义端点回退 BM25 + `semantic_fallback: true` |
| API 调用失败（网络/限流/超时） | `embed_texts()` try/except 返回 None，调用方降级 | 日志 warning + BM25 回退 |
| API 返回维度异常（空向量/维度不匹配） | `embed_texts()` 返回 None，调用方降级 | 日志 warning + BM25 回退 |

**AC-EA-1**：
- **Given** embedding API 配置已设置（model + api_key 或 api_base）
- **When** 用户执行 `saw search "concept" --mode semantic`
- **Then** `embed_texts()` 通过 litellm API 获取向量，语义检索返回结果，`semantic_fallback: false`，exit 0

**AC-EA-2**：
- **Given** embedding API 未配置（无 model/api_key）
- **When** 用户执行 `saw search "concept" --mode semantic`
- **Then** 自动降级到 BM25，`meta.semantic_fallback: true`，exit 0，不报错

### 3.2 F-EA-2：维度可配置 + embedding_store dim 驱动 + 重建检测

**WHAT**：API embedding 模型维度（如 1536）≠ 本地 ST 的 384。`embedding_store` 表已有 `dim` 列（`migrations.py:337-358`，`dim INTEGER NOT NULL`）和 `model` 列，须可配 dim。索引重建时检测维度变更——`search_cmd.py::rebuild_embeddings` 已有维度变更检测范式（`search_cmd.py:217-227`：`SELECT DISTINCT dim FROM embedding_store` 比对 `current_dim`，不匹配则 `DELETE FROM embedding_store` 全量重建）。API 模型切换后 dim 变更须自动触发全量重建。`EmbeddingSink.write()` 存储的 `model` 列须从硬编码 `"all-MiniLM-L6-v2"`（`embedding_sink.py:73`）改为动态使用当前配置的 model 名。

**用户故事**：作为 DEV，我想切换 embedding 模型时维度自动检测并重建索引，以便不同 API 模型（不同 dim）无缝切换。

**优先级**：P0

**业务规则**：
1. `embedding_store` 表结构不变（已有 `dim` + `model` 列），无需新 migration——dim 驱动已有。
2. `rebuild_embeddings` 的维度变更检测逻辑须适配 API provider——probe dim 时调 `embed_texts(["dimension probe"])` 获取当前 API 模型 dim（`search_cmd.py:219-227` 既有范式沿用）。
3. `EmbeddingSink.write()` 的 `model` 列值须动态反映当前 provider model 名（非硬编码 `all-MiniLM-L6-v2`）。
4. 维度变更时全量重建——旧 dim 向量与新 dim 不兼容，须 `DELETE FROM embedding_store` 后全量重新嵌入。

**交互流程**：入口 `saw rebuild-embeddings` → 步骤：probe 当前 API model dim → 比对 `embedding_store` 已有 dim → 不匹配则 wipe 全表 → 全量 claim + wiki 页面重新嵌入 → 成功反馈 "Rebuilt N vectors (dim=D)"；失败处理同 embed_texts 降级。

**异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| API 模型切换后 dim 变更 | 检测 dim 不匹配，wipe 旧向量，全量重建 | "Dimension changed (OLD → NEW), wiping old vectors." |
| rebuild 时 API 调用失败（chunk 级） | 跳过该 chunk，继续其他 chunk | "Embedding failed for a chunk, skipping." |
| rebuild 时 API 完全不可用 | 提示配置 API，exit 0 | "Embeddings unavailable. Configure embedding API in config." |

**AC-DIM-1**：
- **Given** `embedding_store` 有 dim=384 的旧向量（v1.10.0 本地 ST 生成），用户切换到 API 模型（dim=1536）
- **When** 用户执行 `saw rebuild-embeddings`
- **Then** 检测到 dim 不匹配，wipe 旧向量，用 API 模型重新嵌入全量 claim/wiki，新向量 dim=1536，model 列反映当前 API 模型名

**AC-DIM-2**：
- **Given** embedding API 配置可用，用户执行 `saw ingest` 写入新 claim
- **When** `EmbeddingSink.write()` 被调用
- **Then** 向量以当前 API 模型 dim 入库，`model` 列值为当前配置的 model 名（非硬编码 `all-MiniLM-L6-v2`）

### 3.3 F-EA-3：本地 ST 可选 fallback

**WHAT**：本地 sentence-transformers 降为**可选 fallback**——`[learn]` extra 仍可装（`pyproject.toml:64` `learn = ["fsrs>=4.0", "sentence-transformers>=2.2"]`），装了 ST 且 API 未配置时可走本地 ST（向后兼容 v1.10.0 用户）；不装 ST 时走 API（默认路径）。provider 选择优先级：API 配置可用 → 走 API；API 不可用但本地 ST 可用 → 走本地 ST；两者都不可用 → 降级 BM25。

**用户故事**：作为 OPS，我想在 API 不可用时仍能用本地 ST（如果已装），以便离线/内网环境也有 embedding 能力。

**优先级**：P1

**业务规则**：
1. 默认走 API（不要求本地 ST）——这是 v1.12.0 的核心 pivot。
2. 本地 ST 作为 fallback：仅当 `[learn]` extra 已装且 API 不可用时启用。
3. `embeddings_available()` 返回 True 的条件：API 配置可用 **OR** 本地 ST 可 import（二者满足其一即 FULL tier）。
4. 不装 ST 不影响任何功能——CI 不再 importorskip skip，改 API mock 测试。
5. `cluster_by_embedding()`（Learn 引擎用，`embeddings.py:74`）同样走新 provider——provider 重构在 `embed_texts()` 层面，`cluster_by_embedding` 调 `embed_texts` 自动受益。

**交互流程**：入口 `embed_texts()` → 步骤：检查 API 配置 → API 可用则调 API；API 不可用则检查本地 ST → ST 可用则走本地；两者不可用返回 None → 调用方降级。

**异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| API 可用 + ST 已装 | 走 API（默认优先） | 无 |
| API 不可用 + ST 已装 | 走本地 ST fallback | 日志 info "API unavailable, falling back to local ST" |
| API 不可用 + ST 未装 | 返回 None，降级 BM25 | tier=LIGHTWEIGHT |
| API 可用 + ST 未装 | 走 API | 无（默认形态） |

**AC-FB-1**：
- **Given** `[learn]` extra 已装（本地 ST 可用），embedding API 未配置
- **When** 用户执行 `saw search "concept" --mode semantic`
- **Then** 走本地 ST fallback，语义检索返回结果，`semantic_fallback: false`，日志提示 "API unavailable, falling back to local ST"

**AC-FB-2**：
- **Given** `[learn]` extra 未装，embedding API 已配置
- **When** 用户执行 `saw search "concept" --mode semantic`
- **Then** 走 API，语义检索返回结果，`semantic_fallback: false`，无需本地 ST

### 3.4 F-EA-4：测试改 API mock + benchmark

**WHAT**：v1.10.0 的 7 个 importorskip 测试（`test_embedding_index.py` 3 个 + `test_semantic_search.py` 2 个 + `test_related_pages_embedding.py` 2 个）改为 API mock 测——不再 `pytest.importorskip("sentence_transformers")`，改为 mock litellm embedding API 返回固定向量，CI 可跑（不 skip、不依赖本地 SDK）。既有 4 个降级 mock 测试（`test_embedding_degradation.py`）的 mock 目标从 `embeddings_available` 扩展到也覆盖 API 不可用场景。新增 benchmark：semantic vs BM25 召回 + P99（用 API mock 跑，真实 API key 可选 E2E）。

**用户故事**：作为 DEV，我想 embedding 测试在 CI 全 pass（不 skip），以便真实验证语义检索逻辑而非仅降级路径。

**优先级**：P0

**业务规则**：
1. 7 个原 importorskip 测试去掉 `pytest.importorskip("sentence_transformers")`，改 mock litellm API 返回固定维度向量（如 1536 维 mock）。
2. mock 须验证：向量入库、cosine 排序、空索引处理、维度变更检测、upsert——即原 AC-EMB-1/3、AC-SEM-1/3、AC-LINK-1/3 的逻辑验证不变，只是向量来源从本地 ST 改为 API mock。
3. CI workflow 不再需要装 `[learn]` extra 跑 embedding 测试（但 distiller/fsrs/trends 的 importorskip 先例不变——那些是 `[learn]` extra 的其他用途）。
4. benchmark 测试用 API mock 生成固定向量集，对比 semantic vs BM25 召回率 + P99 延迟（mock 延迟为 0，真实 E2E benchmark 须用户配 API key 可选跑）。
5. `test_ci_workflow.py` 中 importorskip 检测逻辑须更新——embedding 测试不再 importorskip ST。

**交互流程**：入口 `pytest tests/unit/test_embedding*.py tests/unit/test_semantic_search.py tests/unit/test_related_pages_embedding.py` → 步骤：mock litellm API → 测试向量入库/检索/排序逻辑 → 全 pass（不 skip）。

**异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| CI 环境 litellm mock 失败 | 测试 fail（不 skip），须修复 | CI 红灯 |
| 用户本地配真实 API key 跑 E2E | 可选跑真实 API embedding benchmark | benchmark 输出召回 + P99 |
| API mock 返回维度与预期不符 | 测试 assert dim 一致 | 测试 fail |

**AC-TEST-1**：
- **Given** CI 环境未安装 `[learn]` extra（无 sentence_transformers）
- **When** `pytest tests/unit/test_embedding_index.py tests/unit/test_semantic_search.py tests/unit/test_related_pages_embedding.py` 执行
- **Then** 全部测试 pass（不 skip），用 API mock 验证语义检索逻辑

**AC-TEST-2**：
- **Given** CI workflow 文件
- **When** 检查 embedding 测试执行状态
- **Then** 无 `importorskip("sentence_transformers")`，embedding 测试全 pass，CI 不需 `[learn]` extra

**AC-TEST-3**：
- **Given** benchmark 测试已编写（API mock 向量集）
- **When** 执行 benchmark 测试
- **Then** 输出 semantic vs BM25 召回率对比 + P99 延迟（mock 数据），结果可记录为 baseline [TBD]

## 4. 非功能需求

| NFR | 指标 | 验收标准 |
|---|---|---|
| API embedding P99 延迟 | [TBD]（须优于或接近 BM25 的毫秒级） | benchmark 对比（真实 API key 可选 E2E） |
| 无本地 torch 加载 | runner 进程不 import torch | CI 日志 + `pip show torch` 不存在 |
| 既有测试不回归 | ≥2064 passed | pytest CI |
| ruff lint | 0 error | ruff check src/ tests/ |
| 降级策略 | API 失败 → BM25，不报错不中断 | tier< LIGHTWEIGHT 时语义端点回退 |
| workspace 隔离 | embedding 索引须遵守 workspace_id 隔离（`embedding_store` PK (doc_id, workspace_id)） | 跨 workspace 查询不泄漏 |
| 向量索引存储开销 | [TBD]（每 claim/wiki 页面向量大小 × 总量） | 磁盘测量 |

## 5. 数据需求

| 数据 | 来源 | 说明 |
|---|---|---|
| claim 内容 | `claim` 表（`workspace_id` 列已有，migrations.py v8） | embedding 输入文本 |
| wiki 页面内容 | `WikiRepository.read(slug)` | embedding 输入文本 |
| embedding 向量 | `embed_texts()`（改用 litellm API，dim 可配） | 持久化入 `embedding_store` |
| 向量-claim 映射 | `EmbeddingSink`（`embedding_sink.py` Write Queue sink 范式） | doc_id → 向量 |
| embedding API 配置 | config（base_url/api_key/model，复用 `LLMSettings` 范式） | provider 配置 |
| workspace_id | `embedding_store` 表 PK (doc_id, workspace_id) | 向量索引 workspace 隔离 |

## 6. 验收标准

| AC ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-EA-1 | API 配置可用时语义检索 | embedding API 已配置 | `saw search "concept" --mode semantic` | litellm API 获取向量，返回语义结果，`semantic_fallback: false` |
| AC-EA-2 | API 未配置时降级 | API 未配置 | `saw search "concept" --mode semantic` | 降级 BM25，`semantic_fallback: true`，不报错 |
| AC-DIM-1 | 维度变更触发重建 | 旧 dim=384 向量存在，切换到 API dim=1536 | `saw rebuild-embeddings` | 检测 dim 不匹配，wipe 旧向量，全量重建 dim=1536 |
| AC-DIM-2 | ingest 写入正确 model | API 配置可用 | `saw ingest` 写入新 claim | `EmbeddingSink.write()` 存储的 model 列为当前 API model 名 |
| AC-FB-1 | 本地 ST fallback | `[learn]` 已装，API 未配置 | `saw search --mode semantic` | 走本地 ST，返回结果，`semantic_fallback: false` |
| AC-FB-2 | 无 ST 走 API | `[learn]` 未装，API 已配置 | `saw search --mode semantic` | 走 API，返回结果，无需本地 ST |
| AC-TEST-1 | CI embedding 测试全 pass | CI 无 `[learn]` | `pytest test_embedding*.py test_semantic_search.py test_related_pages_embedding.py` | 全 pass（不 skip），API mock |
| AC-TEST-2 | CI 无 importorskip | CI workflow | 检查 embedding 测试 | 无 `importorskip("sentence_transformers")`，CI 不需 `[learn]` |
| AC-TEST-3 | benchmark 可执行 | benchmark 测试已编写 | 执行 benchmark | 输出 semantic vs BM25 召回 + P99（mock baseline [TBD]） |

## 7. 排期估算

[TBD]——排期归 04 阶段 WBS/WAVE-PLAN。预期 2-3 Wave（F-EA-1 provider 重构先行 → F-EA-2 维度配置 + F-EA-3 fallback → F-EA-4 测试 + benchmark）。

## 8. 风险与依赖

### 8.1 前置依赖

- **v1.11.0 基线**：已 Released（@5fca85b），2064 passed，coverage 65.36%，fail_under=65。
- **litellm**：已在核心依赖（`pyproject.toml:13` `litellm>=1.83.13`），`litellm.embedding`/`aembedding` 可用。不引入新框架。
- **embedding API 配置**：base_url/api_key/model 走 config（复用既有 `LLMSettings` 的 `api_base`/`api_key` 范式，`settings.py:19-26`）。
- **既有 `embedding_store` 表**：已有 `dim` + `model` 列（migrations.py v10），无需新 migration。
- **不要求**本地 sentence-transformers（API 为默认路径）。

### 8.2 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| API 限流/延迟影响检索体验 | 中 | 中 | 降级策略：API 失败 → BM25；P99 benchmark 后定 baseline |
| API key 配置门槛 | 中 | 低 | 复用既有 LLM 同套 env 范式（`OPENAI_API_KEY` 等），用户已有 LLM 配置时零额外配置 |
| 维度切换数据迁移 | 低 | 中 | `rebuild_embeddings` 已有 dim 变更检测 + wipe 重建范式（`search_cmd.py:217-227`） |
| 测试 mock 与真实 API 行为偏差 | 中 | 低 | mock 验证逻辑路径；真实 API key 可选 E2E benchmark 补充 |
| coverage 回归 | 低 | 低 | 去掉 importorskip 后测试从 skip 变 pass，coverage 应升不降 |
| workspace 隔离遗漏 | 低 | 中 | `embedding_store` PK (doc_id, workspace_id) 既有，不变 |

### 8.3 续留 findings（跨迭代 backlog）

以下 findings 不在本轮处理范围，续留：

| finding | 严重度 | 说明 |
|---|---|---|
| N3 / K2 | Medium / P2 | per-request workspace 注入（v2.0 架构演进候选） |
| M2 | Medium / P2 | agent "最近活动"未聚合（须 event bus） |
| L2 | Low / P3 | 链接自动 apply 未做（suggest 只输出不自动改文件） |
| O1 | Low / P2 | semantic cache 命中率未 benchmark |
| O2 | Low / P3 | coverage 65.36% 余量薄 |
| O3 | Low / P3 | REST 行为变更无 CHANGELOG |
| O4 | Low / P3 | tag 指向 reconcile 非 release commit |

### 8.4 硬约定

- **#12**：缺依赖须用户确认——本轮**不要求**用户装 `[learn]` extra（API 为默认路径）；`[learn]` 装了可用作 fallback，不装不影响功能。

---

## Ground 自源码

| claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|
| `embed_texts()` 当前走本地 `SentenceTransformer("all-MiniLM-L6-v2").encode()` | `src/saw/adapters/embeddings.py:29,41,43,53,57` | `_get_model()` 加载 `SentenceTransformer("all-MiniLM-L6-v2")`（:41）；`embed_texts()` 调 `model.encode(texts, normalize_embeddings=True)`（:57）；返回 L2-normalized 向量或 None（:50）。**provider 重构点**。 | TRUE |
| litellm 已在核心依赖且已用于 LLM 调用 | `pyproject.toml:13` + `src/saw/adapters/llm/router.py:16,98,110` | `pyproject.toml:13` `litellm>=1.83.13`；`router.py:16` `import litellm`；`router.py:98-110` `_completion_with_retry` 调 `litellm.completion(**kwargs)`。`litellm.embedding`/`aembedding` 同包可用。 | TRUE |
| `LLMSettings` 已有 `api_base`/`api_key`/`model` 配置范式 | `src/saw/config/settings.py:19-26` | `LLMSettings` 有 `extraction_model`/`query_model`/`api_key`/`api_base`/`timeout`/`enable_thinking`。embedding 配置可复用此范式。 | TRUE |
| `detect_tier()` FULL 检测本地 ST | `src/saw/config/settings.py:79,92-93,116-120` | `detect_tier()` 调 `_embeddings_available()`（:92-93）；`_embeddings_available()` 用 `importlib.import_module("sentence_transformers")`（:117-120）。**须改：检测 API embedding 配置而非本地 ST**。 | TRUE |
| `_semantic_search` 调 `embed_texts` + 从 `embedding_store` 读向量 | `src/saw/engines/query/engine.py:461,474,477,497-498,518-520` | `_semantic_search` 从 `saw.adapters.embeddings` import `cosine_similarity`/`embed_texts`/`embeddings_available`（:474-477）；检查 `embeddings_available()`（:498）；调 `embed_texts([question])`（:505）；从 `embedding_store WHERE workspace_id = ?` 读向量（:520）。**provider 换了接口不变**。 | TRUE |
| `embedding_store` 表有 `dim` + `model` 列 | `src/saw/db/migrations.py:337-358` | `_create_embedding_store`（:337-358）表含 `doc_id`/`entity_type`/`model`/`vector BLOB`/`dim INTEGER`/`workspace_id`/`created_at`，PK (doc_id, workspace_id)。**dim 列已存在，可配 dim 无需新 migration**。 | TRUE |
| `rebuild_embeddings` 已有维度变更检测范式 | `src/saw/drivers/cli/commands/search_cmd.py:176,181,185,203,205,217,219,227` | `rebuild_embeddings`（:176）检查 `embeddings_available()`（:205）；`SELECT DISTINCT dim FROM embedding_store`（:217）比对 `current_dim`（:219 probe）；不匹配则 `DELETE FROM embedding_store`（:227）。**范式沿用，适配 API**。 | TRUE |
| `EmbeddingSink.write()` 硬编码 model 名 `all-MiniLM-L6-v2` | `src/saw/write_queue/sinks/embedding_sink.py:18,24,46-48,62-66,73` | import `embed_texts`/`embeddings_available`（:18）；`write()` 检查 `embeddings_available()`（:47）；调 `embed_texts([content])`（:52）；INSERT 时 model 列硬编码 `"all-MiniLM-L6-v2"`（:73）。**须改动态 model 名**。 | TRUE |
| 7 个测试用 `importorskip("sentence_transformers")` | `tests/unit/test_embedding_index.py:6` / `tests/unit/test_semantic_search.py:6` / `tests/unit/test_related_pages_embedding.py:6` | 三文件首行 `pytest.importorskip("sentence_transformers")`；共 7 个测试（3+2+2）在 CI 全 skip。**须改 API mock**。 | TRUE |
| 4 个降级测试用 mock `embeddings_available` | `tests/unit/test_embedding_degradation.py` | 无 importorskip；用 `patch("saw.adapters.embeddings.embeddings_available", return_value=False)` mock 降级（4 测试 pass）。**mock 目标须扩展到 API 不可用**。 | TRUE |
| `compute_related_pages` 有 embedding 信号（权重 2.5） | `src/saw/engines/query/related_pages.py:25,61-66,70,75,110-129,165-166` | `embedding_sim` 字段（:25）；检查 `embeddings_available()`（:66）；从 `embedding_store` 读向量（:70,119）；`cosine_similarity` 计算相似度（:125）；权重 2.5（:127）。**provider 重构在 embed_texts 层，自动受益**。 | TRUE |
| litellm LLM 调用的 `_endpoint_kwargs` 范式 | `src/saw/adapters/llm/router.py:187-194` | `_is_ollama_model()`（:187）+ `_endpoint_kwargs()`（:191-194）处理 `api_base`/`api_key` 路由。embedding API 调用可复用此范式。 | TRUE |
| `_MODEL_ENV_KEYS` 映射 model prefix → env var | `src/saw/adapters/llm/router.py:133` | `{"gpt":"OPENAI_API_KEY", "claude":"ANTHROPIC_API_KEY", ...}`。embedding model 同样可走 env var 范式。 | TRUE |

## 下一步建议

- [ ] 进入需求拆解 → 把 4 个功能模块翻成 Feature 清单 + 依赖图 + NFR，落 `.csp/decomposition/`
- [ ] F-EA-1（provider 重构）先行；F-EA-2（维度配置）+ F-EA-3（fallback）依赖 F-EA-1；F-EA-4（测试 + benchmark）与各 Feature 并行
- [ ] 进入 03 技术方案 → 读 PRD + decomposition + PMS，litellm embedding API 具体调用参数/模型名/异步 vs 同步选型 + Spec
- [ ] ADR 候选：embedding provider 选型（litellm API vs 本地 ST fallback 优先级）、维度变更数据迁移策略
- 当前产物：`docs/prd/PRD-embedding-api-v1.12.0.md`（status: Approved）+ `.csp/product-spec/PMS-embedding-api.md`（ready）+ `docs/prd/PRD-INDEX.md` 已登记 + `PMS-INDEX.md` 已登记。已写 `.csp/lifecycle-state.json`：01 done，current_stage=02-decomposition。
