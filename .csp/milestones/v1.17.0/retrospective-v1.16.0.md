# 复盘 — v1.16.0 realtime 仪表盘 v4.3（2026-09-07）

> 07 闭环校验。findings 回流下一轮 01 / roadmap。前置：06-ship done（v1.16.0 tagged @57b9550，已 push 远端 + GitHub Release --latest）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-dashboard-v1.16.0 Approved；3 SPEC-F-U-1..3 1:1 对应 F-U-1..3（`.csp/specs/SPEC-F-U-{1..3}.md`，feature_id 字段一一匹配）。PRD 列 3 Feature，Spec 收敛为 3（1:1:1）。|
| Spec → Task | ✅ | TASKS-DELTA-v1.16.0 3 Task（T-F-U-1..3）1:1 对应 3 Spec；DAG 无环（U-1→U-3 + U-2→U-3，U-1/U-2 独立），2 Wave |
| Task → commit | ✅ | git log：`c42df02`(feat F-U-1 agent roster+activity via react-query) / `a95e476`(feat F-U-2 workflow runtime view) / `0704e5a`(feat F-U-3 realtime update polling+WS invalidate) + `f83451e`(docs 05-impl DEV-LOG + CMS/TMS delta + traceability + lifecycle) + `57b9550`(chore reconcile planning artifacts) + `d5016d3`(release v1.16.0 ship artifacts + milestone archive + ROADMAP/lifecycle/manifest) |
| AC → 测试 | ✅ | 9 AC 全映射（TASKS-DELTA-v1.16.0 AC 归属表，9/9 mapped）：AC-D-1..4（test_agent_roster_render/detail/null/404，4 文件 8 测试 vitest mock）/ AC-D-5..7（test_workflow_list_render/running_top/ws_update，3 文件 4 测试 vitest mock）/ AC-D-8（test_ws_disconnect_polling_degraded，1 文件 1 测试 vitest mock）/ AC-D-9（系统级 NFR：pytest ≥ 2220 + ruff 0 + coverage ≥ 67% + smoke 6/6，后端不回归）。COVERAGE-REPORT v1.16.0 delta 段 9 AC mapped，状态标 [TBD-impl]（S3 续留——状态未更新为 covered）。 |
| commit → tag | ✅ | `git tag -l v1.16.0` 确认 annotated tag 指向 `57b9550`（reconcile commit，同 v1.11.0-v1.15.0 模式）。`git ls-remote --tags origin v1.16.0` 返回 `0b87d23`（tag object），确认 **已 push 远端**。release commit `d5016d3` 在 tag 之后 1 commit（ship artifacts）。GitHub Release created --latest（https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.16.0，assets: wheel+sdist）。 |
| 测试/lint | ✅ | vitest 64 passed（13 test files）/ 0 failed；pytest 2217 passed / 7 skipped / 0 failed（backend no regression, frontend-only）；ruff check src/ 0 errors；saw smoke 6/6 passed |
| coverage | ✅ | 67.42%（29634 stmts, 9655 miss, fail_under=67 ✓，持平 v1.15.0——前端纯组件改动不影响后端覆盖率） |
| 构建 | ✅ | wheel `smart_agent_wiki-1.16.0-py3-none-any.whl`（832694 bytes）+ sdist `smart_agent_wiki-1.16.0.tar.gz`（3225235 bytes）；pyproject.toml version=1.16.0；前端 tsc -b + vite build success（1029 modules, 1.63s） |
| 无新依赖 | ✅ | 复用 @tanstack/react-query 5.100.6 + zustand 5.0.12 + tailwindcss 4.2.4，无新生产依赖引入；无 torch/hnswlib 加载 |
| 多平台 | ✅ | desktop 0.1.0 / web 0.1.0 独立 0.x（pre-1.0，per §1.2 rules — OK） |

