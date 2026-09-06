# PMS: agent-link — agent/link 能力

> 产品说明书（living baseline）。下游 02 拆解/03 技术方案不得越出本模块边界。

## 模块边界

**做什么**：
- 自定义 agent 角色注册：用户通过配置文件注册自定义 agent 角色（name/model_tier/system_prompt/tools_allowed），合并到 `build_default_agents()` 返回的 roster
- L2 links auto-apply：`saw links apply` 命令读取 suggest 输出，将 `[[link]]` 插入 wiki 页面文件（默认 dry-run，须 `--confirm` 写回）
- M2 agent 活动聚合：通过 event bus 订阅 WorkflowStep 事件，聚合 agent 最近活动/调用次数，`GET /api/v1/agents/{name}/activity` 返回聚合

**不做什么**：
- 不修改 `build_default_agents()` 签名和返回结构（自定义角色是 additive 合并）
- 不持久化 agent 活动聚合（内存态，进程重启丢失；持久化属 v2.0 候选）
- 不实现 links apply 的撤销机制（dry-run 预览 + confirm 是安全边界，不实现 undo）
- 不实现自定义角色的动态热加载（启动时扫描加载，运行时不重载）
- 不描述 event bus 订阅的具体 HOW（handler 数据结构、并发安全留 03 技术方案）

## 验收形态

| 功能 | 验收形态 | AC |
|---|---|---|
| 自定义角色注册 | `saw agents` 输出含自定义角色行（标注 custom）；workflow YAML 可引用自定义角色名 | AC-A-1..4 |
| links auto-apply | `saw links apply <page> --confirm` 写回 `## Related` 段落 + frontmatter related 更新；dry-run 不写回 | AC-B-1..4 |
| agent 活动聚合 | `GET /api/v1/agents/{name}/activity` 返回 calls/failures/last_action/last_active_at；无活动返回空 | AC-C-1..4 |

## 对外接口契约摘要

| 接口 | 方法 | 路径 | 说明 |
|---|---|---|---|
| CLI | `saw links apply` | `saw links apply <page> --path . [--confirm] [--top N] [--dry-run]` | 应用 suggest 链接到 wiki 页面 |
| REST | GET | `/api/v1/agents/{name}/activity` | 返回指定 agent 的活动聚合 |
| REST | GET | `/api/v1/agents` | roster 增加 `activity_summary` 字段（可选 null） |
| Event | subscribe | `WorkflowStep`（既有事件，新增订阅者） | 活动聚合器订阅此事件 |

## 关联 PRD

- `docs/prd/PRD-agent-link-v1.15.0.md`

## 关联 Spec

- `.csp/specs/SPEC-F-T-1.md`（自定义 agent 角色注册）
- `.csp/specs/SPEC-F-T-2.md`（L2 links auto-apply）
- `.csp/specs/SPEC-F-T-3.md`（M2 agent 活动聚合）

## 状态

- ready（边界已定，待 02 拆解）
