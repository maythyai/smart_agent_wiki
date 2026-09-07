# 复盘 — v1.15.0 agent/link 能力（2026-09-06）

> 07 闭环校验。findings 回流下一轮 01 / roadmap。前置：06-ship done（v1.15.0 tagged @d5b644f，已 push 远端 + GitHub Release --latest）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-agent-link-v1.15.0 Approved；3 SPEC-F-T-1..3 1:1 对应 F-T-1..3（`.csp/specs/SPEC-F-T-{1..3}.md`，feature_id 字段一一匹配）。PRD 列 3 Feature，Spec 收敛为 3（1:1:1）。|
| Spec → Task | ✅ | TASKS-DELTA-v1.15.0 3 Task（T-F-T-1..3）1:1 对应 3 Spec；DAG 无环（3 Task 互相独立，无边），1 Wave 全并行 |
| Task → commit | ✅ | git log：`53cd582`(feat F-T-1 custom agent role registry YAML+CLI+REST) / `8f6ad2b`(feat F-T-2 links auto-apply confirm+dry-run) / `59f9552`(feat F-T-3 agent activity aggregation event_bus subscriber+REST/CLI) + `570eaf6`(docs 05-impl DEV-LOG + CMS/TMS delta + traceability + lifecycle) + `d5b644f`(chore reconcile planning artifacts) + `62f0d90`(release v1.15.0 ship artifacts + milestone archive + ROADMAP/lifecycle/manifest) |
| AC → 测试 | ✅ | 12 AC 全映射（TASKS-DELTA-v1.15.0 AC 归属表，12/12 mapped）：AC-A-1..4（test_custom_agents.py 7 用例 + test_agents_api.py AC-A-4）/ AC-B-1..4（test_links_apply.py 4 用例 mock compute_related_pages）/ AC-C-1..4（test_agent_activity.py 8 用例 + test_agents_api.py AC-C-3/4）。COVERAGE-REPORT v1.15.0 delta 段 12 AC mapped。 |
| commit → tag | ✅ | `git tag -l v1.15.0` 确认 annotated tag 指向 `d5b644f`（reconcile commit，同 v1.11.0-v1.14.0 模式）。`git ls-remote --tags origin v1.15.0` 返回 `ea5decd`（tag object），确认 **已 push 远端**。release commit `62f0d90` 在 tag 之后 1 commit（ship artifacts）。GitHub Release created --latest（https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.15.0，assets: wheel+sdist）。 |
| 测试/lint | ✅ | 2220 passed / 3 skipped / 1 deselected (pre-existing S2 scale_curve) / 0 failed；ruff check . 0 errors；saw smoke 6/6 passed |
| coverage | ✅ | 67.42%（29634 stmts, 9655 miss, fail_under=67 ✓，较 v1.14.0 67.34% +0.08pp） |
| 构建 | ✅ | wheel `smart_agent_wiki-1.15.0-py3-none-any.whl`（832KB）+ sdist（3.1MB）；pyproject.toml version=1.15.0 |
| 无新依赖 | ✅ | 复用既有 yaml/typer/fastapi，无新生产依赖引入；无 torch/hnswlib 加载 |
| 多平台 | ✅ | desktop 0.1.0 / web 0.1.0 独立 0.x（pre-1.0，per §1.2 rules — OK） |

### 闭环校验诚实标注
- 12 AC 全部经单元测试 / mock / 文件断言 pass。AC-A-1..4 自定义角色注册+validate+重名跳过+REST custom:true；AC-B-1..4 dry-run 不写回/confirm 写回 ## Related+related 同步/去重不重复/audit 无新断链；AC-C-1..4 事件聚合/空活动/404/agents 端点含 activity_summary。
- 无 vLLM benchmark 本轮——agent/link 为非 embedding 能力（F-T-1..3：自定义角色 + links apply + 活动聚合），不涉及语义搜索/向量检索路径。
- pre-existing `test_ac_c_3_scale_curve` 1 deselected（v1.14.0 S2 finding：合成向量 384dim vs qwen 1024dim 不匹配，vLLM-env 依赖），非 v1.15.0 引入。
- examples/demo `utils.py:42` F841 lint fix（pre-existing，ruff 0.16.5 捕获，非本轮功能代码）。