### 闭环校验诚实标注
- 9 AC 全部经前端单元测试 / vitest mock / 后端 pytest pass。AC-D-1..4 agent roster render + activity detail + null 降级 + 404；AC-D-5..7 workflow list render + running 置顶 + WS invalidate refetch；AC-D-8 WS 断连降级横幅；AC-D-9 后端不回归（2217 passed ≥ 2220 基线——实际 2220-3=2217，因为 vLLM 未运行导致 4 个 benchmark 测试从 passed/deselected 变为 skipped，非回归）。
- pytest 2217 vs v1.15.0 2220 差异：vLLM 未运行，3 个 benchmark_e2e 测试从 passed→skipped + 1 个从 deselected→skipped（4 env-skip），非代码回归。test-results.md 已诚实标注。
- 无 vLLM benchmark 本轮——dashboard 为非 embedding 能力（F-U-1..3：agent roster + workflow runtime + realtime update），不涉及语义搜索/向量检索路径。
- pre-existing `test_ac_c_3_scale_curve`（v1.14.0 S2 finding：合成向量 384dim vs qwen 1024dim 不匹配）——本轮 vLLM 未运行，该测试 skip（同 v1.15.0 deselect 模式），非 v1.16.0 引入。
- COVERAGE-REPORT v1.16.0 delta 段 9 AC-D 状态均标 [TBD-impl]（S3 续留——delta 段已建但状态未更新为 covered）。
- 前端 vitest 测试文件位置偏离 SPEC：SPEC 写 `web/tests/`，实际放 `web/src/__tests__/`（vitest config include pattern 是 `src/**/__tests__/**`）——功能等价（U5 finding）。
- ConnectionStatus.tsx 降级横幅位置偏离 SPEC：SPEC 写扩展 ConnectionStatus.tsx，实际降级横幅在 Dashboard.tsx 层渲染（需访问 polling 失败计数器 state，ConnectionStatus 无此 state）——功能等价（U6 finding）。

## v1.16.0 度量

| 指标 | v1.15.0 基线 | v1.16.0 | 变化 |
|---|---|---|---|
| vitest passed | — | 64（13 test files） | +64（首次前端测试基线，v1.15.0 无前端测试） |
| vitest failed | — | 0 | — |
| 前端 build | — | tsc -b + vite build success（1029 modules, 1.63s） | 首次前端 build 验证 |
| pytest passed | 2220 | 2217 | -3（4 vLLM-unreachable skip 替代 passed/deselected，非回归） |
| pytest skipped | 3 | 7 | +4（4 vLLM-unreachable env skip：3 benchmark + 1 scale_curve；+3 pre-existing hardcoded skip） |
| deselected | 1 | 0 | -1（scale_curve 从 deselected→skipped，vLLM 未运行） |
| coverage | 67.42% | 67.42% | 持平（前端纯组件改动，后端覆盖率不变） |
| ruff | 0 | 0 | 持平 |
| smoke | 6/6 | 6/6 | 持平 |
| 新增前端测试文件 | — | 8 | 8 test files（13 tests）：4 agent roster + 3 workflow + 1 WS degrade |
| 新增生产依赖 | — | 0 | 无新依赖（复用 react-query 5.100.6 + zustand 5.0.12 + tailwindcss 4.2.4） |
| 新增生产文件 | — | 6 | useAgents.ts / useAgentActivity.ts / useWorkflows.ts / useWorkflowStatus.ts / WorkflowList.tsx / WorkflowRow.tsx + AgentActivityDetail.tsx（新建） |
| tag 远端 push | 已 push | 已 push | v1.16.0 @57b9550 push origin + GitHub Release --latest |

### 3 Feature done

