---
id: ROADMAP
project: smart-agent-wiki
version: 1.14
last_updated: 2026-09-18
status: active
tracks: [core-trust, platform-team, ecosystem-integration, intelligence-adaptation]
north_star: trustworthy-claim coverage
version_scheme: SemVer
see_also: docs/strategy/STRATEGY.md | docs/prd/PRD-INDEX.md | docs/analysis/COMPETITIVE-REFERENCE.md | .csp/review/REVIEW-FINDINGS-*.json
---

# Roadmap: Smart Agent Wiki

> 版本号规则权威 + 1 年/3 年/长期路径。只给方向 + 版本主题 + 关键价值，详细 spec 留 01/03。路线图示方向不示日期；排期归任务管理。

## 1. 版本号规则（权威定义，06 release reference 本节）

### 1.1 方案：SemVer（canonical）+ 内部里程碑

采用 **SemVer** `MAJOR.MINOR.PATCH[-pre.N]` 作为**对外发布版本**的唯一规范：

- **MAJOR**：不兼容 API 变更 / 移除已弃用能力 / 范式跃迁。**仅在 06 发布时验证到实际 breaking API 变更才 bump**——新增模块/新端点/新功能是 additive（MINOR），不是 MAJOR，无论战略愿景多宏大。
- **MINOR**：向后兼容的功能新增（对应一个版本主题）
- **PATCH**：向后兼容的 bug 修复
- **pre**：`alpha`（功能未完，内部测）/ `beta`（功能完，公开测）/ `rc`（发布候选）

**理由**：SAW 同时是 pip 可装的 Python 包（被他人依赖，SDK 性质）与桌面/Web 应用——SemVer 对 SDK 的依赖契约最清晰。CalVer 不采用。

### 1.2 既有漂移收口（已完成）

历史存在版本号漂移，自 v1.0.1 起已**收口完成**：

| 载体 | 现状 | 规则 |
|---|---|---|
| `pyproject.toml`（Python 包） | `1.18.1` | **canonical 真源**。最新已发布 = `v1.18.0`（per-request workspace，MINOR）。下一个发布 = `v1.18.1`（fix: AUDIT-F-08/W1 sub-service contextvar + W2 E2E test，PATCH） |
| git tags `v1.0.1` … `v1.9.0` | 全部 SemVer annotated，与 pyproject 一致 | 保留，对外发布基线 |
| git tags `v3.4.0` / `v3.7.0` | 历史 internal sprint 里程碑号 | 重新定性为**内部 milestone label**（见 1.3），不作为对外发布版本；不可变，不移动/删除 |
| `desktop/`（tauri.conf.json + package.json） | `1.0.0` | 桌面端达 1.0，与 canonical 版本对齐 |
| `web/package.json` | `1.0.0` | web 为桌面 bundle，随 desktop 版本（1.0 后对齐） |

> 历史内部 milestone `v3.7` 对应对外 release `v1.2.0`；`v3.8` → `v1.3.0`。此后内部 milestone 进入 v4.x 序列（见 1.3）。

### 1.3 内部里程碑（lifecycle-state 专用，advisory）

`.csp/lifecycle-state.json` 的 `milestone` 字段使用内部里程碑号（当前 `v4.0`），跟踪 sprint 级迭代，**不等于**对外发布版本。内部 milestone 与 SemVer 发布号**内外分离**，避免 sprint 节奏污染 SemVer 契约。

当前映射（advisory，非权威）：

| 内部 milestone | 对外 SemVer | 状态 |
|---|---|---|
| `v3.7` | v1.2.0 | released |
| `v3.8` | v1.3.0 | released |
| `v4.0` | v1.10.0 | released |
| `v4.1` | v1.11.0 | released |
| `v4.2` | v1.12.0 | released |
| `v4.3` | v1.13.0 | released |
| `v4.4` | v1.14.0 | released |
| `v4.5` | v1.15.0 | released |
| `v4.6` | v1.16.0 | released |
| `v4.7` | v1.17.0 | released |
| `v4.8` | v1.18.0 | released (2026-09-07) |

> lifecycle-state `next_cycle: v1.18.0`。v1.17.0 = desktop 完成 v4.4（已 released）；v1.18.0 = per-request workspace 注入 via contextvar + O4 tag 流程修复（additive MINOR，非 MAJOR）。v2.0.0 MAJOR 推迟到真实 breaking。

### 1.4 Tag 规则

- `v` 前缀 + annotated tag（`git tag -a v1.x.0 -m "..."`）
- **不可变**：已推送 tag 不移动/不删除/不改写
- CI 触发：`tags: ['v*']`（06 release 执行）

### 1.5 预发布与质量分级

- **预发布**：`v1.x.0-alpha.1` / `-beta.1` / `-rc.1`
- **pip 预发布渠道**：PyPI 主版本号 + `--pre` 安装预发布；GitHub Releases 标 Pre-release
- **质量分级**：`exploration`（内部探路）→ `insider`（beta 公开测）→ `stable`（正式）

### 1.6 多平台版本一致性

canonical = `pyproject.toml`。发布时以下必须与之一致，用脚本校验禁止人工同步（执行细节见 06「版本与发布规范」）：

- `pyproject.toml` `[project].version`
- `desktop/src-tauri/tauri.conf.json` `version`（1.0 后对齐）
- `web/package.json` `version`
- git tag / GitHub Release tag
- Docker image tag
- Homebrew formula `homebrew/saw.rb`（若涉及）

## 2. 1 年路径（版本序列 + 主题）

> 每版本摘要级。详细 PRD/spec 留 01/03，此处只点明做什么 + 价值。

### v1.0.1 — MVP 可运行基线（status: released）

- **目标**：首个对外正式发布基线，验证"四层存储 + 治理引擎 + 多代理"核心假设可运行。
- **价值描述**：从原型到"能跑"。
- **成功指标**：五引擎冒烟主链路通。

### v1.1.0 — MCP 思考工具 + 前端可用性 + 提取器增强（status: released, @e806d61）

- **目标**：在 v1.0.1 可运行基线上交付首批用户可感知的功能增强，并批量清理 correctness/security/dark-mode 缺陷。
- **关键功能（摘要级）**：MCP 思考工具（F-MCP-01）/ Breadcrumb 导航（F-WEB-08）/ JSON·表格提取器（F-INGEST-03）/ 41 批缺陷收敛。
- **价值描述**：从"能跑"到"好用"的首步。
- **07 回流**：security 修复批次纳入 Wave 1 硬化输入。

### v1.2.0 — 安全/可观测硬化 Wave 1（status: released, 2026-09-03, @532710f）

> 内部 milestone `v3.7`。真正的"产品加固"版本。

- **目标**：建立安全审计与可观测性闭环，使产品达到"安全可审计、运行可观测"基线。
- **关键功能（摘要级）**：Ed25519 receipt 链 / 裸路由检测 / Token 同源校验 / JSON 结构化日志默认 / `/health/ready` engine-aware / 覆盖率基线落 CI。
- **07 回流**：Wave 1 findings 回流至 v1.3.0 硬化尾巴。

### v1.3.0 — 硬化尾巴 + 技术债清理（status: released, @a82f0e3）

> 内部 milestone `v3.8`。承接 Wave 1，完成 Wave 2/3 冒烟链与技术债收口。

- **目标**：完成 Wave 2/3 冒烟，清理技术债，使产品达到"宣称一致、trace 贯穿、CI 有门禁"的完整可用状态。
- **关键功能（摘要级）**：五引擎端到端冒烟基线补全 / 宣称-实现一致性校准（自动 diff）/ Trace 贯穿 / CI 覆盖率门禁 / ruff lint 收口（baseline → 0，F823 真 bug 修）/ roadmap 重写。
- **成功指标**：冒烟 6/6；ruff 0；1874 passed。
- **07 回流**：G1(F401/F841 defer) / G2(coverage 棘轮) / G3(heavy-SDK importorskip) → v1.4.0。

### v1.4.0 — 平台化与团队协作（status: released, @a05d6b7）

> platform-team track。从单机 local-first 走向可自托管的多用户平台。

- **目标**：从单机 local-first 走向可自托管的多用户平台。
- **关键功能（摘要级）**：RBAC 深化（13 用例）/ 团队部署形态（docker-compose.prod + secrets）/ 可观测生产闭环（health/audit）/ workspace 隔离原语（ADR-005, migration v8）/ ruff F401 启用（313 auto-fix）。
- **价值描述**：覆盖团队场景，打开 to-B 路径。
- **07 回流**：H1(F841 defer) / H2(workspace 仅原语级，全路径未做) / H4(Cedar 热加载无端点) / H5(coverage 仍 60) → v1.5.0。

### v1.5.0 — 智能与自适应（status: released, @89b284e）

> intelligence-adaptation track。让知识库自我演进。

- **目标**：代理编排与学习引擎真实落地。
- **关键功能（摘要级）**：多代理 workflow 编排生产级（ADR-006 resume 状态机）/ Learn 引擎（distill/trends）/ Token 优化实测 / agent 角色一致性（ADR-007 workspace scope）/ ruff F841 启用（27 手审）/ query coverage + fail_under 60→63。
- **价值描述**：差异化"会进化的知识库"。
- **07 回流**：I1(workspace 路由仅搜索路径) / I2(coverage 63 未达 65) / I4(policy reload 仅 CLI) → v1.6.0。

### v1.6.0 — 债务收口 II（workspace 读写全路径）（status: released, @62f36cc）

> core-trust track。承接 H2/I1：workspace 隔离从原语层走到全路径。

- **目标**：完成 workspace 读全路径（tree/compile）+ 写隔离（insert/ingest）+ query 深覆盖 + policy Web 端点。
- **关键功能（摘要级）**：ADR-008 workspace 写入 / tree_mode+compiler scope 注入 / insert+ingest 写隔离 / query 子模块深覆盖（engine 14→94% / compare 23→91% / tree 21→66%）/ `POST /api/admin/policy/reload`。
- **成功指标**：1959 passed；workspace 读写双闭环。
- **07 回流**：J1(coverage 65 未达，gap 移至 compile/compiler 17%) / J2(graph_traverse entity 表无 ws 列) / J3(setattr 私有属性耦合) → v1.7.0。

### v1.7.0 — 债务收口 III（graph workspace 隔离）（status: released, @2c4a9d7）

> core-trust track。workspace 三闭环收尾。

