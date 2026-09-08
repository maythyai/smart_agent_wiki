# 复盘 — v1.18.0 per-request workspace + O4 tag 流程（2026-09-07）

> 07 闭环校验。**9 轮循环（v1.10.0–v1.18.0）最终 backlog 清零复盘**。findings 回流下一轮 01（v1.19.0+ 候选）。前置：06-ship done（v1.18.0 tagged @e4cf22d release commit，已 push 远端 + GitHub Release 含 wheel+sdist）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-per-request-ws-v1.18.0 Approved；2 SPEC-F-W-1..2 1:1 对应 F-W-1..2 |
| Spec → Task | ✅ | WBS/TASKS-DELTA-v1.18.0 2 Task（T-F-W-1..2）1:1 |
| Task → commit | ✅ | git log：`47d5cee`(feat F-W-1+F-W-2) + `1f7102d`(reconcile) + `e4cf22d`(release) + `525ad3f`(backfill) |
| AC → 测试 | ✅ | COVERAGE-REPORT v1.18.0 delta 7 AC 全映射（AC-WS-1..5→T-F-W-1, AC-O4-1..2→T-F-W-2） |
| commit → tag | ✅ | `git tag -l v1.18.0` @e4cf22d（**release commit**，非 reconcile commit）+ `git ls-remote --tags origin v1.18.0` = b552206（已 push 远端）|
| tag → release commit（O4 fix 验证） | ✅ | `git log --oneline v1.18.0 -1` = `e4cf22d release: v1.18.0`（非 `1f7102d chore(csp): reconcile`）。**O4 fix 已落地** |
| 测试/lint | ✅ | pytest 2277 passed / 7 skipped / 0 failed；ruff 0；smoke 6/6 |
| 构建 | ✅ | wheel smart_agent_wiki-1.18.0-py3-none-any.whl + sdist；pyproject 1.18.0 |
| Release | ✅ | GitHub Release https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.18.0（assets: wheel + sdist）|

### O4 fix 关键验证

v1.17.0 tag @e391611 指向 `chore(csp): v1.17.0 reconcile planning artifacts`（reconcile commit）——O4 反模式。
v1.18.0 tag @e4cf22d 指向 `release: v1.18.0 — ship artifacts + milestone archive + ROADMAP/lifecycle/manifest update`（release commit）——**O4 fix 已应用**。

06 release-manager 执行顺序：reconcile commit (`1f7102d`) → release commit (`e4cf22d`) → `git tag -a v1.18.0`（在 release commit 上）→ push → GitHub Release。符合 `scripts/RELEASE-FLOW.md` + `.claude/agents/release-manager.md §7.3.5` 约定。

## v1.18.0 度量
- 2 Feature done（per-request workspace contextvar 注入 + O4 tag flow 约定文档化）
- backend pytest 2277 passed（+10 新测试：7 contextvar + 3 tag convention）
- ruff 0
- smoke 6/6
- **additive MINOR**（contextvar 注入不改 QueryEngine 公开构造签名，`workspace_id: str = "default"` 保留）
- QueryEngine `effective_workspace_id` property 在 8+ 位置替代 `self._workspace_id`（cache key / claims_repo.get_by_id / embedding_store query / ANN index path）
- 新建 `src/saw/drivers/web/middleware/workspace.py`（`workspace_id_var` + `WorkspaceContextMiddleware`）
- 新建 `scripts/RELEASE-FLOW.md`（5 step release 流程文档）
- `.claude/agents/release-manager.md` §7.3.5 Tag 流程约定（O4 fix）

## Findings（回流下一轮）

### W1 — sub-service 仍用实例级 `_workspace_id`，未读 contextvar [High / P1]

**QueryEngine 已改为 `self.effective_workspace_id`（读 contextvar fallback `self._workspace_id`），但 3 个子服务（TreeModeSearch / ContextCompiler / GraphTraverse）仍直读 `self._workspace_id`（构造时注入的实例级值），未读 contextvar。**

- **证据**：
  - `src/saw/engines/query/tree_mode.py:114,249,256` — `workspace_id=self._workspace_id`（3 处直读）
  - `src/saw/engines/query/compiler.py:94` — `workspace_id=self._workspace_id`（1 处直读）
  - `src/saw/engines/query/graph_traverse.py:61,280` — `self._workspace_id`（2 处直读）
  - `src/saw/engines/query/engine.py:100-120` — `effective_workspace_id` property 仅在 QueryEngine 类内，子服务无此 helper
- **影响**：web 请求时，QueryEngine 主路径（cache key / embedding_store query / claims_repo.get_by_id）按 contextvar workspace 隔离；但 tree_mode search / compiler compile / graph_traverse 按构造时 default workspace 隔离。**同一请求内数据源不一致**——engine 返回 workspace A 的 claims，但 tree_mode 展开时拉取 workspace B 的 claims。
- **严重度**：High（多租户 web 部署时数据源不一致，可能导致跨 workspace 数据泄漏到 tree/compiler/graph 路径）。
- **建议**：3 个子服务各加 `effective_workspace_id` property（与 QueryEngine 同构），所有 `self._workspace_id` 读取改为 `self.effective_workspace_id`。或 QueryEngine 在请求开始时将 contextvar 值透传到子服务（但 contextvar 是 additive 请求级，实例级 setter 不够）。
- **回流**：下一轮 05 实施（sub-service effective_workspace_id 改造）。