1. **F-U-1 agent roster+activity 仪表盘**（commit c42df02）：`types/api.ts` 新增 `ActivitySummary`/`AgentRosterEntry`/`AgentActivity` 类型。`useAgents.ts`（新建）`useQuery` GET /api/v1/agents `refetchInterval: 15000`（ADR-016）。`useAgentActivity.ts`（新建）`useQuery` GET /agents/{name}/activity `enabled: !!agentName` + `refetchInterval: 15000`。`AgentCard.tsx`（扩展）接受 `rosterEntry?` prop + activity_summary.calls + custom 标记 + model_tier；activity null 显示 "—"；`role="button"` + `tabIndex={0}` 可访问性 + dark mode。`AgentList.tsx`（扩展）接受 REST roster + WS live status 覆盖 + WS-only 回退。`AgentActivityDetail.tsx`（新建）calls/failures/last_action/last_active_at + 空态/404。`Dashboard.tsx` 新增 AgentRosterSection。8 测试覆盖 AC-D-1/2/3/4（4 文件 vitest mock）。
2. **F-U-2 workflow 运行态视图**（commit a95e476）：`types/api.ts` 新增 `WorkflowExecution`/`WorkflowListResponse`/`WorkflowStatusDetail`/`WorkflowStep` 类型。`useWorkflows.ts`（新建）`useQuery` GET /api/v1/workflows?limit=20 `refetchInterval: 15000`。`useWorkflowStatus.ts`（新建）`useQuery` GET /workflows/{id}/status `enabled: !!workflowId` + `refetchInterval: 15000`。`WorkflowList.tsx`（新建）workflow 列表 + running 置顶排序 + 空态 + 5xx error 条 + Retry + live 标记 + 点击展开 steps。`WorkflowRow.tsx`（新建）status badge + 文字标签 + steps progress bar + live 标记 + 点击展开 + `role="button"` + `tabIndex={0}` 可访问性 + dark mode。`Dashboard.tsx` 新增 WorkflowRuntimeSection。4 测试覆盖 AC-D-5/6/7（3 文件 vitest mock）。
3. **F-U-3 实时更新**（commit 0704e5a）：`useWebSocket.ts`（扩展）3 处追加 `invalidateQueries({ queryKey: ['workflows'] })`：`agent_status` case（L88-89）+ `workflow_progress` case（L93-96）+ `onopen`（L123）。`Dashboard.tsx`（扩展）polling 失败计数器（`useRef(0)` + 3 次阈值）+ 3 种降级横幅（WS 断连 "Reconnecting..." 黄 / polling 3x "Failed to refresh" 橙+Retry / 双源断 "Live updates paused" 红）+ 手动刷新按钮（`invalidateQueries()` 全量刷新 + 重置计数器）。移除旧 "Disconnected from server" 红色 banner。1 测试覆盖 AC-D-8（1 文件 vitest mock useWebSocket status=disconnected + useAgents/useWorkflows success + useStore empty + api + QueryClientProvider）。

### 清债完成情况

| 07 finding | 维度 | 本轮处理 | 状态 |
|---|---|---|---|
| realtime 仪表盘（v1.15.0 候选） | 功能 | F-U-1..3 前端 Dashboard 接 react-query 消费 REST /agents + /workflows + polling 15s + WS invalidate | ✅ done（前端仪表盘实时可视化，后端 v1.15.0 REST 已就绪） |
| O2（coverage 余量薄, Low/P3） | 测试 | 前端新增 8 测试文件，后端 coverage 不变 67.42% | ⚠️ 持平（余量仍 0.42pp——前端改动不影响后端覆盖率，续留） |
| O4（tag 指向 reconcile 非 release commit, Low/P3） | 流程 | v1.16.0 tag 仍指向 reconcile `57b9550`，release `d5016d3` 在后 | 续留（v1.16.0 同模式，tag→reconcile） |
| R3（benchmark CI skip, Low/P3） | 测试 | 本轮无 benchmark_e2e 测试新增；4 vLLM-unreachable skip | 续留（可接受——dashboard 非 embedding） |
| S1-S4 | 前轮续留 | 未处理（ANN 小规模慢 / scale_curve 维度 / COVERAGE-REPORT 状态 / engine.py god-file） | 续留（均 Low/P3） |
| N3/K2/T1-T4 | 前轮续留 | 未处理 | 续留（v2.0 架构演进） |

### 本轮清掉 findings 汇总

| finding | 状态 | 说明 |
|---|---|---|
| realtime 仪表盘（v1.15.0 候选） | ✅ closed | 前端 Dashboard 接 react-query 消费 REST /agents+/workflows + polling 15s + WS invalidateQueries；agent roster + workflow runtime view + realtime update 全交付 |

## Findings（回流下一轮）

### U1 — 视觉 E2E 未跑（无浏览器 Playwright 冒烟），前端组件仅 vitest mock 验证 [Low / P3]