- **目标**：graph 隔离 + scope 清理 + coverage 棘轮。
- **关键功能（摘要级）**：ADR-009 entity workspace 隔离（entity 表加 ws 列 + graph 路由注入）/ scope 清理（消除 setattr 私有属性，AC-ARCH-1）/ synthesize 深覆盖（engine 37→65% / scheduler 32→85%，fail_under 63→64）。
- **成功指标**：1977 passed；**workspace 三闭环完成**（读+写+graph 全通）。
- **07 回流**：K1(coverage 65 未达，compile/compiler 17%) / K2(per-request workspace 未做，仍引擎级) / K3(entity_relation JOIN 过滤) → v1.8.0。workspace 故事告一段落，转新能力。

### v1.8.0 — Smart Linking + AI Summarization（status: released, @0ae5149）

> intelligence-adaptation track。转新能力首轮。

- **目标**：智能链接建议 + 链接审计 + AI 摘要。
- **关键功能（摘要级）**：`saw links suggest`（3-signal 启发式相关度，排除已链）/ `saw links audit`（孤儿页 + 断链）/ `saw summarize`（在线 AI 摘要，无 LLM 报错）。复用 query/LLM 引擎，无新引擎。
- **成功指标**：1983 passed；smoke 6/6。
- **07 回流**：L1(suggest 噪声，可加 embedding) / L2(自动 apply 未做) / L3(coverage 未增) → 后续。K1/K2 续留。

### v1.9.0 — Agent & Workflow 可视化（status: released, 2026-09-04, @246f3d4）

> intelligence-adaptation track。续新能力第二轮。

- **目标**：agent 与 workflow 运行态可视化。
- **关键功能（摘要级）**：`saw workflow list`（durable DB 历史）/ `saw agents` roster CLI（6 角色静态）/ `GET /api/v1/agents` REST（JSON）。复用 workflow 基建 + build_default_agents，无新引擎。
- **成功指标**：1987 passed；coverage 64.2%（fail_under=64 持）。
- **07 回流**：M1(embedding 语义搜索 defer，须用户确认装 SDK) / M2(agent "最近活动"未聚合) / M3(CLI list vs REST 语义双重) → v2.0.0。

### v1.10.0 — embedding 语义搜索（status: released, 2026-09-04, @3865c75）

> intelligence-adaptation track。采纳内部候选 v4.2。**additive**——按 1.1 规则发 MINOR，不强行 MAJOR（无 breaking API 变更）。

- **目标**：引入 embedding 语义搜索，从 BM25 词面匹配扩到语义匹配，直接提升 trustworthy-claim coverage 北极星，并解掉 L1(smart-linking suggest 启发式噪声)。
- **关键功能（摘要级）**：
  1. embedding 索引（claim/wiki 页面向量入库，复用 `[learn]` extra 的 sentence-transformers）
  2. 语义检索端点/CLI（query engine 增 semantic 模式，与既有 BM25 并行/融合）
  3. smart-linking suggest 接 embedding 相似度（替代/增强 3-signal 启发式，解 L1）
  4. heavy-SDK 测试 importorskip 模式沿用（distiller/fsrs/trends 已有先例）
- **价值描述**：用户价值——语义查询不再漏同义结果、链接建议更准；业务价值——north-star 杠杆，且让"会进化的知识库"具备语义层。
- **成功指标**：embedding 索引可建；语义检索召回率优于纯 BM25 `[TBD]`；L1 suggest 噪声下降 `[TBD]`。
- **前置依赖**：v1.9.0 基线 + 用户本地/CI 装 `[learn]` extra（sentence-transformers，heavy SDK，硬约定 #12）。
- **07 回流**：M1(embedding defer 解除) + L1(smart-linking 噪声)。K1(coverage 65)/K2(per-request ws) 续留。

> v2.0.0（MAJOR）推迟到出现真实 breaking API 变更/范式跃迁时再 bump；当前 v1.x 序列继续 additive 逼近。

### v1.11.0 — 债务收口 IV / bug fix（status: released, 2026-09-05, @5fca85b）

> core-trust track。采纳 07 复盘"清债/修 bug"候选（内部 milestone v4.1）。**additive**——bug fix + 测试覆盖 + 行为统一，无 breaking API 变更 → MINOR。

- **目标**：收敛 v1.10.0 及累积的可修缺陷（不引入新能力、不需 SDK），把 coverage 棘轮推进到 65，统一既有行为语义。
- **关键功能（摘要级，源自 07 findings）**：
  1. **N7** semantic search 走 query cache（复用 F-QS-07 cache 路径，query-text→embedding→results，TTL + 索引变更失效）——修 v1.10.0 新引入的 perf bug
  2. **N2/K1** compile/compiler.py 17% → 深覆盖（拖 6 轮的最后 coverage 洼地），fail_under 64→65
  3. **M3** CLI `saw workflow list` vs REST `/workflows` 语义双重——统一 REST 读 DB（merge live + durable）消歧
  4. **N5** SPEC-F-N-1 命令名回更（`saw rebuild-embeddings` 实现偏离 Spec，回更 Spec）
  5. **N6** tag hash 一致性复核（ROADMAP/lifecycle = @3865c75）
- **价值描述**：用户价值——semantic 重复查询变快、workflow list 语义一致；业务价值——coverage 65 北极星达成，技术债收敛。
- **成功指标**：semantic cache 命中率 `[TBD]`；coverage ≥65%（fail_under 65）；REST/CLI workflow 语义一致；1993+ passed；ruff 0。
- **前置依赖**：v1.10.0 基线。**不需** `[learn]` extra（N1/N4 embedding E2E/benchmark 续留，须用户装 SDK）。
- **07 回流**：N7 + N2/K1 + M3 + N5 + N6。续留：N1(embedding E2E) / N3(K2 per-request ws) / N4(benchmark) / M2 / L2。

### v1.12.0 — embedding 改用 OpenAI 风格 API + E2E 验证（status: released, 2026-09-05, @50fc8e8）

> intelligence-adaptation track。**用户决策 pivot**：不跑本地重 ML 服务（torch/sentence-transformers 本地模型——会打死 runner 且非生产形态），embedding 改用 **OpenAI 风格 API**（litellm，与既有 LLM 调用同范式）。闭合 v1.10.0 N1（High/P1）。**additive**——换 provider + E2E 验证 + benchmark，无 breaking → MINOR。

- **目标**：把 `embeddings.py::embed_texts()` 的 provider 从本地 `SentenceTransformer` 重构为 litellm OpenAI 风格 embedding API（`litellm.embedding`/`aembedding`，模型可配置如 `text-embedding-3-small`/`bge` 类），去掉本地 torch 重依赖，E2E 用 API mock 验证（不再 importorskip、不再打死 runner），并 benchmark semantic vs BM25（闭合 N1 + N4）。
- **关键功能（摘要级）**：
  1. `embeddings.py` provider 重构：litellm.embedding API 替代本地 SentenceTransformer（base_url/api_key/model 走 config，复用 LLM 同套 env）
  2. embedding 维度可配置（API 模型 dim 如 1536 ≠ 本地 384），embedding_store dim 列驱动，索引重建检测维度变更
  3. 本地 ST 降级为**可选 fallback**（`[learn]` extra 仍可装，但默认走 API；不装 ST 不影响功能）
  4. v1.10.0 的 7 个 importorskip 测试改为 API mock 测（不依赖本地 SDK，CI 可跑）+ 真实 API key 可选 E2E
  5. benchmark：semantic vs BM25 召回 + P99（API embedding）
- **价值描述**：embedding 从"本地重 SDK、未验证"到"API 轻接入、E2E 实测通过"，真正可上线——生产部署不依赖本地 torch/模型下载。
- **成功指标**：embedding 测试全 pass（API mock，不 skip）；semantic 召回优于 BM25；P99 优于或接近 BM25 `[TBD]`；2064+ passed 不回归；ruff 0；**无本地 torch 加载**（runner 稳定）。
- **前置依赖**：v1.11.0 基线 + litellm（已在依赖）。**不要求**本地 sentence-transformers。
- **07 回流**：N1(embedding E2E) + N4(benchmark)。续留：N3(K2) / M2 / L2 / O1-O4。

### v1.13.0 — E2E 收尾轮（status: released, 2026-09-06, @779d6cb）

> core-trust track。内部 milestone `v4.3`。**additive**——ingest fix + benchmark script + REST alias + coverage ratchet + retrospective closure，无 breaking → MINOR。

- **目标**：闭合 v1.12.0 embedding E2E 尾巴——修 ingest 目录递归、跑真实 vLLM benchmark、REST 兼容 alias + CHANGELOG、coverage 棘轮 67%、Q1/Q3 复盘闭环。
- **关键功能（摘要级）**：
  1. **F-R-1** `saw ingest <dir>` 目录递归（os.walk，不再报 "Is a directory"）
  2. **F-R-2** `scripts/benchmark_semantic.py` 真实 vLLM benchmark（semantic vs BM25 recall + P99 + cache hit，≤9 items）
  3. **F-R-3** REST `GET /api/v1/workflows` 加 `name`/`workflow` alias 字段 + 根 CHANGELOG.md
  4. **F-R-4** coverage fail_under 65→67（+75 supplementary tests，linter/code_wiki/concept_graph/archiver/feedback）
  5. **F-R-5** Q1(real API E2E verified) / Q3(ST fallback removed, API-only) 闭环
- **成功指标**：2179 passed；coverage 67.27%；smoke 6/6；semantic recall 5.0 vs BM25 0.0（vLLM qwen_embedding 在线）；ruff 0。
- **前置依赖**：v1.12.0 基线。
- **07 回流**：Q1/Q3 清掉。续留：N3/M2/L2 + O1/O2/O3/O4 + cache hit timing flakiness (new)。

### v1.14.0 — semantic 性能优化（status: released, 2026-09-06, @136befe）

> intelligence-adaptation track。承接 v1.13.0 benchmark 发现（R1 cache 阈值不适配 + R2 semantic P99 97ms 慢）。**additive**——cache 可配 + ANN 加速，无 breaking → MINOR。

- **目标**：让 semantic 检索在生产规模下可扩展——cache 对远程 API 有收益、ANN 索引加速向量检索，闭合 R1/R2。
- **关键功能（摘要级，源自 v1.13.0 复盘 findings）**：
  1. **R1 cache 阈值可配**：semantic cache 命中阈值（当前 50%）改为 config 驱动（`SAW_SEMANTIC_CACHE_THRESHOLD_MS`），远程 API 慢时启用、本地 vLLM 快时关闭或低阈值；cache 仅对语义结果（query-text→embedding→results）生效
  2. **R2 ANN 索引**：向量检索从全量 cosine（O(n)）改 ANN——候选 sqlite-vss（SQLite 扩展）/ hnswlib（pure python, pip, MIT）/ numpy 分块；本地优先 + 可选 ext。规模 >N 时自动走 ANN，小规模保持 cosine
  3. benchmark 更新：v1.13.0 脚本加 ANN vs cosine 对比 + 不同规模延迟曲线
