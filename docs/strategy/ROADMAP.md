---
id: ROADMAP
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-02
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

- **MAJOR**：不兼容 API 变更 / 移除已弃用能力
- **MINOR**：向后兼容的功能新增（对应一个版本主题）
- **PATCH**：向后兼容的 bug 修复
- **pre**：`alpha`（功能未完，内部测）/ `beta`（功能完，公开测）/ `rc`（发布候选）

**理由**：SAW 同时是 pip 可装的 Python 包（被他人依赖，SDK 性质）与桌面/Web 应用——SemVer 对 SDK 的依赖契约最清晰。CalVer 不采用。

### 1.2 既有漂移收口（重要）

当前存在版本号漂移，本规则即收口基线：

| 载体 | 现状 | 收口规则 |
|---|---|---|
| `pyproject.toml`（Python 包） | `1.0.1` | **canonical 真源**。下一个发布 = `1.1.0` |
| git tags `v3.4.0` / `v3.7.0` | 内部 sprint 里程碑号 | 重新定性为**内部 milestone label**（见 1.3），不作为对外发布版本。今后对外 tag 一律 SemVer |
| git tag `v1.0.1` | 与 pyproject 一致 | 保留，首个对外正式发布基线 |
| `desktop/` (tauri.conf.json + package.json) | `0.1.0` | 桌面端**未达 1.0**，独立 0.x 跟踪至稳定；达 v1.0 后与 canonical 对齐 |
| `web/package.json` | `0.1.0` | web 为桌面 bundle，随 desktop 版本 |

> **决策点（用户可 override）**：是否将历史 `v3.x` git tag 保留为内部里程碑标记。默认保留（不移动/删除已推送 tag，遵守不可变），仅今后新增对外 tag 走 SemVer。lifecycle-state 当前的 `milestone: v3.7` 重新定性为内部里程碑，对应到对外版本 `v1.1.0`（见 2.1）。

### 1.3 内部里程碑（lifecycle-state 专用）

`.csp/lifecycle-state.json` 的 `milestone` 字段使用内部里程碑号（如 `v3.7`），跟踪 sprint 级迭代，**不等于**对外发布版本。映射：内部 milestone `v3.7` → 对外 release `v1.1.0`。内外分离，避免 sprint 节奏污染 SemVer 契约。

### 1.4 Tag 规则

- `v` 前缀 + annotated tag（`git tag -a v1.1.0 -m "..."`）
- **不可变**：已推送 tag 不移动/不删除/不改写
- CI 触发：`tags: ['v*']`（06 release 执行）

### 1.5 预发布与质量分级

- **预发布**：`v1.1.0-alpha.1` / `-beta.1` / `-rc.1`
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

### v1.1.0 — 产品加固与端到端可用（status: in-progress）

> 对应当前 lifecycle milestone `v3.7`、PRD `PRD-product-hardening-v1`（05-impl Wave1 进行中）。

- **目标**：把"可运行代码"打磨为"端到端可用、宣称一致、安全可审计、测试有门禁"的可用产品。
- **关键功能（摘要级）**：
  1. 五引擎主链路端到端冒烟基线（ingest→compile→query→govern→learn，干净库从 0 起跑）
  2. 宣称-实现一致性校准（README/docs vs 代码自动 diff，产可信能力清单）
  3. 安全深化闭环（RBAC/限流/Ed25519 receipt 高危操作全覆盖）
  4. 可观测性闭环（RequestId/结构化日志/跨模块一致性）
  5. 测试门禁（核心链路覆盖率 ≥80% 基线 `[TBD]`，纳入 CI）
- **价值描述**：用户价值——按 README 试用不踩坑、端到端可复跑；业务价值——建立可信 ground，为后续扩张提供基线。
- **成功指标**：冒烟通过率 100% / 宣称一致率 100% / receipt 覆盖 100% / 覆盖率 ≥80% `[TBD]`。
- **前置依赖**：无外部依赖；承接 00-04 已完成产物。
- **07 回流**：暂无 findings（`.csp/review/` 未建）。

### v1.2.0 — 可信治理深化（status: planned）

- **目标**：让"信任"从"有模块"升级为"规模化可用"——治理能力可在真实库量级上运行。
- **关键功能（摘要级）**：
  1. 矛盾检测规模化（跨源 claim 冲突批量发现与去重）
  2. 置信度传播（claim 间置信度联动，源质量加权）
  3. 新鲜度巡检与失效提醒闭环
  4. 审计 receipt 全生命周期（签发→校验→过期）
- **价值描述**：用户价值——库越大越敢信；业务价值——北极星（trustworthy-claim coverage）显著提升。
- **成功指标**：trustworthy-claim coverage 目标值 `[TBD]`；矛盾检出准确率 `[TBD]`。
- **前置依赖**：v1.1.0 端到端基线与测试门禁。
- **07 回流**：待 v1.1.0 复盘。

### v1.3.0 — 平台化与团队协作（status: planned）