## v1.15.0 度量

| 指标 | v1.14.0 基线 | v1.15.0 | 变化 |
|---|---|---|---|
| pytest passed | 2192 | 2220 | +28（7 custom agents + 4 links apply + 8 agent activity + 9 agents API 扩展） |
| skipped | 3 | 3 | 持平（1 fsrs importorskip + 2 pre-existing） |
| deselected | 4 | 1 | -3（v1.14.0 benchmark_e2e 4→1 pre-existing S2 scale_curve；agent/link 无 benchmark_e2e） |
| coverage | 67.34% | 67.42% | +0.08pp（fail_under=67 持平，余量从 0.34pp 升至 0.42pp） |
| ruff | 0 | 0 | 持平 |
| smoke | 11/11 | 6/6 | -5（v1.14.0 smoke chain 扩展 11→v1.15.0 回到 6/6 标准；功能无损） |
| 新增测试文件 | — | 3 | test_custom_agents.py / test_links_apply.py / test_agent_activity.py + 扩 test_agents_api.py |
| 新增生产依赖 | — | 0 | 无新依赖（复用 yaml/typer/fastapi） |
| 新增生产文件 | — | 1 | src/saw/engines/collaborate/activity_tracker.py（AgentActivityTracker 类） |
| tag 远端 push | 已 push | 已 push | v1.15.0 @d5b644f push origin + GitHub Release --latest |

### 3 Feature done

1. **F-T-1 自定义 agent 角色注册**（commit 53cd582）：`agents/__init__.py` 新增 `load_custom_agents(llm_router, agents_dir)` 扫描 `.saw/agents/*.yaml`（`yaml.safe_load` + name/model_tier/system_prompt/tools_allowed/constraints 校验 + 重名跳过 warning + 非法 model_tier 跳过 + 空 prompt 跳过 + 目录不存在降级）+ 新增 `build_agent_roster(llm_router, feedback_engine)` additive 合并 `build_default_agents` + custom（不改 `build_default_agents` 源码/签名）。`collaborate.py` `list_agents()` 改调 `build_agent_roster` + `custom: true/false` 标记。`agents_cmd.py` CLI 输出含 `custom` 列。`workflow_parser.py` `validate()` available_agents 含自定义角色。`workflow_cmd.py` lint 改调 `build_agent_roster`。`app.py` `create_app_from_config` engine agents 改调 `build_agent_roster`。7 测试覆盖 AC-A-1/2/3 + AC-A-4。
2. **F-T-2 links auto-apply**（commit 8f6ad2b）：`links_cmd.py` 新增 `apply` 子命令 `saw links apply <page> [--confirm] [--top N] [--dry-run] [--suggestion <slug>]`。复用 `compute_related_pages` suggest 逻辑 + `extract_unique_targets` 去重 → 默认 dry-run 打印表格不写回 → `--confirm` 写回 `WikiRepository.write()`（`## Related` 段落追加 `[[link]]` 或新建段落 + frontmatter `related` 字段同步）。pre-filter + write-back double-check 双重去重。单页写回失败不中断。4 测试覆盖 AC-B-1/2/3/4。mock `compute_related_pages`，tmp_path wiki，无 embedding/vLLM。
3. **F-T-3 agent 活动聚合**（commit 59f9552）：新建 `activity_tracker.py` `AgentActivityTracker` 类 — `subscribe(event_bus)` 调 `add_subscriber("WorkflowStep", handler)` + `_handle_event` 解析 `{agent}.{action}` + `status` 更新内存计数器（calls/failures/last_action/last_active_at）+ handler try/except 不传播 + `get_activity(name)` 返回聚合 + `get_summary(name)` 返回紧凑摘要或 None。`collaborate.py` 新增 `GET /api/v1/agents/{name}/activity` 端点（200 有活动/200 空活动 calls=0/404 agent 不存在）+ `list_agents()` 扩展 `activity_summary` 字段。`app.py` lifespan 初始化 tracker + subscribe event_bus + 模块级单例。`agents_cmd.py` 转为 Typer sub-app — `saw agents` list roster（向后兼容）+ 新增 `saw agents activity <name>` 子命令。8 测试覆盖 AC-C-1/2 + AC-C-3/4。