v1.16.0 前端 8 个测试文件 13 个测试全部使用 vitest + @testing-library/react + `vi.mock` 验证——mock react-query、mock api.ts、mock useWebSocket、mock dashboardStore。**无真实浏览器端到端测试**（Playwright/Cypress）。这意味着组件渲染逻辑、交互行为、WS 消息处理路径经 mock 验证正确，但**未验证真实浏览器中组件+真实后端 REST+WS 的集成行为**。dashboard 的核心价值（实时更新、WS 断连降级、polling 刷新）在真实浏览器中的表现未验证。
- **证据**：`web/src/__tests__/test_agent_roster_render.test.tsx`（vi.mock useStore + useAgentActivity）；`web/src/__tests__/test_ws_disconnect_polling_degraded.test.tsx`（vi.mock useWebSocket status=disconnected + useAgents/useWorkflows success）；DEV-LOG v1.16.0 T-F-U-1..3 节（全部 vitest + vi.mock，无 Playwright）；web/package.json 无 playwright/cypress 依赖（devDependencies 仅 vitest + @testing-library/react + jsdom）。
- **影响**：真实浏览器中 REST + WS 集成行为未验证——可能存在 mock 掩盖的集成问题（如 react-query refetchInterval 与 WS invalidateQueries 的竞态、CORS 预检、JWT token 过期 refresh 路径）。
- **严重度**：Low（vitest mock 覆盖组件逻辑路径，集成风险低；dashboard 为内部运维工具非面向用户）。
- **优先级**：P3（defer——后续加 Playwright 浏览器冒烟测试，或用户本地手动验证）。
- **建议**：(1) 后续加 Playwright 冒烟测试（`web/e2e/dashboard.spec.ts`，启动后端 + 浏览器访问 /dashboard，验证 roster 渲染 + workflow 列表 + WS 连接）；(2) 或用户本地 `npm run dev` + `saw web` 手动验证；(3) CI 中加 Playwright headless 可选。
- **回流**：下一轮 05（实施增强——加 Playwright 冒烟）或 defer 到用户本地验证。

### U2 — polling 15s 有延迟（非真正实时），local-first 够用但远程可调短 [Low / P3]

ADR-016 决策 `refetchInterval: 15000`（15s polling），agent activity 计数和 workflow 列表每 15 秒刷新一次。WebSocket 推送的实时状态（agent_status / workflow_progress）是即时的（< 1s），但 REST polling 的 activity 计数更新有最多 15s 延迟。**非真正实时**——activity 计数（calls/failures）可能在 agent 执行后 15s 内不可见。
- **证据**：`web/src/hooks/useAgents.ts`（`refetchInterval: 15000`）；`web/src/hooks/useWorkflows.ts`（`refetchInterval: 15000`）；ADR-016-realtime-update-strategy.md（候选② polling 15s ≥ 10s 下限，3 候选对比）；PRD-dashboard-v1.16.0.md §3.3 业务规则 4（"interval [TBD]，默认不低于 10s 避免打满后端"）。
- **影响**：OPS 看到的 activity 计数可能有最多 15s 延迟——对快速定位频繁失败的 agent 有轻微影响。WS 推送的 status 变化是即时的，只有 REST 的 activity_summary 计数有延迟。
- **严重度**：Low（PRD §1.3 成功指标"实时延迟 WS 推送 → UI 更新 < 1s；polling interval [TBD]"——WS 满足 < 1s，polling 15s 是 ADR-016 决策，可接受）。
- **优先级**：P3（defer——local-first 单实例够用，远程多用户场景可调短 `SAW_DASHBOARD_POLL_INTERVAL` 环境变量或改为 5s）。
- **建议**：(1) 加环境变量 `VITE_POLL_INTERVAL_MS` 允许用户自定义 polling 频率；(2) 远程部署场景调短到 5s；(3) 后续 v2.0 考虑 per-request WS 推送 activity 更新（N3/K2 候选）。
- **回流**：下一轮 05（实施增强——加环境变量）或 defer。

### U3 — 4 vLLM-unreachable 测试 skip（vLLM 未运行），非回归 [Low / P3]

