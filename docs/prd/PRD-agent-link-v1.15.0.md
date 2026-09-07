---
id: PRD-agent-link-v1.15.0
title: agent/link 能力
version: 1.0
status: Released
author: S1-prd
date: 2026-09-06
product_type: platform
feature_count: 3
mvp_scope: [custom-agent-roles, links-auto-apply, agent-activity-aggregation]
thin_sections: []
upstream_source: .csp/artifacts/retrospective-v1.14.0.md#M2-L2 + v1.5.0 留候选
roadmap_ref: docs/strategy/ROADMAP.md#v1.15.0
target_version: v1.15.0
related_pms: [.csp/product-spec/PMS-agent-link.md]
related_specs: [.csp/specs/SPEC-F-T-1.md, .csp/specs/SPEC-F-T-2.md, .csp/specs/SPEC-F-T-3.md]
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
---

# PRD: agent/link 能力

## 1. 背景与目标

### 1.1 背景

v1.15.0 承接近续留 findings 的三项补齐：

| finding | 来源 | 续留轮次 | 现状 |
|---|---|---|---|
| **自定义 agent 角色** | v1.5.0 留 v2.0 候选 | v1.5.0→v1.15.0 | `build_default_agents()` 硬编码 6 角色（Librarian/Writer/Critic/Linker/Scholar/Guardian），用户无法注册自定义角色 |
| **L2 links auto-apply** | v1.8.0 L2 | v1.8.0→v1.15.0 | `saw links suggest` 只输出建议列表，不自动写回 wiki 页面文件 |
| **M2 agent 活动聚合** | v1.9.0 M2 | v1.9.0→v1.15.0 | `GET /api/v1/agents` 返回静态 roster，无最近活动/调用次数聚合 |

不做会怎样：多代理协作框架角色固定不可扩展，知识链接停留在"手动添加"，agent 运行态不可观测——多代理协作与知识链接不完整。

做了会怎样：用户可注册领域自定义 agent 角色，链接建议一键应用（须确认），agent 活动可观测——多代理协作与知识链接闭环。

### 1.2 目标用户

| 用户角色 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|
| KW（知识工作者） | 使用 SAW 管理知识库，熟悉 wiki 语法 | 链接一键应用而非手动编辑 | 审阅 `saw links suggest` 输出后批量应用建议链接 |
| DEV（开发者/集成者） | 编写 workflow YAML，配置 agent 角色 | 注册领域自定义 agent 角色（name/model_tier/tools）适配领域需求 | 为特定知识领域（如医学/法律）注册领域专家 agent 角色 |
| OPS（运维/团队管理员） | 监控多 agent 运行态，排查 workflow 问题 | 查看 agent 最近活动/调用次数/状态 | 通过 `GET /api/v1/agents/{name}/activity` 排查 agent 是否活跃 |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| 自定义角色可注册+调用 | 自定义角色注册后可被 workflow YAML 引用并执行 | ≥1 个自定义角色端到端调用成功 | AC-A-1..4 测试 |
| links apply 插入正确 | `[[link]]` 插入到页面正确位置且不重复 | apply 后 `saw links audit` 无新断链 | AC-B-1..4 测试 |
| agent activity 端点返回聚合 | `GET /api/v1/agents/{name}/activity` 返回最近活动 | 端点返回 ≥1 条活动记录（有 workflow 运行后） | AC-C-1..4 测试 |
| 不回归 | pytest passed ≥ 2192 | 0 regression | CI 全量测试 |
| lint 通过 | ruff 0 errors | 0 | CI ruff check |

## 2. 需求概述

补齐 agent 自定义角色注册 + 链接自动 apply + agent 活动聚合，让多代理协作与知识链接更完整。

## 3. 详细功能设计

### 3.1 自定义 agent 角色注册（custom-agent-roles）

