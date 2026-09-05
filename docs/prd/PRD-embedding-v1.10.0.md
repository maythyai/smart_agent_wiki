---
id: PRD-embedding-v1.10.0
title: embedding 语义搜索
version: 1.0
status: Released
author: lifecycle-orchestrator
date: "2026-09-04"
product_type: platform
feature_count: 4
mvp_scope: [embedding-index, semantic-search-endpoint, smart-linking-embedding, importorskip-heavy-sdk]
thin_sections: [3]
upstream_source: "docs/strategy/ROADMAP.md#v1.10.0 + .csp/artifacts/retrospective-v1.9.0.md (findings M1 + L1)"
target_version: v1.10.0
roadmap_ref: docs/strategy/ROADMAP.md#v1.10.0
related_pms:
  - .csp/product-spec/PMS-embedding.md
related_decomposition: ".csp/decomposition/DECOMPOSITION-DELTA-v1.10.0.md"
related_retrospective: .csp/artifacts/retrospective-v1.9.0.md
related_specs:
  - .csp/specs/SPEC-F-N-1.md
  - .csp/specs/SPEC-F-N-2.md
  - .csp/specs/SPEC-F-N-3.md
  - .csp/specs/SPEC-F-N-4.md
related_adr:
  - .csp/tech-decisions/ADR/ADR-010-embedding-storage-retrieval.md
related_tms:
  - .csp/test-spec/TMS-DELTA-v1.10.0.md
---

# PRD-embedding-v1.10.0：embedding 语义搜索

> v1.9.0 闭环后新一轮 01。采纳内部候选 v4.2（embedding）。**additive MINOR**——按 ROADMAP §1.1 规则发 MINOR，不强行 MAJOR（无 breaking API 变更）。直接提升 trustworthy-claim coverage 北极星，并解掉 L1（smart-linking suggest 启发式噪声）+ M1（embedding defer 解除）。

## 1. 背景与目标

### 1.1 背景

SAW 当前检索基于 FTS5 + BM25 词面匹配（`src/saw/engines/query/search.py`，`FTS5Search.search()` 用 `bm25(fts_index)` 排序）。BM25 在精确词面命中场景表现良好，但无法覆盖同义/近义查询——用户搜"机器学习"时无法召回内容为"ML"或"machine learning"的 claim，导致语义层召回缺失。

v1.5.0 已引入 `src/saw/adapters/embeddings.py`（`embed_texts()` / `cosine_similarity()` / `cluster_by_embedding()`），但仅用于 Learn 引擎的 claim 聚类（`cluster_by_embedding`），**未接入 Query 引擎的检索路径**——FULL tier 检测存在（`config/settings.py::detect_tier`），但语义检索端点缺失。

v1.8.0 smart-linking `compute_related_pages`（`src/saw/engines/query/related_pages.py`）使用 3-signal 启发式（shared tags Jaccard 权重 2.0 / shared links Jaccard 权重 3.0 / type affinity 权重 1.0），复盘 L1 指出"启发式噪声大，可加 embedding 替代/增强"。

本轮将 embedding 从 Learn 引擎专用扩展到 Query 引擎检索 + smart-linking 建议，使"会进化的知识库"具备语义层。

### 1.2 目标

1. **embedding 索引可建**：claim/wiki 页面向量入库，复用 `[learn]` extra 的 sentence-transformers（既有 `embeddings.py` 已加载 `all-MiniLM-L6-v2` 模型）。
2. **语义检索端点+CLI**：Query 引擎增 semantic 模式，与既有 BM25 并行/融合。
3. **smart-linking suggest 接 embedding 相似度**：替代/增强 3-signal 启发式，解 L1 噪声。
4. **heavy-SDK 测试 importorskip 沿用**：distiller/fsrs/trends 已有先例（`tests/unit/engines/learn/test_fsrs.py:15` `pytest.importorskip("fsrs")`），embedding 测试同样模式。

### 1.3 目标用户

| 角色 | 简称 | 场景 |
|---|---|---|
| Knowledge Worker | KW | 语义查询不再漏同义结果；`saw search --mode semantic "概念A"` 召回内容用词不同但语义相同的 claim |
| Developer | DEV | `GET /api/v1/search?mode=semantic` 端点可编程调用；smart-linking suggest 输出更精准 |
| Operator | OPS | 无 `[learn]` extra 时自动降级到 BM25（`detect_tier` 返回 LIGHTWEIGHT），不报错不中断 |

