# CLAUDE.md — Smart Agent Wiki 项目记忆（新会话自动加载）

> 本文件是 Claude Code 进入项目时**自动加载**的记忆。任何新会话读本文件即知：项目是什么、流程怎么跑、当前在哪、下一步做什么、硬约定是什么。电报体，规则式。

## 项目概览
- **Smart Agent Wiki (SAW)** — local-first 多智能体知识平台。CLI `saw`。知识是"编译"的结果而非检索的对象。
- 仓库：`github.com/chensaics/smart_agent_wiki`（本地 trunk = `master`，**tag 已建未 push 远端**）
- 栈：Python 3.11+（`src/saw/`，hatchling build）+ React 19/Vite/TS（`web/`）+ Tauri 2（`desktop/`）+ uv.lock
- 四层存储：**Vault（不可变原始）→ Claims（主张，SQLite）→ Wiki（可变综合，Markdown）→ Index（FTS5+Graph）**
- 六角架构：`domain/`（纯 Python）→ `engines/`（业务）→ `adapters/`（基建）→ `drivers/`（CLI/Web/MCP）
- 五引擎：Ingest / Query / Govern / Learn / Collaborate
- **Write Queue（SQLite outbox）是唯一变更网关**；多 Sink 并行写入
- 6 agent 角色：Librarian / Writer / Critic / Linker / Scholar / Guardian（按模型路由，Guardian 纯规则零成本）
- 版本源 `pyproject.toml`（name `smart-agent-wiki`，v1.3.0）。LiteLLM 统一 100+ LLM；FastMCP 实现 MCP Server（64+ 工具）
- 测试：pytest，**1874 passed / 3 skipped**（v1.3.0）；ruff 0 errors

## 全流程（外环 + 内环 00-07）
**外环**（跑一次用很久）：`.planning/ROADMAP.md`（版本号规则 SemVer + 版本-主题表 + phase 路径）+ `.planning/PROJECT.md`（战略锚点/需求/约束/决策）

**内环**（每版本迭代跑一轮 00-07）：
1. `00 知识中枢` → `.csp/AGENTS.md`（路由契约，进 .csp 必先读）+ `manifest.json`（唯一索引）+ `lifecycle-state.json`（阶段状态）+ `sources.tsv`（输入注册表）。棕地先蒸馏 CMS
2. `01 PRD / PMS` → `docs/prd/PRD-{slug}.md` + `.csp/product-spec/PMS-*.md`（PMS 模块边界，下游不得越界）
3. `02 需求拆解` → `.csp/decomposition/`（Feature + DAG + NFR）
4. `03 技术方案` → `.csp/tech-decisions/ADR/` + `.csp/tech-design/` + `.csp/specs/SPEC-F-*.md`（Spec 数 == 原子 Feature 数 1:1，穷尽门控）+ `.csp/test-spec/TMS-*.md`
5. `04 任务拆解` → `.csp/tasks/`（WBS + WAVE-PLAN + DAG）
6. `05 实施` → 代码（Python/React/Tauri）+ `.csp/artifacts/implement.md`（DEV-LOG，记录偏离/决策）+ CMS delta `.csp/code-spec/`
7. `06 审查·发布` → 质量门控（pytest/ruff/build/smoke）+ CMS re-align + review + git tag annotated（immutable）+ 本地 trunk
8. `07 复盘` → `.csp/artifacts/retrospective-v{ver}.md`（findings 回流下一迭代 01 + roadmap）

**流转**：每阶段 done 写 `lifecycle-state.json`（current_stage 推进）；产物即回写 `manifest.json`（source_type/build_status/content_hash）；07 findings → 下一轮 01 `adopted_by` 闭环。

**三说明书**：PMS（产品模块说明书，01）`.csp/product-spec/` · CMS（代码模块说明书，04/增量）`.csp/code-spec/{app}/` · TMS（测试说明书，03）`.csp/test-spec/`。三者经 `manifest.json` 索引互链。

## 当前状态（v1.3.0 shipped）
- 已发布：v1.0.1 / v1.1.0 / v1.2.0 / v1.3.0（tag annotated，**本地 trunk 无 push**）
- `lifecycle-state.json`：v1.3.0 周期闭环（00-07 done），`current_stage=01-prd`，`next_cycle=v1.4.0`
- 1874 测试绿 / 3 skipped / 0 失败；ruff src/+tests/ 0 errors；saw smoke 6/6
- 07 复盘见 `.csp/artifacts/retrospective-v1.3.0.md`（findings **G1-G5 待采纳 v1.4.0**）
- 新一轮 01 已起头：`docs/prd/PRD-platform-team-v1.4.0.md`（commit f6cbb94）
- ROADMAP 下一版本：**v1.4.0**（平台化与团队协作 / platform-team）

