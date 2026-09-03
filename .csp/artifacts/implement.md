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

## 2026-09-03 — Wave 1 收官：5 接线修复 + 集成（M1 达成）

**范围**：E-1（coverage 基线）+ C-1（裸路由）+ C-2（receipt 链）+ C-5（token 同源）+ D-1/D-3（可观测性）。4 worktree 并行（token/auth/receipt/obs），每 worktree 独立 feat 分支。
**集成**：线性 cherry-pick 4 commit 到 master（3850d4f←0c0cf33←a4d8c9d←7ad1a1a←62d95ce）。
**测试**：本轮新增 59 测试（16 token + 23 auth + 11 receipt + 9 obs）；全量回归 **1853 passed, 3 skipped, 0 失败**。

### 决策与偏离
- **Agent 静默写入失败**：4 个 subagent 报告"completed with no output"的 write_file/edit_file 实际未持久化——核验 ground truth 发现 C-2 的 dispatcher.py 3 处编辑 + receipt_store.py + receipt_check.sh 全丢，D-3 的 observability.py + health.py 编辑全丢。仅 migrations.py(v7) + 各 test 文件幸存。**Lead 接手以幸存 test 为 TDD 契约重建**：receipt_store.py 从 11 测试契约反推实现；dispatcher 接线重做；D-3 两处编辑重做 + 补 6 测试。教训：subagent 的"completed"无输出 ≠ 落盘，须 git status 核验。
- **ruff baseline 未绿（pre-existing）**：项目无 ruff 配置文件，用默认值；未修改的 master queue.py 默认下报 7 个 UP017。`timezone.utc`/`except Exception` 是全代码库既有 pattern（queue/dispatcher/ed25519/health/observability 均如此）。决策：**新代码匹配既有 pattern**（receipt_store.py clean；dispatcher 新增用 `timezone.utc` + `# noqa: BLE001` 抑制唯一盲捕获），**不顺手重构既有 UP017/BLE001**（反模式：无计划外变更）。既有 lint debt 单独建 task。
- **C-5 无代码改动**：实机核验前端 token 已同源（authStore.ts:56 / api.ts:134-138 / refresh :65-90 / logout App.tsx:23-27 / ws useWebSocket.ts:146-150），CMS drift D3 不成立→消解。仅产 16 互操作测试钉契约。
- **D-1+D-3 合并提交**：WBS 已将两者串行合并为一 worktree 任务；test 文件共享，按 WBS 边界做单 commit（避免人为拆分共享文件）。
- **release 范围**：Wave 1（10/10）= 本周期 05 交付，M1 可发布里程碑。Wave 2/3 留下一周期（新一轮 01），不推迟发布等全 Wave。

### CMS drift 核验结论（带 file:line）
- **drift D1（6 agent execute() 疑空实现）→ 不成立，更正**：6 个 agent 均有真实 execute()——WriterAgent(writer.py:56 LLM+模板)、LibrarianAgent(librarian.py:53)、CriticAgent(critic.py:56)、LinkerAgent(linker.py:51)、ScholarAgent(scholar.py:56)、GuardianAgent(guardian.py:80 纯规则)。仅 BaseAgent.execute(base.py:56) 是 stub。
- **drift D3（前后端认证各自独立）→ 消解**：见上 C-5，前端 token 拦截链完整同源。
- **行漂移**：SPEC/CMS 标 auth_dep@app.py:267，实际 app.py:275（+8）；observability.py 实际在 drivers/web/middleware/（非 middleware/）。
- **新增调用链**：dispatcher.dispatch_pending→mark_done→_produce_receipt→ReceiptSigner.sign_receipt→ReceiptStore.store（链式 prev_receipt_id via get_last_receipt_id）；ReceiptStore.verify_chain 用 ReceiptSigner() 无 key 实例做签名核验（verify_receipt 不依赖私钥）。health.readiness_check→check_engines(app.state) 探 query/collaborate/write_queue。

### Deferred / [TBD]
- **既有 ruff lint debt**：跨代码库 UP017(timezone.utc)/BLE001(blind except)/S110(try-pass)——超出 Wave 1 scope，单独建 task。
- **Agent execute() 收据钩子**：agent 不经 Dispatcher 路由变更，agent 层收据需架构接入，留后续。
- **`saw security-check routes` CLI 子命令**：以 scripts/security_check.sh 落地，原生 Typer 命令留后续。
- **engine 深探**：check_engines 仅探 None，深 health() 留 Wave 2。

## 2026-09-03 — Wave 1 续推（剩余 6 Task，多 Agent 并行）

