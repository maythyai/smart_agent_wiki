---
id: PRD-semantic-perf-v1.14.0
title: semantic 性能优化
version: 1.0
status: Approved
date: 2026-09-06
product_type: platform
feature_count: 3
mvp_scope: [cache-threshold-config, ann-index, benchmark-update]
thin_sections: [7]
upstream_source: .csp/artifacts/retrospective-v1.13.0.md#R1-R2
roadmap_ref: docs/strategy/ROADMAP.md#v1.14.0
target_version: v1.14.0
related_pms: [.csp/product-spec/PMS-semantic-perf.md]
related_specs:
  - .csp/specs/SPEC-F-S-1.md
  - .csp/specs/SPEC-F-S-2.md
  - .csp/specs/SPEC-F-S-3.md
  - .csp/tech-decisions/ADR/ADR-014-ann-vector-index.md
related_decomposition: .csp/decomposition/DECOMPOSITION-DELTA-v1.14.0.md
---

# PRD: semantic 性能优化

## 1. 背景与目标

### 1.1 背景

v1.13.0 真实 vLLM benchmark 暴露两个性能问题：

1. **R1 — cache 阈值不适配 vLLM 本地**：vLLM `qwen_embedding@8001` 本地响应 37ms（first=41.41ms, second=45.34ms），benchmark 的 cache 命中判定阈值（第 2 次延迟 < 第 1 次 × 50%）未触发——cache hit=false。原因是 vLLM 本地推理极快（37ms），embedding 计算本身是瓶颈而非检索路径，cache 命中与否对延迟差异不显著。cache 机制对**远程 API**（网络延迟 100-500ms）有收益（cache 命中可跳过 API 调用），对**本地 vLLM**（37ms）无收益。

2. **R2 — semantic P99（97.82ms）比 BM25（0.37ms）慢 264×**：semantic 每次查询须调 embedding API + 全量 cosine 排序 O(n)。当前 ≤15 文档规模下 97ms 可接受，但规模增大时 cosine 排序线性增长，不可扩展。

**关键发现（ground 自源码）**：v1.13.0 benchmark 的 cache 命中测量逻辑（`scripts/benchmark_semantic.py:176`，`"hit": lat2 < lat1 * 0.5`）是一个**延迟比较阈值**，不是生产 cache 代码的行为。生产 cache（`src/saw/engines/query/cache.py:48-72`，`get()`/`set()`）是纯 LRU+TTL 缓存——命中即 `get()` 返回非 None，没有"50% 阈值"概念。benchmark 的 `_semantic_search`（`benchmark_semantic.py:126-139`）是独立函数，不经过 `QueryEngine._semantic_search` 的 cache 路径，因此 benchmark 实际未测试生产 cache 行为。

不做会怎样：semantic 检索在生产规模（>1000 文档）下延迟不可接受；cache 在本地 vLLM 部署下是无效写入开销；benchmark 无法准确度量 cache 真实行为。做了会怎样：semantic 从"功能可用"到"生产可扩展"——大规模库不退化、远程 API cache 省钱省时、benchmark 准确度量。

### 1.2 目标用户

| 用户角色 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|
| KW（知识工作者） | 日常查询知识库，期望秒级响应 | 大规模库 semantic 检索不退化 | 查询 1000+ 文档的知识库 |
| DEV（开发者） | 自托管 SAW，配置 embedding API 端点 | cache 行为可按部署形态调整 | 本地 vLLM vs 远程 API 部署 |
| OPS（运维） | 监控检索延迟、API 调用成本 | 可观测 cache 命中率、ANN 切换阈值 | 性能调优、成本优化 |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| ANN 加速大规模检索 | ANN P99 vs cosine P99（≥1k 规模） | ANN P99 < cosine P99 `[TBD]` | benchmark 脚本对比 |
| cache 可配生效 | env 配置 cache 启用/禁用/阈值 | 配置变更后行为可验证 | 单元测试 + benchmark |
| 不回归 | pytest passed | ≥2179 | CI |
| 覆盖率不回归 | coverage | ≥67% | CI fail_under |

## 2. 需求概述

让 semantic 检索在生产规模下可扩展——cache 阈值可按部署形态配置，ANN 索引替代全量 cosine 扫描，benchmark 准确度量 ANN vs cosine 及 cache 真实行为。

## 3. 详细功能设计

### 3.1 cache 阈值可配（R1）