- **描述**：用户可在 `build_default_agents()` 之外注册自定义 agent 角色，配置 name / model_tier / system_prompt / tools_allowed，注册后的角色可被 workflow YAML 引用并执行。
- **用户故事**：作为 DEV，我想注册自定义 agent 角色（如 "MedicalExpert" / "LegalAnalyst"），以便 workflow 可以调度领域专家 agent 完成通用 6 角色无法覆盖的任务。
- **优先级**：P0

- **业务规则**：
  1. 自定义角色通过配置文件（YAML 或 Python API）注册，不修改 `build_default_agents()` 源码
  2. 自定义角色 name 不得与内置 6 角色（Librarian/Writer/Critic/Linker/Scholar/Guardian）重名
  3. model_tier 仅允许 `haiku` / `sonnet` / `opus` / `rule` 四个值（复用 `BaseAgent.__init__` 已有 Literal 约束）
  4. tools_allowed 为工具名列表，可为空（表示无工具权限）
  5. 自定义角色注册后，出现在 `saw agents` CLI 输出和 `GET /api/v1/agents` REST 返回中
  6. workflow YAML `validate()` 校验 `step.agent` 时，自定义角色名也在 `available_agents` 集合中
  7. 自定义角色未配置 llm_router 时，行为与内置角色一致（fallback 到 heuristic）

- **交互流程**：
  1. 入口：用户在 `.saw/agents/` 目录下放置角色定义文件（YAML），或通过 API 注册
  2. 加载：系统启动时扫描 `.saw/agents/*.yaml`，解析角色定义，合并到 `build_default_agents()` 返回的 roster 中
  3. 验证：校验 name 唯一性 + model_tier 合法性 + tools_allowed 格式
  4. 成功反馈：`saw agents` 显示内置 + 自定义角色列表（自定义角色标注 `custom`）
  5. 失败处理：角色定义文件格式错误时报错并跳过该角色，不阻断启动

- **异常处理**：

  | 场景 | 处理 | 用户提示 |
  |---|---|---|
  | 自定义角色 name 与内置角色重名 | 跳过注册，日志警告 | "Agent role '{name}' conflicts with built-in, skipped" |
  | model_tier 值非法 | 跳过注册，日志警告 | "Invalid model_tier '{value}' for agent '{name}', must be haiku/sonnet/opus/rule" |
  | YAML 格式错误 | 跳过该文件，日志错误 | "Failed to parse agent definition '{file}': {error}" |
  | system_prompt 为空 | 跳过注册，日志警告 | "Agent '{name}' missing system_prompt, skipped" |

### 3.2 L2 links auto-apply（links-auto-apply）

- **描述**：`saw links apply` 命令读取 `compute_related_pages` 的 suggest 输出，将建议的 `[[link]]` 自动插入到目标 wiki 页面文件中。此操作修改用户文件，属破坏性操作，须用户确认。
- **用户故事**：作为 KW，我想在审阅 `saw links suggest` 输出后一键应用建议链接，以便不必手动编辑每个页面添加 `[[link]]`。
- **优先级**：P0

- **业务规则**：
  1. `saw links apply <page> --suggestion` 读取 `compute_related_pages` 输出的建议列表
  2. 用户须通过 `--confirm` 标志确认执行（默认 dry-run，只预览不写）
  3. 链接插入位置：页面 content 末尾新增 `## Related` 段落，追加 `[[slug]]` 列表
  4. 已存在的 `[[link]]` 不重复插入（去重检查）
  5. 写回通过 `WikiRepository.write()` 机制（复用既有 write，不绕过）
  6. apply 后页面 frontmatter 的 `related` 字段同步更新
  7. 支持 `--top N` 限制应用数量（默认全部建议）
  8. 支持 `--dry-run` 预览将插入的链接列表但不写回
  9. 用户可指定单条建议 `--suggestion <slug>` 只应用一条

- **交互流程**：
  1. 入口：`saw links apply <page> --path . --top 5`
  2. 步骤 1：计算 suggest（复用 `compute_related_pages`）
  3. 步骤 2：过滤已链接的（复用 suggest 的去重逻辑）
  4. 步骤 3（dry-run）：打印将插入的 `[[link]]` 列表 + 目标页面，提示 "Run with --confirm to apply"
  5. 步骤 4（confirm）：逐页写回（`WikiRepository.write`），打印成功/失败汇总
  6. 成功反馈："N links applied to M pages"
  7. 失败处理：单页写回失败不中断，继续处理其余页面，最后汇总失败列表