### 清债完成情况

| 07 finding | 维度 | 本轮处理 | 状态 |
|---|---|---|---|
| M2（agent "最近活动" 聚合, Medium/P2） | 可观测性 | F-T-3 AgentActivityTracker event_bus subscriber + REST/CLI activity 端点 | ✅ done（M2 闭合——agent 活动聚合 event_bus 订阅 + `GET /api/v1/agents/{name}/activity` + `saw agents activity` CLI） |
| L2（链接自动 apply, Low/P3） | 功能 | F-T-2 `saw links apply` dry-run/confirm + 去重 + `## Related` 写回 + frontmatter 同步 | ✅ done（L2 闭合——links apply 命令实现，默认 dry-run + `--confirm` 写回） |
| 自定义 agent 角色（v1.5.0 留 v2.0 候选） | 功能 | F-T-1 `load_custom_agents` YAML + `build_agent_roster` additive 合并 | ✅ done（自定义角色闭合——YAML 注册 + CLI/REST/workflow 可见） |
| O2（coverage 余量薄, Low/P3） | 测试 | 新增 28 测试，coverage 67.34→67.42% | ⚠️ 改善（余量从 0.34pp 升至 0.42pp——微增但仍薄，续留） |
| O4（tag 指向 reconcile 非 release commit, Low/P3） | 流程 | v1.15.0 tag 仍指向 reconcile `d5b644f`，release `62f0d90` 在后 | 续留（v1.15.0 同模式，tag→reconcile） |
| R3（benchmark CI skip, Low/P3） | 测试 | 本轮无 benchmark_e2e 测试（agent/link 非 embedding），1 deselected 为 pre-existing S2 | 续留（可接受——CI 跑 mock 逻辑路径） |
| S1-S4 | 前轮续留 | 未处理（ANN 小规模慢 / scale_curve 维度 / COVERAGE-REPORT 状态 / engine.py god-file） | 续留（均 Low/P3） |
| N3/K2 | per-request workspace 注入 | 未处理 | 续留（v2.0 架构演进） |

### 本轮清掉 findings 汇总

| finding | 状态 | 说明 |
|---|---|---|
| M2 | ✅ closed | AgentActivityTracker + event_bus subscriber + REST/CLI activity 端点 |
| L2 | ✅ closed | `saw links apply` dry-run/confirm + 去重 + `## Related` 写回 + frontmatter 同步 |
| 自定义角色 | ✅ closed | `load_custom_agents` YAML + `build_agent_roster` additive 合并 + CLI/REST/workflow 可见 |

## Findings（回流下一轮）

### T1 — agent activity 内存聚合不持久化（重启丢失），后续若需持久化加 DB [Low / P3]