- **描述**：semantic cache 行为从"始终启用"改为"config 驱动"——支持通过环境变量配置 cache 启用/禁用及触发阈值，适配本地 vLLM（快，不需要 cache）与远程 API（慢，cache 有收益）两种部署形态。
- **用户故事**：作为 DEV，我想通过环境变量控制 semantic cache 行为，以便本地 vLLM 部署时禁用 cache（避免无效写入开销），远程 API 部署时启用 cache（省 API 调用）。
- **优先级**：P0
- **业务规则**：
  1. 默认行为不变（cache 始终启用，TTL 300s），确保向后兼容。
  2. 环境变量 `SAW_SEMANTIC_CACHE_ENABLED`：`true`（默认）/ `false`——设为 `false` 时 `_semantic_search` 跳过 cache.get/cache.set，直接执行 embedding + cosine。
  3. 环境变量 `SAW_SEMANTIC_CACHE_THRESHOLD_MS`：整数毫秒——当 embedding API 响应延迟低于此阈值时，cache 写入视为无效开销，跳过 cache.set（cache.get 仍可命中已有缓存）。设为 `0`（默认）表示不设阈值（始终写 cache）。
  4. 可选自适应：当 `SAW_EMBEDDING_API_BASE` 含 `localhost` 或 `127.0.0.1` 时，自动判定为本地部署，默认禁用 cache（可通过 `SAW_SEMANTIC_CACHE_ENABLED=true` 覆盖）。此行为为 `[TBD]`——03 技术方案决定是否实现自适应。
  5. cache 禁用不影响 `_keyword_search` 的 cache 路径（F-QS-07），两个 cache 路径独立控制。
  6. cache 行为变更不改变 `_semantic_search` 的返回值结构（`QueryResult` 不变），仅影响内部 cache 命中/写入路径。
- **交互流程**：入口 `_semantic_search(question)` → 检查 cache 配置 → 若禁用则跳过 cache.get/set，直接 embedding + cosine → 若启用则走既有 cache.get（命中即返回）/ cosine / cache.set 路径 → 返回 `QueryResult`
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 环境变量值非法（非 true/false） | 忽略，回退默认（enabled=true） | 日志 warning |
| cache 配置读取异常 | 不阻断查询，回退默认行为 | 日志 warning |

### 3.2 ANN 索引（R2）

- **描述**：向量检索从全量 cosine O(n) 扫描改为 ANN（近似最近邻）索引，大规模时自动切换 ANN 路径，小规模保持 cosine。ANN 库选型须本地优先、不引入 faiss/torch 等重依赖。
- **用户故事**：作为 KW，我想在 1000+ 文档的知识库中 semantic 检索时延迟不退化，以便大规模库仍可交互级响应。
- **优先级**：P0
- **业务规则**：
  1. 规模阈值 `SAW_ANN_THRESHOLD`：整数，默认 `[TBD]`（03 技术方案定）——当 `embedding_store` 行数超过此阈值时自动切换 ANN 路径；低于阈值保持全量 cosine。
  2. ANN 库选型约束：须纯 Python 或轻量 C 扩展（pip 可装），MIT/Apache 许可；**不引入 faiss（重依赖）/ torch（重依赖）**。候选包括 sqlite-vss（SQLite 扩展）/ hnswlib（pure python, pip, MIT）/ numpy 分块矩阵乘（无新依赖）。具体选型留 03 技术方案 ADR。
  3. ANN 索引在 `rebuild-embeddings` 时构建，随 `embedding_store` 写入增量更新（或重建）。索引生命周期与 embedding_store 一致。
  4. ANN 检索结果与 cosine 排序结果在 top-K 上应一致或近似（ANN 是近似的，允许召回率 ≥95%）。具体精度指标 `[TBD]`。
  5. ANN 路径失败（库未装、索引损坏）时降级到全量 cosine，不报错不中断（`meta.ann_fallback: true`）。
  6. ANN 索引不改变 `embedding_store` 表结构（向量仍 BLOB 存储），索引为附加结构（内存或辅助表）。
  7. `related_pages.py` 的 embedding 相似度计算（`src/saw/engines/query/related_pages.py:70-125`）同样从全量 cosine 改为 ANN——复用同一 ANN 路径，不重复实现。
- **交互流程**：入口 `_semantic_search(question)` → 检查 embedding_store 规模 → 若 > 阈值走 ANN 索引检索 top-K → 若 ≤ 阈值走全量 cosine → 若 ANN 失败降级 cosine → 返回 `QueryResult`
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| ANN 库未安装 | 降级全量 cosine，日志 warning | `meta.ann_fallback: true` |
| ANN 索引损坏/过期 | 降级全量 cosine，触发异步重建 | `meta.ann_fallback: true` |
| ANN 召回率低（top-K 与 cosine 差异大） | 不阻断，返回 ANN 结果 | 日志 warning |