- **价值描述**：用户价值——大规模库 semantic 检索不退化、远程 API cache 省钱省时；业务价值——semantic 从"功能可用"到"生产可扩展"。
- **成功指标**：ANN 检索 P99 优于全量 cosine（规模 ≥1k 时）`[TBD]`；cache 阈值可配生效；2179+ passed 不回归；ruff 0；coverage ≥67。
- **前置依赖**：v1.13.0 基线 + vLLM qwen_embedding（benchmark 项需）。
- **07 回流**：R1(cache 阈值) + R2(ANN)。续留：N3/M2/L2/O4 + 后续 v1.15-1.17/v2.0 候选。



### v1.15.0 — agent/link 能力（status: released, 2026-09-06, @d5b644f）

> intelligence-adaptation track。承接近续留 findings（M2/L2 + v1.5.0 留候选）。**additive**——新能力，无 breaking → MINOR。

- **目标**：补齐 agent 自定义 + 链接自动化 + 活动可观测，让多代理协作与知识链接更完整。
- **关键功能（摘要级）**：
  1. **自定义 agent 角色注册**（v1.5.0 留 v2.0 候选）：用户注册自定义 agent 角色（name/model_tier/tools 配置），`build_default_agents` 之外可扩展
  2. **L2 links auto-apply**：`saw links apply <page> --suggestion` 自动插入 `[[link]]`（须用户确认，破坏性）
  3. **M2 agent 活动聚合**：event bus 聚合 workflow_step 事件，`GET /api/v1/agents/{name}/activity` 返回最近活动/调用次数
- **价值描述**：用户价值——自定义角色适配领域、链接一键应用、agent 活动可观测；业务价值——多代理协作闭环。
- **成功指标**：自定义角色可注册+调用；links apply 插入正确；agent activity 端点返回聚合；2192+ passed 不回归；ruff 0。
- **前置依赖**：v1.14.0 基线。
- **07 回流**：M2(agent 活动聚合) + L2(links apply) + 自定义角色。续留：N3(K2)/O2/R3/S1-S4。

### v1.16.0 — realtime 仪表盘 v4.3（status: released, 2026-09-07, @57b9550）

> ecosystem-integration track。前端可视化，承接 v1.15.0 后端 activity 聚合。**additive**——新前端能力，无 breaking → MINOR。

- **目标**：agent/workflow 运行态实时可视化——前端仪表盘展示 agent roster + activity + workflow 执行状态，实时更新。
- **关键功能（摘要级）**：
  1. 仪表盘页（web/src 新路由）：agent roster 表 + 每 agent 活动计数/最近调用（接 `GET /api/v1/agents` + `/api/v1/agents/{name}/activity`）
  2. workflow 运行态视图（接 `/workflows` durable + live merge）：最近执行列表 + 状态（running/done/failed）+ 步骤进度
  3. 实时更新（SSE 或 polling）：agent activity + workflow 状态变化实时推送/刷新
- **价值描述**：用户价值——运维可观测 agent/workflow 运行态；业务价值——从 CLI 静态查到前端实时看板。
- **成功指标**：仪表盘页可访问 + 显示 roster/activity/workflows；实时更新生效；web vitest 通过；2220+ 后端测试不回归。
- **前置依赖**：v1.15.0 基线（后端 activity + workflow REST 就绪）。
- **07 回流**：M3(CLI vs REST 语义双重，v1.11.0 已清 REST 读 DB) + realtime 可视化。续留：N3/S1-S4/T1-T4。

### v1.17.0 — desktop 完成 v4.4（status: released, 2026-09-07, @e391611）

> ecosystem-integration track。Tauri 桌面端 0.1.0→1.0，集成 v1.16.0 web 仪表盘。**additive**——桌面端独立 0.x→1.0，无后端 breaking → MINOR（pyproject），desktop 自身 0.1.0→1.0.0。

- **目标**：桌面端达 1.0——Tauri build 可产出原生包，集成 web 仪表盘（load web/dist），与后端 API 协同。
- **关键功能（摘要级）**：
  1. desktop 版本 0.1.0→1.0.0（package.json + tauri.conf.json）+ tauri.conf 配置收敛
  2. web 仪表盘集成（desktop 加载 web/dist，dev/prod 模式）
  3. tauri build 验证（`tauri build` 产出原生包，至少 mac .app）
  4. desktop 与后端协同（dev proxy + prod 嵌入 saw server 或独立）
- **价值描述**：用户价值——桌面原生应用一键启动；业务价值——desktop 达 1.0，覆盖非 CLI 用户。
- **成功指标**：`tauri build` 成功产出包；desktop 1.0.0；web 仪表盘在 desktop 内可访问；后端测试不回归。
- **前置依赖**：v1.16.0 基线（web 仪表盘就绪）+ Rust 工具链（已装）。
- **07 回流**：desktop v4.4。续留：N3/S/T/U 续留 + v2.0 per-request ws。

> v1.14.0 周期闭环 2026-09-06（07-retro done，retrospective-v1.14.0.md）。v1.15.0 周期闭环 2026-09-06（07-retro done，retrospective-v1.15.0.md）。v1.16.0 周期闭环 2026-09-07（07-retro done，retrospective-v1.16.0.md）。v1.17.0 周期闭环 2026-09-07（07-retro done，retrospective-v1.17.0.md：.dmg unsigned defer / 仅 mac aarch64 / sidecar defer v2.0+）。以下为候选主题，**不定论**，供下一轮 01 PRD 决策。

> **v2.0.0 MAJOR 判断**（07 复盘结论）：per-request workspace 注入若用 contextvar（不改公开 API）→ additive → 应发 **v1.18.0 MINOR**，非 MAJOR；只有引入不兼容 API（QueryEngine 构造签名改/移除 deprecated）才 v2.0.0 MAJOR。诚实按 SemVer，不强行 MAJOR。v2.0.0 MAJOR 推迟到真实 breaking。

| 候选 | findings 关联 | 说明 |
|---|---|---|
| **v1.17.0 desktop 完成（v4.4 Tauri→1.0）** | U4 | 桌面端达 v1.0，与 canonical 版本对齐 |
| v2.0 per-request workspace 注入 | N3/K2 续留 | web 路径请求级 workspace 隔离（v2.0 架构演进候选） |
| agent activity 持久化 | T1 | DB 持久化 agent 活动日志（v2.0 候选，当前内存态满足 PRD） |
| links apply undo/rollback | T2 | git stash 提示或 `--rollback` 标志 |
| 自定义角色分享/导入 | T3 | `saw agents export/import` 命令或角色仓库 |
| benchmark scale_curve 修复 + ANN 大规模实证 | S1/S2 | 修复合成向量维度不匹配（384→1024dim）+ 跑 ≥500 规模验证 ANN 优势 |
| COVERAGE-REPORT 状态更新 | S3 | 将 [TBD-impl] 更新为 covered，更新全局汇总 AC 数 |
| engine.py 拆分 | S4 | 提取 semantic_search 子模块，god-file 858/900 行 |
| Playwright 浏览器冒烟 | U1 | 加 Playwright E2E 验证 dashboard 真实集成 |
| polling interval 可配 | U2 | 加环境变量 `VITE_POLL_INTERVAL_MS` 允许用户自定义 |
| per-request WS 推送 activity | U2 + N3/K2 | activity 计数实时推送（非 polling），v2.0 候选 |

续留 findings（跨迭代 backlog）：N3/K2(per-request ws) / O2(coverage 余量薄 67.42%, fail_under=67) / O4(tag 指向 reconcile 非 release commit) / R3(benchmark CI skip) + S1(ANN 小规模慢) / S2(scale_curve 维度不匹配) / S3(COVERAGE-REPORT 状态未更新) / S4(engine.py god-file 膨胀) + T1(agent activity 不持久化) / T2(links apply 无 undo) / T3(自定义角色无分享机制) / T4(agents_cmd CLI 结构变更) + U1(视觉 E2E 未跑 Playwright) / U2(polling 15s 延迟非真正实时) / U3(4 vLLM-unreachable test skip) / U5(vitest 测试路径偏离 SPEC) / U6(ConnectionStatus 降级横幅位置偏离 SPEC)。v1.17.0 清掉 U4(desktop 0.1.0→1.0.0)。

### 竞品借鉴候选（Phase 0.5，详见 `docs/analysis/COMPETITIVE-REFERENCE.md`）

> 2026-09-09 外环 roadmap Phase 0.5 产出。deep-read 6 个同类开源项目（WeKnora/Khoj/GraphRAG/Cognee/Letta/Potpie，clone 于 `开源项目参考/`）后提炼。**候选非定论**，供下一轮 01 PRD 决策。版本号按 SemVer 增量续编（additive=MINOR）。借鉴方向 = **强化 SAW 护城河（溯源+治理+数据主权）**，非堆 feature。

**差异化判断**：6 个竞品各做 SAW 的一部分，无一同时覆盖溯源+治理+数据主权。SAW 不被吞的护城河 = 这三者耦合。

| 版本 | Track | 候选主题（来源） |
|---|---|---|
| **v1.20.0** | core-trust + ecosystem | B1 `contradicts` 矛盾边+置信(Cognee) / B2 `memory_rethink` 矛盾重评(Letta) / A1 agent 自蒸馏自维护 Wiki(WeKnora) / C1 `saw_resolve` 任务级上下文(Potpie) / C2 `saw_record` 持久学习(Potpie) / **C3 coding-harness skills 包**(Potpie——直接填补已删 phase-29 的真实需求，轻量 skills 而非 in-product phase) |
| **v1.21.0** | intelligence + platform | A2 层次社区检测+社区报告(GraphRAG) / A3 DRIFT 混合检索(GraphRAG) / B3 claim TRUE/FALSE/SUSPECTED 状态轴(GraphRAG) / C4 Agent File 便携角色格式(Letta，闭合 backlog T3) / D1 Langfuse 式 trace(WeKnora) |
| **v1.22.0** | intelligence + ecosystem | A4 深度研究模式(Khoj) / A5 调度自动化(Khoj) / C5 IM serving+Obsidian 插件(Khoj/WeKnora) / D2 Write Queue 运维 dashboard(WeKnora) |
| **v1.23.0** | core-trust + ecosystem | B4 FastGraphRAG NLP 降本层(GraphRAG) / B5 provenance+auto-feedback(Cognee) / C6 skill sandbox 执行(WeKnora) / D3 heartbeat 主动巡检(Letta) |