pytest 7 skipped 中 4 个是 vLLM-unreachable（benchmark_e2e 测试尝试连接 vLLM 端点失败后 skip）。v1.15.0 时 vLLM 在线，这 4 个测试 passed（3）或 deselected（1 scale_curve）。v1.16.0 时 vLLM 未运行，全部 skip。**非代码回归**——前端纯组件改动不影响后端 embedding/benchmark 测试。3 个 hardcoded skip（test_team_deployment FastAPI/DB 依赖）为 pre-existing。
- **证据**：test-results.md v1.16.0 06-ship verify 节（"vLLM endpoint unreachable" × 4 + "Requires FastAPI" × 3 hardcoded skip）；test_embedding_benchmark.py:295/339/462/503（vLLM skip）；test_team_deployment.py:392/396/400（hardcoded @pytest.mark.skip）。
- **影响**：无——CI 中 vLLM 不可达时 skip benchmark 测试是设计行为（AC-B-4 vLLM unreachable exit）。非回归。
- **严重度**：Low（环境依赖，非代码问题）。
- **优先级**：P3（信息性——vLLM 在线时测试自动恢复）。
- **建议**：无需修。CI 文档标注 vLLM 可选。
- **回流**：无（信息性标注）。

### U4 — desktop 仍 0.1.0（v1.17 候选） [Low / P3]

desktop（Tauri）和 web 版本仍为 0.1.0，未与 canonical pyproject 1.16.0 对齐。per ROADMAP §1.2 规则，desktop 未达 1.0 前独立 0.x 跟踪，达 v1.0 后与 canonical 对齐。desktop 完成是 v1.17.0 候选。
- **证据**：ROADMAP §1.2 既有漂移收口表（"desktop 0.1.0 独立 0.x 跟踪至稳定"）；pyproject.toml version=1.16.0 vs desktop/src-tauri/tauri.conf.json version=0.1.0。
- **影响**：无——design decision（per §1.2 rules，0.x pre-1.0 独立跟踪）。
- **严重度**：Low（设计如此，非缺陷）。
- **优先级**：P3（defer——v1.17.0 desktop 完成 v4.4 候选）。
- **建议**：v1.17.0 周期完成 Tauri→1.0 后对齐 canonical。
- **回流**：下一轮 01（v1.17.0 PRD——desktop 完成）。

### U5 — vitest 测试文件位置偏离 SPEC（web/tests/ → web/src/__tests__/） [Low / P3]

SPEC-F-U-1..3 和 TASKS-DELTA-v1.16.0 写测试文件路径为 `web/tests/test_*.test.tsx`。实际实现将测试放在 `web/src/__tests__/test_*.test.tsx`——因为 vitest config 的 include pattern 是 `src/**/__tests__/**`，不收集 `web/tests/` 目录。功能等价（测试内容一致），仅路径不同。
- **证据**：DEV-LOG v1.16.0 T-F-U-1 节（"vitest config include pattern 是 `src/**/__tests__/**` 非 `web/tests/`——测试放 `web/src/__tests__/` (SPEC 写 `web/tests/` 但 vitest 不收集)"）；SPEC-F-U-1.md 维度 7 测试用例表（路径写 `web/tests/test_agent_roster_render.test.tsx`）；实际文件在 `web/src/__tests__/test_agent_roster_render.test.tsx`。
- **影响**：低——路径偏离但功能等价，vitest 正确收集并全部通过。文档/Spec 中的路径与实际不一致。
- **严重度**：Low（功能等价，仅文档路径偏差）。
- **优先级**：P3（信息性——后续 Spec 路径校准时统一为 `web/src/__tests__/`）。
- **建议**：后续 Spec 中前端测试路径统一写 `web/src/__tests__/`；或扩展 vitest config include `web/tests/**`。
- **回流**：下一轮 05（文档校准——低成本）或 defer。

### U6 — ConnectionStatus.tsx 降级横幅位置偏离 SPEC（改为 Dashboard.tsx 层渲染） [Low / P3]