### 3.3 benchmark 更新（R1+R2 度量）

- **描述**：v1.13.0 benchmark 脚本更新——修正 cache 命中测量（改为检测实际 `cache.get()` 返回值，不再用延迟比较 50% 阈值）、增加 ANN vs cosine 延迟对比、增加不同规模（100/500/1000/5000 文档）延迟曲线。
- **用户故事**：作为 OPS，我想 benchmark 准确度量 cache 真实命中率和 ANN vs cosine 延迟曲线，以便性能调优和成本优化。
- **优先级**：P1
- **业务规则**：
  1. cache 命中测量改为直接调用 `QueryEngine._semantic_search`（经过生产 cache 路径），而非独立 `_semantic_search` 函数——度量真实 cache 行为。
  2. cache 命中判定：第 1 次查询后检查 `cache.stats()` 的 `hits` 计数是否增加，第 2 次查询后检查 `hits` 是否再增加——而非延迟比较。
  3. ANN vs cosine 对比：同一数据集分别跑 ANN 路径和 cosine 路径，输出 P99 延迟对比。
  4. 规模延迟曲线：生成 100/500/1000/5000 文档的合成数据集，分别跑 semantic 检索，输出延迟 vs 规模曲线（JSON 格式）。
  5. benchmark 脚本保持 vLLM 可达检查（AC-B-4），不可达报错退出。
  6. benchmark_e2e 测试仍 CI skip（无 vLLM），但 cache 命中测量的单元测试（不依赖 vLLM，用 mock embedding）可在 CI 跑。
- **交互流程**：`python scripts/benchmark_semantic.py --vllm-base http://localhost:8001` → health check → 构建 DB + embedding 索引 → cache 命中率（真实 cache 路径）→ ANN vs cosine P99 → 规模延迟曲线 → JSON 输出
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| vLLM 不可达 | 报错退出（AC-B-4） | stderr 错误消息 |
| ANN 库未装 | cosine-only 结果，ANN 字段标 `null` | JSON 中 `ann: null` |
| 合成数据集生成失败 | 跳过该规模，继续其他 | 日志 warning |

## 4. 非功能要求

| 类别 | 要求 | 验收标准 |
|---|---|---|
| 性能 — ANN 加速 | ANN 检索 P99 优于全量 cosine（规模 ≥1k 时） | benchmark 输出 ANN P99 < cosine P99 @ ≥1k 文档 `[TBD]` |
| 性能 — cache 可配 | env 配置 cache 启用/禁用后行为可验证 | `SAW_SEMANTIC_CACHE_ENABLED=false` 时 cache.stats() 无新增 hit；`=true`（默认）时行为不变 |
| 回归 — 测试 | 2179+ passed 不回归 | CI pytest ≥2179 passed |
| 回归 — 覆盖率 | coverage ≥67% 不回归 | CI fail_under=67 |
| 回归 — lint | ruff 0 | `ruff check src/ tests/ scripts/` 0 errors |
| 依赖约束 | 不引入重依赖 | 不新增 faiss/torch/scikit-learn 等重依赖；ANN 库须 pip 可装、MIT/Apache 许可 |
| 向后兼容 | 默认行为不变 | 不设 env 时行为与 v1.13.0 一致（cache 始终启用 + 全量 cosine） |

## 5. 数据需求

| 事件名 | 触发条件 | 关键属性 | 用途 |
|---|---|---|---|
| semantic_cache_hit | `_semantic_search` cache.get 命中 | `query_hash`, `workspace_id`, `mode=semantic` | 度量 cache 收益 |
| semantic_cache_miss | `_semantic_search` cache.get 未命中 | `query_hash`, `workspace_id`, `mode=semantic` | 度量 cache 覆盖率 |
| semantic_cache_skipped | cache 配置禁用或阈值跳过 | `query_hash`, `reason=disabled\|threshold` | 度量 cache 禁用频率 |
| ann_search_executed | ANN 路径执行 | `doc_count`, `top_k`, `latency_ms` | 度量 ANN 使用率 |
| ann_fallback_triggered | ANN 失败降级 cosine | `reason`, `doc_count` | 度量 ANN 稳定性 |

## 6. 验收标准