**不借鉴（聚焦代价）**：Khoj 云托管/图像生成/voice（偏离 local-first 与编译定位）；WeKnora 腾讯生态强绑定（厂商锁定）；GraphRAG 全 LLM 抽取作唯一路径（成本高，SAW 采 NLP+LLM 分层）；Letta OS 虚拟内存全套（SAW 已有四层存储+Write Queue）。AGPL(Khoj) 仅借鉴思路不引代码。

### 版本-主题表（1 年）

| 版本 | 主题 | Track | status |
|---|---|---|---|
| v1.0.1 | MVP 可运行基线 | core-trust | released |
| v1.1.0 | MCP 思考工具 + 前端可用性 + 提取器增强 | core-trust | released |
| v1.2.0 | 安全/可观测硬化（Wave 1） | core-trust | released (2026-09-03) |
| v1.3.0 | 硬化尾巴 + 技术债清理 | core-trust | released |
| v1.4.0 | 平台化与团队协作 | platform-team | released |
| v1.5.0 | 智能与自适应 | intelligence-adaptation | released |
| v1.6.0 | 债务收口 II（workspace 读写全路径） | core-trust | released |
| v1.7.0 | 债务收口 III（graph workspace 隔离） | core-trust | released |
| v1.8.0 | Smart Linking + AI Summarization | intelligence-adaptation | released |
| v1.9.0 | Agent & Workflow 可视化 | intelligence-adaptation | released (2026-09-04) |
| v1.10.0 | embedding 语义搜索 | intelligence-adaptation | released (2026-09-04) |
| v1.11.0 | 债务收口 IV / bug fix（N7 cache + K1 coverage + M3 + N5/N6） | core-trust | released (2026-09-05) |
| v1.12.0 | embedding 改用 OpenAI 风格 API + E2E 验证（闭合 N1/N4） | intelligence-adaptation | released (2026-09-05) |
| v1.13.0 | E2E 收尾轮（ingest recursion + benchmark + REST alias + coverage 67 + Q1/Q3 closure） | core-trust | released (2026-09-06) |
| v1.14.0 | semantic 性能优化（R1 cache 阈值可配 + R2 ANN 索引） | intelligence-adaptation | released (2026-09-06) |
| v1.15.0 | agent/link 能力（自定义 agent 角色 + L2 links apply + M2 活动聚合） | intelligence-adaptation | released (2026-09-06) |
| v1.16.0 | realtime 仪表盘 v4.3（agent/workflow 运行态前端可视化） | ecosystem-integration | released (2026-09-07) |
| v1.17.0 | desktop 完成 v4.4（Tauri→1.0 + 集成 web 仪表盘） | ecosystem-integration | released (2026-09-07, @e391611) |
| v1.18.0 | per-request workspace 注入 + O4 tag 流程 | platform-team | released (2026-09-07, @e4cf22d) |
| v1.18.1 | fix: AUDIT-F-08/W1 sub-service contextvar + W2 E2E test | platform-team | planned (audit 2026-09-08) |
| v1.19.0 | production hardening: links rollback / agents export-import / activity-routing fix / T4 decouple / S4 engine.py split / CLI+govern tests | core-trust+ecosystem | shipped (2026-09-09) |
| v1.20.0 | C3 coding-harness skills package (.claude/skills/saw-tools) + AUDIT-F-04 coverage tests (lint/search/freshness/verify functional) | core-trust+ecosystem | shipped (2026-09-09) |
| v1.21.0 | B1 contradicts 矛盾边+置信（4级置信双claim+receipt列+图边暴露+saw_conflicts 修复）| core-trust | shipped (2026-09-09) |
| v1.22.0 | C1 saw_resolve + C2 saw_record (agent-native MCP 原语: task context + durable record) | core-trust+ecosystem | shipped (2026-09-09) |
| v1.23.0 | A1 saw_wiki_distill (agent 自维护 Wiki) / B2 rethink_contradiction (memory_rethink) / saw_resolve 语义升级 | core-trust+ecosystem | shipped (2026-09-09) |
| v1.24.0 | A2 saw_communities/community_of (Louvain) + D1 langfuse_span (env-gated) / C4 Agent File (done v1.19.0) | intelligence+platform | shipped (2026-09-09) |
| v1.25.0 | A3 saw_drift_search (DRIFT hybrid) + B3 ClaimStatus (TRUE/FALSE/SUSPECTED) | intelligence+platform | shipped (2026-09-09) |
| v1.26.0 | B4 saw_nlp_keywords (NLP 降本) + B5 saw_record_feedback (auto-feedback) + D3 HeartbeatScheduler (heartbeat 巡检) | core-trust+ecosystem | shipped (2026-09-09) |
| v1.27.0 | D2 Write Queue 运维 dashboard + A5 调度自动化（复用 D3 apscheduler 周期 Scholar/Guardian 任务）| ecosystem-integration | shipped (2026-09-16) |
| v1.28.0 | C5a Obsidian 插件（触达 KW 用户：只读 sync+chat）+ i18n 基建（prompt/CLI EN 选项）| ecosystem-integration | shipped (2026-09-16) |
| v1.29.0 | core-trust+perf 硬化：coverage→70%+（AUDIT-F-04 续）+ thin CLI 功能测试 | core-trust | shipped (2026-09-16) |
| v1.30.0 | A4 深度研究模式（Scholar 编排 web+claims→可溯源报告）+ C5b IM serving（webhook 起步）| intelligence-adaptation | shipped (2026-09-16) |
| v1.30.1 | fix: audit 快速修复批（AUDIT-F-02 MCP 工具数断言 / F-07 nav / F-09 死按钮 aria / F-10 graph 空态）| core-trust | shipped (2026-09-18) |
| v1.31.0 | Provenance Verification API + Activity 持久化 + wiki 索引 YAML 韧性（AUDIT-F-03 折入）| core-trust | planned |
| v1.32.0 | Compliance & Audit Tier（Ed25519 receipt 导出 + 数据驻留 + 删除传播）| platform-team | planned |
| v1.33.0 | Playwright E2E + Desktop 签名/跨平台（AUDIT-F-07/V1/V2 闭合）| ecosystem-integration | planned |
| v1.34.0 | ANN ≥5000 实证 + coverage 72% + Write Queue 压测（S1/S2/O2）| core-trust | planned |
| v1.35.0 | Structured Context API v1（统一 vector+graph+ontology+state，★品类定位）| intelligence-adaptation | planned |
| v1.36.0 | Incremental Graph + Logical-Symbolic Reasoning（借鉴 LightRAG/KAG 差异化）| intelligence-adaptation | planned |
| v1.37.0 | Claim Exchange Format v0（联邦互操作种子，借鉴 COGX 差异化）| ecosystem-integration | planned |
| v1.38.0 | Multi-Agent Orchestration + Sleeptime（借鉴 Letta/EverOS 差异化）| intelligence-adaptation | planned |
| v1.39.0 | RBAC 深化 + 多租户生产级（4 级 + 配额 + SSO/OIDC）| platform-team | planned |
| v1.40.0 | Plugin Marketplace v1（registry + SDK v1 + connector framework）| ecosystem-integration | planned |
| v1.41.0 | Skill Sandbox 执行（C6 闭合，Docker/E2B）| ecosystem-integration | planned |
| v1.42.0 | IM Serving 全链路 + Obsidian/Logseq 深集成（C5 续）| ecosystem-integration | planned |
| v1.43.0 | Coding-Harness 全平台 + Governed Code Intelligence（vs CodeGraph/Graphify）| ecosystem-integration | planned |
| v1.44.0 | Token Optimizer 产品化（成本层，OpenClaw/$47k 痛点）| intelligence-adaptation | planned |
| v1.45.0 | Deep Research v2 + Web Grounding（A4 续）| intelligence-adaptation | planned |
| v1.46.0 | Agent Self-Evolution + Dreaming（借鉴 Dreaming V3/EverOS 差异化）| intelligence-adaptation | planned |
| v1.47.0 | Observability v2（Langfuse-grade + W3C traceparent + A2A）| platform-team | planned |
| v1.48.0 | Federated Knowledge Graph v0（跨实例联邦，v3.0 seed）| ecosystem-integration | planned |
| v1.49.0 | Pre-v2.0 硬化 + 迁移工具 + property/fuzz 基建 | core-trust | planned |
| v1.50.0 | v2.0 RC + 统一 Context API freeze | intelligence-adaptation | planned |
| v2.0.0 | 平台化 MAJOR（仅真实 breaking API 变更才 bump）| platform-team | planned |
| v2.1.0 | Post-2.0 生态扩展（marketplace v2 + 多语言 SDK + 连接器长尾）| ecosystem-integration | planned |
| v2.2.0 | 联邦生产化 + claim 互操作标准提案外部化 | ecosystem-integration | planned |
| v2.3.0 | Governance-as-a-Service（治理层 sidecar 可嵌入外部 RAG）| platform-team | planned |
| v2.4.0 | 多模态编译（image/audio/video/table→claim 锚定原文位置）| intelligence-adaptation | planned |
| v2.5.0 | Agent Skill 市场与分享（skill exchange format，携带 provenance）| ecosystem-integration | planned |
| v2.6.0 | 自治知识体（Guardian 全自动 expire/晋升/矛盾仲裁闭环）| core-trust | planned |
| v2.7.0 | 联邦信任网络（跨实例 trust scoring + receipt notarization 共识）| ecosystem-integration | planned |
| v2.8.0 | 知识图谱标准提案（claim graph schema 开放标准草案 v1）| core-trust | planned |
| v3.0.0 | 生态/开放 MAJOR（范式跃迁，仅真实 breaking 才 bump）| ecosystem-integration | planned |
| v3.1.0 | 行业垂直合规包（医疗/金融/法律 ontology + 审计模板）| platform-team | planned |
| v3.2.0 | 边缘部署（离线自治 + 按需联邦，弱网/断网可用）| ecosystem-integration | planned |
| v3.3.0 | 知识资产经济（claim attribution/许可/计费，可信知识可交易）| ecosystem-integration | planned |