**Lead 先决（用户确认）**：
- **装 dev 依赖**：`uv pip install -e ".[dev]"` + pytest-cov（pytest 9.1.1 / ruff 0.16.5 / pytest-cov 7.1.0）。用户选"全装 dev + pytest-cov"。前轮 E-1 defer 的依赖问题解除。
- **trust-governance 脏工作区**：master 有一批未提交的 trust-governance/v1.2.0 规划产物（新 PMS、PRD-trust-governance-v1.md、`.csp/review/`、改 uv.lock），与 hardening v3.7 无关。`git stash -u` 暂存（stash@{0}），master 恢复干净。
- **optional extras 补装**：起点基线 2 失败（test_architecture_guards / test_wecom_constant_time）源于 optional extras 缺失（watchdog/xmltodict/fsrs）。装 `[connectors]` + fsrs（轻量，不含 sentence-transformers）清干净。记为基线 env 决策。
- **起点基线绿**：1780 passed / 3 skipped / 0 failed。

**并行编排**（4 worktree 隔离 + Lead 自做 E-1）：
| 子 Agent | Task | worktree | 分支 |
|---|---|---|---|
| Security/QA | T-F-C-1-1 权限矩阵 | ../saw-w1-auth | feat/auth-matrix |
| Backend Security | T-F-C-2-1 receipt 闭环 | ../saw-w1-receipt | feat/receipt-chain |
| Backend Security | T-F-C-5-1 token 同源 | ../saw-w1-token | feat/token-interop |
| Backend/Observability | T-F-D-1-1+T-F-D-3-1（串行）| ../saw-w1-obs | feat/observability |
| Lead | T-F-E-1-1 coverage 基线 | 主 worktree | — |

并行检测：C-1/C-2/C-5 文件无重叠并行；D-1/D-3 共享 observability.py 故同 worktree 串行；E-1 仅写 .csp/artifacts 不冲突。ci.yml 共享资源在 E-2/E-3（后续 Wave），本波不触碰。

### T-F-E-1-1 coverage 基线（Lead 完成）
- **实测**：TOTAL 62%（28386 stmt / 10649 missing）；核心引擎+write_queue+code_graph 64%；非核心 51%。
- **阈值决策（Spec 偏离）**：SPEC-F-E-1 原设核心≥80%/非核心≥60%。实测均低于此。Lead 决策：E-2 门禁阈值设为**实测基线 floor**（核心 64%/非核心 51%/全量 62%，no-regression ratchet），80%/60% 为 north-star 目标，gap 透明记录。理由：棕地硬化应 ratchet 不应致 CI 恒红；低洼地（compile 14-31%、collaborate agents 23-30% 印证 CMS drift D1 空实现）属后续 Wave/03 范畴。
- **产物**：`.csp/artifacts/coverage-baseline.md`。

## 2026-09-03 — v1.5.0 智能与自适应（8 Task，3 Wave，Lead 单线推进）

**范围**：F-I-1..4（workflow/learn/token/policy CLI surface + agent lint）+ F-Z-6..9（F841 / workspace 路由 / policy reload / query 覆盖）。
**模式**：Lead 单线实施（未 spawn 并行 worktree——8 Task 文件重叠度低且 Lead 直做更快；沿用既有 patterns）。3 Wave 串行：Wave1 CLI surface → Wave2 workspace 路由 → Wave3 F841 串行末位。
**Commits**：404c787(Wave1) / c6d6b10(Wave2) / 616d929(Z-9) / 4b45a61(Z-6)，每 Wave 一原子 commit。
**测试**：1929 passed / 3 skipped / 0 failed（+31 新测试）；ruff src/+tests/ 0 errors（F841 启用）；coverage 63%（ratchet 60→63）。

### 决策与偏离
- **F-I-1 resume 索引制（ADR-006）**：`WorkflowExecutor.resume()` 复用既有 M-16 状态机 + HI-9 持久化；从 `steps_completed` index 续跑。context 不持久化（thin，v2.0 演进全量快照）。CLI `saw workflow resume <id> --def <yaml>` 重解析 def（表只存 definition_name）。
- **F-I-4 与 F-I-1 bundle**：lint 与 run/validate/resume/status 同 `workflow_cmd.py` 文件 → bundle 为一 commit（不并行 split）。lint 复用 `WorkflowParser.validate(available_agents)` + `build_default_agents()`，不引新 lint 引擎。
- **F-Z-7 scope 收窄（关键偏离）**：PRD H2"全查询路径路由"本轮**只做 claims search/get_by_id + QueryEngine 搜索路径**注入 workspace scope + 修 query-cache 跨 ws 泄漏（cache key 加 workspace_id）。AC-WS-3 在搜索数据路径满足（A ws claim 在 B ws 搜索返回空）。**graph_traverse / tree_mode / compiler / ingest-write 的 workspace 注入 defer** [TBD] 下一周期——面广，本轮增量推进不贪全。诚实标注非"全覆盖"。
- **F-Z-9 coverage ratchet 60→63（非 65，偏离 TMS）**：TMS-DELTA 原写"60→65"。实测 63.1%。硬约定 #10：不设高于实测致 CI 恒红。Lead 决策设 fail_under=63（实测 floor，no-regression）。65 留待 query engine.py（14%）+ compare/tree_mode（21-23%）深覆盖后。north-star 80% 不变。
- **F841 27 处手审（Z-6）**：分类——纯赋值删行（datetime.now/Path/.get/None literal 等 19 处）；side-effect RHS 保裸调用（auto_ingest._save_source / load_config 验证 / FeedConfig 验证 / _get_strawberry guard / WebhookEvent ctor / transform_to_claim / selector.get_sync_cursors 等 8 处）。FeishuUser.from_event 的 `sender` 是**已用**变量（脚本误删首现，git 核验后恢复）——教训：批量 replace 首现对同名变量危险，逐文件核。
- **F401 级联（4 处）**：Z-6 删赋值后 4 import 变 orphan（FreshnessTracker / Optional / datetime,timezone），即清。