`AgentActivityTracker` 使用内存 `dict[str, dict]` 存储活动计数器，进程重启后全部活动数据丢失。PRD §3.3 业务规则 6 明确"活动聚合为内存态（进程重启后丢失），不持久化（持久化属 v2.0 候选）"——**设计如此，可接受**。但当前无任何持久化路径——若后续 OPS 需跨重启查看历史活动（如"最近 24h agent 调用次数"），需加 DB 持久化层（如 `agent_activity_log` 表 + 定期 flush 或 event-driven INSERT）。
- **证据**：`src/saw/engines/collaborate/activity_tracker.py`（`self._activities: dict[str, dict[str, Any]] = {}`，纯内存 dict）；PRD-agent-link-v1.15.0.md §3.3 业务规则 6；DEV-LOG v1.15.0 T-F-T-3 节（"内存计数器 calls/failures/last_action/last_active_at"）。
- **影响**：进程重启后 agent 活动数据清零——OPS 无法查看重启前的 agent 调用历史。当前可接受（单实例 local-first，重启频率低），但生产部署后需持久化。
- **严重度**：Low（PRD 明确不持久化，设计如此——非缺陷，是设计约束）。
- **优先级**：P3（defer——v2.0 架构演进时加 DB 持久化层，当前内存态满足 PRD 需求）。
- **建议**：后续 v2.0 周期加 `agent_activity_log` 表（migration），`_handle_event` 改为 INSERT 或 batch flush；`get_activity` 查 DB 聚合。或用 SQLite WAL + 定期 flush。
- **回流**：下一轮 01（v2.0 PRD 需求——agent 活动持久化）或 defer。

### T2 — links apply 破坏性写文件，已有 dry-run + confirm 保护，但无 undo 回滚 [Low / P3]

`saw links apply --confirm` 执行破坏性文件写回——向 wiki 页面追加 `## Related` 段落 + `[[link]]` 列表 + frontmatter `related` 字段同步。已有保护：(1) 默认 dry-run 不写回；(2) 须 `--confirm` 标志方写回；(3) 去重检查防止重复插入。但**无 undo/回滚机制**——一旦 `--confirm` 执行后想撤销，需手动编辑文件移除链接。PRD §3.2 未要求 undo，**可接受**。但建议后续加 git 回滚提示或 `--rollback` 标志。
- **证据**：`src/saw/drivers/cli/commands/links_cmd.py` apply 子命令（`--confirm` 写回 `WikiRepository.write()`，无 undo 路径）；PRD-agent-link-v1.15.0.md §3.2（无 undo 需求）；SPEC-F-T-2.md 异常处理表（无 undo 行）；DEV-LOG v1.15.0 T-F-T-2 节（"单页写回失败不中断"）。
- **影响**：用户 `--confirm` 后后悔，需手动编辑移除链接——无内置回滚。低风险（dry-run 默认 + confirm 双保险）。
- **严重度**：Low（已有 dry-run + confirm 双重保护，undo 非必须）。
- **优先级**：P3（defer——后续加 `--rollback` 或 git stash 提示）。
- **建议**：(1) apply confirm 前提示用户 `git stash` 或自动 stash；(2) 或记录 apply 前文件快照，`--rollback` 恢复；(3) 或 apply 后输出 "Run `git checkout {file}` to revert" 提示。
- **回流**：下一轮 05（实施增强——低成本，加 git 提示或 rollback 标志）。

### T3 — 自定义角色 YAML 仅本地 `.saw/agents/`，无分享/导入/导出机制 [Low / P3]

自定义 agent 角色通过 `.saw/agents/*.yaml` 文件注册，角色定义仅存在于本地文件系统——无分享、导入、导出机制。团队 A 注册的 `MedicalExpert` 角色无法直接共享给团队 B（需手动复制 YAML 文件）。PRD 未要求分享机制，**可接受**（local-first 设计）。但后续若需团队协作共享角色，需加导入/导出命令或角色仓库。
- **证据**：`src/saw/engines/collaborate/agents/__init__.py` `load_custom_agents()`（扫描 `.saw/agents/*.yaml`，无导入/导出路径）；PRD-agent-link-v1.15.0.md §3.1（仅本地 `.saw/agents/` 目录，无分享需求）；DEV-LOG v1.15.0 T-F-T-1 节（"YAML 加载 + additive 合并"）。
- **影响**：角色定义无法跨实例/团队共享——需手动复制 YAML 文件。低影响（local-first 设计，单实例为主）。
- **严重度**：Low（PRD 未要求，设计约束）。
- **优先级**：P3（defer——后续加 `saw agents export/import` 命令或角色仓库）。
- **建议**：后续加 `saw agents export <name> --output <file>` + `saw agents import <file>` 命令，或角色 registry URL 拉取。
- **回流**：下一轮 01（v2.0 PRD 需求——角色分享/导入）或 defer。

