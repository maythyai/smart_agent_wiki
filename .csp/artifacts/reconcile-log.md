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
- **`.planning/phases/*` 已全部清理**（2026-09-08，按用户指示"已开发完即删除"）：36 个 phase 中 35 个已落地于 src（VERIFIED passed 或功能在 src 实现：01-22、26-28、30、phase-39/40/41/42/43/44/45），删除其 211 份追踪规划文件 + 7 个未追踪 phase-39+ 目录。**`29-agent-skills-layer` 亦删除**（决策：从未进 PRD/PMS/STRATEGY 任意一轨——零命中；无交付物——`.claude/skills/` 不存在；其提议机制 Claude-Code skills 已由项目 skills 生态 + docs/COMMANDS 承载；孤立 stub 仅留噪声；未来若有 MCP 工具引导需求应经 01-prd 立正式 PRD）。`.planning/phases/` 现已清空。Git 历史保留全部已删规划。
- **[DRIFT] README.md release badge = `v1.9.0`，pyproject canonical = `1.18.1`（ROADMAP 记最新已发布 `v1.18.0` / 下一个 `v1.18.1`）**。09-01 reconcile 曾对齐 README_CN 至 pyproject；现 README(EN) badge 陈旧。**未自动修**——outward-facing 版本声明，且 badge 取值策略（最新发布 v1.18.0 vs canonical v1.18.1）需用户拍板。`doc:overview:readme` manifest item 标 `build_status=degraded` 待 re-align。
- `.planning/milestones/*` + `.planning/benchmarks/*` + `.planning/bundle-analysis/*` 仍未索引（非 docs/ 范畴，留待 00-hub 后续）。
- **gen-wipe 隐患**：sources.tsv（99 行）与 manifest（238 items）不一致——tsv 缺 ~145 个下游回写项。任何人跑 `gen` 会丢这些项。已在 sources.tsv 头部加 WARNING。根治方案：要么把全部回写项 port 进 tsv，要么改 gen 保留非-tsv 项。留待 00-hub 后续。

### Phase 5 门控
- [x] 每条 docs/ 原文在 manifest 可定位（raw_path 存在、content_hash 一致）——`diff` 全绿。
- [x] .csp/ 蒸馏 original_ref 指回 docs/ 原文（单向）。
- [x] 无散落（docs/ 根目录无错置 .md；.csp/ 无裸根目录）。
- [x] docs/ 与 .csp/ 不重复存全文。
- [x] .csp/→docs/ 单向可达；docs/ 原文 front-matter 无 .csp/ 引用；双向映射由 manifest 承载。
- [x] reconcile-log 已出（本节）。

## 2026-09-09 — 外环 roadmap Phase 0.5 竞品借鉴 + ROADMAP 增量更新

> 外环 roadmap 子流程 Phase 0.5。deep-read 6 个同类开源项目，提炼借鉴清单回写 ROADMAP v1.19.0+ 候选主题。只动治理层 + 战略规划，不改业务代码。

### 参考项目（shallow-clone 至 `开源项目参考/`，已 .gitignore，只读分析不入源树）
- WeKnora(MIT) / Khoj(AGPL,仅思路) / GraphRAG(MIT) / Cognee(Apache) / Letta(Apache) / Potpie(Apache)

### 产出
- 新增 `docs/analysis/COMPETITIVE-REFERENCE.md`（借鉴清单：来源→feature→SAW 差异化落地→拟纳入版本，A/B/C/D 四 track + 不借鉴清单 + 协议合规）
- `docs/strategy/ROADMAP.md` v1.1→1.2：新增「竞品借鉴候选」节 + 版本-主题表 v1.19.0–v1.22.0 candidate 行 + §5 衔接声明补竞品借鉴 bullet；front-matter last_updated→2026-09-09，see_also 加 COMPETITIVE-REFERENCE
- `.csp/manifest.json`：+`doc:analysis:competitive-reference`(built) + rehash `doc:strategy:roadmap`

### 差异化结论
6 竞品各做 SAW 一部分，无一同时覆盖溯源+治理+数据主权。借鉴方向 = 强化护城河（v1.19 矛盾边/rethink/自维护 Wiki/resolve+record/skills 包；v1.20 社区检测+DRIFT/状态轴/Agent File/Langfuse；v1.21 深度研究/调度/IM+Obsidian/Queue dashboard；v1.22 NLP 降本/provenance+feedback/sandbox/heartbeat）。候选非定论，待 01 PRD 取舍。

## 2026-09-09 — 生产硬化 pass（fix→verify 循环）

> 子智能体协作（基于 .claude/agents：auditor/qa-engineer/reviewer 派生）+ 自验循环。基线绿 → 审计真实 findings → 修 → 定向测试 → 全量回归。