- **目标**：从单机 local-first 走向可自托管的多用户平台。
- **关键功能（摘要级）**：
  1. 多用户与 RBAC 深化（角色/权限/ Cedar 策略生产级）
  2. 团队部署形态（docker-compose.prod 成熟 + 配置收敛）
  3. 可观测性生产闭环（健康巡检、告警、审计面板）
  4. 多工作空间隔离
- **价值描述**：用户价值——OPS 可自托管运维；业务价值——覆盖团队场景，打开 to-B 路径。
- **成功指标**：部署一键化 `[TBD]`；高危操作审计覆盖率持续 100%。
- **前置依赖**：v1.1.0 安全/可观测闭环。
- **07 回流**：待前版本复盘。

### v1.4.0 — 生态与集成扩展（status: planned）

- **目标**：稳定插件 SDK + 连接器 + MCP surface，让 SAW 成为 agent 生态的可信知识后端。
- **关键功能（摘要级）**：
  1. 插件 SDK 稳定化（事件钩子、沙箱隔离落地）
  2. 连接器框架加固（现有 7 平台一致性、新增候选 `[TBD]`）
  3. MCP 工具面规范化（版本化、废弃策略）
  4. 桌面端达 v1.0 与 canonical 对齐
- **价值描述**：用户价值——DEV 可安心集成扩展；业务价值——生态粘性，护城河前置。
- **成功指标**：插件 API 稳定承诺 `[TBD]`；连接器一致性通过率 `[TBD]`。
- **前置依赖**：v1.3.0 平台化基座。
- **07 回流**：待前版本复盘。

### v1.5.0 — 智能与自适应（status: planned）

- **目标**：让知识库自我演进——代理编排与学习引擎真实落地。
- **关键功能（摘要级）**：
  1. 多代理 workflow 编排生产级（声明式 workflow yaml + 执行器）
  2. Learn 引擎落地（distill 蒸馏、trends 趋势）
  3. Token 优化真实可用（从理论 benchmark 走到实测收益）
  4. agent 角色执行链路一致性校验
- **价值描述**：用户价值——库自动保鲜、人工介入降低；业务价值——差异化"会进化的知识库"。
- **成功指标**：workflow 执行成功率 `[TBD]`；Token 实测节省 `[TBD]`。
- **前置依赖**：v1.1.0 基线 + v1.2.0 治理。
- **07 回流**：待前版本复盘。

### 版本-主题表（1 年）

| 版本 | 主题 | Track | status |
|---|---|---|---|
| v1.1.0 | 产品加固与端到端可用 | core-trust | in-progress |
| v1.2.0 | 可信治理深化 | core-trust | planned |
| v1.3.0 | 平台化与团队协作 | platform-team | planned |
| v1.4.0 | 生态与集成扩展 | ecosystem-integration | planned |
| v1.5.0 | 智能与自适应 | intelligence-adaptation | planned |

## 3. 3 年路径（大版本里程碑）

> 主题演进与关键能力跃迁。不排具体功能，只给"到那时产品该是什么样"。

### v2.0 — 平台化（约第 2 年）

- **方向主题**：SAW 成为可自托管、多租户的"可信知识编译平台"。
- **关键能力跃迁**：多租户隔离生产级、治理即平台原语（暴露给第三方插件/连接器）、插件/连接器 marketplace 雏形、部署与升级零停机。
- **预期市场位置**：local-first + self-hosted 知识平台的开源标杆，AI agent 生态的默认可信后端候选。

### v3.0 — 生态 / 开放（约第 3 年）

- **方向主题**：从产品走向生态——开放知识图谱标准与联邦。
- **关键能力跃迁**：claim/证据的开放交换格式（跨 SAW 实例联邦）、知识图谱标准提案、第三方代理即插即用接入治理层、治理能力以 API 服务化输出。
- **预期市场位置**：定义"可验证知识"的互操作标准之一，云上 RAG 黑盒之外的可信替代。

## 4. 长期愿景（3 年+）

SAW 的终局是**AI agent 与人类共用的、可验证、可溯源、可治理的本地知识编译层**。护城河不是模型也不是检索，而是**溯源 + 治理 + 数据主权**三件事的耦合——云上 RAG 难以同时提供这三点（溯源需原始结构、治理需全生命周期、主权需 local-first）。可持续性来自：开源 + 插件/连接器生态 + agent 原生（MCP）带来的网络效应。最终，"知识值不值得信"这件事的答案，沉淀在 SAW 编译出的库里，而非某次模型生成的回答里。

## 5. 衔接声明

- **01 PRD** 读本文件定位本版本主题；PRD front-matter 标 `roadmap_ref: ROADMAP` + `target_version`（如 v1.1.0）。
- **06 release** 用「版本号规则」节（SemVer/Tag/预发布/多平台一致性），不另立方案。
- **07 复盘** findings（status=open/deferred）回流更新本文件下一版本主题与版本-主题表 status（planned→in-progress→shipped→deferred）。
- **lifecycle**：读 `.csp/lifecycle-state.json` 对齐在跑版本；本文件不写 lifecycle（外环）。
