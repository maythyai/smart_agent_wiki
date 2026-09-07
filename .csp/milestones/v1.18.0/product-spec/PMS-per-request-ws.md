# PMS — per-request workspace 注入 + O4 tag 流程

> 模块说明书：per-request workspace contextvar 注入 + O4 tag 流程修复。
> 关联 PRD: `docs/prd/PRD-per-request-ws-v1.18.0.md`
> 状态: ready

## 模块边界

### 做什么

1. **per-request workspace contextvar 注入**：web 多租户路径支持请求级 workspace 隔离。middleware 提取 workspace_id 设入 contextvar，QueryEngine 及子服务内部优先读 contextvar（fallback 构造时默认值），公开构造签名不变。
2. **O4 tag 流程修复**：06 release-manager tag 打在 release commit 上（非 reconcile commit），确保 `git checkout vX.Y.Z` 检出完整发布态。

### 不做什么

- **不改 QueryEngine 公开构造签名**（additive MINOR，非 MAJOR）
- **不做 workspace 持久化/管理**（workspace 创建/删除/列表仍由 CLI/ingest 路径管理）
- **不做 agent activity 持久化**（T1 续留 P3）
- **不做 desktop sidecar**（V3 续留 P3，v2.0+ 候选）

## 验收形态

- 多租户 web 测试跨 workspace 零泄漏
- CLI 路径行为不变
- 06 tag 指向 release commit
- pytest 2267+ passed，ruff 0
- QueryEngine 构造签名与 v1.17.0 一致

## 对外接口契约摘要

| 接口 | 变更 |
|---|---|
| `QueryEngine.__init__` | **不变**（workspace_id 参数保留，语义不变） |
| web middleware | 新增 workspace contextvar 注入（X-Workspace-Id header） |
| JSON 日志 | payload 新增 `workspace_id` 字段 |
| 06 ship 流程 | tag 顺序调整（reconcile → release → tag） |

## 关联 PRD

- `docs/prd/PRD-per-request-ws-v1.18.0.md`（v1.0, Approved）

## 关联 Spec

- `.csp/specs/SPEC-F-W-1.md`（per-request workspace 注入：FastAPI middleware contextvar + QueryEngine fallback 读取）
- `.csp/specs/SPEC-F-W-2.md`（O4 tag 流程修复：release-manager tag 指向 release commit）