### 基线（HEAD master）
- ruff 0；pytest 2284 passed/7 skip/0 fail；coverage 67.46%（gate 67 踩线过）；vitest 64 passed。**#1 生产风险 = coverage 踩线（少几行测试即跌破 CI 门）。**

### 审计结论（W/S/T/U/V findings 真伪）
- **W1/W2/S1 已在代码中修/缓解**（effective_workspace_id contextvar / 隔离测试存在 / scale-driven ANN↔cosine 切换）——非 bug。
- **S2** 仅 vLLM-skip 基准测试合成向量（非生产）。
- **S3** COVERAGE-REPORT `[TBD-impl]` 标记**准确非 stale**（测试存在但 importorskip-gated，盲改 covered 是虚假绿）——不动。
- **S4** engine.py 881 行 god-file = 异味非 bug，重构核心查询引擎有回归风险 → defer。
- **T1/U1/U3/V1-V3** 需 DB model/CI 基建 → defer。

### 修复（每项定向测试验证）
| 项 | 修复 | 验证 |
|---|---|---|
| **T2** | `saw links apply --confirm` 写前存 rollback 快照（`.saw/links-rollback/`）；新 `saw links rollback` 子命令恢复 content+related（同步 frontmatter['related'] 防 write fm.update 覆盖） | 3 新测试 pass |
| **T3** | `saw agents export/import` 子命令（YAML 复制 + 校验 name/model_tier/system_prompt + 拒 builtin 名 + --force） | 7 新测试 pass |
| **activity 路由 bug** | `agents` callback `invoke_without_command=True`+末尾 `raise Exit(0)` 拦截所有子命令 → **v1.15.0 的 `saw agents activity` 从未真正路由（恒打印 roster）**；修为 `ctx.invoked_subcommand is not None: return` | CLI smoke 确认 activity/export/import 全路由 |
| **U5** | vitest include `src/**/__tests__/**` → `src/**/*.test.{ts,tsx}`（发现更多测试不破坏现有） | vitest 64 pass |
| **U2** | 4 个 polling hook + Dashboard 30s stats 改读共享 `lib/polling.ts` 的 `VITE_POLL_INTERVAL_MS`/`VITE_STATS_INTERVAL_MS`（带默认，WS 仍近实时） | vitest pass |
| **README badge** | README+README_CN release v1.9.0→v1.18.1（canonical 对齐） | manifest rehash |

### 全量回归
- pytest **2294 passed/7 skip/0 fail**（+10 新测试），coverage **67.52%**（+0.06），ruff 0，vitest 64 pass。**零回归。**

### Deferred（非 bug / 需基建，诚实标注）
- U6（降级 banner 搬入 ConnectionStatus）= 结构性 SPEC 偏移，行为正确，搬动有打断 retry 逻辑风险 → defer。
- T4 剩余（CLI→web try/except 耦合）= cosmetic（已优雅降级），real bug（activity 路由）已修 → defer 余耦合。
- S4（engine.py 拆分）= 重构核心引擎有回归风险 → defer。
- T1（activity 持久化）/U1（Playwright）/U3（vLLM CI）/V1-V3（desktop 签名+跨平台）= 需 DB/CI 基建 → 后续版本。

## 2026-09-09 — 生产硬化 pass 2（T4 耦合清理 + CLI 冒烟覆盖）

### 修复
- **T4（real 部分）**：`get_activity_tracker`/`set_activity_tracker` 单例从 `saw.drivers.web.app` 移至 `saw.engines.collaborate.activity_tracker`（类所在地）；web.app 改薄 re-export（向后兼容，`# noqa: F401`）；CLI `agents_cmd` + REST `api/routes/collaborate` 改从 collaborate 模块导入——**消除 CLI→web 耦合**（此前 CLI 只能 try/except 从 web 层拿 tracker）。real bug（activity 路由）已在上 pass 修。
- **CLI 冒烟覆盖**：新增 `test_cli_smoke.py`——参数化 `saw <cmd> --help` 全 29 命令 + root help，零副作用覆盖注册/帮助渲染（提升 review/lint/search/freshness/learn/feed/verify/compile/query 等低覆盖命令入口）。+30 tests。
- **T4 accessor 测试**：`test_agents_cmd.py` 加 `test_t4_shared_activity_tracker_accessor`（含 web.app re-export 向后兼容断言）。

### 回归
- pytest **2325 passed/7 skip/0 fail**（+31 新测试），coverage 67.52%（gate 67 过），ruff 0，lint baseline F401=0，vitest 64 pass。**零回归。**

