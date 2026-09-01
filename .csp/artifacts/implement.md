# DEV-LOG — 05 实施开发偏离/决策记录

## 2026-09-01 — Wave 1 低风险切片（4 Task）

**范围**：T-F-C-4-1（URL 守卫审计）/ T-F-C-3-1（限流验证）/ T-F-B-1-1（claim_diff）/ T-F-A-1-1（冒烟骨架）。
**分支**：`feat/hardening-wave1-slice`（worktree `/Users/cs/projects/saw-w1slice`）。
**Commits**：`fece73d` / `cf5b86b` / `622859c` / `d92ece0`（每 Task 一个原子 commit）。
**测试**：30 新测试全绿；回归 59 passed 无破坏；`saw smoke --self-check` 2/2 PASS exit 0。

### 决策与偏离
- **worktree 隔离**：用户选 feat 分支 + worktree。建 `../saw-w1slice` worktree；因 editable install + .venv 绑定主项目根，用 `PYTHONPATH=<worktree>/src` 使 `import saw` 解析到 worktree 代码（已验证 `saw.__file__` 指向 worktree）。
- **延迟 console 导入**：`smoke_cmd.py` 顶部 `from saw.drivers.cli.main import console` 与 main.py 循环导入；改为函数内延迟导入（匹配既有 `status_cmd.py` 模式）。
- **命令名 [TBD] 落定**：冒烟命令名定为 `saw smoke`（与 `audit` 不混淆）。
- **claim_diff MVP 范围**：通用 NLP 宣称-vs-代码 diff 推迟 V1.1（F-B-2 能力清单覆盖 per-capability file:line）；MVP = 实际计数 + curated stale-pattern 检测（deep_audit 已知过时断言）+ 历史快照标注豁免。
- **smoke 引擎节点**：F-A-1 仅骨架 + self-check；ingest/query/govern/learn 节点体在 F-A-2..4（Wave 2），`saw smoke` 无 `--self-check` 时回退骨架并打印 note，不静默 no-op。

### Deferred / [TBD]
- **T-F-E-1-1（coverage 基线）defer**：`pytest-cov`/`coverage` 未在 pyproject dev deps；装 dev 依赖是独立决策，不计划外变更。需用户确认后 `pip install pytest-cov` 再实测基线。
- **ruff lint 未跑**：`.venv` 未装 ruff（dev dep 缺失）；测试 + import 已验。装 ruff 后补 lint。
- **未实施（留后续 Wave）**：T-F-C-1/2/5、T-F-D-1/2/3、T-F-A-2..6、T-F-E-2/3、T-F-B-2/3 —— 按 WAVE-PLAN 排后续波次。

### 遵循规约
- Spec 唯一蓝图：每 Task 实现前读对应 SPEC；未越 PMS 边界。
- CMS ground：CLI 命令模式、rate_limit/url_guard 既有实现均 reference，未臆造。
- TDD：红→绿（棕地 hardening 以回归守卫测试为主）；每 commit 独立可测过。
- 原子提交：4 commit，conventional commits，无 WIP 破码。
- 无计划外变更：未顺手重构；E-1 缺依赖 defer 而非擅自装包。