### v1.18.0 — per-request workspace 注入 + O4 tag 流程（status: released, 2026-09-07, @e4cf22d）

> platform-team track。闭合 N3/K2 + O4（最后的 backlog 项）。**additive**——contextvar 注入不改公开 API 契约，MINOR（非 MAJOR）。

- **目标**：web 多租户路径支持 per-request workspace 隔离（contextvar 注入 QueryEngine 内部读，构造签名不变）+ 修复 O4 tag 流程（06 tag release commit 非 reconcile）。
- **关键功能（摘要级）**：
  1. **per-request workspace 注入**（N3/K2）：contextvar 持有 workspace_id，QueryEngine 内部读（fallback 默认），web 中间件 per-request 设 contextvar；REST `/workflows`/`/agents` 等读 DB 时自动按当前请求 workspace 隔离；构造签名不变（additive）
  2. **O4 tag 流程修复**：06 release-manager 改 tag release commit（非 reconcile commit），确保 `git tag -l vX.Y.Z` 指向 release artifacts
- **价值描述**：用户价值——多租户 web 部署时请求级 workspace 隔离；业务价值——N3/K2 闭合，per-request 架构债清零。
- **成功指标**：contextvar 注入生效；多租户 web 测试跨 workspace 不泄漏；06 tag 指向 release commit；2267+ passed 不回归；ruff 0。
- **前置依赖**：v1.17.0 基线。
- **07 回流**：N3(K2 per-request ws) + O4(tag 流程)。续留：V1-V3(desktop 签名/跨平台/sidecar 后续专项) + S/T/U 续留 P3 defers。

## 下一年路径 v1.27.0+（竞品借鉴近尾声，新战略主题，按四 track 逼近 v2.0）

> 竞品借鉴 18 项已 ship 13；剩余多为基建型（C6 sandbox 需 Docker、C5 IM 需 SDK、A4 需 web search）。v1.27+ 转向**四 track 均衡推进** + 把 deferred gate 项变可执行，向 v2.0 平台化逼近。每版本摘要级（详细 spec 留 01/03）。

### v1.27.0 — 运维 dashboard + 调度自动化（ecosystem-integration track）— status: shipped
- 实际 SemVer：v1.27.0（additive=MINOR）
- 目标：让 Write Queue 运维态可观测 + agent 任务可周期化，平台化基建。
- 关键功能：D2 Write Queue 运维 dashboard endpoint（队列深度/背压/失败重试/死信可视化，复用既有 dispatcher metrics）；A5 调度自动化（复用 D3 apscheduler——Scholar/Guardian 周期任务，用户可配 cron）。
- 价值：运维可见（不再黑盒队列）+ 主动巡检自动化（D3 心跳的扩展到任意 agent 任务）。
- 成功指标：dashboard endpoint 覆盖核心运维指标 `[TBD]`；A5 跑 ≥1 周期任务无回归。
- 前置依赖：v1.26.0（D3 HeartbeatScheduler 复用）。

### v1.28.0 — Obsidian 插件 + i18n 基建（ecosystem-integration track）— status: shipped
- 目标：触达 SAW 的核心 KW 用户（Obsidian/Logseq 用户）+ 全球化基础。
- 关键功能：C5a Obsidian 插件（只读 sync：SAW claims→Obsidian notes + chat 查询入口）；i18n 基建（抽取 CLI/prompt 硬编码中文字符串，EN 选项 env-gated）。
- 价值：降低 KW 用户上手门槛（Obsidian 是 SAW 定位人群的 PKM hub）+ 为 v2.0 全球化铺路。
- 成功指标：Obsidian 插件 MVP 可 sync + query `[TBD]`；i18n 覆盖 CLI 命令 help。
- 前置依赖：v1.27.0。

### v1.29.0 — core-trust + 性能硬化（core-trust track）— status: shipped
- 目标：把质量门从踩线（cov 68%/gate 67）推到安全区 + 验证大规模。
- 关键功能：coverage→70%+（补 compile/feed/learn/review CLI 功能测试——AUDIT-F-04 续）；规模性能（ANN hnswlib ≥500 规模实证 benchmark / Write Queue 吞吞吐压 + DLQ 压测）。
- 价值：CI 门不再踩线（少几行测试即跌破的风险消除）+ 给 v2.0 多租户规模背书。
- 成功指标：coverage ≥70%；ANN ≥500 规模 benchmark P95 `[TBD]`。
- 前置依赖：v1.28.0。

### v1.30.0 — 深度研究 + IM serving（intelligence-adaptation track）— status: shipped
- 目标：把 Scholar 从"单步检索"升到"多步研究"+ 让 SAW 经 IM 被 agent 生态调用。
- 关键功能：A4 深度研究模式（Scholar 编排 web 搜索 + 库内 claims→可溯源研究报告，结论锚定可信 claims）；C5b IM serving（webhook 起步——经通用 webhook serve Q&A，后续接飞书/Slack SDK）。
- 价值：产品化"深度研究"（Khoj 同赛道功能 SAW 差异化：结论锚定库内可信 claims）+ agent 生态后端入口。
- 成功指标：A4 产研究报告带 ≥N 可溯源 claims `[TBD]`；C5b webhook serve Q&A 端到端通。
- 前置依赖：v1.29.0。

> deferred gate 项（不动，需基建/PRD 决策）：AUDIT-F-05 activity 持久化（PRD §3.3 rule 6）/ AUDIT-F-06 banner SPEC 偏移（risk-gated，行为正确）/ AUDIT-F-07 desktop 签名+vLLM CI+Playwright（infra）/ C6 skill sandbox（需 Docker/E2B）。

## 2.6 下下年路径 v1.31.0+（v2.0 逼近 · Structured Context Infrastructure）

> 2026-09-18 外环 roadmap 增量更新。基于桌面调研（行业/竞品/客户/经济模型，见 `docs/analysis/COMPETITIVE-REFERENCE.md` 扩展）+ 既有 ROADMAP。v1.27–v1.30 已 ship，自此向后推演。**战略主线**：把 SAW 自我定位为 **"agent 的可信编译知识层 / Structured Context Infrastructure"**——vector(找相似)+graph(关系)+ontology(什么算什么)+state(现实此刻)+permission(谁能知/做)+action(可改什么)（2026.09 行业论点，SAW 架构本就覆盖），并以 **provenance + 治理 + 数据主权** 作护城河（97% 多 agent 系统从不做溯源验证、2026.05《智能体规范》把可信定为底线）。每版本摘要级，详细 spec 留 01/03。SemVer：全 additive = MINOR，**v2.0.0 MAJOR 仅在 06 验证到真实 breaking API 变更才 bump**（见 §1.1）。

### v1.30.1 — fix: audit 快速修复批（PATCH）— status: planned
- 实际 SemVer：v1.30.1（fix=PATCH，攒批 4 项审计快速修复，不开 MINOR）
- 目标：闭合 v1.30.0 审计中 `快速修复=true` 的 P0/P3 项。
- 关键功能（摘要级，源自 `.csp/audit/AUDIT-FINDINGS-v1.30.0.json`）：
  1. **AUDIT-F-02** [P0] 更新 `tests/unit/drivers/test_mcp_tools.py` expected_tools +1（34→35）+ README/manifest/test 三处工具数对齐
  2. **AUDIT-F-07** [/integrations nav] `web/src/App.tsx` 顶部 nav 增 Integrations NavLink
  3. **AUDIT-F-09** [/integrations 死按钮] 图标按钮补 `aria-label`
  4. **AUDIT-F-10** [/graph 空态] /graph 空数据加 CTA（Import/新建页面）
- 价值：P0 测试失败收敛 + a11y/IA/UX 快速整改，解 06 gate。
- 成功指标：pytest 0 failed；ruff 0；AUDIT-F-02/07/09/10 → closed。
- 前置依赖：v1.30.0。07 回流：v1.30.0 审计（AUDIT-F-02/07/09/10）。
- **未并入本批（折入后续版本，见审计交棒 `docs/analysis/AUDIT-TO-ROADMAP.md`）**：AUDIT-F-05/06（saw web 挂 SPA + proxy 配置化）→ v1.33.0；AUDIT-F-01/04（god-files + coverage 70）→ v1.34.0；AUDIT-F-03（wiki 索引韧性）→ v1.31.0；AUDIT-F-08（404→200）→ v1.33.0；CRITIC-F-01（Dashboard 状态卡）→ v1.35.0。

### Phase A — 信任加固与合规楔子（core-trust / platform）

**v1.31.0 — Provenance Verification API + Activity 持久化**（core-trust track）— status: planned
- 实际 SemVer：v1.31.0（additive=MINOR）
- 目标：把"溯源"从存储能力升为可调 API，闭合 AUDIT-F-05 + 直击跨 agent 知识污染（81% 系统经历、97% 从不验证）。
- 关键功能：`saw_verify_provenance` MCP 原语（claim→证据链校验，返回 receipt+原文路径）；agent activity 持久化到 DB（跨重启，闭合 AUDIT-F-05）；`/api/v1/provenance/{claim_id}` REST；contamination scan（检测衍生自过期/被取代源的 claim）。
- 用户场景/竞品差距：企业需"信息溯源验证"——**只有 SAW 能做**（四层存储 Vault→Claims→Wiki→Index 是物理基础），KAG 有 provenance 但无四层锚定原文。
- 成功指标：provenance 链可校验 `[TBD]`；activity 跨重启不丢；`[TBD]`。
- 前置依赖：v1.30.0。07 回流：AUDIT-F-05 + W1(stale)。

**v1.32.0 — Compliance & Audit Tier（医疗/金融/政务）**（platform-team track）— status: planned
- 目标：把 Ed25519 receipt + RBAC + provenance 打包为合规产品 tier，对齐 2026.05《智能体规范》可信底线。
- 关键功能：audit receipt 导出（Ed25519 签名 bundle，类 SBOM）；数据驻留控制（workspace→存储后端绑定 + on-prem 断言）；留存/删除策略引擎（GDPR/PIPL 被遗忘权传播到 claims/receipts）；合规配置 profile。
- 用户场景/竞品差距：金融/医疗/政务准入需审计链；to-B 楔子。WeKnora 有审计日志但无密码学 receipt 链。
- 成功指标：receipt bundle 可被第三方校验 `[TBD]`；删除传播覆盖 claims+receipts+索引。
- 前置依赖：v1.31.0。

