# Reconcile Log — 知识与文档治理整改清单

> 本阶段（00-hub 初始化）治理整改。**只动治理层（路径/版本/索引/front-matter/重复/陈旧），不改业务内容语义**。幂等：重跑只处理新 delta。

## 执行时间
- 2026-09-01（首次初始化基线）

## 整改维度结果

### 版本一致
- 单一事实源：`pyproject.toml` → `version = "1.0.1"`，`name = "smart-agent-wiki"`。
- README.md badge `release-v1.0.1` ✓ 对齐。
- **[FIXED] README_CN.md** badge `release-v3.7.0` → 已对齐 pyproject `v1.0.1`（release badge 属版本号治理层，按新规约默认自动执行）。
  - 类型：version-bumped（已执行）
  - 理由：单一事实源 pyproject `1.0.1`；README.md(EN, 2026-08-11) 已用 v1.0.1；README_CN(2026-06-22) 的 v3.7.0 为陈旧标注。同时把 release 链接 host 由 chensaics 修正为 maythyai（与 origin remote 一致）。
  - 影响项：`doc:overview:readme-cn`（manifest `build_status` 保持 pending，仅 raw 文本变更，待下次 `diff` 标 degraded re-align）。
- **注**：`docs/smart_agent_wiki_deep_audit.md` 行 4「项目版本: v3.7.0」为 2026-06-23 历史审计快照记录，属历史文档正文，不在本阶段越权改动（00 只动治理层）。v3.7 与 v1.0.1 分属 roadmap 里程碑轴与 package release 轴，CMS 已标注此 drift。

### 散落归位
- 资料源均在约定路径：`docs/`、`docs/audit/`、`docs/integrations/`、`.planning/`、`.planning/research/`、`.planning/milestones/`、`.planning/phases/`。根级 tracked .md 仅 README/CLAUDE/ARCHITECTURE_REVIEW，属合理根级文档。
- **结论：无散落需归位。**

### 重复副本
- `docs/smart_agent_wiki_deep_audit.md`（本项目自审，v3.7.0/2026-06-23，344 行）与 `docs/remote_project_audit_findings.md`（竞品分析，2026-04-25，302 行）**已 diff 复核：非重复**——前者审本项目，后者审外部 181 项目清单。同名异本为巧合（字节数相近），**不合并**，两份均保留。
- **结论：无重复需删。**

### 陈旧/临时
- `saw.db`（413KB SQLite 运行库）、`venv_test/`、`.saw/`、`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/` 均为**运行/构建产物且未被 git 追踪**，不影响 hub。
- `.tmp/`/`*.zip` 未发现。
- **结论：无陈旧业务文档需归档/删除。**

### 命名/结构
- docs/ 文件名符合 slug 约定；audit/ 已按 `NN-` 序号规整。
- **结论：无需改名/移位。**

### front-matter
- 既有 `docs/` 资料源为 raw 性质，**不强制加 front-matter**（raw 只读，front-matter 规范适用于 `.csp/` 内实质页）。
- `.csp/` 内新建产物（AGENTS.md/manifest.json/lifecycle-state.json）为治理文件，非实质内容页，无需 front-matter。
- 后续 01-04 阶段产出的实质页（PMS/CMS/TMS/Spec）必须内联 frontmatter，废弃 `.meta.json` 侧车（已由 `doctor` 守卫）。

## 本次实际执行动作
| 路径 | 类型 | 理由 |
|---|---|---|
| `.gitignore` | frontmatter-fixed（追加条目） | 忽略 `.csp/.hub-run/` 运行工作区，不污染仓库 |
| `.csp/sources.tsv` | created | 输入注册表，登记 66 项资料源 |
| `.csp/manifest.json` | created | 编译索引，66 items 全 `pending` |

## 未执行（待人工确认）
- [ ] 无待确认项。README_CN 版本对齐已执行；审计稿去重已复核为非重复。

> **幂等**：下次重跑本阶段，仅处理新 delta（README_CN raw hash 已变 → `diff` 会标 degraded re-align）。

## 2026-09-03 — B3 文档修正 + unverified 标注（T-F-B-3-1）

- `docs/CAPABILITIES.md`（F-B-2 产出）现为准绳清单：每条 capability 带 file:line，`[inferred]` 场景标 `[unverified]`，不臆造"已支持"。
- deep_audit.md 行 4「v3.7.0」保持历史快照不动（历史正文，v3.7=roadmap 里程碑轴，非 release 轴——见 ROADMAP 内外映射）。
- CMS drift D1（6 agent execute() 疑空）→ 不成立，已更正（见 implement.md 2026-09-03）；drift D3（前后端 token 独立）→ 消解（前端已同源）。两条 drift 状态在 retrospective-v1.2.0.md 归档。

## 2026-09-08 — 棕地文档整合 delta（brownfield-doc-integration 子流程）

> 00-hub 子流程：`docs/` → `.csp/` 双轨整合增量 pass。只动治理层（索引/hash/工具），不改 docs/ 原文业务语义。幂等。

