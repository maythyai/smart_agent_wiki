# Collaborate 多代理协作与工作流 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/engines/collaborate/*`、`src/saw/api/routes/collaborate.py`、`workflows/*`
> 独立复核: F-COLLAB-01/02 已由主审读取 `dispatcher.py:160`、`agents/base.py:80`、`collaborate.py:141` 确认。

## 1. 执行摘要
- 架构完整（6 Agent + A2A + YAML 工作流 + 门控 + 持久化恢复），但关键执行路径存在阻断性 bug：fallback 调度路径 TypeError、占位合成文本被写入真实 Wiki。
- 核心功能完成度约 **55%**。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| 6 Agent 注册 | 完整 | agents/* |
| A2A 协议 | 完整 | a2a_protocol.py |
| YAML 工作流解析 | 完整 | workflow_parser.py |
| 工作流执行（fallback 路径） | 崩溃 | F-COLLAB-01 |
| Jinja2 输入模板 | 未渲染 | F-COLLAB-03 |
| 崩溃恢复用户可见性 | 缺失 | F-COLLAB-06 |
| 取消运行中工作流 | 缺失 | F-COLLAB-04 |

## 4. Findings 列表

### F-COLLAB-01 — fallback 调度路径 TypeError
- **P0** | 严重度 4 | 置信度 high（已独立复核） | **原则** #1
- **位置**: `engines/collaborate/dispatcher.py:160`（正常路径 :146 不受影响）
- **问题**: `dispatch` fallback 分支调用 `agent.execute(task, context, tools or [], model_tier_override=fallback_tier)`，但 `Agent.execute` 签名为 `(self, task, context, tools)`，无 `**kwargs`，传 `model_tier_override` 必 TypeError。
- **后果**: 模型降级回退时工作流步骤失败（被外层 `except` 标记 failed）。校准：非"每次调度"，仅 fallback/降级路径。
- **修复**: 在 `Agent.execute` 加 `**kwargs` 或在 dispatcher 不传该 kwarg。

### F-COLLAB-02 — 占位合成文本写入真实 Wiki
- **P0** | 严重度 4 | 置信度 high（已独立复核） | **原则** #1/#9
- **位置**: `api/routes/collaborate.py:141`（+ `_publish` 步骤 :153）
- **问题**: 搜索无结果时 `synthesis = f"# {question}\n\n(No source material found; stub synthesis.)"`，随后 publish 步骤调用 `_publish(...)` 经 WriteQueue 写入 Wiki。
- **后果**: 假内容污染知识库，用户不知情。
- **修复**: 无来源时应标记 `status=failed` 并向用户提示，绝不写入占位内容。

### F-COLLAB-03 — Jinja2 输入模板未渲染
- **P1** | 严重度 3 | **原则** #4
- **问题**: `render_template` 存在于 parser 但执行器从不调用，`{{ query }}` 被当字面键。

### F-COLLAB-04 — 无取消运行中工作流的 API
- **P1** | 严重度 3 | **原则** #3
- **问题**: 用户必须等待超时或完成。

### F-COLLAB-05 — 团队模式步骤恒显示 pending
- **P1** | 严重度 3 | **原则** #1
- **问题**: `_run_via_engine` 中未调用 `_set_step`，全程显示 pending。

### F-COLLAB-06 — 崩溃恢复对用户不可见
- **P1** | 严重度 3 | **原则** #1/#6
- **问题**: `workflow_executions` 表行在 `list_workflows` 中不显示（仅读内存字典）。

### F-COLLAB-07 — 模型降级回退是装饰性
- **P1** | 严重度 2 | **原则** #4
- **问题**: Agent 硬编码模型名（如 `claude-opus-4-20250514`）并忽略 `model_tier_override`。

> 其余 P2/P3：静默持久化失败、离线降级无透明度、本地模式误导性 Agent 状态广播、缺失崩溃恢复日志、低质量合成输出。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 2 |
| 3 | 4 |
| 2 | 5 |
| 1 | 4 |
| 优先级 | P0×2 P1×4 P2×5 P3×4 |

## 6. 修复优先级
- **Foundation**: F-COLLAB-01/02
- **Core UI**: F-COLLAB-03/05/06
- **Interactions & States**: F-COLLAB-04/07
- **Polish**: 其余

## 7. 下一步建议
- 绝不让 stub 内容进入 WriteQueue；统一模型降级机制；工作流进度/取消/恢复对用户可见。