### 1.4 成功指标

| 指标 | 当前基线 | 目标 | 测量方式 |
|---|---|---|---|
| 语义检索召回率 vs 纯 BM25 | N/A | 优于纯 BM25 [TBD] | 同义查询集对比 |
| L1 suggest 噪声下降 | 启发式 3-signal | 噪声下降 [TBD] | 用户评审/采样 |
| embedding 索引可建 | 不可用 | 可建 | `saw search --mode semantic` 返回结果 |
| 测试全绿 | 1987 passed | ≥1987 passed | pytest CI |
| 无 `[learn]` 时降级 | N/A | 降级到 BM25，不报错 | tier=LIGHTWEIGHT 时语义端点回退 |

## 2. 需求概述

### 2.1 模块边界

embedding 语义索引与检索 + smart-linking 语义增强。不新建引擎——复用 Query 引擎（`QueryEngine`）+ 既有 `embeddings.py` 适配器 + Write Queue sink 范式。

### 2.2 Feature 列表

| Feature | 描述 | 优先级 |
|---|---|---|
| F-EMB-1 | embedding 索引（claim/wiki 页面向量入库） | P0 |
| F-EMB-2 | 语义检索端点 + CLI（Query engine 增 semantic 模式） | P0 |
| F-EMB-3 | smart-linking suggest 接 embedding 相似度（解 L1） | P1 |
| F-EMB-4 | heavy-SDK 测试 importorskip 沿用 | P0 |

### 2.3 非目标

- 实时 WS 仪表盘（v4.3 完整前端工程，留后续）。
- desktop 完成（v4.4，Tauri，defer）。
- K1（coverage 65）/ K2（per-request workspace）债务（续留）。
- M2（agent "最近活动"未聚合）/ M3（CLI list vs REST 语义双重）（续留）。
- 向量数据库选型/部署（本轮只在本地 SQLite 生态内做，不引入外部 DB——HOW 归 03 技术方案）。

## 3. 详细功能设计

> **只描述 WHAT，不指定 HOW**（不指定 DB/框架/库版本）。技术选型归 03 阶段 ADR。

### 3.1 F-EMB-1：embedding 索引

**WHAT**：对已有 claim 和 wiki 页面生成 embedding 向量并持久化入库，使得后续语义检索可查。向量生成复用既有 `embeddings.py::embed_texts()`（已加载 `all-MiniLM-L6-v2`，L2-normalized）。索引构建通过 Write Queue sink 范式（参照 `fts5_sink.py` 的 `write(op)` + `can_handle(sink_name)` 模式），在 claim/wiki 写入时同步触发向量入库。

**前置条件**：`[learn]` extra 已安装（`embeddings_available()` 返回 True，tier=FULL）。

**AC-EMB-1**：
- **Given** 一个已初始化的 wiki，`[learn]` extra 已安装
- **When** 用户执行 `saw ingest` 写入新 claim 或 wiki 页面
- **Then** 对应的 embedding 向量被生成并持久化，可在后续语义检索中召回

**AC-EMB-2**：
- **Given** `[learn]` extra 未安装（tier=LIGHTWEIGHT）
- **When** 用户执行 `saw ingest`
- **Then** claim 正常写入（FTS5 索引正常），不生成 embedding 向量，不报错，日志提示"embeddings unavailable, skipping vector index"

**AC-EMB-3**：
- **Given** 已有存量 claim/wiki 页面（FTS5 索引已有但无向量）
- **When** 用户执行重建索引命令（具体命令名归 02/03 设计）
- **Then** 全量页面被扫描、生成向量、入库；已删除的 claim 不被索引

**异常 1**：`sentence_transformers` 模型下载失败（网络/OOM）——`embed_texts()` 已有 try/except 返回 None，调用方须降级到非语义路径。
**异常 2**：向量维度不匹配（模型变更后旧向量维度不一致）——索引重建须检测维度变更并全量重建。

### 3.2 F-EMB-2：语义检索端点 + CLI

