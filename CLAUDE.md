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