### 3.1 cache 阈值可配

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-A-1 | cache 禁用 | `SAW_SEMANTIC_CACHE_ENABLED=false` | 连续两次相同 semantic 查询 | `cache.stats().hits` 不增加（cache 被跳过） |
| AC-A-2 | cache 启用（默认） | 无 env 或 `SAW_SEMANTIC_CACHE_ENABLED=true` | 连续两次相同 semantic 查询 | 第 2 次 `cache.stats().hits` 增加（cache 命中） |
| AC-A-3 | 阈值跳过写入 | `SAW_SEMANTIC_CACHE_THRESHOLD_MS=100`，API 响应 < 100ms | semantic 查询 | cache.get 仍可命中已有缓存，但 cache.set 被跳过（新查询不写入） |
| AC-A-4 | 向后兼容 | 无任何 `SAW_SEMANTIC_CACHE_*` env | semantic 查询 | 行为与 v1.13.0 一致（cache 始终启用） |
| AC-A-5 | keyword cache 不受影响 | `SAW_SEMANTIC_CACHE_ENABLED=false` | 连续两次相同 keyword 查询 | keyword cache 正常命中（`mode=search` 路径不受影响） |

### 3.2 ANN 索引

| ID | 场景 | Given | When | Then | Then |
|---|---|---|---|---|---|
| AC-B-1 | ANN 自动切换 | embedding_store 行数 > `SAW_ANN_THRESHOLD` | semantic 查询 | 走 ANN 路径，`meta` 不含 `ann_fallback` | ANN P99 < cosine P99 @ ≥1k `[TBD]` |
| AC-B-2 | 小规模保持 cosine | embedding_store 行数 ≤ `SAW_ANN_THRESHOLD` | semantic 查询 | 走全量 cosine 路径，`meta` 不含 ANN 标记 | — |
| AC-B-3 | ANN 降级 | ANN 库未安装或索引损坏 | semantic 查询 | 降级全量 cosine，`meta.ann_fallback: true`，不报错 | — |
| AC-B-4 | ANN 召回一致性 | ANN 路径 vs cosine 路径，同一查询 | 比较 top-K 结果 | 召回率 ≥95%（top-K 重叠率）`[TBD]` | — |
| AC-B-5 | related_pages 复用 ANN | `related_pages.py` embedding 相似度计算 | 规模 > 阈值 | 走 ANN 路径，不重复实现 cosine 扫描 | — |

### 3.3 benchmark 更新

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-C-1 | cache 命中真实度量 | benchmark 通过 `QueryEngine._semantic_search` 跑查询 | 检查 `cache.stats()` | 第 2 次查询后 `hits` 增加（非延迟比较） |
| AC-C-2 | ANN vs cosine 对比 | benchmark 构建规模 ≥1k 数据集 | 分别跑 ANN 和 cosine 路径 | JSON 输出含 `ann_p99_ms` 和 `cosine_p99_ms` |
| AC-C-3 | 规模延迟曲线 | benchmark 生成 100/500/1000/5000 文档数据集 | 分别跑 semantic 检索 | JSON 输出含 `scale_curve: [{doc_count, p99_ms}, ...]` |
| AC-C-4 | vLLM 不可达报错 | vLLM endpoint 不可达 | `python scripts/benchmark_semantic.py` | stderr 报错退出（exit code 1），不 mock |
| AC-C-5 | cache 单元测试 CI 可跑 | 不依赖 vLLM，用 mock embedding | CI 跑 cache 命中测试 | 测试 pass（不 skip） |

## 7. 排期估算

| 阶段 | 预估工作量 | 依赖 | 风险 |
|---|---|---|---|
| 02 需求拆解 | `[TBD]` | 本 PRD Approved | — |
| 03 技术方案（含 ANN 库选型 ADR） | `[TBD]` | 02 done | ANN 库选型是关键决策点 |
| 04 任务拆解 | `[TBD]` | 03 done | — |
| 05 实施 | `[TBD]` | 04 done | ANN 索引集成复杂度 |
| 06 发布 | `[TBD]` | 05 done + verify 全绿 | — |

## 8. 风险与依赖

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| ANN 库选型不当（重依赖/不稳定） | Medium | High | 03 技术方案 ADR 对比候选（sqlite-vss / hnswlib / numpy 分块），约束不引 faiss/torch；降级 cosine 兜底 |
| ANN 召回率不足（top-K 与 cosine 差异大） | Low | Medium | 设召回率 ≥95% 验收门槛；不达标时降级 cosine |
| cache 阈值配置语义混乱 | Low | Low | 默认行为不变（向后兼容）；文档明确部署形态推荐值 |
| benchmark 规模数据集生成慢 | Low | Low | 合成数据集用随机向量（不需真实 embedding），仅 P99 测量用真实 vLLM |
| ANN 索引与 embedding_store 增量同步 | Medium | Medium | rebuild-embeddings 全量重建索引；写入时增量更新或标记 dirty |