**v1.33.0 — Playwright E2E + Desktop 签名/跨平台**（ecosystem-integration track）— status: planned
- 目标：闭合 AUDIT-F-07 + V1/V2，四层 round-trip 视觉回归 + 桌面端可分发。
- 关键功能：Playwright E2E（dashboard/四层联动视觉回归，U1 闭合）；Apple Developer ID 签名 + notarization（V1）；跨平台 CI matrix（win/linux/mac x86_64+aarch64，V2）；GitHub Release per-platform artifacts。
- 用户场景/竞品差距：非 CLI 用户需可分发桌面包；审计 §5"未验证-范围"四层联动补位。
- 成功指标：Playwright 回归套件通过；.dmg/.exe/.AppImage 签名产出。
- 前置依赖：v1.32.0。07 回流：AUDIT-F-07 / U1 / V1 / V2。

**v1.34.0 — ANN 大规模实证 + 性能硬化 II**（core-trust track）— status: planned
- 目标：闭合 S1/S2/O2，给 v2.0 多租户规模背书。
- 关键功能：ANN hnswlib ≥5000 规模 benchmark + scale_curve 维度修复（S1/S2）；coverage→72%+（compile/compiler/synthesize 深覆盖，O2 续）；Write Queue 吞吐压测 + DLQ 混沌；query P95 SLO 基线。
- 成功指标：ANN ≥5000 P95 优于全量 cosine `[TBD]`；coverage ≥72%；DLQ 压测无丢数据。
- 前置依赖：v1.33.0。07 回流：S1/S2/O2。

### Phase B — 结构化上下文基础设施（intelligence-adaptation）★ 品类定位主线

**v1.35.0 — Structured Context API v1（统一 vector+graph+ontology+state）**（intelligence-adaptation track）— status: planned
- 目标：**SAW 品类定位版本**——把 vector 语义 / graph 遍历 / DRIFT / logical-symbolic 统一到一个 `saw_context` API，对齐 2026.09 "Structured Context Infrastructure" 论点。无单一竞品同时覆盖六要素。
- 关键功能（摘要级，5 条）：
  1. `saw_context` 统一 MCP+REST 接口（单一入口，`mode=semantic|graph|drift|hybrid|logical`，替代分散的 query/search/drift 原语直调）
  2. ontology 层（concept type/relation type + claim→concept 归纳，借鉴 KAG LLMFriSPG；差异化：concept 锚定 claims+receipts，可溯源到原文）
  3. state 层（claim freshness/置信/矛盾态作一等查询维度，可按"仅 fresh / 置信≥X / 排除 contradicted"过滤）
  4. 自适应查询路由（confidence 门控：低置信 claim 触发扩展检索/多跳，借鉴 BeyondUncertainty；差异化：用 SAW 4 级置信作门控）
  5. permission 维度接入（query 按 RBAC workspace 过滤可见 claim，使 permission 成为 context 的第六要素）
- 用户场景/竞品差距：agent 需"外部世界"context（对象+关系+状态+权限+动作），非一摞文档。LightRAG 有 graph+增量无 ontology/state/permission；KAG 有 ontology+逻辑推理无 local-first/code。
- 成功指标：统一 API 覆盖 4 检索模式 `[TBD]`；自适应路由降低无效检索 `[TBD]`。
- 前置依赖：v1.34.0。

**v1.36.0 — Incremental Graph + Logical-Symbolic Reasoning**（intelligence-adaptation track）— status: planned
- 目标：检索侧补齐 LightRAG 级增量 + KAG 级逻辑推理，差异化锚定可信 claims。
- 关键功能（摘要级，5 条）：
  1. claims 图 delta-merge 增量更新（新文档只更新受影响子图，不全量重建，借鉴 LightRAG dual-level+incremental；差异化：delta 走 Write Queue+receipt）
  2. logical-symbolic reasoner（plan/retrieve/reason 三算子，自然语言→逻辑表达式→图谱推理+chunk 检索+LLM 推理混合求解，借鉴 KAG；差异化：结论锚定可信 claims+置信+receipt）
  3. hierarchical community report v2（社区报告锚定 claims+置信，B3 status 轴续，每社区主题可溯源到支撑 claims）
  4. hybrid reranker（semantic+graph+logical 三路融合排序，低置信 claim 降权）
  5. temporal reasoning（双时态：事件发生时间+系统记录时间，借鉴 Zep/Graphiti bi-temporal；差异化：时态锚定 Vault 原文版本）
- 用户场景/竞品差距：GraphRAG 维护模式留真空；LightRAG 无治理；KAG 无四层溯源。
- 成功指标：增量更新不重建全图 `[TBD]`；多跳推理准确率 `[TBD]`。
- 前置依赖：v1.35.0。

**v1.37.0 — Claim Exchange Format v0（联邦互操作种子）**（ecosystem-integration track）— status: planned
- 目标：定义可移植 claim bundle 格式（claim+证据+receipt+置信+新鲜度，签名），为 v3.0 联邦铺路。
- 关键功能：portable claim bundle 格式 v0；跨 SAW 实例 import/export；从 Mem0/Letta/Zep/Cognee 迁移（借鉴 cognee COGX，差异化：SAW bundle 携带 provenance+receipts）；联邦只读协议（查远端 SAW + 验 receipts）。
- 用户场景/竞品差距：cognee COGX 兴起；SAW 差异化=携带溯源链。开启"可信知识跨实例交换"品类。
- 成功指标：bundle 可跨实例校验+导入 `[TBD]`。
- 前置依赖：v1.36.0。

**v1.38.0 — Multi-Agent Orchestration + Sleeptime**（intelligence-adaptation track）— status: planned
- 目标：多 agent 协作 + 后台整理，差异化锚定 receipt。
- 关键功能：多 agent workflow（A2A 感知，agent handoff 带 provenance 标签 context）；sleeptime 整理（Guardian/Scholar 后台 reconcile，借鉴 Letta sleeptime，差异化：reconcile 写 contradicts 边+receipt）；agent skill 沉淀（重复成功路径→可复用 skill，借鉴 EverOS/OpenClaw，差异化：skill 锚定库内 claims）。
- 成功指标：多 agent handoff 不丢 provenance `[TBD]`；sleeptime 跑 ≥1 周期。
- 前置依赖：v1.37.0。

### Phase C — 平台化与多租户生产级（platform-team / ecosystem）

**v1.39.0 — RBAC 深化 + 多租户生产级**（platform-team track）— status: planned
- 目标：多租户生产级隔离 + 权限决策可审计。
- 关键功能：4 级 RBAC（Owner/Admin/Contributor/Viewer，借鉴 WeKnora，差异化：权限决策产 receipt）；per-workspace 配额+限流；tenant 隔离硬化（跨子服务再验 per-request ws，W1 闭合确认）；SSO/OIDC。
- 成功指标：跨 tenant 不泄漏 E2E `[TBD]`；权限操作产 receipt。
- 前置依赖：v1.38.0。

**v1.40.0 — Plugin Marketplace v1（非破坏）**（ecosystem-integration track）— status: planned
- 目标：稳定插件 SDK + 连接器框架 + 注册安装。
- 关键功能：插件 registry + `saw plugin install`（git/zip/registry，借鉴 WeKnora 技能目录，差异化：插件走 Write Queue+receipt）；Plugin SDK v1 stable（事件 hook、生命周期）；connector framework v1（GitHub/Notion/Slack/飞书 ingest，通用不绑厂商）；`.claude/skills` 打包。
- 成功指标：外部插件可装+跑 hook `[TBD]`。
- 前置依赖：v1.39.0。

**v1.41.0 — Skill Sandbox 执行（C6 闭合）**（ecosystem-integration track）— status: planned
- 目标：闭合 C6，agent 代码操作受沙箱治理。
- 关键功能：Docker/E2B 沙箱执行 agent 代码（借鉴 WeKnora/Cognee，差异化：沙箱操作产 receipt+受治理）；`saw sandbox exec`（per-workspace 网络策略）；skill catalog 安装（ClawHub/SkillHub/git）。
- 成功指标：沙箱 exec 不触达宿主敏感路径 `[TBD]`。
- 前置依赖：v1.40.0。07 回流：C6。

**v1.42.0 — IM Serving 全链路 + Obsidian/Logseq 深集成**（ecosystem-integration track）— status: planned
- 目标：C5 serving 侧补全，触达 KW 用户。
- 关键功能：飞书/Slack/企微 SDK serving（Q&A 带可溯源 claims，C5b 续）；Obsidian 插件双向 sync + Logseq connector；web widget embed（域名白名单+限流，借鉴 WeKnora，差异化：答案带 provenance）。
- 成功指标：IM Q&A 端到端带引用 `[TBD]`。
- 前置依赖：v1.41.0。

### Phase D — 生态与 agent-native 扩张（ecosystem / intelligence）

**v1.43.0 — Coding-Harness 全平台 + Governed Code Intelligence**（ecosystem-integration track）— status: planned
- 目标：在拥挤的 code-intelligence 赛道用"治理+溯源"差异化。
- 关键功能：coding-harness skills for Codex/Cursor/OpenCode（C3 续，vs Potpie）；"governed code intelligence" 楔子（impact+staleness+provenance，vs CodeGraph/Graphify code-only）；tree-sitter AST zero-LLM 解析（planned）；code↔doc anchoring（claims 锚定 code symbol）。
- 用户场景/竞品差距：CodeGraph 29k★/Graphify 55k★ 但 code-only 无治理/溯源——SAW 差异化。
- 成功指标：AST 解析 zero-LLM `[TBD]`；impact 锚 claims。
- 前置依赖：v1.42.0。

**v1.44.0 — Token Optimizer 产品化（成本层）**（intelligence-adaptation track）— status: planned
- 目标：把已有 Token Optimizer（65% 理论节省）产品化为成本层，直击 OpenClaw token 黑洞 / $47k 跑飞痛点。
- 关键功能（摘要级，5 条）：
  1. token ledger served 层（Anatomy/Cerebrum/BugLog/Tracker 暴露为 `/api/v1/tokens` REST + `saw_tokens` MCP，agent 可查自身消耗）
  2. cost dashboard（per-session/workspace/agent token 消耗+理论节省+预算告警）
  3. context-compaction（自动蒸馏过期/低价值 context，差异化：compaction 锚定可信 claims，非无差别压缩——压缩后仍可溯源）
  4. token budget 策略（per-agent/per-workspace 预算+超限自动降级到更便宜模型 tier）
  5. 重复读检测+提示（Session Tracker 升级：检测 agent 重复读同一文件→提示用已索引 claim，直击 OpenClaw system-prompt 底噪 + 重复探索黑洞）