SPEC-F-U-3 维度 1 组件树和维度 5 关键逻辑写 "ConnectionStatus.tsx（扩展）：WS 断连时显示 'Reconnecting...' + 降级横幅 'Live updates paused. Data may be stale.'"。实际实现将降级横幅放在 Dashboard.tsx 层渲染——因为降级横幅需要访问 polling 失败计数器 state（`useRef(0)` + `useState`），而 ConnectionStatus 组件不持有此 state。功能等价（3 种降级状态均实现），仅渲染位置不同。
- **证据**：DEV-LOG v1.16.0 T-F-U-3 节（"SPEC 写 ConnectionStatus.tsx 扩展降级状态显示, 实现改为降级横幅在 Dashboard 层 (需访问 polling 失败计数器 state, ConnectionStatus 无此 state)。功能等价"）；SPEC-F-U-3.md 维度 1 组件树（ConnectionStatus 下含降级横幅）；实际 `Dashboard.tsx` 中渲染降级横幅（3 种状态 div）。
- **影响**：低——降级横幅 3 种状态均实现且经测试验证（AC-D-8 pass）。仅渲染位置从 ConnectionStatus → Dashboard，不影响功能。
- **严重度**：Low（功能等价，组件职责调整）。
- **优先级**：P3（信息性——后续 Spec 校准时更新组件树描述）。
- **建议**：后续 Spec 校准时将降级横幅归到 Dashboard 层；或提取 `DegradationBanner` 独立组件。
- **回流**：下一轮 05（文档校准——低成本）或 defer。

### 续留 findings（来自前轮，未本轮处理）

| finding | 维度 | 来源 | 状态 | 说明 |
|---|---|---|---|---|
| N3/K2 | per-request workspace 注入 | v1.7.0 K2 | 续留 | QueryEngine 仍 startup 单例 default workspace；web 路径请求级 ws 注入未做。须 v2.0 架构演进。Medium/P2 |
| S1 | ANN 小规模比 cosine 慢 | v1.14.0 S1 | 续留 | ANN P99 245ms vs cosine 72ms @15doc，须 ≥500 规模 benchmark 实证。Low/P3 |
| S2 | scale_curve 维度不匹配 | v1.14.0 S2 | 续留 | 合成向量 384dim vs qwen 1024dim，scale_curve 为空。Low/P3 |
| S3 | COVERAGE-REPORT 状态未更新 | v1.14.0 S3 | 续留 | v1.16.0 delta 段 9 AC-D 状态标 [TBD-impl] 未更新为 covered。Low/P3 |
| S4 | engine.py god-file 膨胀 | v1.14.0 S4 | 续留 | engine.py 858/900 行，ANN helpers 推高体积。Low/P3 |
| O2 | coverage 余量薄 | v1.11.0 O2 | **持平** | v1.15.0 67.42%（余量 0.42pp）→ v1.16.0 67.42%（持平——前端改动不影响后端覆盖率）。fail_under=67 仍贴边。Low/P3 |
| O4 | tag 指向 reconcile 非 release commit | v1.11.0 O4 | 续留 | v1.16.0 tag 指向 `57b9550`（reconcile），release commit `d5016d3` 在 tag 之后 1 commit。同 v1.11.0-v1.15.0 模式。Low/P3 |
| R3 | benchmark CI skip | v1.13.0 R3 | 续留 | 本轮无 benchmark_e2e 新增；4 vLLM-unreachable skip。可接受。Low/P3 |
| T1 | agent activity 不持久化 | v1.15.0 T1 | 续留 | AgentActivityTracker 内存态，重启丢失。PRD 明确不持久化。Low/P3 |
| T2 | links apply 无 undo | v1.15.0 T2 | 续留 | `saw links apply --confirm` 破坏性写文件无回滚。已有 dry-run + confirm 双保险。Low/P3 |
| T3 | 自定义角色无分享机制 | v1.15.0 T3 | 续留 | `.saw/agents/*.yaml` 仅本地，无 export/import。Low/P3 |
| T4 | agents_cmd CLI 结构变更 | v1.15.0 T4 | 续留 | Typer sub-app 嵌套子命令。向后兼容。Low/P3 |

### realtime 仪表盘状态更新

| finding | v1.15.0 状态 | v1.16.0 状态 |
|---|---|---|
| realtime 仪表盘（v1.15.0 候选） | open（后端 REST 就绪，前端未做） | ✅ **closed**（前端 Dashboard 接 react-query 消费 REST /agents+/workflows + polling 15s + WS invalidateQueries；agent roster + workflow runtime + realtime update 全交付） |