**WHAT**：Query 引擎（`QueryEngine.query()`）增 `semantic` 模式，与既有 `search`/`graph`/`compare`/`tree` 模式并行。语义检索用查询文本的 embedding 与已索引 claim/wiki 向量做相似度计算，返回 top-K 结果。CLI `saw search` 增 `--mode semantic` 选项（参照既有 `--mode default|tree` 范式，`search_cmd.py`）。REST 端点 `GET /api/v1/search` 增 `mode=semantic` 参数。

**AC-SEM-1**：
- **Given** `[learn]` extra 已安装，embedding 索引已建
- **When** 用户执行 `saw search "machine learning" --mode semantic`
- **Then** 返回语义相似结果（包括内容为"ML"或"machine learning"的 claim），结果按相似度降序排列，exit 0

**AC-SEM-2**：
- **Given** `[learn]` extra 未安装（tier=LIGHTWEIGHT）
- **When** 用户执行 `saw search "query" --mode semantic`
- **Then** 自动降级到 BM25 词面检索，结果中 meta 标注 `semantic_fallback: true`，exit 0，不报错

**AC-SEM-3**：
- **Given** `[learn]` extra 已安装但 embedding 索引为空（刚 init 未 ingest）
- **When** 用户执行 `saw search "query" --mode semantic`
- **Then** 返回空结果或提示"embedding index empty, use BM25 mode"，exit 0

**异常 1**：`GET /api/v1/search?mode=semantic` 端点在 tier=LIGHTWEIGHT 时返回 BM25 结果 + `semantic_fallback: true`（不返回 500）。
**异常 2**：查询文本 embedding 失败（模型异常）——降级到 BM25，meta 标注 `embedding_error`。

### 3.3 F-EMB-3：smart-linking suggest 接 embedding 相似度

**WHAT**：`compute_related_pages`（`src/saw/engines/query/related_pages.py`）当前用 3-signal 启发式（shared tags / shared links / type affinity）。本轮在 embedding 可用时增第 4 信号：页面内容 embedding 相似度。当 tier=FULL 时，相似度信号参与排序（可加权或替代启发式信号）；当 tier<FULL 时，保持原有 3-signal 不变。

**AC-LINK-1**：
- **Given** `[learn]` extra 已安装，wiki 页面已有 embedding 索引
- **When** 用户执行 `saw links suggest <page>`
- **Then** 建议列表包含语义相似页面（即使无共享 tag/link），排序优于纯启发式，exit 0

**AC-LINK-2**：
- **Given** `[learn]` extra 未安装
- **When** 用户执行 `saw links suggest <page>`
- **Then** 使用原有 3-signal 启发式，行为与 v1.8.0 一致，不报错

**AC-LINK-3**：
- **Given** 两页面共享 tag 但内容语义不同（如 tag "python" 但一个是爬虫、一个是 Web 框架）
- **When** embedding 信号参与排序
- **Then** 语义不相似的页面排名下降，减少 L1 噪声

**异常 1**：页面无 embedding 向量（未索引）——该页面跳过 embedding 信号，仅用 3-signal 评分。
**异常 2**：全部页面均无 embedding 向量——`compute_related_pages` 完全降级到 3-signal，行为不变。

### 3.4 F-EMB-4：heavy-SDK 测试 importorskip 沿用

**WHAT**：embedding 相关测试须用 `pytest.importorskip("sentence_transformers")` 模式（参照 `tests/unit/engines/learn/test_fsrs.py:15` 的 `pytest.importorskip("fsrs")` 先例），使 `pytest tests/` 在无 `[learn]` extra 的 CI 环境下自动跳过，不需 `--ignore`。

**AC-TEST-1**：
- **Given** CI 环境未安装 `[learn]` extra
- **When** `pytest tests/` 执行
- **Then** embedding 相关测试被 skip（status=skipped），不 fail，不需 `--ignore`

**AC-TEST-2**：
- **Given** 本地环境安装了 `[learn]` extra
- **When** `pytest tests/unit/.../test_embedding_*.py` 执行
- **Then** 测试正常运行并 pass

**AC-TEST-3**：
- **Given** CI workflow 文件
- **When** 检查 coverage step
- **Then** coverage 不因 embedding 测试 skip 而下降（沿用既有 `--ignore learn` → `importorskip` 策略，参照 `tests/unit/test_ci_workflow.py:62-70`）