- **异常处理**：

  | 场景 | 处理 | 用户提示 |
  |---|---|---|
  | 目标页面不存在 | 跳过该链接 | "Page '{slug}' not found, skipped" |
  | 页面已有该 `[[link]]` | 跳过，不重复 | "Link [[{slug}]] already exists in {page}, skipped" |
  | 写回时磁盘错误 | 记录失败，继续其余 | "Failed to write {page}: {error}" |
  | 无 `--confirm` 标志 | 仅预览不写 | "Dry run — {N} links would be applied. Run with --confirm to apply." |

### 3.3 M2 agent 活动聚合（agent-activity-aggregation）

- **描述**：通过 event bus 订阅 `WorkflowStep` 事件，聚合每个 agent 的最近活动/调用次数，新增 `GET /api/v1/agents/{name}/activity` REST 端点返回聚合结果。
- **用户故事**：作为 OPS，我想查看某个 agent 的最近活动和调用次数，以便排查 agent 是否活跃、workflow 是否正常调度。
- **优先级**：P0

- **业务规则**：
  1. 活动聚合器通过 `InMemoryEventBus.add_subscriber("WorkflowStep", handler)` 订阅 WorkflowStep 事件
  2. 每条 WorkflowStep 事件包含 `step`（格式 `"{agent}.{action}"`）和 `status`（`completed` / `failed`）
  3. 聚合器按 agent name 分组，记录：最近活动时间戳、调用次数（completed）、失败次数（failed）、最近 action
  4. `GET /api/v1/agents/{name}/activity` 返回该 agent 的活动聚合
  5. `GET /api/v1/agents` 返回的 roster 中每个 agent 增加 `activity_summary` 字段（最近活动时间 + 调用次数），可为 null（无活动时）
  6. 活动聚合为内存态（进程重启后丢失），不持久化（持久化属 v2.0 候选）
  7. 聚合器不阻塞 workflow 执行（event bus handler 在 publisher 线程同步执行，须轻量）

- **交互流程**：
  1. 入口：workflow 执行时，`WorkflowExecutor._publish_event` 发布 WorkflowStep 事件
  2. event bus fan-out 到所有 subscriber（含活动聚合器 handler）
  3. 聚合器 handler 更新内存中 agent 活动计数器
  4. 用户访问 `GET /api/v1/agents/Scholar/activity`
  5. 成功反馈：返回 `{ "agent": "Scholar", "calls": 3, "failures": 0, "last_action": "synthesize", "last_active_at": "2026-09-06T..." }`
  6. 失败处理：agent 无活动记录时返回 200 + 空活动（`calls: 0, last_active_at: null`），不返回 404

- **异常处理**：

  | 场景 | 处理 | 用户提示 |
  |---|---|---|
  | agent name 不存在于 roster | 返回 404 | HTTP 404 "Agent '{name}' not found in roster" |
  | agent 存在但无活动记录 | 返回 200 + 空活动 | `{ "agent": "Guardian", "calls": 0, "failures": 0, "last_action": null, "last_active_at": null }` |
  | event bus handler 抛异常 | bus 已有 try/except，不传播 | 日志 "Event handler raised for 'WorkflowStep'" |

## 4. 非功能要求

| 类别 | 要求 | 验收标准 |
|---|---|---|
| 不回归 | pytest passed ≥ 2192（v1.14.0 基线） | CI 全量测试 0 regression |
| lint | ruff check src/ tests/ 0 errors | CI ruff 0 |
| links apply 破坏性确认 | apply 命令默认 dry-run，须 `--confirm` 方写回 | AC-B-2 Given-When-Then |
| activity 聚合不阻塞 workflow | event bus handler 轻量，不抛异常不传播 | workflow 执行时间不因聚合器增加（无可感知延迟） |
| 自定义角色向后兼容 | 不修改 `build_default_agents()` 签名和返回 | 内置 6 角色行为不变，自定义角色是 additive |
| coverage | fail_under=67 持平 | coverage ≥ 67% |