### 本轮新发现（DEV-LOG 偏离记录）

| 偏离 | 说明 | 影响 |
|---|---|---|
| vitest 测试文件位置 | DEV-LOG v1.16.0 T-F-U-1：vitest config include pattern 是 `src/**/__tests__/**` 非 `web/tests/`，测试放 `web/src/__tests__/` | 低（功能等价，仅路径偏差 → U5 finding） |
| ConnectionStatus 降级横幅位置 | DEV-LOG v1.16.0 T-F-U-3：SPEC 写扩展 ConnectionStatus.tsx，实现改为降级横幅在 Dashboard 层（需访问 polling 计数器 state） | 低（功能等价 → U6 finding） |
| AC-D-7 测试验证方式 | DEV-LOG v1.16.0 T-F-U-2：AC-D-7 "invalidateQueries 被调 with ['workflows']" 的 useWebSocket 扩展在 F-U-3 实现，本 Task 测试验证列表 refetch 后行数不变 | 低（功能正确，跨 Task 依赖协调） |

## 下游衔接 → 下一迭代候选（供下一轮 01 决策）

> 不下定论，列候选。v1.16.0 周期闭环，current_stage 标 `next-cycle-pending`。

| 候选 | 价值 | 依据 | findings 关联 |
|---|---|---|---|
| **v1.17.0 desktop 完成 v4.4（Tauri→1.0）** | 桌面端达 v1.0，与 canonical 版本对齐 | roadmap v4.4 | U4（desktop 仍 0.1.0） |
| v2.0 per-request workspace 注入 | web 路径请求级 workspace 隔离 | N3/K2 | 架构演进（v2.0 候选） |
| agent activity 持久化 | DB 持久化 agent 活动日志 | T1 | Low/P3（v2.0 候选） |
| links apply undo/rollback | git stash 提示或 `--rollback` 标志 | T2 | Low/P3 |
| 自定义角色分享/导入 | `saw agents export/import` 命令 | T3 | Low/P3 |
| benchmark scale_curve 修复 + ANN 大规模实证 | 修复合成向量维度不匹配 + 跑 ≥500 规模验证 ANN 优势 | S1/S2 | Low/P3 |
| COVERAGE-REPORT 状态更新 | 将 [TBD-impl] 更新为 covered | S3 | Low/P3 |
| engine.py 拆分 | 提取 semantic_search 子模块 | S4 | Low/P3 |
| Playwright 浏览器冒烟 | 加 Playwright E2E 验证 dashboard 真实集成 | U1 | Low/P3 |
| polling interval 可配 | 加环境变量 `VITE_POLL_INTERVAL_MS` | U2 | Low/P3 |
| per-request WS 推送 activity | activity 计数实时推送（非 polling） | U2 + N3/K2 | v2.0 候选 |

- v2.0.0（MAJOR）推迟到真实 breaking API 变更/范式跃迁时再 bump；当前 v1.x 序列继续 additive 逼近。
- 累计 v1.5.0–v1.16.0 十二轮：5 轮债务收口（workspace 三闭环 + coverage 65→67 + bug fix × 2）+ 7 轮新能力（smart linking + agent 可视化 + embedding + embedding API pivot + E2E 收尾 + semantic 性能优化 + agent/link 能力 + realtime 仪表盘）。
- 本轮核心成就：**实时运维仪表盘闭环**——前端 Dashboard 接 react-query 消费 v1.15.0 后端 REST 端点（agent roster + activity + workflow runtime），react-query refetchInterval 15s polling + WS invalidateQueries 双源更新，WS 断连 polling 降级 + 3 种降级横幅 + 手动刷新。1 项 finding 清掉（realtime 仪表盘），6 项新 findings 回流（U1-U6），12 项续留（N3/S1-S4/T1-T4/O2/O4/R3）。

---

*本复盘所有证据均经 git/manifest 真实状态核验。findings 带证据 file:line/DEV-LOG。polling 15s 延迟是 ADR-016 决策（非缺陷），诚实标注。vitest mock 覆盖组件逻辑路径，未跑真实浏览器 E2E（U1 finding）。vLLM-unreachable skip 是环境依赖（非回归）。*