### 续留 findings（不在本轮处理）

| finding | 维度 | 说明 |
|---|---|---|
| N3/K2 | per-request workspace 注入 | QueryEngine 仍 startup 单例 default workspace；须 v2.0 架构演进 |
| M2 | agent "最近活动"聚合 | roster 静态，需 event bus 聚合 |
| L2 | 链接自动 apply | suggest 只输出不自动改文件 |
| O2 | coverage 余量薄 | 67.27%，fail_under=67，余量 0.27pp |
| O4 | tag 指向 reconcile 非 release commit | 同 v1.11.0-v1.13.0 模式 |

## 附录

### ground 自源码

| claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|
| R1: cache "50% 阈值"在 benchmark 脚本，非生产 cache 代码 | `scripts/benchmark_semantic.py:176` | `"hit": lat2 < lat1 * 0.5` — benchmark 的 cache 命中**测量**逻辑（50% 延迟比较阈值）。生产 cache 无此概念 | TRUE |
| R1: 生产 cache 是纯 LRU+TTL，无阈值/配置 | `src/saw/engines/query/cache.py:22,48-72` | `QueryCache(max_size=1000, default_ttl=300)`，`get()` 返回非 None 即命中。无 env var 控制 | TRUE |
| R1: `_semantic_search` cache.get/set 始终执行 | `src/saw/engines/query/engine.py:493,589` | `_cache.get(question, _cache_params)` / `_cache.set(question, _cache_params, _qr)` — 无条件执行，无 env 判断 | TRUE |
| R1: benchmark `_semantic_search` 不经过生产 cache 路径 | `scripts/benchmark_semantic.py:126-139` | 独立函数，直接调 `embed_texts()` + cosine，不 import `get_cache` | TRUE |
| R2: semantic 检索是全量 cosine O(n) 扫描 | `src/saw/engines/query/engine.py:520,535-536` | `SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = ?` → for 循环 `struct.unpack` + `cosine_similarity` 逐条计算 | TRUE |
| R2: cosine_similarity 是纯 Python dot product | `src/saw/adapters/embeddings.py:237-242` | `dot = sum(x * y for x, y in zip(a, b))` + `math.sqrt(...)` — 无 numpy 向量化 | TRUE |
| R2: embedding_store 无向量索引 | `src/saw/db/migrations.py:339-358` | `vector BLOB NOT NULL`，仅 `idx_embedding_workspace` + `idx_embedding_model` 标量索引，无 ANN/向量索引 | TRUE |
| R2: related_pages 也全量 cosine | `src/saw/engines/query/related_pages.py:70-125` | `SELECT vector, dim FROM embedding_store` → for 循环 `cosine_similarity` — 同 O(n) 模式 | TRUE |
| benchmark P99 测量每次 clear cache | `scripts/benchmark_semantic.py:152` | `cache.clear()` 在 P99 测量循环内——但因 benchmark `_semantic_search` 不用 cache，clear 是 no-op | TRUE |
| cache key 含 mode + workspace_id 隔离 | `src/saw/engines/query/cache.py:34-37` | `_make_key` → SHA256(query + params sort_keys)，params 含 `mode` + `workspace_id` | TRUE |

### 下一步建议

- [ ] 进入需求拆解 → 把 3 个功能模块翻成 Feature 清单 + 依赖图 + NFR，落 `.csp/decomposition/`
- [ ] 进入 03 技术方案（含 ANN 库选型 ADR）→ 读 PRD + decomposition + PMS，对比 sqlite-vss / hnswlib / numpy 分块，选型约束：不引 faiss/torch、pip 可装、MIT/Apache
- [ ] cache 阈值配置项的具体 env var 名最终确认（03 技术方案）
- [ ] ANN 规模阈值 `SAW_ANN_THRESHOLD` 默认值（03 技术方案定，需 benchmark 实测确定 cosine 可接受延迟的拐点）

当前产物：`docs/prd/PRD-semantic-perf-v1.14.0.md`（status: Approved）+ `.csp/product-spec/PMS-semantic-perf.md`（ready）+ `docs/prd/PRD-INDEX.md` 已登记 + `.csp/product-spec/PMS-INDEX.md` 已登记。已写 `.csp/lifecycle-state.json`：01 done，current_stage=02-decomposition。