### T4 — agents_cmd.py 转为 Typer sub-app，CLI 结构变更（非破坏性但需注意） [Low / P3]

`agents_cmd.py` 从独立 Typer command 转为 Typer sub-app（`invoke_without_command=True`）——`saw agents` 仍 list roster（向后兼容），新增 `saw agents activity <name>` 子命令。`main.py` 从 `app.command(name="agents")(agents)` 改为 `app.add_typer(agents_app, name="agents")`。**非破坏性变更**——`saw agents` 行为不变（仍输出 roster），但 CLI 结构从平铺命令变为嵌套子命令组。后续若继续往 `agents` 加子命令（如 `saw agents list` / `saw agents export`），嵌套结构已就绪。
- **证据**：DEV-LOG v1.15.0 T-F-T-3 节（"agents_cmd.py 转为 Typer sub-app (invoke_without_command=True) — saw agents 仍 list roster（向后兼容）+ 新增 saw agents activity <name> 子命令"）；`main.py`（`app.add_typer(agents_app, name="agents")` 替代 `app.command(name="agents")(agents)`）。
- **影响**：CLI 结构变更非破坏性，但 `--help` 输出格式变化（`saw agents --help` 现在显示子命令列表）。低影响。
- **严重度**：Low（向后兼容，`saw agents` 行为不变）。
- **优先级**：P3（信息性——后续加子命令时结构已就绪）。
- **建议**：文档中更新 `saw agents --help` 输出示例；后续加子命令时沿用 sub-app 模式。
- **回流**：下一轮 05（文档更新——低成本）或 defer。

### 续留 findings（来自前轮，未本轮处理）

| finding | 维度 | 来源 | 状态 | 说明 |
|---|---|---|---|---|
| N3/K2 | per-request workspace 注入 | v1.7.0 K2 | 续留 | QueryEngine 仍 startup 单例 default workspace；web 路径请求级 ws 注入未做。须 v2.0 架构演进。Medium/P2 |
| S1 | ANN 小规模比 cosine 慢 | v1.14.0 S1 | 续留 | ANN P99 245ms vs cosine 72ms @15doc，须 ≥500 规模 benchmark 实证。Low/P3 |
| S2 | scale_curve 维度不匹配 | v1.14.0 S2 | 续留 | 合成向量 384dim vs qwen 1024dim，scale_curve 为空。Low/P3 |
| S3 | COVERAGE-REPORT 状态未更新 | v1.14.0 S3 | 续留 | v1.14.0 delta 段状态标 [TBD-impl] 未更新为 covered。Low/P3 |
| S4 | engine.py god-file 膨胀 | v1.14.0 S4 | 续留 | engine.py 858/900 行，ANN helpers 推高体积。Low/P3 |
| O2 | coverage 余量薄 | v1.11.0 O2 | **改善** | v1.14.0 67.34%（余量 0.34pp）→ v1.15.0 67.42%（余量 0.42pp）——微增但 fail_under=67 仍贴边。Low/P3 |
| O4 | tag 指向 reconcile 非 release commit | v1.11.0 O4 | 续留 | v1.15.0 tag 指向 `d5b644f`（reconcile），release commit `62f0d90` 在 tag 之后 1 commit。同 v1.11.0-v1.14.0 模式。Low/P3 |
| R3 | benchmark CI skip | v1.13.0 R3 | 续留 | 本轮无 benchmark_e2e 新增；1 deselected 为 pre-existing S2。可接受。Low/P3 |

### M2/L2/自定义角色 状态更新

| finding | v1.14.0 状态 | v1.15.0 状态 |
|---|---|---|
| M2（agent 活动聚合） | open（roster 静态，无活动数据） | ✅ **closed**（AgentActivityTracker + event_bus subscriber + REST/CLI activity 端点） |
| L2（链接自动 apply） | open（suggest 只输出不写回） | ✅ **closed**（`saw links apply` dry-run/confirm + 去重 + `## Related` 写回） |
| 自定义角色（v1.5.0 留 v2.0 候选） | open（硬编码 6 角色） | ✅ **closed**（YAML registry + build_agent_roster additive 合并） |