## 硬约定（不可违背）
1. **不臆造**：未读代码不下结论；grep 不到不写；推断标置信度；结论带 `file:line`；业务数据/SLA/量级未定标 `[TBD]`
2. **ground CMS**：棕地必须读 `.csp/code-spec/` 既有入口点/调用链/分层约定，结论带 `file:line`；CMS drift 实机核验（spec 行号会漂移，以源码为准并回更）
3. **Spec 是施工蓝图**：05 写码前完整读对应 `SPEC-F-*.md`；偏离记 `.csp/artifacts/implement.md`（DEV-LOG）
4. **PMS 模块边界**：跨模块改先回 01 改 PMS，不在开发期擅越
5. **原子提交**：一逻辑一 commit，conventional commits（`feat(scope):`/`fix:`/`docs(csp):`/`test:`/`release:`），禁 WIP 破码；trunk-based `master`，线性 cherry-pick 集成 worktree 分支；tag annotated 不可变（`release: vX.Y.Z`）
6. **Wave 顺序**：按 `WAVE-PLAN.md` + DAG 依赖执行；共享资源（如 db-engineer）串行；Wave 间全量测试绿才进下一
7. **manifest 回写**：每实质产物落盘即回写对应 item `build_status=built` + `content_hash`（git blob sha1）
8. **WHAT not HOW（PRD 层）**：PRD/PMS 不指定 DB/框架；技术细节归 03
9. **测试 living**：TMS 随 Spec 同步；AC 有测试覆盖；绿测试 ≠ 覆盖需求（用追溯矩阵 `.csp/traceability/` 找缺口）
10. **ruff/coverage 怪癖**：lint config 在 `pyproject.toml`（line-length 100；select E4/E7/E9/F）；**F401/F811/F841 故意 ignore**（626+25+27 处，需 `__init__` re-export / 死赋值审计，tracked T-F-Z-1b/1c）——勿盲删 import；coverage `fail_under=60` 是 62% 实测基线的 no-regression 棘轮（north-star 80%，随测试增长逐步上调，勿一步设 80% 致 CI 恒红）；heavy-SDK learn 测试（distiller/fsrs/trends）需 sentence-transformers，CI coverage 步 ignore
11. **subagent 静默写入陷阱**：subagent 报告 "completed" 无输出 ≠ 落盘；**Lead 每个 worktree 须 `git status` 核验**才信，不信任 subagent 回报（v1.2.0 曾 4 subagent 全故障，v1.3.0 已稳但仍核验）
12. **无计划外变更**：不顺手重构既有 pattern；缺依赖（如装包）defer 而非擅自装，须用户确认；新代码匹配既有 idiom（`timezone.utc`/`except Exception` 全库既有，勿 refactor）

## 关键路径（新会话接续 v1.4.0 第一步）
1. 读 `.csp/AGENTS.md`（.csp 路由契约，含目录权威/依赖方向/操作路由表）
2. 读 `.csp/lifecycle-state.json`（确认当前阶段 = 01-prd）
3. 读 `.planning/ROADMAP.md`（版本主题 v1.4.0 platform-team）+ `.csp/artifacts/retrospective-v1.3.0.md`（07 findings G1-G5 待采纳）
4. 进入 `01 PRD`：续写 `docs/prd/PRD-platform-team-v1.4.0.md`（已起头），front-matter `upstream_source` 引 07 findings + roadmap
5. 探测既有代码（`src/saw/connectors/`、`engines/collaborate/`、`auth/` schema 是否已存在）ground 范围，避免 Spec 漂移
6. 跑 02→07（同前几轮模式）：02 拆解 → 03 spec/TMS → 04 WBS/WAVE → 05 实施（worktree 并行）→ 06 门控+tag → 07 复盘

## 常用命令
```bash
# Python 后端
uv pip install -e ".[dev]"            # 装 dev 依赖（pytest/ruff/pytest-cov）
pip install -e ".[connectors]"        # 连接器 SDK（watchdog/slack-sdk/lark-oapi 等）
pip install -e ".[learn]"             # fsrs + sentence-transformers（FULL 学习层）
saw                                   # CLI 入口
pytest tests/ -v                      # 全量测试
pytest --cov=src/saw                  # 覆盖率（gate fail_under=60）
ruff check src/                       # lint（0 errors 门控）
ruff check tests/
saw smoke --self-check                # 自检冒烟（6/6）
saw web                               # Web UI → http://localhost:8000（/docs API）
saw mcp                               # MCP Server
saw status                            # 知识库概览

# Hub CLI（纯 git+grep，零依赖）
bash scripts/hub_manifest.sh gen       # sources.tsv → manifest.json（合并旧 build_status）
bash scripts/hub_manifest.sh status   # items / built / pending / failed
bash scripts/hub_manifest.sh diff     # added/changed/removed（content_hash）
bash scripts/hub_manifest.sh doctor    # 自检

# Web 前端（web/）
cd web && npm install
cd web && npm run dev                 # 开发服务器
cd web && npm run build
cd web && npm run test
cd web && npx tsc --noEmit             # 类型检查

# 桌面（desktop/）
cd desktop && npm run tauri:dev
cd desktop && npm run tauri:build

# 发布：cherry-pick 集成 → master → git tag -a vX.Y.Z → 本地（push 需用户确认）
```