## 5. 数据需求

| 事件名 | 触发条件 | 关键属性 | 用途 |
|---|---|---|---|
| `WorkflowStep`（既有） | workflow 步骤完成/失败 | `workflow_id`, `step`（`{agent}.{action}`）, `status`, `output_key` | 活动聚合器订阅此事件聚合 agent 活动 |
| `AgentRoleRegistered`（新增） | 自定义角色注册成功 | `name`, `model_tier`, `source`（file/api） | 审计自定义角色注册 |
| `LinksApplied`（新增） | links apply 写回完成 | `page`, `applied_slugs[]`, `skipped_slugs[]` | 审计链接应用操作 |

## 6. 验收标准

### 3.1 自定义 agent 角色注册

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-A-1 | 自定义角色注册并出现在 roster | `.saw/agents/expert.yaml` 定义 name=MedicalExpert, model_tier=sonnet, system_prompt 非空 | 执行 `saw agents` | 输出列表包含 MedicalExpert 行，标注 custom |
| AC-A-2 | 自定义角色被 workflow 引用 | 自定义角色 MedicalExpert 已注册 | workflow YAML 中 step.agent=MedicalExpert | `WorkflowParser.validate()` 返回无错误 |
| AC-A-3 | 重名角色被拒绝 | 自定义角色 name=Librarian（与内置重名） | 系统加载时 | 该角色被跳过，日志输出 conflict warning |
| AC-A-4 | REST 端点返回自定义角色 | 自定义角色已注册 | `GET /api/v1/agents` | 响应包含自定义角色，`custom: true` 标记 |

### 3.2 L2 links auto-apply

| ID | 场景 | Given | When | Then | 
|---|---|---|---|---|
| AC-B-1 | dry-run 预览不写回 | 页面 A 有 3 条 suggest 建议 | `saw links apply A --path .`（无 --confirm） | 打印 3 条将应用的链接，不修改任何文件 |
| AC-B-2 | confirm 写回 | 页面 A 有 3 条 suggest 建议，已 `--confirm` | `saw links apply A --path . --confirm` | 页面 A 文件新增 `## Related` 段落含 3 个 `[[link]]`，frontmatter related 同步更新 |
| AC-B-3 | 已有链接不重复 | 页面 A 已含 `[[page-b]]` | `saw links apply A --confirm` | `[[page-b]]` 不重复插入，提示 skipped |
| AC-B-4 | apply 后 audit 无新断链 | apply 已执行 | `saw links audit` | 插入的链接目标都存在，无新断链 |

### 3.3 M2 agent 活动聚合

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-C-1 | activity 端点返回聚合数据 | Scholar agent 在某次 workflow 中执行了 synthesize 步骤 | `GET /api/v1/agents/Scholar/activity` | 返回 calls≥1, last_action="synthesize", last_active_at 非空 |
| AC-C-2 | 无活动的 agent 返回空活动 | Guardian agent 注册后从未被 workflow 调用 | `GET /api/v1/agents/Guardian/activity` | 返回 200, calls=0, last_active_at=null |
| AC-C-3 | 不存在的 agent 返回 404 | roster 中无 agent "NonExistent" | `GET /api/v1/agents/NonExistent/activity` | 返回 404 "Agent not found" |
| AC-C-4 | agents 端点含 activity_summary | Scholar 有 3 次调用记录 | `GET /api/v1/agents` | Scholar 行含 `activity_summary: {calls: 3, last_active_at: "..."}` |

## 7. 排期估算