### CMS drift 核验（ground 自源码）
- F-I-1：WorkflowExecutor state machine M-16（`workflow_executor.py:_WORKFLOW_TRANSITIONS` + `validate_workflow_transition`）+ HI-9 `_persist_workflow`（upsert workflow_executions v4 表）+ startup recovery（`app.py:_recover_stranded_workflows`）均**已落地**——PRD 原 [TBD] 风险消解，已回更 PRD。
- F-Z-7：migration v8 `claim.workspace_id`（default 'default'）+ `user_workspace_auth` 存在；但 QueryEngine/IngestPipeline/claims repo search 0 workspace 引用（grep 确认）→ 确证 H2 gap 真实。
- F-Z-8：`CedarPolicyEngine.reload()`（`cedar_policy.py`）已实现（AC-SEC-5），gap 仅 CLI surface。

### Deferred / [TBD]
- **F-Z-7 全路径**：graph_traverse / tree_mode / compiler / ingest-write 的 workspace scope 注入——下一周期专项。
- **F-I-1 resume 全量 context 快照**：v2.0（需序列化 context dict）。
- **F-Z-8 Web admin 端点 `POST /api/admin/policy/reload`**：本轮仅 CLI，Web 端点 thin。
- **coverage 65%+**：query engine.py / compare / tree_mode 深覆盖——下一周期随测试增长 ratchet。

## 2026-09-03 — v1.6.0 债务收口（4 Task，2 Wave，Lead 单线）

**范围**：F-J-1（tree_mode+compiler workspace 读路由）/ F-J-2（insert 持久化+ingest 透传）/ F-J-3（query 深覆盖）/ F-J-4（policy Web admin 端点）。
**Commits**：627957b(Wave1) / 895c948(Wave2)。
**测试**：1959 passed / 3 skipped / 0 failed（+30 新测试）；ruff 0；coverage 63.7%；smoke 6/6。

### 决策与偏离
- **F-J-1 scope 透传方式**：tree_mode/compiler 加 workspace_id 参数；QueryEngine.__init__ 用 setattr 同步 `_workspace_id` 到子服务（而非改 search/compile 签名）——最小侵入，匹配既有耦合（getattr(_wiki_repo) 模式）。
- **F-J-2 insert 列补全（ADR-008）**：v1.5.0 发现 insert SQL 丢 workspace_id（Claim.workspace_id 字段存但落库总 default）。补 INSERT 列；ingest(workspace_id=) stamp claims。upsert UPDATE 分支不动 workspace_id（防覆盖）。
- **F-J-4 Web 端点保护位置**：admin router 的 require_role 守卫放 include_router 级（dependencies=admin_auth_dep）而非 route 装饰器——为过 test_security_matrix（源码扫 include_router 的 auth_dep）。
- **F-J-3 AC-COV-2 未达 65（关键偏离）**：TMS-DELTA 原写"63→65"。query 深覆盖完成（engine 14→94% / compare 23→91% / tree_mode 21→66%），但**全量仅 63.7%**——gap 在非 query 模块（compile/compiler 17% / synthesize/scheduler 32%）。硬约定 #10：不设高于实测。Lead 决策 fail_under 持 63（63.7% 有余量，无回归），65 标 finding J1 defer v1.7.0。

### CMS drift 核验
- F-J-1：v1.5.0 repo.get_by_id(workspace_id) 已支持→不改 repo；tree_mode/compiler 调 get_by_id 未传 ws（grep 确证）→本轮补。
- F-J-2：Claim.workspace_id 字段存（domain/claims.py:37）但 insert SQL 无 workspace_id 列（claims_repository.py:155 原 SQL）→确证 gap，补列。
- F-J-4：app.state.cedar v1.4.0 P-1 已装配（app.py）；require_role 就绪。

### Deferred / [TBD]
- **J1（coverage 65）**：compile/compiler.py（17%）/ synthesize/scheduler.py（32%）深覆盖——v1.7.0。
- **graph_traverse workspace 隔离**：entity 表无 workspace_id 列（需 migration）→defer v1.7.0+。
- **resume 全量 context 快照**（I3）：v2.0。