## 角色提示词 / Subagent（每阶段详细 prompt）
**每阶段 system prompt 已落地为 Claude Code 项目级 subagent，在 `.claude/agents/`。** 用法见 `.claude/agents/README.md`。新会话不需贴 prompt——直接调对应 agent。

| 阶段 | subagent | 触发语（手动）|
|---|---|---|
| 外环 | `roadmap-planner` | "长期规划"/"路线图"/"版本规划" |
| 00 | `knowledge-hub` | "知识中枢"/"知识库初始化" |
| 01 | `prd-writer` | "写 PRD"/"需求文档" |
| 02 | `decomposer` | "拆需求"/"feature 分解" |
| 03 | `tech-designer` | "技术方案"/"架构"/"出 spec" |
| 04 | `task-breaker` | "拆 task"/"WAVE" |
| 05 | `dev-lead`（spawn backend/frontend/db/qa）| "开发"/"实现" |
| 06 | `release-manager` | "发版"/"发布" |
| 07 | `reviewer` | "复盘"/"整体审查" |
| 调度 | `lifecycle-orchestrator` | "跑流程"/"从 00 开始"/"推进到下一步" |

**自动端到端**：说"跑流程"→ `lifecycle-orchestrator` 读 `lifecycle-state.json` → 按链路 spawn 各阶段 agent → 全自动推进到 06 发布（仅战略根本模糊 / PRD Rejected / 真破坏操作 / 多 tag 不明 / stage 报错无法 auto-resolve 才打断问用户）。

**手动单阶段**：说对应触发语 → 直接 spawn 该 stage agent，它读 `.csp/AGENTS.md` + `lifecycle-state.json` 重建上下文执行。

**黑板机制**：子 agent 上下文互不共享，靠 `.csp/` 文件系统当黑板传递（lifecycle-state 调度信号 / manifest 产物索引 / front-matter 互链 prd_ref→related_specs→related_tasks→adopted_by）。05 内 dev-lead 按 Wave + 文件无重叠 spawn 角色 sub-agent，每独立 git worktree 隔离并行，集成后 Wave 间全量测试。

> 本 CLAUDE.md 编码流程概览+状态+约定；`.claude/agents/*.md` 编码每阶段详细 prompt，`.csp/AGENTS.md` 编码 .csp 路由契约。三者互补，新会话自动加载 CLAUDE.md 即知全貌+如何调 subagent。

## 反模式速查
臆造引用（无 file:line）· 越界 PMS · 跳 Wave · 巨石/WIP commit · 顺手重构 · 推测性抽象 · subagent 回报当落盘（须 git status 核验）· 擅自装包 · 盲删 ignore 的 F401/F841 import · coverage 一步设 80% 致 CI 恒红 · 带红测试往下推 · 假装完整（用 [TBD] + thin_sections）

## CSP 知识中枢 & Agent 团队

本项目用 `.csp/` 作为**编程管理统一文档库**（PMS/CMS/TMS + 流水线产物），`.claude/agents/` 为多智能体团队。约定详见 `.claude/agents/README.md`。

### 知识中枢（进入 workspace 先读）
- `.csp/AGENTS.md`：路由契约。
- `.csp/manifest.json`：唯一产物索引（`source_id`+`content_hash`+`build_status`）。
- `.csp/lifecycle-state.json`：流水线阶段状态（现在第几步、下一步谁）。
- **若 `.csp/AGENTS.md` 不存在** → 先运行 `knowledge-hub` agent 初始化：建 `AGENTS.md`/`manifest.json`/`lifecycle-state.json` + 棕地 CMS 蒸馏（`.csp/code-spec/`）+ 既有文档整改（Phase 1.5）。这是整条链路（00→07）的第一步，未初始化不进 01。

### Agent 团队（`.claude/agents/`）
- 外环 `roadmap-planner`（战略锚点+版本号规则+1/3年路径，跑一次）
- 内环：`knowledge-hub`(00) → `prd-writer`(01) → `decomposer`(02) → `tech-designer`(03) → `task-breaker`(04) → `dev-lead`(05) → `release-manager`(06) → `reviewer`(07)
- 主调度：`lifecycle-orchestrator`（读 lifecycle-state 自动派 agent；gate 即授权，仅破坏性/无解才问人）
- 05 角色：`backend-engineer`/`frontend-engineer`/`db-engineer`/`qa-engineer`（由 dev-lead spawn + worktree 并行）