**异常 1**：`sentence_transformers` 安装但模型下载失败——`embed_texts()` 返回 None，测试 mock 模型行为。
**异常 2**：CI workflow 回归——须验证 `test_ci_workflow.py` 中 importorskip 检测逻辑覆盖 embedding 测试文件。

## 4. 非功能需求

| NFR | 指标 | 测量 |
|---|---|---|
| 向量检索 P99 延迟 | [TBD]（须优于或接近 BM25 的毫秒级） | 本地 benchmark |
| 无 `[learn]` extra 时降级 | 自动降级到 BM25，不报错不中断 | tier=LIGHTWEIGHT/OFFLINE 时语义端点回退 |
| 向量索引存储开销 | [TBD]（每 claim/wiki 页面向量大小 × 总量） | 磁盘测量 |
| 既有测试不回归 | ≥1987 passed | pytest CI |
| ruff lint | 0 error | ruff check |
| workspace 隔离 | embedding 索引须遵守 workspace_id 隔离（claim 表已有 `workspace_id` 列，ADR-008/009） | 跨 workspace 查询不泄漏 |

## 5. 数据需求

| 数据 | 来源 | 说明 |
|---|---|---|
| claim 内容 | `claim` 表（`workspace_id` 列已有，migrations.py:290） | embedding 输入文本 |
| wiki 页面内容 | `WikiRepository.read(slug)` | embedding 输入文本 |
| embedding 向量 | `embed_texts()`（`all-MiniLM-L6-v2`，L2-normalized） | 持久化入库 |
| 向量-claim 映射 | Write Queue sink（参照 `fts5_sink.py` 范式） | doc_id → 向量 |
| workspace_id | claim/entity 表已有列（ADR-008/009） | 向量索引须含 workspace 隔离 |

## 6. 验收标准

| AC ID | 描述 | 验证方式 |
|---|---|---|
| AC-EMB-1 | embedding 索引随 ingest 写入 | `[learn]` 已装时 ingest 后向量可查 |
| AC-EMB-2 | 无 `[learn]` 时不报错 | tier=LIGHTWEIGHT 时 ingest 正常 |
| AC-EMB-3 | 存量重建索引 | 重建命令全量扫描 |
| AC-SEM-1 | 语义检索返回同义结果 | `--mode semantic` 召回 BM25 漏的结果 |
| AC-SEM-2 | 无 `[learn]` 降级 BM25 | `semantic_fallback: true` |
| AC-SEM-3 | 空索引优雅处理 | 空结果 + 提示 |
| AC-LINK-1 | suggest 含语义相似页面 | 无共享 tag/link 的语义相似页面出现 |
| AC-LINK-2 | 无 `[learn]` 保持 3-signal | 行为与 v1.8.0 一致 |
| AC-LINK-3 | 语义不相似排名下降 | L1 噪声降低 |
| AC-TEST-1 | CI skip embedding 测试 | `pytest tests/` 无 fail |
| AC-TEST-2 | 本地 embedding 测试 pass | `[learn]` 已装时全绿 |
| AC-TEST-3 | coverage 不回归 | coverage ≥ 既有基线 |

## 7. 排期估算

[TBD]——排期归 04 阶段 WBS/WAVE-PLAN。预期 2-3 Wave（F-EMB-1 索引先行 → F-EMB-2 检索 → F-EMB-3 smart-linking + F-EMB-4 测试并行）。

## 8. 风险与依赖

### 8.1 前置依赖

- **v1.9.0 基线**：已 Released（@246f3d4），1987 passed。
- **用户本地/CI 装 `[learn]` extra**（sentence-transformers，heavy SDK）——硬约定 #12"缺依赖须用户确认"，不擅自安装。本轮 PRD 假定用户已确认安装；未安装时所有功能降级到 BM25，不报错。
- 既有 `src/saw/adapters/embeddings.py`（`embed_texts` / `cosine_similarity` / `cluster_by_embedding`）已可用，本轮扩展其调用方。
- 既有 `config/settings.py::detect_tier()` 已检测 `sentence_transformers` 可用性（FULL tier）。