- 用户场景/竞品差距：OpenClaw 月 $3600、多 agent $47k——成本危机。SAW 现成基建产品化。
- 成功指标：context-compaction 降 token `[TBD]`。
- 前置依赖：v1.43.0。

**v1.45.0 — Deep Research v2 + Web Grounding**（intelligence-adaptation track）— status: planned
- 目标：A4 深度研究升级到多步+web grounding。
- 关键功能：Scholar deep-research 多步（web 搜索+库内 claims+logical-symbolic reasoner→可溯源报告）；web-grounded claim 摄入（URL→claim 带 freshness timer+source authority）；研究报告 provenance 导出。
- 成功指标：研究报告带 ≥N 可溯源 claims `[TBD]`。
- 前置依赖：v1.44.0。07 回流：A4 续。

**v1.46.0 — Agent Self-Evolution + Dreaming**（intelligence-adaptation track）— status: planned
- 目标：agent 自我演进，差异化锚定 receipt。
- 关键功能：skill 沉淀引擎（重复成功路径→skill，借鉴 EverOS，差异化：锚定 claims+receipt）；"dreaming" 离线 reconcile（批量 Guardian freshness/矛盾/expire，借鉴 OpenAI Dreaming V3/Letta sleeptime，差异化：走治理引擎+receipt）；auto-distill trends。
- 成功指标：dreaming 跑 ≥1 周期无回归 `[TBD]`。
- 前置依赖：v1.45.0。

### Phase E — 平台收口与 v2.0 跃迁

**v1.47.0 — Observability v2（Langfuse-grade）+ A2A**（platform-team track）— status: planned
- 目标：D1 trace 升级到 Langfuse 级 + A2A 适配。
- 关键功能：Langfuse/W3C traceparent 全链路（D1 续，OpenTelemetry 导出）；A2A 协议适配器（agent 间通信带 provenance 标签）；per-claim lifecycle 可观测（freshness/置信/矛盾 over time）。
- 前置依赖：v1.46.0。07 回流：D1 续。

**v1.48.0 — Federated Knowledge Graph v0（跨实例联邦）**（ecosystem-integration track）— status: planned
- 目标：v3.0 生态种子，跨 SAW 实例联邦。
- 关键功能：联邦查询跨实例（用 v1.37 exchange 格式）；跨实例矛盾检测；联邦信任策略（哪些实例的 claim 在何级别被信）。
- 前置依赖：v1.47.0。

**v1.49.0 — Pre-v2.0 硬化 + 迁移工具**（core-trust track）— status: planned
- 目标：v2.0 MAJOR 前奏，硬化 + 迁移就绪。
- 关键功能：v2.0 breaking 变更 deprecation 警告；迁移指南 + `saw migrate v2` 工具；coverage→75%；property/fuzz 测试基建（audit §6 补位，hypothesis/atheris）。
- 前置依赖：v1.48.0。

**v1.50.0 — v2.0 RC + 统一 Context API freeze**（intelligence-adaptation track）— status: planned
- 目标：冻结统一 Structured Context API 面，发 v2.0.0-rc.1。
- 关键功能：freeze 统一 Context API（v1.35 演进）；claim exchange 格式 v1 stable；评估 v2.0 是否含 breaking SDK（marketplace v2）→ 若 breaking 则推到 v2.0.0。
- 前置依赖：v1.49.0。

**v2.0.0 — 平台化 MAJOR（仅真实 breaking 时 bump）**（platform-team track）— status: planned
- 目标：SAW 成为可自托管、多租户的可信知识编译平台。**⚠️ 按 §1.1：仅当 06 验证到真实不兼容 API 变更**（统一 Context API 移除旧 QueryEngine 签名 / claim exchange 格式替换内部表示 / marketplace v2 SDK breaking）才 bump MAJOR。若 v1.50 仅 additive → 实际发 v1.50.0 MINOR，v2.0.0 继续推迟到真实 breaking。战略号 v2.0 是叙事愿景，不是确定 tag。
- 关键能力跃迁：多租户平台生产级、治理即平台原语、marketplace v2、claim 互操作标准 v1、零停机升级。
- 预期市场位置：local-first + self-hosted 可信知识编译平台开源标杆，agent 生态默认可信后端候选。
- 逼近说明：v1.x 序列（v1.31–v1.50）逐步逼近 v2.0；workspace 三闭环(v1.5–1.7)+per-request ws(v1.18) 已铺隔离地基，v1.31–v1.50 把溯源/治理/平台/生态补齐，v2.0.0 是否 bump 取决于是否引入不兼容 API。

### v2.0 后演进（Phase F–H，v2.1 → v3.3，向 v3.0 生态/开放 + 功能饱和）

> 续推 v2.0 之后至功能饱和。SemVer 续编：v2.x MINOR；v3.0.0 MAJOR 仅在真实 breaking（claim 交换格式 v1 stable 替换内部表示 + SDK v3 breaking）才 bump。每版本摘要级，详细 spec 留 01/03。

### Phase F — 生态深化与标准化（v2.1–v2.4，ecosystem / platform）

**v2.1.0 — Marketplace v2 + 多语言 SDK**（ecosystem-integration track）— status: planned
- 目标：Post-2.0 生态扩展，第三方插件/连接器激增 + 多语言 SDK 降低接入门槛。
- 关键功能：marketplace v2（第三方插件 registry + 评分+签名校验，借鉴 WeKnora/ClawHub，差异化：插件操作产 receipt）；多语言 SDK（Python canonical + TypeScript + Rust，借鉴 cognee 多 SDK，差异化：SDK 内置 provenance 验证调用）；连接器长尾（社区贡献 GitHub/Notion/Slack/飞书/Jira/Confluence connector）；agent skill 市场。
- 成功指标：第三方插件 ≥N 上架 `[TBD]`；TS/Rust SDK 可调核心 API。
- 前置依赖：v2.0.0。

**v2.2.0 — 联邦生产化 + Claim 互操作标准提案**（ecosystem-integration track）— status: planned
- 目标：跨实例联邦从 v0 到生产，claim 互操作标准外部化。
- 关键功能：联邦查询生产级（跨 SAW 实例，用 v1.37/v1.50 exchange 格式，带缓存+一致性）；跨实例矛盾仲裁（联邦矛盾触发 Guardian reconcile）；claim 互操作标准草案 v1 外部化（向 standards body/W3C-style 提案）；联邦信任策略 UI。
- 成功指标：联邦查询跨实例 P95 `[TBD]`；标准草案发布。
- 前置依赖：v2.1.0。

**v2.3.0 — Governance-as-a-Service（治理即服务）**（platform-team track）— status: planned
- 目标：把置信/新鲜度/矛盾/receipt 作为可嵌入外部 RAG/agent 的 API 服务——差异化"治理层可嵌入"，vs 云 RAG 黑盒。
- 关键功能：governance sidecar（外部 RAG 可调 `saw_verify`/`saw_freshness`/`saw_contradicts` API 给自己的 chunk 加治理标签）；governance SDK（嵌入任意 agent 框架的 middleware）；治理标签同步（外部 chunk→SAW claim 双向映射）。
- 用户场景/竞品差距：企业已有 RAG 但无治理——SAW 作治理层 sidecar 嵌入，不要求迁移。云 RAG 黑盒无此能力。
- 成功指标：sidecar 可给外部 chunk 打置信+新鲜度 `[TBD]`。
- 前置依赖：v2.2.0。

**v2.4.0 — 多模态编译**（intelligence-adaptation track）— status: planned
- 目标：把编译能力从文本扩到多模态，claim 锚定原文位置。
- 关键功能：image claim 抽取（图表/流程图→claim 锚定像素区域+VLM 描述）；audio/video 转录→claim（时间戳锚定，借鉴 VideoRAG，差异化：锚定+receipt）；table 结构化抽取（表格→claim 保留行列结构）；多模态 wiki 页（混合文本/图/表，可溯源）。
- 用户场景/竞品差距：RAG-Anything/VideoRAG 多模态但无编译/治理；SAW 多模态 claim 可溯源+置信。
- 成功指标：多模态 claim 可锚定原文位置 `[TBD]`。
- 前置依赖：v2.3.0。

### Phase G — 自治知识体与 v3.0 跃迁（v2.5–v2.8 + v3.0）

**v2.5.0 — Agent Skill 市场与分享**（ecosystem-integration track）— status: planned
- 目标：skill 作为可分享资产，携带 provenance。
- 关键功能：skill exchange format（skill 包含步骤+依赖+provenance 链，借鉴 ClawHub/SkillHub，差异化：skill 锚定库内 claims+受治理）；skill 分享/安装 CLI；skill 版本+签名；社区 skill registry。
- 成功指标：外部 skill 可装+跑+溯源 `[TBD]`。
- 前置依赖：v2.4.0。

**v2.6.0 — 自治知识体（self-governing knowledge body）**（core-trust track）— status: planned
- 目标：Guardian 全自动闭环——知识体自演进：自动 expire/归档/置信晋升/矛盾仲裁，无需人工。
- 关键功能：自动置信晋升（单源→交叉验证→人工验证 的自动升级路径，复用 v1.31 contamination scan）；自动 expire/归档（过期 claim 自动降权+归档，freshness 驱动）；矛盾仲裁（多源矛盾自动 reconcile 或标记待人工，写 contradicts 边+receipt）；自治策略配置（per-workspace 治理规则）。
- 用户场景/竞品差距：知识库"自己维护自己"——cognee/Letta 有记忆整理但无四层治理闭环。
- 成功指标： Guardian 跑 ≥1 周期自动晋升/expire/仲裁 `[TBD]`。
- 前置依赖：v2.5.0。

**v2.7.0 — 联邦信任网络**（ecosystem-integration track）— status: planned
- 目标：跨实例 trust scoring + receipt notarization 共识，local-first 优先。
- 关键功能：跨实例 trust scoring（实例声誉——哪些实例的 claim 更可信，基于历史 receipt 验证率）；receipt notarization 共识（关键 claim 的 receipt 跨实例公证，借鉴 blockchain notarization 但 local-first，不依赖公链）；信任策略可配。
- 成功指标：跨实例信任分可计算+生效 `[TBD]`。
- 前置依赖：v2.6.0。