### 文档边界
- `.csp/` = 编程管理产物（PMS/CMS/TMS + specs/tasks/tech-design/traceability/artifacts/ship/ops/milestones），git 跟踪。
- `docs/` = 非编程人类文档（README/USER-GUIDE/PRD 原文/CHANGELOG）。
- 版本号默认 SemVer（X.Y.Z），不自动用日期形式 tag。

### 用法
- 端到端：说"跑流程/从 00 开始/推进" → `lifecycle-orchestrator` 自动推进到 06 发布。
- 单阶段：说"写 PRD/拆 task/发版/复盘" → 对应 agent。
- 产物遵循 `.csp/` 格式（front-matter 互链 + manifest 回写 + lifecycle-state 推进）。

<!-- csp-begin (do not edit between these markers) -->
# CSP (Code Skills Package)

本项目已安装 CSP 技能包（310 个 skills，五层架构）。

## 使用方式

在 CLAUDE.md 中添加路由指令即可自动使用：

```
使用 CSP (Code Skills Package) 技能包。当用户给出任务时,先通过 csp-router 路由到合适的 skill 组合。
```

## 核心规则

1. **收到任务时，先通过 csp-router 路由** — 识别任务类型并加载对应 skill 组合
2. **设计先于编码** — 功能需求先做 brainstorming 和 plan
3. **测试先于实现** — 写代码前先写测试（TDD）
4. **验证先于完成** — 声称完成前必须运行验证命令

## 可用 Skills

Skills 位于 `.claude/skills/` 目录，按五层架构组织。

