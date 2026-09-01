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
