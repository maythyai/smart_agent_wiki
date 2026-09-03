---
id: ROADMAP
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-03
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
| `pyproject.toml`（Python 包） | `1.4.0` | **canonical 真源**。下一个发布 = `1.5.0` |
| git tags `v3.4.0` / `v3.7.0` | 内部 sprint 里程碑号 | 重新定性为**内部 milestone label**（见 1.3），不作为对外发布版本。今后对外 tag 一律 SemVer |
| git tag `v1.0.1` | 与 pyproject 一致 | 保留，首个对外正式发布基线 |
| `desktop/` (tauri.conf.json + package.json) | `0.1.0` | 桌面端**未达 1.0**，独立 0.x 跟踪至稳定；达 v1.0 后与 canonical 对齐 |
| `web/package.json` | `0.1.0` | web 为桌面 bundle，随 desktop 版本 |

> **决策点（用户可 override）**：是否将历史 `v3.x` git tag 保留为内部里程碑标记。默认保留（不移动/删除已推送 tag，遵守不可变），仅今后新增对外 tag 走 SemVer。lifecycle-state 当前的 `milestone: v3.8` 重新定性为内部里程碑，对应到对外版本 `v1.3.0`（见 2.1）。内部 milestone `v3.7` 对应对外版本 `v1.2.0`。

### 1.3 内部里程碑（lifecycle-state 专用）

`.csp/lifecycle-state.json` 的 `milestone` 字段使用内部里程碑号（如 `v3.7`），跟踪 sprint 级迭代，**不等于**对外发布版本。映射：内部 milestone `v3.7` → 对外 release `v1.2.0`；`v3.8` → 对外 release `v1.3.0`。内外分离，避免 sprint 节奏污染 SemVer 契约。

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

### v1.1.0 — MCP 思考工具 + 前端可用性 + 提取器增强（status: released）

> 对应 git tag `v1.1.0`（e806d61）。首个功能版本，承接 v1.0.1 基线。

- **目标**：在 v1.0.1 可运行基线上交付首批用户可感知的功能增强——MCP 思考工具、前端导航可用性、内容提取器扩展，并批量清理 correctness/security/dark-mode 缺陷。
- **关键功能（摘要级）**：
  1. MCP 思考工具（F-MCP-01）——agent 可调用的结构化思考/推理工具面
  2. Breadcrumb 导航（F-WEB-08）——前端多层级页面定位与回溯
  3. JSON/表格提取器（F-INGEST-03）——ingest 侧结构化内容提取增强
  4. 41 批 correctness / security / dark-mode 修复（累计缺陷收敛）
- **价值描述**：用户价值——agent 获得结构化思考能力、前端导航不再迷路、提取器覆盖更多格式；业务价值——从"能跑"到"好用"的首步。
- **成功指标**：MCP 工具可调用；breadcrumb 全页面覆盖；提取器支持 JSON + 表格格式。
- **前置依赖**：v1.0.1 基线。
- **07 回流**：security 修复批次纳入后续 Wave 1 硬化输入。

### v1.2.0 — 安全/可观测硬化（Wave 1）（status: released, 2026-09-03）

> 对应 git tag `v1.2.0`（532710f，2026-09-03）。内部 milestone `v3.7`。真正的"产品加固"版本——安全与可观测基础闭环落地。

- **目标**：在 v1.1.0 功能基线上建立安全审计与可观测性闭环（Wave 1），使产品达到"安全可审计、运行可观测"的基线。
- **关键功能（摘要级）**：
  1. Ed25519 receipt 链——高危操作签名验签，receipt 不可篡改
  2. 裸路由检测——未鉴权路由自动发现与拦截
  3. Token 同源校验——前后端 token 来源一致性校验
  4. JSON 结构化日志默认——可观测性基线（结构化、可聚合）
  5. /health/ready engine-aware——健康探针感知引擎状态
  6. 覆盖率基线建立——核心链路 coverage 基线落 CI
- **价值描述**：用户价值——操作可审计、运行可观测；业务价值——建立安全/可观测 ground，为后续扩张提供基线。
- **成功指标**：receipt 链覆盖率 100%；裸路由检出率 100%；JSON 日志默认开启；/health/ready engine-aware。
- **前置依赖**：v1.1.0 功能基线。
- **07 回流**：Wave 1 findings 回流至 v1.3.0 硬化尾巴。

### v1.3.0 — 硬化尾巴 + 技术债清理（status: in-progress）

> 对应 PRD `PRD-hardening-tail-v1.3.0`（进行中）。内部 milestone `v3.8`。承接 v1.2.0 Wave 1 硬化，完成 Wave 2/3 冒烟链与技术债收口。

- **目标**：完成 v1.2.0 未竟的硬化尾巴（Wave 2/3），并清理积累的技术债，使产品达到"宣称一致、trace 贯穿、CI 有门禁"的完整可用状态。
- **关键功能（摘要级）**：
  1. Wave 2/3 冒烟链——五引擎主链路端到端冒烟基线补全（ingest→compile→query→govern→learn）
  2. 宣称-实现一致性校准——README/docs vs 代码自动 diff，产可信能力清单
  3. Trace 贯穿——RequestId/结构化日志跨模块一致性
  4. CI 门禁——核心链路覆盖率门禁纳入 CI
  5. 技术债清理——ruff lint 规则收口、roadmap 重写（本文件）、迁移文档
- **价值描述**：用户价值——按 README 试用不踩坑、端到端可复跑；业务价值——补全安全/可观测闭环，为 v1.4.0 平台化提供干净基座。
- **成功指标**：冒烟通过率 100%；宣称一致率 100%；trace 贯穿率 100%；CI 覆盖率门禁生效。
- **前置依赖**：v1.2.0 Wave 1 硬化基线。
- **07 回流**：暂无 findings（`.csp/review/` 未建）。

### v1.4.0 — 平台化与团队协作（status: planned）

> platform-team track。从单机 local-first 走向可自托管的多用户平台。

- **目标**：从单机 local-first 走向可自托管的多用户平台。
- **关键功能（摘要级）**：
  1. 多用户与 RBAC 深化（角色/权限/ Cedar 策略生产级）
  2. 团队部署形态（docker-compose.prod 成熟 + 配置收敛）
  3. 可观测性生产闭环（健康巡检、告警、审计面板）
  4. 多工作空间隔离
- **价值描述**：用户价值——OPS 可自托管运维；业务价值——覆盖团队场景，打开 to-B 路径。
- **成功指标**：部署一键化 `[TBD]`；高危操作审计覆盖率持续 100%。
- **前置依赖**：v1.3.0 硬化尾巴 + 技术债清理完成。
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
- **前置依赖**：v1.3.0 硬化尾巴基线 + v1.4.0 平台化。
- **07 回流**：待前版本复盘。

### 版本-主题表（1 年）

| 版本 | 主题 | Track | status |
|---|---|---|---|
| v1.1.0 | MCP 思考工具 + 前端可用性 + 提取器增强 | core-trust | released |
| v1.2.0 | 安全/可观测硬化（Wave 1） | core-trust | released (2026-09-03) |
| v1.3.0 | 硬化尾巴 + 技术债清理 | core-trust | in-progress |
| v1.4.0 | 平台化与团队协作 | platform-team | planned |
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