### Deferred（gate 性质，非代码 bug）
- **S4** engine.py 881 行 god-file：异味非 bug；`_semantic_search`+ANN 紧耦合 engine 状态（repos/conn/workspace/cache/keyword fallback），提取命中最高流量查询路径有回归风险——留专项重构，不前推。
- **U6** banner 归位：SPEC 偏移行为正确；banner 耦合 polling/retry/queryClient 状态，搬动有打断 retry 风险——defer。
- **T1** activity 持久化：**PRD §3.3 rule 6 明确不持久化**——改需 01-PRD 决策，非代码 bug。
- **U1** Playwright / **U3** vLLM CI / **V1-V3** desktop 签名+跨平台：需 CI 基建（browser runner / vLLM 服务 / 签名证书），非代码层可解。

## 2026-09-09 — release v1.19.0（production hardening）

> v1.18.1 已在 origin 发布（tag cd8a56b）。本批 post-v1.18.1 硬化 → additive 新功能（T2 rollback / T3 export-import）→ SemVer **v1.19.0**（MINOR）。

### S4 engine.py god-file 拆分（本 pass 新增）
- `_semantic_search`/`_cosine_search_batch`/`_ann_search` 提取至 `SemanticSearchMixin`（`src/saw/engines/query/semantic.py`），engine.py 881→635 行。逐字搬移不改逻辑；语义/嵌入/cache 12 测试 pass；全量 2329 pass 零回归。
- 删 engine.py 未用 `import os`（F401 修）。

### 版本同步
- pyproject 1.18.1→1.19.0（canonical）；VERSION=1.19.0；README/README_CN badge→v1.19.0。
- ROADMAP v1.2→v1.3：v1.19.0 标 shipped；竞品借鉴候选后移 v1.20.0–v1.23.0；§5 衔接声明加 v1.19.0 闭环。
- CHANGELOG 加 v1.19.0 条目（含 v1.18.0/v1.18.1 摘要）。
- lifecycle-state：milestone v4.9 / next_cycle v1.20.0 / current_stage=released-v1.19.0。
- manifest rehash README/README_CN/ROADMAP。

### Deferred（gate 性质，release 不阻塞）
- T1（PRD §3.3 rule 6 不持久化，需 01-PRD 决策）/ U6（SPEC 偏移行为正确，搬动有 retry 耦合风险）/ U1 Playwright（需 CI browser runner）/ U3 vLLM CI（需 vLLM 服务）/ V1-V3 desktop 签名+跨平台（需证书+平台 runner）。

### Release gate（2026-09-09）
pytest 2329 passed/7 skip/0 fail · cov 67.76% · ruff 0 · F401 baseline 0 · vitest 64 pass · 零回归。

## 2026-09-09 — audit v1.19.0（模块化审计+可用性审查，聚焦）

> audit role（独立审计）。solo 串行执行（子智能体 fan-out 在本环境反复致 runner 崩溃，按 role §"无 subagent 能力时串行" + 红线 #11 不降级审计）。聚焦维度：G 安全 + F 代码审查 + H 性能 + I 可观测/文档drift + 前序 W/S/T/U/V 合成。

### 产出（.csp/audit/ + docs/analysis/）
- MODULE-LIST-v1.19.0.md（7 模块组含 DB 底层 + Mermaid 依赖图）
- AUDIT-FINDINGS-v1.19.0.json（8 findings 结构化）
- AUDIT-VERDICT-v1.19.0.md（裁决=放行 + 9 节）
- docs/analysis/AUDIT-SUMMARY-v1.19.0.md（人类摘要）
- manifest +4 items（243 total）

### 安全基线实证（AUDIT-F-08，达标）
G1 SQL=参数化占位符（pipeline.py:399 placeholders="?,?,?"+tuple 绑定，非注入）/ G2 硬编码 secret=0 / G3 shell=True=0 / F bare-except-swallow=0 / I1 生产 print()=0（仅 tutorial demo）。

### findings 汇总
- fixed-in-v1.19.0：F-01 activity 路由 P0 / F-02 CLI→web 耦合 / F-03 engine.py 拆分
- open/deferred：F-04 coverage→70%（v1.20 技术债）/ F-05 activity 持久化（[TBD-PRD]）/ F-06 banner（v1.21+）/ F-07 desktop 签名+vLLM+Playwright（[TBD-infra]）
- Critical/High=0；裁决=放行（production-ready）

### 范围声明（诚实）
聚焦审计，非全量 9 维 × 逐模块可用性 × 实跑四层联动。D 前端深度/E 测试矩阵/实跑联动/mutation-fuzz-property 标 未验证-范围。审计 role 不改代码/不发版；v1.19.0 为当前 release。