### 8.2 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| heavy SDK 安装阻力 | 中 | 降级策略：无 `[learn]` 时全功能回退 BM25，用户零感知 |
| 模型下载失败（网络/OOM） | 中 | `embed_texts()` 已有 try/except 返回 None，调用方降级 |
| 向量维度变更（模型升级） | 低 | 索引重建检测维度变更，全量重建 |
| smart-linking 排序回归 | 低 | tier<FULL 时完全保持 3-signal，行为不变 |
| workspace 隔离遗漏 | 中 | 向量索引须含 workspace_id（参照 ADR-008/009 范式） |
| coverage 回归 | 低 | importorskip 跳过的测试不计入 fail |

### 8.3 硬约定

- **#12**：缺依赖须用户确认——不擅自安装 heavy SDK。PRD 假定用户已确认；未确认时降级。

---

## Ground 自源码

| claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|
| sentence-transformers 已有用法（embed_texts/cosine_similarity/cluster_by_embedding） | `src/saw/adapters/embeddings.py:29,41,43` | `embeddings_available()` 检测可用性；`_get_model()` 加载 `SentenceTransformer("all-MiniLM-L6-v2")`；`embed_texts()` 返回 L2-normalized 向量或 None；`cluster_by_embedding()` 用于 Learn 引擎聚类。**未接入 Query 检索路径**。 | TRUE |
| BM25/FTS5 词面检索（FTS5Search.search） | `src/saw/engines/query/search.py:41,60,69,84` | `FTS5Search.search()` 执行 `bm25(fts_index)` 排序；`FTS5Sink`（`src/saw/write_queue/sinks/fts5_sink.py`）通过 Write Queue 写索引。 | TRUE |
| Query engine 无 semantic 模式 | `src/saw/engines/query/engine.py:58,107-120` | `QueryEngine.__init__` 接受 `search: FTS5Search` 等；`query()` 支持 mode: auto/search/graph/compare/tree，**无 semantic**。 | TRUE |
| smart-linking 3-signal 启发式（L1 噪声） | `src/saw/engines/query/related_pages.py:26,35-57` | `compute_related_pages()` 用 shared tags (Jaccard, 权重 2.0) + shared links (Jaccard, 权重 3.0) + type affinity (权重 1.0)。无 embedding 信号。 | TRUE |
| CLI 注册范式（app.command / app.add_typer） | `src/saw/drivers/cli/main.py:78-110` | `app.command(name="search")(search)` / `app.add_typer(links_app, name="links")`。search_cmd 有 `--mode default|tree`。 | TRUE |
| importorskip 测试范式 | `tests/unit/engines/learn/test_fsrs.py:15` | `pytest.importorskip("fsrs")`；CI workflow 检测逻辑在 `tests/unit/test_ci_workflow.py:62-70`。 | TRUE |
| detect_tier FULL 检测 sentence_transformers | `src/saw/config/settings.py:115-120` | `_embeddings_available()` 用 `importlib.import_module("sentence_transformers")` 检测；`detect_tier()` 返回 FULL 当 embeddings 可用。 | TRUE |
| workspace_id 已有（claim 表 migration v8 / entity 表 ADR-009） | `src/saw/db/migrations.py:283-325` | claim 表 `workspace_id` 列（:290-296）+ entity 表 `workspace_id` 列（:319-325）。Query engine 已透传 workspace_id（`engine.py:58,86`）。 | TRUE |
| FTS5Sink Write Queue 范式 | `src/saw/write_queue/sinks/fts5_sink.py:18-40` | `FTS5Sink.write(op)` 通过 `upsert_fts_entry()` 原子 DELETE+INSERT；`can_handle(sink_name)` 匹配。embedding sink 可参照此范式。 | TRUE |

## 下一步建议

1. → **02 分解**：F-EMB-1..4 各拆 Feature + DAG；F-EMB-1（索引）先行，F-EMB-2（检索）依赖 F-EMB-1，F-EMB-3（smart-linking）依赖 F-EMB-1，F-EMB-4（测试）与各 Feature 并行。
2. → **03 技术方案**：向量存储方案（本地 SQLite 生态内 vs 引入向量库）需 ADR；embedding 模型选型（沿用 `all-MiniLM-L6-v2` 或升级）需决策；BM25+semantic 融合策略（并行/加权/RRF）需 Spec。
3. → **04 任务**：预估 3-4 Task，2-3 Wave。
4. **硬约定 #12 确认**：须在 05 实施前确认用户/CI 已装 `[learn]` extra；未装时降级策略须测试覆盖。