| 阶段 | 预估工作量 | 依赖 | 风险 |
|---|---|---|---|
| 02 需求拆解 | [TBD] | 本 PRD Approved | — |
| 03 技术方案 | [TBD] | 02 done | event bus 订阅机制已有，但聚合器设计须不阻塞 workflow |
| 04 任务拆解 | [TBD] | 03 done | — |
| 05 实施 | [TBD] | 04 done | 自定义角色 YAML 解析 + links apply 写回 + 活动聚合器 |
| 06 发布 | [TBD] | 05 done + 全量测试 | — |

## 8. 风险与依赖

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| links apply 破坏性写回用户文件 | Medium | High | 默认 dry-run + `--confirm` 标志 + 单页失败不中断 |
| 活动聚合器阻塞 workflow 执行 | Low | Medium | handler 轻量（仅计数器更新），event bus 已有 try/except 不传播 |
| 自定义角色 YAML 格式多样性 | Medium | Low | 严格 schema 校验 + 跳过无效定义不阻断启动 |
| N3/K2 per-request workspace 续留 | — | — | 续留（v2.0 架构演进候选），本轮不处理 |
| S1-S4 续留 | — | — | ANN 小规模慢 / scale_curve 维度 / COVERAGE-REPORT 状态 / engine.py god-file，均 Low/P3，本轮不处理 |

## 附录

### Ground 自源码

| # | claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|---|
| 1 | `build_default_agents()` 硬编码 6 角色，无自定义注册机制 | `src/saw/engines/collaborate/agents/__init__.py:35` | 构造 Librarian/Writer/Critic/Linker/Scholar/Guardian 6 个实例返回 dict，无外部注册入口 | TRUE |
| 2 | `BaseAgent.__init__` 接受 name/model_tier/system_prompt/tools_allowed/constraints | `src/saw/engines/collaborate/agents/base.py:23` | 构造函数签名含 5 参数，model_tier 为 Literal["haiku","sonnet","opus","rule"]，可被自定义角色复用 | TRUE |
| 3 | `saw links suggest` 只输出不写回 | `src/saw/drivers/cli/commands/links_cmd.py:51` | suggest 命令调用 `compute_related_pages` 打印表格，不调用 `WikiRepository.write` | TRUE |
| 4 | `WikiRepository.write()` 存在，可写回 wiki 页面 | `src/saw/adapters/storage/wiki_repository.py:42` | 接受 WikiPage 对象，序列化为 Markdown+YAML frontmatter 写入磁盘 | TRUE |
| 5 | `GET /api/v1/agents` 返回静态 roster | `src/saw/api/routes/collaborate.py:426` | 调用 `build_default_agents(llm_router=None)` 返回 name/model_tier/tools_allowed/rule，无活动数据 | TRUE |
| 6 | `WorkflowExecutor._execute_step` 发布 WorkflowStep 事件含 agent name | `src/saw/engines/collaborate/workflow_executor.py:389` | 事件 dict `{"type":"WorkflowStep","step":f"{step.agent}.{step.action}","status":"completed"}`，含 agent name | TRUE |
| 7 | `InMemoryEventBus.add_subscriber` 支持按事件类型订阅 | `src/saw/plugins/event_bus.py:71` | `add_subscriber(event_type, handler)` 注册回调，匹配 `event_type` 或 None（全部）；handler 在 publisher 线程同步执行 | TRUE |
| 8 | `workflow_executions` 表存 workflow 级状态但不存 per-agent 活动 | `src/saw/db/migrations.py:189` | CREATE TABLE workflow_executions(workflow_id, definition_name, status, steps_completed, steps_total, errors_json, updated_at, finished_at)，无 agent_name 列 | TRUE |

### 下一步建议

- [ ] 进入需求拆解 → 把 3 功能模块翻成 Feature 清单 + 依赖图 + NFR，落 `.csp/decomposition/`
- [ ] 自定义角色 YAML schema 具体字段定义留 02 拆解 / 03 技术方案
- [ ] event bus 订阅聚合器具体 HOW（handler 数据结构、并发安全）留 03 技术方案
- [ ] links apply 的 `## Related` 段落插入策略（追加 vs frontmatter related 字段同步）留 03 技术方案
