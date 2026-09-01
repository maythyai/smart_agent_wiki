# AGENTS.md — CSP Knowledge Hub Routing Contract

> 进入 workspace 先读本文件。写入前读 schema/manifest；查询前读 `wiki/index.md`。
> 电报体，规则式。manifest（`.csp/manifest.json`）是唯一同步基线；`sources.tsv` 仅作输入注册表。

## 1. 项目概览

- Smart Agent Wiki (SAW) — local-first 多智能体知识平台。CLI `saw`。
- 栈：Python 3.11+（`src/saw/`）+ React 19/Vite（`web/`）+ Tauri 2（`desktop/`）。版本源 `pyproject.toml`（name `smart-agent-wiki`, v1.0.1）。
- 六角架构：domain → engines → adapters → drivers(cli/web/mcp)。五引擎：Ingest/Query/Govern/Learn/Collaborate。Write Queue（SQLite outbox）为唯一变更网关。
- 6 agent 角色：Librarian/Writer/Critic/Linker/Scholar/Guardian。
- 既有资料源：`docs/`（30+ 设计/审计/ADR）+ `.planning/`（research/roadmap/milestones）+ `wiki/entities/`（8 实体页）。`.csp/` 为本 hub。

## 2. 目录权威与依赖方向

- 依赖单向：`raw/docs` → `spec/wiki` → 派生产物。raw 下载后只读，任何 skill 不得改。
- `manifest.json` 唯一索引；`wiki/` 内不存 manifest、不存符号链接。
- 增量判据：`content_hash`（git blob）。禁 mtime/文件大小。
- frontmatter 内联；禁 `.meta.json` 侧车；每页自包含。
- 凭据不入 workspace；Git 发布需用户确认。
- `.csp/.hub-run/<run-id>/` 运行工作区不提交。

```
.csp/
├── AGENTS.md            # 本文件（路由契约）
├── manifest.json        # 唯一 source index（同步基线）
├── sources.tsv          # 输入注册表（人工编辑 → gen 编译进 manifest）
├── lifecycle-state.json # 流水线阶段状态
├── artifacts/           # 治理产物（reconcile-log 等）
├── product-spec/        # PMS（01 阶段产物）
├── code-spec/{app}/     # CMS（04 阶段产物/增量）
├── test-spec/{module}/  # TMS（03 阶段产物）
├── specs/               # 全栈 feature spec（03 阶段）
├── decomposition/      # 需求拆解（02 阶段）
├── tech-decisions/      # 技术选型+ADR（03 阶段）
├── tech-design/         # TDD（03 阶段）
├── tasks/               # 任务拆解（04 阶段）
├── ship/ ops/           # 发布/运维（05 阶段）
├── traceability/        # 追溯矩阵（贯穿）
├── wiki/                # 通用项目 wiki
├── code-wiki/{system}/  # 代码 Q&A wiki
├── intel/               # 会话知识
└── milestones/{m}/      # 里程碑归档（05 阶段）
```

## 3. 三说明书定位

- **PMS**（产品模块说明书，01 阶段）：`.csp/product-spec/modules/MOD-*.md`，`type: module-spec`，`source_type=pms`。
- **CMS**（代码模块说明书，04 阶段/增量）：`.csp/code-spec/{app}/CODE-*.md`，`type: module-spec`，`source_type=cms`。每模块产出 auto-align 写回 manifest。
- **TMS**（测试说明书，03 阶段）：`.csp/test-spec/{module}/TMS-*.md`，`type: test-spec`，`source_type=tms`。
- 当前状态：三说明书均未建，manifest items 全 `pending`，待蒸馏。

## 4. manifest 索引约定

- `source_id` 全局唯一，前缀分类：`pms:` `cms:` `tms:` `doc:` `wiki:` `codewiki:` `memory:` `archive:`。
- `content_hash`=git blob，判 added/changed/removed。raw 下载成功→`status=ready`+更新 hash；失败→保留 item 标 `blocked`/`degraded`。
- 删除来源→二次确认后从 items 移除。
- `build_status`：`pending`→`built`→（变更时）`degraded` 待 re-align；`failed`=构建异常。
- 每阶段产出实质页必须回写对应 item 的 `build_status`/`output_path`/`wiki_pages`。

## 5. 操作路由表

| 意图 | 读 | 写 |
|---|---|---|
| 初始化/增量 hub | `.csp/AGENTS.md` `sources.tsv` | `.csp/manifest.json` `lifecycle-state.json` |
| 生成 PMS | `docs/` `.planning/research` + manifest 定位 | `.csp/product-spec/modules/*.md` + 回写 manifest |
| 需求拆解 | PMS | `.csp/decomposition/FEATURE-DETAILS/*.yaml` |
| 技术方案/Spec | PMS + `docs/ARCHITECTURE` + src | `.csp/specs/SPEC-*.md` `.csp/tech-design/` `.csp/tech-decisions/ADR/` |
| 生成 TMS | Spec + src/tests | `.csp/test-spec/*/TMS-*.md` + 回写 manifest |
| 生成 CMS（棕地优先） | `src/saw/` + `docs/audit/` | `.csp/code-spec/saw/*.md` + auto-align 回写 manifest |
| 实施/codegen | CMS + matching 既有模式 | `src/` `web/` 等；CMS 变更 auto-align |
| 审查 CR | CMS + TMS | `.csp/artifacts/` 评审记录 |
| 发布 ship | CR 产物 + PMS | `.csp/ship/` `.csp/milestones/{m}/` + PMS 闭环 + manifest `archive` |
| 查询代码 Q&A | `wiki/index.md` + `code-wiki/{system}/` | 查询只读；未覆盖明说缺口，不编造 |
| 同步变更 | `hub_manifest.sh diff` | delta 同步 manifest |

## 6. 闭环（需求→code→test）

```
需求对齐 (PMS) ──manifest index──▶ code (CMS ground design/codegen)
      ▲                                       │
      │                                       ▼
 test (TMS) ◀──manifest index── 审查(CR 读 CMS+TMS) ◀─ ship(PMS 闭环)
```

- 需求对齐：PMS 模块边界+验收形态入 spec 页 + manifest。
- code：CMS 蒸馏入口点/调用链；生码读 CMS 匹配既有模式；CMS 变更 auto-align。
- test：TMS 需求→方法矩阵+存量用例；增量只对 delta。
- ship：PMS 闭环 + 三说明书 delta 折叠进 canonical；里程碑快照入 manifest `source_type=archive`。

---

## CLI（`scripts/hub_manifest.sh`，纯 git+grep，零依赖）

```bash
bash scripts/hub_manifest.sh gen              # sources.tsv → manifest.json（合并旧 build_status）
bash scripts/hub_manifest.sh status           # items / built / pending / failed
bash scripts/hub_manifest.sh locate <query>   # 跨 spec/wiki/memory 定位
bash scripts/hub_manifest.sh diff             # added/changed/removed（content_hash）
bash scripts/hub_manifest.sh list --type cms  # 按 source_type 列项
bash scripts/hub_manifest.sh doctor           # 自检
```

## 阶段状态

读 `.csp/lifecycle-state.json` 定位当前阶段；每阶段完成时写回推进。00=done，current_stage=01-prd。

## 下游衔接

- hub 已就绪 → 进入 01 PRD 生成（首条 PMS 入 manifest，`build_status=built`）。
- 棕地项目（本仓即棕地）→ 先蒸馏 CMS（04 能力）再设计：`docs/audit/00-13` + `src/saw/` 为蒸馏源。
- 各阶段产物持续回写 manifest，保持索引实时。