- **csp-router**: >
- **csp-context-engineering**: Optimizes agent context setup. Use when starting a new session, when agent outpu
- **csp-verification**: >
- **csp-test-methodology**: >
- **csp-mvp-scoping**: >
- **csp-spec-contract**: Transform ideas, requirements, or discussions into CSP SPEC contracts with trace
- **csp-receiving-code-review**: Use when receiving code review feedback, before implementing suggestions, especi
- **csp-source-driven-development**: Grounds every implementation decision in official documentation. Use when you wa
- **csp-doubt-driven-development**: Subjects every non-trivial decision to a fresh-context adversarial review before
- **csp-using-skills**: Use when starting any conversation - establishes how to find and use skills, req
- **csp-skill-optimizer**: Use when collecting user feedback on skill behavior, identifying skill coverage 
- **csp-interview-me**: Extracts what the user actually wants instead of what they think they should wan
- **csp-code-graph**: Code knowledge graph methodology and lifecycle orchestration. Use when starting 
- **csp-executing-plans**: Use when you have a written implementation plan to execute in a separate session
- **csp-using-git-worktrees**: Use when starting feature work that needs isolation from current workspace or be
- **csp-requesting-code-review**: Use when completing tasks, implementing major features, or before merging to ver
- **csp-systematic-debugging**: Use when encountering any bug, test failure, or unexpected behavior, before prop
- **csp-writing-skills**: Use when creating new skills, editing existing skills, or verifying skills work 
- **csp-tdd**: >
- **csp-party-mode**: Multi-agent collaboration for complex problem-solving with specialized AI agents
- **csp-spec-driven-development**: CSP-native spec-driven methodology integrated with CSP phase workflows. Use when
- **csp-scope-guard**: >
- **csp-finishing-a-development-branch**: Use when implementation is complete, all tests pass, and you need to decide how 
- **csp-agent-teams**: >
- **csp-writing-plans**: Use when you have a spec or requirements for a multi-step task, before touching 
- **csp-doc-review**: Review requirements or plan documents using parallel persona agents that surface
- **csp-brainstorming**: >
- **csp-competitive-analysis**: >
- **csp-code-understanding**: 
- **csp-prd-change-impact**: 
- **csp-code-spec**: >
- **csp-code-wiki**: >
- **csp-knowledge-hub**: >
- **csp-requirement-decomposition**: 
- **csp-indie-deploy-ops**: >
- **csp-fullstack-spec-generator**: 
- **csp-hotfix**: 
- **csp-graph-architecture**: Codebase architecture analysis via knowledge graph. Use when onboarding to a cod
- **csp-user-story-decomposition**: >
- **csp-lifecycle-orchestrator**: 
- **csp-plan-phase**: 
- **csp-graph-build**: Build and maintain the code knowledge graph. Use when indexing a new repository,
- **csp-product-metrics-review**: >
- **csp-domain-driven-design**: 
- **csp-requirement-prioritization**: >
- **csp-test-spec**: >
- **csp-doc-lifecycle-manager**: Manage project documentation lifecycle: categorize, archive, index, and prune do
- **csp-prd-traceability**: 
- **csp-deprecation-and-migration**: Manages deprecation and migration. Use when removing old systems, APIs, or featu
- **csp-tech-debt-paydown**: >
- **csp-compound-learning**: Document a recently solved problem to compound your team's knowledge. Captures s
- **csp-simple-dev**: 
- **csp-compound-refresh**: Refresh stale learning and pattern docs under docs/solutions/ by reviewing them 
- **csp-session-knowledge-extractor**: Extract reusable knowledge from development sessions and route to appropriate do
- **csp-workflow-schema**: >
- **csp-parallel-worktree**: >
- **csp-project-doc-architect**: Design and maintain project documentation architecture: folder structure, naming
- **csp-roadmap-update**: >
- **csp-user-feedback-analysis**: >
- **csp-qa-cr-review**: 系统化 Code Review 评审工作流。覆盖影响范围、安全性、代码质量、测试覆盖、性能、可维护性六个维度，支持大 CR 并行模式、蒸馏增强调用链追溯、增量版
- **csp-tech-stack-advisor**: 
- **csp-multi-review**: Structured code review using tiered persona agents, confidence-gated findings, a
- **csp-design-hub**: 
- **csp-explore**: Exploration phase specialist for understanding codebases, investigating patterns
- **csp-implementation-phase**: Implementation phase specialist for executing planned work with proper patterns,
- **csp-tech-task-breakdown**: 
- **csp-codebase-audit**: Multi-dimensional codebase audit: parallel Explore agents investigate one dimens
- **csp-product-spec**: >
- **csp-graph-review**: Graph-powered code review with minimal context assembly and risk scoring. Use wh
- **csp-tweak**: 
- **csp-full**: 
- **csp-tech-design-review**: 
- **csp-defect-mining**: Systematic defect discovery via DIVERSE test methodologies — when a test suite h
- **csp-product-discovery-orchestrator**: 
- **csp-strategy**: Create or maintain STRATEGY.md - the product's target problem, approach, users, 
- **csp-graph-refactor**: Graph-powered safe refactoring. Use when renaming symbols, moving code between m
- **csp-product-pulse**: Generate a time-windowed pulse report on what users experienced and how the prod
- **csp-tech-solution-design**: 
- **csp-effort-estimation**: 
- **csp-tech-risk-assessment**: 
- **csp-integration-design**: 
- **csp-solo-oncall**: >
- **csp-prd-parser**: 
- **csp-prd-generation**: >
- **csp-legacy-modernization**: >
- **csp-verify-phase**: Verification phase specialist ensuring all acceptance criteria are met, tests pa
- **csp-graph-impact**: Graph-powered change impact analysis. Use when a diff or PR is ready and you nee
- **csp-shipping-and-launch**: Prepares production launches. Use when preparing to deploy to production. Use wh
- **csp-agentic-identity-trust**: Identity systems architect for autonomous AI agents — designs cryptographic iden
- **csp-api-tester**: Comprehensive API testing specialist — functional validation, performance testin
- **csp-data-engineer**: Data pipeline architect specializing in reliable ETL/ELT, lakehouse architecture
- **csp-multi-agent-architect**: Systems architect for multi-agent AI pipelines — topology selection, context man
- **csp-workflow-architect**: Workflow design specialist who maps complete workflow trees — happy paths, all b
- **csp-prompt-engineer**: Prompt design and LLM behavior specialist — crafts, tests, and systematically op
- **csp-project-standards-reviewer**: >
- **csp-csharp-reviewer**: >
- **csp-incident-commander**: Production and security incident management specialist — severity classification
- **csp-springboot-reviewer**: >
- **csp-web-performance-auditor**: Web performance engineer focused on Core Web Vitals, loading, rendering, and net
- **csp-model-qa**: Independent ML model QA auditor — end-to-end audits from documentation review, d
- **csp-test-engineer**: QA engineer specialized in test strategy, test writing, and coverage analysis. U
- **csp-mcp-builder**: Model Context Protocol specialist who designs, builds, and tests MCP servers tha
- **csp-minimal-change-engineer**: Surgical implementation specialist — fixes only what was asked, refuses scope cr
- **csp-document-generator**: Programmatic document creation specialist — generates professional PDF, PPTX, DO
- **csp-swift-actor-persistence**: Thread-safe data persistence in Swift using actors — in-memory cache with file-b
- **csp-fal-ai-media**: Unified media generation via fal.ai MCP — image, video, and audio. Covers text-t
- **csp-cloud-platform-patterns**: >
- **csp-django-patterns**: Django architecture patterns, REST API design with DRF, ORM best practices, cach
- **csp-web-artifacts**: 用于创建复杂、多组件的 HTML 网页，采用现代前端 Web 技术（React、Tailwind CSS、shadcn/ui）。适用于需要状态管理、路由或 sh
- **csp-crosspost**: Multi-platform content distribution across X, LinkedIn, Threads, and Bluesky. Ad
- **csp-flow-web**: >
- **csp-deep-research**: Multi-source deep research using firecrawl and exa MCPs. Searches the web, synth
- **csp-db-backup**: >
- **csp-golang-patterns**: >
- **csp-cross-layer-testing**: >
- **csp-cicd-pipelines**: >
- **csp-docs-lookup**: >
- **csp-django-security**: Django security best practices, authentication, authorization, CSRF protection, 
- **csp-code-review**: Comprehensive code review specialist for correctness, reuse, simplification, and
- **csp-chart**: >
- **csp-docker-patterns**: >
- **csp-ruff-fixer**: >
- **csp-tech-diagram**: >-
- **csp-python-testing**: >
- **csp-dmux-workflows**: Multi-agent orchestration using dmux (tmux pane manager for AI agents). Patterns
- **csp-kotlin-testing**: Kotlin testing patterns with Kotest, MockK, coroutine testing, property-based te
- **csp-user-analytics**: >
- **csp-code-tour-guide**: >
- **csp-codeql-analyst**: >
- **csp-java-coding-standards**: Java coding standards for Spring Boot and Quarkus services: naming, immutability
- **csp-agent-introspection-debugging**: Structured self-debugging workflow for AI agent failures using capture, diagnosi
- **csp-jpa-patterns**: JPA/Hibernate patterns for entity design, relationships, query optimization, tra
- **csp-frame**: >
- **csp-investor-outreach**: Draft cold emails, warm intro blurbs, follow-ups, update emails, and investor co
- **csp-agent-sort**: Build an evidence-backed CSP install plan for a specific repo by sorting skills,
- **csp-webhook-architecture**: >
- **csp-scope**: >
- **csp-cpp-coding-standards**: C++ coding standards based on the C++ Core Guidelines (isocpp.github.io). Use wh
- **csp-data-pipeline-patterns**: Production data pipeline patterns covering Airflow DAG design, dbt transformatio
- **csp-java-testing**: >
- **csp-access**: >
- **csp-mcp-server-patterns**: Build MCP servers with Node/TypeScript SDK — tools, resources, prompts, Zod vali
- **csp-pitch**: >
- **csp-i18n-frameworks**: >
- **csp-swift-protocol-di-testing**: Protocol-based dependency injection for testable Swift code — mock file system, 
- **csp-bun-runtime**: Bun as runtime, package manager, bundler, and test runner. When to choose Bun vs
- **csp-postgres-patterns**: >
- **csp-sql-reviewer**: >
- **csp-typescript-testing**: >
- **csp-react-version-patterns**: >
- **csp-deployment**: >
- **csp-postgres-optimizer**: >
- **csp-qa**: >
- **csp-react-reviewer**: Expert React code reviewer specializing in hooks rules, component patterns, perf
- **csp-market-research**: Conduct market research, competitive analysis, investor due diligence, and indus
- **csp-observability-and-instrumentation**: Instruments code so production behavior is visible and diagnosable. Use when add
- **csp-brand-voice**: Build a source-derived writing style profile from real posts, essays, launch not
- **csp-springboot-security**: Spring Security best practices for authn/authz, validation, CSRF, secrets, heade
- **csp-bench**: >
- **csp-qa-test-engineering**: 全生命周期 QA 测试工程技能。覆盖需求分析→测试计划→测试用例→自动化执行→生产问题调查完整流程。涉及测试规划、测试策略、用例生成、接口测试、回归测试、生产调
- **csp-subscription-management**: >
- **csp-springboot-patterns**: Spring Boot architecture patterns, REST API design, layered services, data acces
- **csp-changelog-management**: >
- **csp-mock-strategies**: >
- **csp-db-performance**: >
- **csp-frontend-performance**: >
- **csp-x-api**: X/Twitter API integration for posting tweets, threads, reading timelines, search
- **csp-prompt-engineering**: Production prompt engineering covering template management with Jinja2/Mustache,
- **csp-refactorer**: >
- **csp-article-writing**: Write articles, guides, blog posts, tutorials, newsletter issues, and other long
- **csp-python-coding-standards**: Python coding standards (Python 3.10+) covering naming & style (PEP 8), type ann
- **csp-responsive-design**: Implement modern responsive layouts using container queries, fluid typography, C
- **csp-journey**: >
- **csp-e2e-case-automation**: >
- **csp-cpp-testing**: Use only when writing/updating/fixing C++ tests, configuring GoogleTest/CTest, d
- **csp-react-patterns**: React 18/19 patterns including hooks discipline, server/client component boundar
- **csp-h5-visual-testing**: >
- **csp-nestjs-patterns**: NestJS architecture patterns for modules, controllers, providers, DTO validation
- **csp-sitemap**: >
- **csp-search-first**: >
- **csp-rust-testing**: Rust testing patterns including unit tests, integration tests, async testing, pr
- **csp-board**: >
- **csp-cross-platform-strategy**: >
- **csp-platform-deploy**: >
- **csp-flow-mobile**: >
- **csp-paper-reader**: 解析、解读、探索、讲解、总结某领域最新论文或某篇具体论文。 触发词：解析论文、解读论文、论文总结、paper review、read paper、论文笔记、最新
- **csp-vps-deploy**: >
- **csp-everything-claude-code**: Development conventions and patterns for JavaScript projects with conventional c
- **csp-product-capability**: Translate PRD intent, roadmap asks, or product discussions into an implementatio
- **csp-frontend-patterns**: >
- **csp-kotlin-patterns**: Idiomatic Kotlin patterns, best practices, and conventions for building robust, 
- **csp-git-conventions**: >
- **csp-html-prototype**: 生成用于 UI 线框图和模型图的交互式 HTML 原型页面。当用户要求创建原型、线框图、模型图、页面设计或 UI 布局时使用。支持移动端、桌面端和平板设备，并可
- **csp-motion-plan**: >
- **csp-stories**: >
- **csp-refactoring-strategies**: >
- **csp-exa-search**: Neural search via Exa MCP for web, code, and company research. Use when the user
- **csp-db-state-assertion**: >
- **csp-playwright-ui-test**: >
- **csp-typescript-patterns**: >
- **csp-fastapi-patterns**: FastAPI patterns for async APIs, dependency injection, Pydantic request and resp
- **csp-strategic-compact**: Suggests manual context compaction at logical intervals to preserve context thro
- **csp-mobile-performance**: >
- **csp-backend-patterns**: >
- **csp-infrastructure-as-code**: >
- **csp-monitoring-alerting**: >
- **csp-mle-workflow**: Production machine-learning engineering workflow for data contracts, reproducibl
- **csp-eval-harness**: Formal evaluation framework for Claude Code sessions implementing eval-driven de
- **csp-monorepo-tooling**: >
- **csp-check**: >
- **csp-code-simplification**: >
- **csp-file-storage**: >
- **csp-nextjs-turbopack**: Next.js 16+ and Turbopack — incremental bundling, FS caching, dev speed, and whe
- **csp-frontend-slides**: Create stunning, animation-rich HTML presentations from scratch or by converting
- **csp-oauth-integration**: >
- **csp-probe**: >
- **csp-avatar**: >
- **csp-edge**: >
- **csp-react-native-patterns**: >
- **csp-webapp-testing**: >
- **csp-visual-regression**: >
- **csp-frontend-design**: Create distinctive, production-grade frontend interfaces with high design qualit
- **csp-autonomous-loops**: Patterns and architectures for autonomous Claude Code loops — from simple sequen
- **csp-api-governance**: >
- **csp-motion-apply**: >
- **csp-vllm-serving**: Production vLLM inference serving patterns covering Docker setup, continuous bat
- **csp-e2e-testing**: >
- **csp-kubernetes-patterns**: >
- **csp-llm-app-development**: Production LLM application development patterns covering prompt engineering, fun
- **csp-content-engine**: Create platform-native content systems for X, LinkedIn, TikTok, YouTube, newslet
- **csp-db-migration**: >
- **csp-browser-testing-with-devtools**: Tests in real browsers via Chrome DevTools MCP. Use when building or debugging a
- **csp-video-editing**: AI-assisted video editing workflows for cutting, structuring, and augmenting rea
- **csp-rust-patterns**: Idiomatic Rust patterns, ownership, error handling, traits, concurrency, and bes
- **csp-package-publishing**: >
- **csp-metric**: >
- **csp-rag-architecture**: Production RAG architecture patterns covering chunking strategies, embedding mod
- **csp-extract**: >
- **csp-agentic-engineering**: >
- **csp-python-reviewer**: Python coding specification and code review specialist. Covers PEP 8, type safet
- **csp-coding-standards**: >
- **csp-audit**: >
- **csp-seo-engineering**: >
- **csp-spec-adr**: >
- **csp-investor-materials**: Create and update pitch decks, one-pagers, investor memos, accelerator applicati
- **csp-tech-debt-assessment**: >
- **csp-signal**: >
- **csp-performance-optimizer**: Performance optimization specialist for identifying bottlenecks, improving effic
- **csp-react-testing**: React component testing with React Testing Library, Vitest/Jest, MSW for network
- **csp-prd**: >
- **csp-content-hash-cache-pattern**: Cache expensive file processing results using SHA-256 content hashes — path-inde
- **csp-api-codegen**: >
- **csp-payment-integration**: >
- **csp-data-analysis**: Implement analytics, data analysis, and visualization best practices using Pytho
- **csp-locale-management**: >
- **csp-python-patterns**: >
- **csp-retro**: >
- **csp-backend-performance**: >
- **csp-pytorch-patterns**: PyTorch deep learning patterns and best practices for building robust, efficient
- **csp-privacy-compliance**: >
- **csp-brief**: >
- **csp-poster**: >
- **csp-golang-testing**: >
- **csp-test**: >
- **csp-security-review**: >
- **csp-email-systems**: >
- **csp-cancel**: Cancel any active CSP mode (autopilot, ralph, ultrawork, ultraqa, swarm, ultrapi
- **csp-create-skill**: 标准技能创建向导 — 交互式引导用户创建高质量 CSP 新技能，自动完成脚手架、注册与校验。当用户想创建/新增/编写/迁移 skill（create skill
- **csp-setup**: Use first for install/update routing — sends setup, doctor, or MCP requests to t
- **csp-mcp-setup**: Configure popular MCP servers for enhanced agent capabilities
- **csp-ralph**: Self-referential loop until task completion with configurable verification revie
- **csp-reference**: CSP agent catalog, available tools, team pipeline routing, commit protocol, and 
- **csp-autopilot**: Full autonomous execution from idea to working code
- **csp-budget-enforcer**: >
- **csp-deep-interview**: Socratic deep interview with mathematical ambiguity gating before explicit execu
- **csp-deepinit**: Deep codebase initialization with hierarchical AGENTS.md documentation
- **csp-ultraqa**: QA cycling workflow - test, verify, fix, repeat until goal met
- **csp-team**: N coordinated agents on shared task list using Claude Code native teams
- **csp-external-context**: Invoke parallel document-specialist agents for external web searches and documen
- **csp-doctor**: Diagnose and fix code-skills-package installation issues
- **csp-trace**: Evidence-driven tracing lane that orchestrates competing tracer hypotheses in Cl
- **csp-ask**: Process-first advisor routing for Claude, Codex, or Gemini via `csp ask`, with a
- **csp-model-selector**: >
- **csp-linked-test-runner**: >
- **csp-project-session-manager**: Worktree-first dev environment manager for issues, PRs, and features with option
- **csp-release**: Generic release assistant — analyzes repo release rules, caches them in .csp/REL
- **csp-skill**: Manage local skills - list, add, remove, search, edit, setup wizard
- **csp-plan**: >
- **csp-autoresearch**: Stateful single-mission improvement loop with strict evaluator contract, markdow
- **csp-learner**: Extract a learned skill from the current conversation
- **csp-scientist**: Orchestrate parallel scientist agents for comprehensive analysis with AUTO mode
- **csp-ultrawork**: Parallel execution engine for high-throughput task completion
- **csp-learning-loop**: >
- **csp-wiki**: >
- **csp-writer-memory**: Agentic memory system for writers - track characters, relationships, scenes, and
- **csp-ccg**: Claude-Codex-Gemini tri-model orchestration via /ask codex + /ask gemini, then C
- **csp-hud**: Configure HUD display options (layout, presets, display elements)
- **csp-skillify**: Turn a repeatable workflow from the current session into a reusable CSP skill dr
- **csp-debug**: Diagnose the current CSP session or repo state using logs, traces, state, and fo
- **csp-file-organizer**: 通过理解上下文、查找重复文件、建议更合理的目录结构并自动化清理任务，智能整理你电脑中的文件与文件夹。降低整理负担，让数字工作空间长期保持整洁有序。
- **csp-deep-dive**: 2-stage pipeline: trace (causal investigation) -> deep-interview (requirements c
- **csp-complexity-classifier**: >
- **csp-skill-creator**: Interactive skill creation wizard — guides users through creating new CSP skills
- **csp-configure-notifications**: Configure notification integrations (Telegram, Discord, Slack) via natural langu
- **csp-visual-verdict**: Structured visual QA verdict for screenshot-to-reference comparisons
- **csp-self-improve**: Autonomous evolutionary code improvement engine with tournament selection
- **csp-ultragoal**: Durable multi-goal workflow that persists plan/ledger artifacts under .csp/ultra
- **csp-local-build-reminder**: Remind the user to rebuild CSP after editing TypeScript when running from a loca
- **csp-remember**: Review reusable project knowledge and decide what belongs in project memory, not
- **csp-cli-teams**: CLI-team runtime for claude, codex, or gemini workers in tmux panes when you nee

## 如何使用

使用 `Skill` 工具加载对应 skill 并严格遵循其流程。如果你认为哪怕只有 1% 的可能性某个 skill 适用，你必须调用该 skill 检查。
<!-- csp-end -->