**v2.8.0 — 知识图谱标准提案**（core-trust track）— status: planned
- 目标：SAW claim graph schema 作为开放标准草案 v1（含 ontology/状态轴/receipt 模型）。
- 关键功能：claim graph schema v1 草案（claim/证据/receipt/置信/新鲜度/矛盾边/ontology 的开放序列化）；与 RDF/SPG 互操作映射；标准参考实现（SAW 自身）；标准文档+一致性测试套件。
- 用户场景/竞品差距：定义"可验证知识"的互操作标准之一——云 RAG 黑盒之外的可信替代。
- 成功指标：schema 草案发布+≥1 第三方实现 `[TBD]`。
- 前置依赖：v2.7.0。

**v3.0.0 — 生态/开放 MAJOR（范式跃迁）**（ecosystem-integration track）— status: planned
- 目标：从产品到生态——claim 开放交换格式成标准，第三方 agent 即插即用接入治理层，治理能力以 API 服务化输出。**⚠️ 按 §1.1：仅当 06 验证到真实 breaking**（claim 交换格式 v1 stable 替换内部表示 + SDK v3 breaking + 治理 API surface 重构）才 bump MAJOR。若 v2.8 仅 additive → 实际发 v2.8.0 MINOR，v3.0.0 继续推迟到真实 breaking。
- 关键能力跃迁：claim/证据开放交换格式成互操作标准、第三方 agent 即插即用接入治理层、治理能力以 API 服务化输出、联邦信任网络生产级。
- 预期市场位置：定义"可验证知识"的互操作标准之一，云上 RAG 黑盒之外的可信替代。
- 前置依赖：v2.8.0。

### Phase H — 远期方向（v3.1+，方向性，功能饱和后）

- **v3.1.0** — 行业垂直合规包（医疗 HIPAA/金融 SOX-2/法律 ontology 包，复用 v1.32 compliance tier，per-行业 schema + 审计模板）。
- **v3.2.0** — 边缘部署（edge/local-first 极致：离线自治+按需联邦，弱网/断网可用，桌面端作联邦节点）。
- **v3.3.0** — 知识资产经济（claim attribution/许可/计费——可信知识作为可交易资产，差异化：provenance 使知识可 attribution，为数据要素流通提供可信底座）。
- **远期愿景**：见 §4——SAW 成为 AI agent 与人类共用的、可验证可溯源可治理的本地知识编译层；护城河=溯源+治理+数据主权三耦合。

## 3. 3 年路径（大版本里程碑）

> 主题演进与关键能力跃迁。战略主题号是叙事愿景，不是确定 tag——实际发布号按 1.1 从 v1.9.0 续编增量，只在真实 breaking/范式跃迁发生时才到达 v2.0/v3.0。

### v2.0 — 平台化（约第 2 年）

- **方向主题**：SAW 成为可自托管、多租户的"可信知识编译平台"——**agent 生态的 Structured Context Infrastructure**（vector+graph+ontology+state+permission+action，2026.09 行业论点，SAW 架构本就覆盖）。
- **关键能力跃迁**：多租户隔离生产级、治理即平台原语（暴露给第三方插件/连接器）、插件/连接器 marketplace v2 雏形、claim 互操作标准 v1、部署与升级零停机。
- **预期市场位置**：local-first + self-hosted 知识平台的开源标杆，AI agent 生态的默认可信后端候选。调研支撑：2026 企业 agent 市场 449 亿→2029 3320 亿 RMB（CAGR 107%），《智能体规范 2026.05》把可信定为底线，97% 多 agent 系统从不做溯源验证——SAW 治理/provenance 是稀缺且政策对齐的楔子。
- **逼近说明**：当前 v1.x 序列正逐步逼近 v2.0；workspace 三闭环（v1.5–v1.7）已铺好隔离地基，v1.31–v1.50 把溯源/治理/平台/生态补齐，v2.0.0 周期是否真正 bump MAJOR 取决于是否引入不兼容 API 变更（统一 Context API 移除旧签名 / claim exchange 格式替换 / marketplace v2 SDK breaking）。战略号 v2.0 是叙事愿景，**不是确定 tag**——在那之前按 SemVer 增量续编（v1.51/v1.52/…），诚实不强行 MAJOR。

### v3.0 — 生态 / 开放（约第 3 年）

- **方向主题**：从产品走向生态——开放知识图谱标准与联邦。
- **关键能力跃迁**：claim/证据的开放交换格式（跨 SAW 实例联邦）、知识图谱标准提案、第三方代理即插即用接入治理层、治理能力以 API 服务化输出。
- **预期市场位置**：定义"可验证知识"的互操作标准之一，云上 RAG 黑盒之外的可信替代。
- **逼近说明**：v2.6–v2.8（自治知识体→联邦信任网络→标准提案）逐步铺路；v3.0.0 是否 bump MAJOR 取决于 claim 交换格式 v1 stable 替换内部表示 + SDK v3 breaking + 治理 API surface 重构。战略号 v3.0 是叙事愿景，不是确定 tag——在那之前按 SemVer 增量续编（v2.9/v2.10/…），诚实不强行 MAJOR。

## 4. 长期愿景（3 年+）

SAW 的终局是**AI agent 与人类共用的、可验证、可溯源、可治理的本地知识编译层**。护城河不是模型也不是检索，而是**溯源 + 治理 + 数据主权**三件事的耦合——云上 RAG 难以同时提供这三点（溯源需原始结构、治理需全生命周期、主权需 local-first）。可持续性来自：开源 + 插件/连接器生态 + agent 原生（MCP）带来的网络效应。最终，"知识值不值得信"这件事的答案，沉淀在 SAW 编译出的库里，而非某次模型生成的回答里。

## 5. 衔接声明

- **01 PRD** 读本文件定位本版本主题；PRD front-matter 标 `roadmap_ref: ROADMAP` + `target_version`（如 v1.11.0）。v1.11.0 周期已闭环（released 2026-09-05）。v1.12.0 周期已闭环（released 2026-09-05，embedding 改用 OpenAI 风格 API + E2E 验证）。v1.13.0 周期已闭环（released 2026-09-06，E2E 收尾轮）。v1.14.0 周期已闭环（released 2026-09-06，semantic 性能优化：cache 阈值可配 + ANN 索引 hnswlib + benchmark cache.stats 真实度量）。v1.15.0 周期已闭环（released 2026-09-06，agent/link 能力：自定义 agent 角色 + L2 links apply + M2 agent 活动聚合）。v1.16.0 周期已闭环（released 2026-09-07，realtime 仪表盘 v4.3：agent roster+activity dashboard + workflow runtime view + realtime polling/WS）。v1.17.0 周期已闭环（released 2026-09-07，desktop 完成 v4.4：Tauri→1.0 + 集成 web 仪表盘 + .app/.dmg build + port convergence）。v1.18.0 周期已闭环（released 2026-09-07，per-request workspace contextvar injection + O4 tag flow convention）。v1.18.1 周期已闭环（released 2026-09-08，fix: AUDIT-F-08/W1 sub-service contextvar + W2 E2E test）。**v1.19.0 周期已闭环**（released 2026-09-09，production hardening：links rollback / agents export-import / agents activity 路由 bug 修复 / T4 activity-tracker 解耦 / S4 engine.py 语义搜索拆分 + CLI/govern 测试补强；additive → MINOR）。**v1.20.0–v1.26.0 周期已闭环**（released 2026-09-09/15，竞品借鉴 13 项 ship：C3 skills / B1 contradicts 边 / C1+C2 resolve+record / A1 wiki distill / B2 rethink / A2 communities / D1 langfuse / C4 Agent File(v1.19) / A3 DRIFT / B3 status / B4 NLP / B5 auto-feedback / D3 heartbeat）。下一候选 **v1.31.0+**（下下年路径见上文 §2.6「下下年路径 v1.31.0+」节——Provenance API / Compliance Tier / Structured Context API / 平台化 / 生态 / v2.0 逼近，2026-09-18 调研更新，待 01 PRD 决策）。
- **06 release** 用「版本号规则」节（SemVer/Tag/预发布/多平台一致性），不另立方案。v1.17.0 为 additive → 发 MINOR，不强行 MAJOR。
- **07 复盘** findings（status=open/deferred）回流更新本文件下一版本主题与版本-主题表 status（planned→in-progress→shipped→deferred）。v1.12.0 findings（N1/N4）已清掉。v1.13.0 findings（Q1/Q2/Q3 + O3）已清掉，O1 改善→R1。v1.14.0 findings（R1/R2）已清掉，R4 改善→S3。v1.15.0 findings（M2/L2 + 自定义角色）已清掉，O2 改善（67.34→67.42%）。v1.16.0 findings（realtime 仪表盘）已清掉，O2 持平（67.42%）。v1.17.0 findings：U4（desktop 0.1.0）已清掉。v1.18.0 findings：N3/K2（per-request workspace contextvar）已清掉，O4（tag flow convention）已清掉。**9 轮 backlog 清零达成**。新增 W1（sub-service _workspace_id 未读 contextvar P1）已修复→v1.18.1 fix / W2（per-request ws 未 E2E P2）已修复→v1.18.1 fix / W3（release-manager.md gitignored P3 info）。当前回流 findings：O2 + R3 + S1/S2/S3/S4 + T1/T2/T3/T4 + U1/U2/U3/U5/U6 + V1/V2/V3。
- **lifecycle**：读 `.csp/lifecycle-state.json` 对齐在跑版本；本文件不写 lifecycle（外环）。v1.18.0 已 released（2026-09-07）。
- **竞品借鉴（Phase 0.5）**：`docs/analysis/COMPETITIVE-REFERENCE.md` 为 v1.19.0+ 候选主题输入（deep-read WeKnora/Khoj/GraphRAG/Cognee/Letta/Potpie）。候选主题见上文「竞品借鉴候选」节 + 版本-主题表 candidate 行；取舍由下一轮 01 PRD 决策。借鉴红线：强化 SAW 护城河（溯源+治理+数据主权），非堆 feature；AGPL(Khoj) 仅借鉴思路不引代码。
- **审计回流（audit v1.19.0）**：`.csp/audit/AUDIT-VERDICT-v1.19.0.md` 裁决=放行（Critical/High=0，AUDIT-F-01/02/03 已在 v1.19.0 修，AUDIT-F-08 安全基线达标）。回流 findings：**AUDIT-F-04**（coverage 67.76%→70% 技术债）→ 并入 v1.20.0 技术债 batch（或与竞品借鉴候选择一）；AUDIT-F-05 activity 持久化→[TBD-PRD]；AUDIT-F-06 banner 归位→v1.21.0+；AUDIT-F-07 desktop 签名/vLLM/Playwright→[TBD-infra]。审计 role §红线：不改代码/不发版，修复归 05/06。