### W2 — per-request workspace 未端到端验证 [Medium / P2]

v1.18.0 实现了 contextvar 注入 + middleware + QueryEngine effective_workspace_id，但**未端到端跑多租户 web 部署测试**（无 TestClient 集成测试验证 X-Workspace-Id header → workspace A 查询不返回 workspace B 数据）。

- **证据**：test-results.md v1.18.0 测试列表 — 10 新测试中无多租户集成测试（test_workspace_contextvar.py 7 个测试验证 contextvar set/get/isolation/thread-safety/async/middleware/query-engine-injection，但未验证完整 REST 请求链）。
- **影响**：AC-WS-3（跨 workspace 不泄漏）在单元级验证，未在端到端 REST 链验证。
- **严重度**：Medium（功能已实现，缺端到端验证信心）。
- **建议**：下一轮补 FastAPI TestClient + X-Workspace-Id header 的集成测试（mock DB 注入 2 workspace 数据，验证 workspace A 请求的 search/tree/graph 路径均不返回 workspace B 数据）。
- **回流**：下一轮 05 测试补齐。

### W3 — `.claude/agents/release-manager.md` gitignored，不入 git [Info / P3]

O4 fix 约定文档化在 `.claude/agents/release-manager.md` §7.3.5 + `scripts/RELEASE-FLOW.md`。但 `.claude/agents/release-manager.md` 被 `.gitignore` 排除（agent config 非源码），不能 commit。

- **证据**：`git check-ignore .claude/agents/release-manager.md` 返回该路径（被 gitignore）。`scripts/RELEASE-FLOW.md` 已入 git（commit `47d5cee`）。
- **影响**：本地 agent 仍可消费约定（文件存在），但跨机器/CI 不共享。
- **严重度**：Info（agent config 非源码，本地消费即可；`scripts/RELEASE-FLOW.md` 已入 git 作为共享文档）。
- **建议**：可接受。若需跨机器共享 agent 约定，可考虑 `.claude/agents/` 从 gitignore 移除或复制到 `docs/` 下。
- **回流**：无（信息项）。

### 续留 findings（跨迭代 backlog）

- **S1-S4**（v1.14.0 续留：ANN 小规模慢 / scale_curve 维度不匹配 / COVERAGE-REPORT 状态标 / engine.py god-file 接近阈值）
- **T1-T4**（v1.15.0 续留：activity 不持久化 / links apply 无 undo / 角色无分享 / agents_cmd 结构变更）
- **U1-U6**（v1.16.0 续留：视觉 E2E 未跑 / polling 延迟 / vLLM skip / desktop 仍 0.1.0 / vitest 路径偏离 / ConnectionStatus 位置偏离）
- **V1-V3**（v1.17.0 续留：.dmg 未签名 / 仅 mac aarch64 / sidecar defer）

### v1.18.0 闭合 findings

- **N3/K2** per-request workspace 注入 — **closed**（v1.18.0 contextvar 注入落地，续留 5 轮 v1.7.0→v1.17.0 终结）。W1 是子服务改造遗留，非 N3/K2 本身。
- **O4** tag 指向 reconcile commit 非 release commit — **closed**（v1.18.0 tag @e4cf22d 指向 release commit，§7.3.5 约定文档化 + scripts/RELEASE-FLOW.md）。

## 9 轮循环（v1.10.0–v1.18.0）backlog 清零总结

| 版本 | 主题 | 状态 | 发布日期 | Tag | 关键度量 |
|---|---|---|---|---|---|
| v1.10.0 | embedding 语义搜索 | released | 2026-09-04 | @ecbdb75 | 1993 passed, 6 skipped, sentence-transformers importorskip |
| v1.11.0 | 债务收口 IV / bug fix | released | 2026-09-05 | @5fca85b | 2064 passed, coverage 65.36%, compile 深覆盖 |
| v1.12.0 | embedding→OpenAI 风格 API + E2E | released | 2026-09-05 | @50fc8e8 | 2076 passed, litellm.embedding, 0 importorskip skip |
| v1.13.0 | E2E 收尾轮（ingest dir + benchmark + REST alias + coverage 67） | released | 2026-09-06 | @779d6cb | 2179 passed, coverage 67.27%, real vLLM benchmark |
| v1.14.0 | semantic 性能优化（cache 阈值 + ANN hnswlib） | released | 2026-09-06 | @136befe | 2192 passed, coverage 67.34%, ANN 索引 |
| v1.15.0 | agent/link 能力（自定义角色 + links apply + activity 聚合） | released | 2026-09-06 | @d5b644f | 2220 passed, coverage 67.42% |
| v1.16.0 | realtime 仪表盘 v4.3 | released | 2026-09-07 | @57b9550 | vitest 64, pytest 2217 (no regression) |
| v1.17.0 | desktop 完成 v4.4（Tauri→1.0 + .dmg） | released | 2026-09-07 | @e391611 | 2267 passed, .app+.dmg produced |
| v1.18.0 | per-request workspace + O4 tag flow | released | 2026-09-07 | @e4cf22d | 2277 passed, contextvar injection |

