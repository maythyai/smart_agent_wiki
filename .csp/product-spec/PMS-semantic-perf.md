# PMS-semantic-perf — 产品模块说明书

> **边界（一句话）**：semantic cache 阈值可配 + ANN 索引替代全量 cosine 扫描 + benchmark 更新（cache 真实度量 + ANN vs cosine 对比 + 规模延迟曲线）。

| 字段 | 值 |
|---|---|
| slug | semantic-perf |
| 边界 | cache 阈值 env 驱动（启用/禁用/触发阈值）+ ANN 索引（规模驱动自动切换，不引 faiss/torch）+ benchmark 修正 cache 度量 + ANN vs cosine + 规模曲线 |
| 优先级 | P0 |
| 关联 PRD | PRD-semantic-perf-v1.14.0 §2 |
| 关联 Spec | SPEC-F-S-1.md, SPEC-F-S-2.md, SPEC-F-S-3.md |
| 关联 ADR | ADR-014-ann-vector-index.md（hnswlib + numpy 批量 cosine 改进） |
| 关联 TMS | TMS-DELTA-v1.14.0.md（15 AC 全映射） |
| 状态 | ready |
| file | PMS-semantic-perf.md |

## 模块范围

- **cache 阈值可配（R1）**：`_semantic_search` 的 cache.get/cache.set 路径增加 env 配置控制——`SAW_SEMANTIC_CACHE_ENABLED`（启用/禁用）、`SAW_SEMANTIC_CACHE_THRESHOLD_MS`（延迟阈值跳过写入）。默认行为不变（向后兼容）。可选自适应：本地部署（api_base 含 localhost）自动禁用 cache `[TBD]`。不影响 `_keyword_search` 的 cache 路径。
- **ANN 索引（R2）**：向量检索从全量 cosine O(n) 改 ANN——规模 > `SAW_ANN_THRESHOLD` 时自动走 ANN，≤ 阈值保持 cosine。ANN 库须 pip 可装、MIT/Apache、不引 faiss/torch。ANN 索引在 rebuild-embeddings 时构建。ANN 失败降级 cosine（`ann_fallback: true`）。`related_pages.py` 复用 ANN 路径。
- **benchmark 更新**：cache 命中测量改为经过 `QueryEngine._semantic_search` 生产 cache 路径（不再用独立函数 + 延迟比较 50% 阈值）；增加 ANN vs cosine P99 对比；增加 100/500/1000/5000 规模延迟曲线。

## 不包含

- ANN 库具体选型（sqlite-vss / hnswlib / numpy 分块——03 技术方案 ADR 决策）。
- embedding provider 变更（沿用 v1.12.0 litellm API，不变）。
- embedding_store 表结构变更（向量仍 BLOB 存储，ANN 索引为附加结构）。
- per-request workspace 注入（N3/K2，续留 v2.0 候选）。
- realtime 仪表盘 / desktop（defer）。
- agent "最近活动"聚合（M2，续留）。
- 链接自动 apply（L2，续留）。

## 降级策略

- ANN 库已装 + 索引可用 + 规模 > 阈值 → 走 ANN 路径（默认大规模路径）。
- ANN 库未装 / 索引损坏 / 规模 ≤ 阈值 → 走全量 cosine（`ann_fallback: true` 或无 ANN 标记），不报错不中断。
- cache 禁用 → 跳过 cache.get/set，直接 embedding + cosine/ANN。
- cache 启用 + 阈值未达 → 正常 cache.get/set。
- cache 启用 + API 响应 < 阈值 → cache.get 可命中已有，cache.set 跳过新写入。

## 关联

- PRD: `docs/prd/PRD-semantic-perf-v1.14.0.md`
- 前身 PRD: `docs/prd/PRD-e2e-tail-v1.13.0.md`（v1.13.0 benchmark 发现 R1/R2）
- 前身 PMS: `.csp/product-spec/PMS-embedding-api.md`（v1.12.0 embedding API 模块，仍有效）+ `.csp/product-spec/PMS-debt-closure.md`（v1.11.0 semantic cache 模块，仍有效）
- 复盘: `.csp/artifacts/retrospective-v1.13.0.md`（findings R1/R2）
- ROADMAP: `docs/strategy/ROADMAP.md#v1.14.0`