### 盘点结果
- docs/ 文件 72 份；manifest 已索引 220 → 本次 +18 = 238 items（built 169 / pending 69）。
- delta 来源：9 份早期 PRD（v1, v1.3.0–v1.9.0）已蒸馏进 PMS 但漏索引；PRD-INDEX；AUDIT-SUMMARY-v1.18.0（已蒸馏进 `.csp/audit/AUDIT-VERDICT`）；claims×3 SQL（被 design docs 引为 DDL 参考）；CAPABILITIES；`.planning` 4 份。

### 删源判定（不删）
经核验，全部"疑似删源候选"均**已被引用 / 已是双轨人读成品**，按项目既定约定（8 份新 PRD v1.10.0+ 一律保留源+索引、从未删除任何 PRD）执行 **index-and-keep**：
- 9 旧 PRD → 已蒸馏进多个 PMS（product-hardening-v1 → claim-alignment/observability/security-hardening/test-gate/e2e-usability 等）；源保留作人读决策记录，manifest 标 `build_status=built`。
- `docs/analysis/AUDIT-SUMMARY-v1.18.0-audit.md` → 被 `.csp/ship/RELEASE-NOTES-v1.18.1.md:33` 引为 human-readable summary，且正是"analysis 人读 docs/ + findings 蒸馏 .csp/audit"双轨；源保留。
- `docs/claims_*.sql` → 被 `docs/smart_agent_wiki_optimization.md`（L324/346-348/447-449）与 `docs/PROJECT_DESIGN_REVIEW.md`（L89）引为 DDL 参考；源保留。
- 偏离流程"删 intake 源"硬规则（红线 #1），但符合项目既定约定 + 引用完整性；如需严格执行删源，需另行确认。

### 执行动作
| 路径 | 类型 | 理由 |
|---|---|---|
| `.csp/manifest.json` | indexed (+18) + realigned (83) | 补索引 9 PRD/PRD-INDEX/AUDIT-SUMMARY/claims×3/CAPABILITIES/.planning×4；重对齐 83 项 content_hash 漂移（file→blob, dir→tree@HEAD） |
| `.csp/manifest.json` | hash-realigned | 7 milestone 目录项 tree-hash 漂移修正（v1.10.0–v1.17.0） |
| `.csp/sources.tsv` | indexed (+9 base-input) | 9 份基础输入 doc 进注册表（PRD 按 sibling 约定 manifest-only，不入 tsv） |
| `scripts/hub_manifest.sh` | tooling-fixed | `cmd_diff` 原用 `[ -f ]` 判路径，目录项恒报 REMOVED 假阳性；改为 `-d` 分支 + `git rev-parse HEAD:<dir>` 算 tree hash |
| `scripts/_brownfield_realign.py` | created (临时) | 程序化重对齐 + 追加 delta 脚本；执行后删除 |

### content_hash 重对齐说明
- 工作树干净（全已提交）；漂移 = manifest 记录的旧 hash 落后于 HEAD blob/tree。
- **未跑 `hub_manifest.sh gen`**：gen 只从 sources.tsv 重写，会丢弃 ~145 个下游阶段（01–07）直接回写进 manifest、但不在 tsv 的项（doc:prd:*/doc:spec:*/doc:tms:*/doc:ship:* 等）。改为程序化直更 manifest 保留全量。
- 重对齐后 `hub_manifest.sh diff` = 0 CHANGED / 0 ADDED / 0 REMOVED（含目录项）。

### 已知缺口（[TBD] 留待后续 pass）
- `.planning/phases/*`（20+ 阶段目录、200+ PLAN/SUMMARY/CONTEXT/VERIFICATION 文件）+ `.planning/milestones/*` + `.planning/benchmarks/*` + `.planning/bundle-analysis/*` 未索引。属 00-hub `.planning` 输入领域的棕地规划蒸馏（Phase 1.7），规模大，本次不处理，标 [TBD]。
- **gen-wipe 隐患**：sources.tsv（99 行）与 manifest（238 items）不一致——tsv 缺 ~145 个下游回写项。任何人跑 `gen` 会丢这些项。已在 sources.tsv 头部加 WARNING。根治方案：要么把全部回写项 port 进 tsv，要么改 gen 保留非-tsv 项。留待 00-hub 后续。

### Phase 5 门控
- [x] 每条 docs/ 原文在 manifest 可定位（raw_path 存在、content_hash 一致）——`diff` 全绿。
- [x] .csp/ 蒸馏 original_ref 指回 docs/ 原文（单向）。
- [x] 无散落（docs/ 根目录无错置 .md；.csp/ 无裸根目录）。
- [x] docs/ 与 .csp/ 不重复存全文。
- [x] .csp/→docs/ 单向可达；docs/ 原文 front-matter 无 .csp/ 引用；双向映射由 manifest 承载。
- [x] reconcile-log 已出（本节）。