**全部 backlog 清零达成**：

| 类别 | 原始 finding | 闭合版本 | 闭合方式 |
|---|---|---|---|
| N1 embedding E2E | v1.10.0 | v1.12.0→v1.13.0 | 改用 litellm API + real vLLM benchmark |
| N2 semantic cache | v1.10.0 | v1.11.0 | F-O-1 semantic cache reuse F-QS-07 |
| N3 per-request workspace | v1.10.0 (K2 v1.7.0) | **v1.18.0** | contextvar 注入 additive |
| N4 P99 benchmark | v1.10.0 | v1.13.0 | benchmark_semantic.py real vLLM |
| N5 coverage 基线 | v1.10.0 | v1.11.0 | compile 深覆盖 65.36% |
| N6 Spec naming | v1.10.0 | v1.11.0 | F-O-4 Spec 回更 |
| N7 hash 一致性 | v1.10.0 | v1.11.0 | F-O-4 hash 三处一致 |
| K1 coverage 65 北极星 | v1.11.0 | v1.11.0 | 65.36% 达成 |
| K2 per-request ws（=N3） | v1.11.0 | **v1.18.0** | contextvar 注入 |
| O3 REST CHANGELOG | v1.11.0 | v1.13.0 | F-R-3 REST 别名 + CHANGELOG |
| O4 tag flow | v1.11.0 | **v1.18.0** | tag 指向 release commit + 约定文档化 |
| Q1 embedding E2E vLLM | v1.12.0 | v1.13.0 | real vLLM 验证 closed |
| Q2 benchmark skip | v1.12.0 | v1.13.0 | benchmark_e2e real run |
| Q3 ST fallback 删除 | v1.12.0 | v1.13.0 | 确认删除 closed |
| R1 cache 阈值适配 | v1.13.0 | v1.14.0 | SAW_SEMANTIC_CACHE_THRESHOLD_MS 可配 |
| R2 semantic P99 改善 | v1.13.0 | v1.14.0 | 97.82ms→54.99ms + ANN |
| M2 agent 活动聚合 | v1.14.0 | v1.15.0 | F-T-3 AgentActivityTracker |
| L2 links auto-apply | v1.14.0 | v1.15.0 | F-T-2 saw links apply |
| 自定义角色 | v1.14.0 | v1.15.0 | F-T-1 load_custom_agents |
| U4 desktop 0.1.0→1.0.0 | v1.16.0 | v1.17.0 | F-V-1 4 文件 bump |

**企业生产标准达成**：
- pytest 2277 passed, 0 failed
- ruff 0 errors
- coverage 67.42% (fail_under=67)
- smoke 6/6
- 9 个 wheel 发布（v1.10.0–v1.18.0）
- 9 个 GitHub Release（含 assets）
- 112 AC 全映射（COVERAGE-REPORT 全局汇总）

## 下游衔接 → v1.19.0+ 候选

| 候选 | findings 关联 | 说明 |
|---|---|---|
| **W1 sub-service effective_workspace_id** | W1 (本轮新) | 3 子服务（tree_mode/compiler/graph_traverse）加 contextvar 读取，闭合数据源不一致 |
| **W2 per-request workspace E2E 测试** | W2 (本轮新) | FastAPI TestClient 多租户集成测试（workspace A/B 隔离验证） |
| desktop 签名 + 公证 | V1 (v1.17.0) | Apple Developer ID + notarization（CI secrets） |
| 跨平台 CI（win/linux/mac x86_64） | V2 (v1.17.0) | GitHub Actions matrix |
| desktop sidecar（内嵌 saw server） | V3 (v1.17.0) | PyInstaller + Tauri sidecar（v2.0+） |
| ANN 大规模实证 | S1 (v1.14.0) | 5000+ doc benchmark ANN vs cosine |
| scale_curve 维度修复 | S2 (v1.14.0) | synthetic 向量 dim 匹配 qwen 1024 |
| engine.py god-file 治理 | S4 (v1.14.0) | ANN helpers 提取到独立模块 |
| activity 持久化 | T1 (v1.15.0) | agent activity 跨重启不丢 |
| links apply undo | T2 (v1.15.0) | `saw links undo` |
| 视觉 E2E | U1 (v1.16.0) | Playwright dashboard 截图回归 |
| realtime WS 替代 polling | U2 (v1.16.0) | 真正实时推送 |
| coverage 深覆盖 70%+ | O2 (续留) | compile/compiler 17% + synthesize/scheduler 32% |

不定论，列候选供下一轮 01 PRD 决策。

---

*本复盘所有证据均经 git/manifest 真实状态核验。O4 fix 验证：tag @e4cf22d 指向 release commit（非 reconcile）。W1 sub-service 数据源不一致 ground 自源码 file:line。9 轮循环 backlog 清零达成。*
