---
id: ROADMAP
project: smart-agent-wiki
version: 1.1
last_updated: 2026-09-05
status: active
tracks: [core-trust, platform-team, ecosystem-integration, intelligence-adaptation]
north_star: trustworthy-claim coverage
version_scheme: SemVer
see_also: docs/strategy/STRATEGY.md | docs/prd/PRD-INDEX.md | .csp/review/REVIEW-FINDINGS-*.json
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
| `pyproject.toml`（Python 包） | `1.11.0` | **canonical 真源**。下一个发布 = `v1.12.0`（待 07 复盘后决策，MINOR） |
| git tags `v1.0.1` … `v1.9.0` | 全部 SemVer annotated，与 pyproject 一致 | 保留，对外发布基线 |
| git tags `v3.4.0` / `v3.7.0` | 历史 internal sprint 里程碑号 | 重新定性为**内部 milestone label**（见 1.3），不作为对外发布版本；不可变，不移动/删除 |
| `desktop/`（tauri.conf.json + package.json） | `0.1.0` | 桌面端**未达 1.0**，独立 0.x 跟踪至稳定；达 v1.0 后与 canonical 对齐 |
| `web/package.json` | `0.1.0` | web 为桌面 bundle，随 desktop 版本 |

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

> lifecycle-state `next_cycle: v1.11.0`。复盘引用的 `v4.2`(embedding) / `v4.3`(realtime 仪表盘) / `v4.4`(desktop) 是**内部候选主题标记**，**不是 SemVer 发布号**——仅作 backlog 索引，实际发布号按 1.1 规则从 v1.10.0 续编。v1.10.0 已采纳 v4.2(embedding) 候选；v1.11.0 采纳"清债/修 bug"候选（N7/N2·K1/M3/N5/N6）。

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

### 下一版本候选（07 复盘回流，待下一轮 01 决策）

> v1.10.0 周期闭环 2026-09-04（07-retro done，retrospective-v1.10.0.md）。以下为候选主题，**不定论**，供下一轮 01 PRD 决策。

| 候选 | findings 关联 | 说明 |
|---|---|---|
| embedding E2E 验证 + benchmark | N1(embedding E2E 未验证, P1) / N4(P99 未 benchmark) | 须用户装 `[learn]` extra（sentence-transformers），跑真实语义检索 + 对比 BM25 P99 |
| realtime 仪表盘（v4.3 完整前端） | M2/M3 续留 | agent/workflow 运行态实时可视化 |
| desktop 完成（v4.4 Tauri） | — | 桌面端达 v1.0 |
| 清 K1/K2 债 | N2(coverage 65, compile/compiler 17%) / N3(per-request ws) | 债务收口第四轮 |
| 自定义 agent 角色注册 | — | v1.5.0 留 v2.0 候选 |
| 缓存优化 + ANN 索引 | N7(semantic 不走 cache) | semantic 检索性能 |

续留 findings（跨迭代 backlog）：K1(coverage 65) / K2(per-request ws) / M2(agent 活动聚合) / M3(CLI vs REST 语义双重) / L2(链接自动 apply) / N5(Spec 命名偏离) / N6(ROADMAP hash 已更正)。

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

## 3. 3 年路径（大版本里程碑）

> 主题演进与关键能力跃迁。战略主题号是叙事愿景，不是确定 tag——实际发布号按 1.1 从 v1.9.0 续编增量，只在真实 breaking/范式跃迁发生时才到达 v2.0/v3.0。

### v2.0 — 平台化（约第 2 年）

- **方向主题**：SAW 成为可自托管、多租户的"可信知识编译平台"。
- **关键能力跃迁**：多租户隔离生产级、治理即平台原语（暴露给第三方插件/连接器）、插件/连接器 marketplace 雏形、部署与升级零停机。
- **预期市场位置**：local-first + self-hosted 知识平台的开源标杆，AI agent 生态的默认可信后端候选。
- **逼近说明**：当前 v1.x 序列正逐步逼近 v2.0；workspace 三闭环（v1.5–v1.7）已铺好隔离地基，v2.0.0 周期是否真正 bump MAJOR 取决于是否引入不兼容 API 变更。

### v3.0 — 生态 / 开放（约第 3 年）

- **方向主题**：从产品走向生态——开放知识图谱标准与联邦。
- **关键能力跃迁**：claim/证据的开放交换格式（跨 SAW 实例联邦）、知识图谱标准提案、第三方代理即插即用接入治理层、治理能力以 API 服务化输出。
- **预期市场位置**：定义"可验证知识"的互操作标准之一，云上 RAG 黑盒之外的可信替代。

## 4. 长期愿景（3 年+）

SAW 的终局是**AI agent 与人类共用的、可验证、可溯源、可治理的本地知识编译层**。护城河不是模型也不是检索，而是**溯源 + 治理 + 数据主权**三件事的耦合——云上 RAG 难以同时提供这三点（溯源需原始结构、治理需全生命周期、主权需 local-first）。可持续性来自：开源 + 插件/连接器生态 + agent 原生（MCP）带来的网络效应。最终，"知识值不值得信"这件事的答案，沉淀在 SAW 编译出的库里，而非某次模型生成的回答里。

## 5. 衔接声明

- **01 PRD** 读本文件定位本版本主题；PRD front-matter 标 `roadmap_ref: ROADMAP` + `target_version`（如 v1.11.0）。v1.11.0 周期已闭环（released 2026-09-05），主题 = 债务收口 IV / bug fix。下一周期 v1.12.0 待 07 复盘后决策。
- **06 release** 用「版本号规则」节（SemVer/Tag/预发布/多平台一致性），不另立方案。v1.11.0 为 additive → 发 MINOR，不强行 MAJOR。
- **07 复盘** findings（status=open/deferred）回流更新本文件下一版本主题与版本-主题表 status（planned→in-progress→shipped→deferred）。当前回流 findings：M1/M2/M3 + K1/K2 + L1-L3。
- **lifecycle**：读 `.csp/lifecycle-state.json` 对齐在跑版本；本文件不写 lifecycle（外环）。
