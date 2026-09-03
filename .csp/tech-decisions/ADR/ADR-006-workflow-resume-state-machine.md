# ADR-006: Workflow 续跑状态机（INTERRUPTED→resume）

## 状态：Accepted
## 上下文
v1.5.0 F-I-1 要 `saw workflow run` crash 可恢复。既有 `WorkflowExecutor`（`engines/collaborate/workflow_executor.py`）已实现 M-16 状态机（`WorkflowStatus` + `_WORKFLOW_TRANSITIONS` + `validate_workflow_transition`）+ HI-9 持久化（`_persist_workflow` upsert `workflow_executions` 表）+ startup recovery（`drivers/web/app.py:_recover_stranded_workflows` 标 running→interrupted）。但缺**显式 resume 语义**：INTERRUPTED 行无人续跑；`execute_definition` 总生成新 workflow_id 从头跑。
## 决策
1. 新增 `resume(workflow_id)` 方法：从 `workflow_executions` 读行，仅当状态 ∈ {INTERRUPTED, FAILED, TIMEOUT} 时允许 resume（state machine 已允许 INTERRUPTED→RUNNING）。
2. resume 复用已持久化的 `steps_completed`，从该 index 续跑剩余 steps（context 从 `errors_json`/outputs 重建 [TBD：context 持久化——本轮仅记 index，context 不持久化故 resume 从下个 step 干净开始，已 completed 步骤的 output 丢失则该步重跑]）。
3. CLI `saw workflow resume <id>` 调用；`saw workflow status <id>` 查行。
4. 不引入新表/列（`workflow_executions` v4 已有 status/steps_completed/errors_json）。
## 备选方案
| 方案 | 优势 | 劣势 | 适用 |
|---|---|---|---|
| index-based resume（选） | 复用既有表，零迁移 | context 不持久化，已 completed 步 output 丢则重跑 | 本轮 ✓ |
| 全量 context 快照持久化 | 真正断点续跑 | 序列化整个 context dict（含 LLM payload），膨胀+耦合 | v2.0 可演进 |
| 始终从头跑 | 简单 | crash 前的副作用（已写 claim/wiki）会重复 | 不可接受（破坏幂等） |
## 理由
既有 state machine + HI-9 已把"可见"做对（interrupted 不丢）；本轮只补"可续"。index-based 复用既有 schema，零迁移成本，符合"复用优先"。context 快照 defer v2.0（标注 thin）。
## 后果
- 正：crash 后可 `saw workflow resume <id>` 续跑；状态机 guard 防非法转换。
- 负：resume 不保证断点精确（context 丢失则该步重跑）；幂等性依赖各 step 的 side-effect 幂等（Write Queue 已是 outbox 幂等）。
- 风险：step 重跑若 side-effect 非幂等则重复——mitigate：Write Queue outbox 幂等 + step 输出 key 覆盖语义。
## 关联 Feature
F-I-1（AC-WF-1）。复用 ADR-005 workspace 隔离（workflow 执行可带 workspace scope）。