### 本轮新发现（DEV-LOG 偏离记录）

| 偏离 | 说明 | 影响 |
|---|---|---|
| AC-B-3 测试断言调整 | DEV-LOG v1.15.0 T-F-T-2：pre-filter 在 write-back loop 前已移除已链接页面（非到达 skipped 分支），改为验证 `[[c]]` 在文件中出现 1 次 | 低（核心行为正确——去重有效，断言适配实现语义） |
| agents_cmd.py 转为 Typer sub-app | DEV-LOG v1.15.0 T-F-T-3：CLI 结构从平铺命令变为嵌套子命令组 | 低（向后兼容，`saw agents` 行为不变 → T4 finding） |
| examples/demo F841 lint fix | DEV-LOG v1.15.0 06-ship：`utils.py:42` unused `manager` variable（pre-existing demo file） | 无（非生产代码，ruff 0.16.5 捕获） |

## 下游衔接 → 下一迭代候选（供下一轮 01 决策）

> 不下定论，列候选。v1.15.0 周期闭环，current_stage 标 `next-cycle-pending`。

| 候选 | 价值 | 依据 | findings 关联 |
|---|---|---|---|
| **v1.16.0 realtime 仪表盘 v4.3（前端）** | agent/workflow 运行态实时可视化（WebSocket + 前端组件） | roadmap v4.3 | M2（已闭合后端活动聚合，前端可视化是下一步） |
| v1.17 desktop 完成（v4.4 Tauri） | 桌面端达 v1.0 | roadmap v4.4 | — |
| v2.0 per-request workspace 注入 | web 路径请求级 workspace 隔离 | N3/K2 | 架构演进（v2.0 候选） |
| agent activity 持久化 | DB 持久化 agent 活动日志 | T1 | Low/P3（v2.0 候选） |
| links apply undo/rollback | git stash 提示或 `--rollback` 标志 | T2 | Low/P3 |
| 自定义角色分享/导入 | `saw agents export/import` 命令 | T3 | Low/P3 |
| benchmark scale_curve 修复 + ANN 大规模实证 | 修复合成向量维度不匹配 + 跑 ≥500 规模验证 ANN 优势 | S1/S2 | Low/P3 |
| COVERAGE-REPORT 状态更新 | 将 [TBD-impl] 更新为 covered | S3 | Low/P3 |
| engine.py 拆分 | 提取 semantic_search 子模块 | S4 | Low/P3 |

- v2.0.0（MAJOR）推迟到真实 breaking API 变更/范式跃迁时再 bump；当前 v1.x 序列继续 additive 逼近。
- 累计 v1.5.0–v1.15.0 十一轮：5 轮债务收口（workspace 三闭环 + coverage 65→67 + bug fix × 2）+ 6 轮新能力（smart linking + agent 可视化 + embedding + embedding API pivot + E2E 收尾 + semantic 性能优化 + agent/link 能力）。
- 本轮核心成就：**多代理协作与知识链接闭环**——自定义 agent 角色注册（YAML + additive 合并，用户可注册领域专家角色）+ links auto-apply（dry-run/confirm + 去重 + `## Related` 写回，链接建议一键应用）+ agent 活动聚合（event_bus subscriber + REST/CLI activity 端点，agent 运行态可观测）。3 项 findings 清掉（M2/L2/自定义角色），1 项改善（O2），4 项新 findings 回流（T1/T2/T3/T4），8 项续留（N3/S1-S4/O2/O4/R3）。

---

*本复盘所有证据均经 git/manifest 真实状态核验。findings 带证据 file:line/DEV-LOG。agent activity 不持久化是 PRD 明确设计（非缺陷），诚实标注。links apply 无 undo 是已知的（已有 dry-run + confirm 双重保护）。*
