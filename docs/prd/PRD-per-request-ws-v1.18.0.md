---
id: PRD-per-request-ws-v1.18.0
title: per-request workspace 注入 + O4 tag 流程
version: 1.0
status: Released
author: prd-writer
date: 2026-09-07
product_type: platform
feature_count: 2
mvp_scope: [per-request-ws-contextvar, o4-tag-flow]
thin_sections: []
upstream_source: .csp/artifacts/retrospective-v1.17.0.md#N3-K2-O4 + v2.0 MAJOR 判断
roadmap_ref: docs/strategy/ROADMAP.md#v1.18.0
target_version: v1.18.0
related_pms: [.csp/product-spec/PMS-per-request-ws.md]
related_specs: [.csp/specs/SPEC-F-W-1.md, .csp/specs/SPEC-F-W-2.md]
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
---

# PRD: per-request workspace 注入 + O4 tag 流程

**Version**: v1.0 | **Author**: prd-writer | **Date**: 2026-09-07 | **Status**: Approved

## 1. 背景与目标

### 1.1 背景

**N3/K2 — per-request workspace 注入**（续留 4 轮：v1.7.0 K2 → v1.8.0 → v1.9.0 → v1.10.0 → … → v1.17.0）：

v1.5.0 引入 workspace 原语（ADR-005，migration v8），v1.6.0–v1.7.0 完成 workspace 三闭环（读全路径 + 写隔离 + graph 隔离）。但 web 路径仍是**引擎级 workspace**——`QueryEngine` 在 `create_app_from_config` 中以 `workspace_id="default"` 构造为启动单例（`engine.py:59,87`），所有 web 请求共享同一 workspace scope。多租户 web 部署时，请求 A（workspace=team-a）与请求 B（workspace=team-b）会读到同一 workspace 的 claim/graph/embedding 数据，**跨 workspace 泄漏**。

**O4 — tag 指向 reconcile commit 非 release commit**（续留自 v1.11.0 07-retro）：

06 release-manager 当前在 reconcile commit 上打 tag（如 `v1.17.0 @e391611` = reconcile commit），而 release commit（`1cca7dc`）在 tag 之后。tag 应指向包含全部 release artifacts 的 release commit，确保 `git checkout vX.Y.Z` 检出完整的发布状态。

**v2.0 MAJOR 判断**（v1.17.0 07-retro 结论）：

若 per-request workspace 注入用 contextvar（不改 QueryEngine 公开构造签名）→ **additive** → 发 v1.18.0 MINOR，非 MAJOR。只有引入不兼容 API 变更才 v2.0.0 MAJOR。诚实按 SemVer，不强行 MAJOR。

### 1.2 目标用户

| 用户角色 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|
| OPS / 平台运维 | 负责多租户 web 部署与运维 | 请求级 workspace 隔离，多租户不泄漏 | 多团队共享 SAW web 实例，每团队数据隔离 |
| Release Manager / CI | 负责版本发布与归档 | tag 指向 release commit，`git checkout` 检出完整发布态 | 06 ship 流程，GitHub Release 关联 |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| 多租户 web 部署数据隔离 | 跨 workspace 查询结果泄漏率 | 0%（零泄漏） | 多租户集成测试（workspace A 查询不返回 workspace B 数据） |
| N3/K2 架构债闭合 | 续留轮次 | 0（本轮闭合） | retrospective 确认 N3/K2 resolved |
| O4 tag 流程修复 | tag 指向 commit 类型 | release commit（非 reconcile） | `git log --oneline vX.Y.Z` 确认 |
| 不回归 | pytest 测试通过率 | 2267+ passed, 0 failed | CI |

## 2. 需求概述

web 多租户路径支持 per-request workspace 隔离（contextvar 注入，不改 QueryEngine 公开构造签名）+ 修复 06 tag 流程（tag 指向 release commit）。

## 3. 详细功能设计

### 3.1 per-request workspace 注入 via contextvar

- **描述**：在 web 请求处理链中引入 per-request workspace_id，使每个 HTTP 请求携带自己的 workspace scope。QueryEngine 内部优先读 contextvar 中的 workspace_id，fallback 到构造时的默认值。
- **用户故事**：作为 OPS，我想在多租户 web 部署中每个请求自动按 workspace 隔离数据，以便不同团队的数据互不可见。
- **优先级**：P0
- **业务规则**：
  1. 引入 `workspace_id_var: ContextVar[str]`，default 值为 `"default"`（与 QueryEngine 构造默认一致）
  2. web 中间件在每请求开始时，从 HTTP header（如 `X-Workspace-Id`）或 query param 或 JWT claim 提取 workspace_id，设入 contextvar；请求结束时 reset
  3. QueryEngine 内部所有读 `self._workspace_id` 的位置改为**先读 contextvar，fallback 到 self._workspace_id**（构造时注入的默认值）
  4. **关键约束：QueryEngine 公开构造签名不变**——`workspace_id` 参数保留，语义不变（作为 fallback default）。contextvar 注入是 additive 行为叠加，不改 API 契约
  5. 子服务（TreeModeSearch、ContextCompiler、GraphTraverse）同样改为先读 contextvar，fallback 到构造值
  6. CLI 路径不受影响——CLI 不走 web 中间件，contextvar 保持 default `"default"`，行为与当前一致
  7. 若请求未提供 workspace_id（无 header/param），contextvar 保持 default `"default"`，行为与当前一致（向后兼容）
- **交互流程**：HTTP 请求 → middleware 提取 workspace_id → contextvar.set → QueryEngine 查询（读 contextvar） → 返回 workspace-scoped 结果 → middleware contextvar.reset
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 请求未携带 workspace_id | contextvar 保持 default | 无（向后兼容，静默 fallback） |
| workspace_id 包含非法字符（路径注入） | middleware 校验（alphanumeric + hyphen，≤64 字符），不合法则 400 | `{"error": "Invalid workspace_id"}` |
| contextvar 未在请求结束 reset | middleware finally 块强制 reset | 无（内部保障） |

### 3.2 O4 tag 流程修复

- **描述**：修复 06 release-manager 的 tag 流程，确保 annotated tag 打在 release commit 上（包含 ship artifacts + milestone archive + ROADMAP/lifecycle/manifest update），而非 reconcile commit。
- **用户故事**：作为 Release Manager，我想 tag 指向 release commit，以便 `git checkout vX.Y.Z` 检出完整的发布状态（含归档与 ROADMAP 更新）。
- **优先级**：P0
- **业务规则**：
  1. 06 ship 流程调整顺序：reconcile commit → release commit → **tag release commit**（当前是 tag reconcile commit）
  2. tag message 包含 release notes 摘要（与当前一致）
  3. release commit 包含 ship artifacts（RELEASE-NOTES + ROLLBACK-PLAN）+ milestone archive + ROADMAP/lifecycle/manifest update
  4. `git tag -a vX.Y.Z` 在 release commit 之后执行，确保 tag 指向 release commit
  5. GitHub Release 关联的 tag 也指向 release commit
- **交互流程**：reconcile commit → release commit（ship artifacts + archive + ROADMAP） → `git tag -a` → push master + tag → GitHub Release
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| release commit 失败（如 archive 路径不存在） | 修复后重 commit，tag 在新 commit 上 | 无（06 流程内闭环） |
| tag 已存在（重跑 06） | 不移动已推送 tag（不可变原则），仅本地未推送时可重建 | "tag already pushed, cannot move" |

## 4. 非功能要求

| 类别 | 要求 | 验收标准 |
|---|---|---|
| 兼容性 | QueryEngine 公开构造签名不变 | `QueryEngine.__init__` 参数列表与 v1.17.0 一致；既有调用方无需修改 |
| 兼容性 | CLI 路径行为不变 | `saw query`/`saw search`/`saw links` 等 CLI 命令行为与 v1.17.0 一致 |
| 安全性 | 多租户 web 测试跨 workspace 不泄漏 | workspace A 的请求不返回 workspace B 的 claim/graph/embedding 数据 |
| 性能 | contextvar 读写开销可忽略 | < 1μs per request（contextvars 是 Python stdlib 原生，O(1)） |
| 测试 | 不回归 | pytest 2267+ passed, 0 failed |
| Lint | ruff 0 | `ruff check src/ tests/` exit 0 |
| 可观测 | per-request workspace_id 出现在结构化日志中 | JSON log payload 包含 `workspace_id` 字段 |

## 5. 数据需求

| 事件名 | 触发条件 | 关键属性 | 用途 |
|---|---|---|---|
| `request_workspace_set` | middleware 设 contextvar | `workspace_id`, `source`（header/param/default） | 审计多租户请求分布 |
| `request_workspace_reset` | middleware finally reset | `workspace_id`, `duration_ms` | 清理确认 |

## 6. 验收标准

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-WS-1 | contextvar 注入生效 | web 实例运行 | 请求携带 `X-Workspace-Id: team-a` | QueryEngine 返回 team-a workspace 的数据 |
| AC-WS-2 | fallback 默认值 | web 实例运行 | 请求未携带 workspace header | QueryEngine 返回 default workspace 的数据（与 v1.17.0 一致） |
| AC-WS-3 | 跨 workspace 不泄漏 | web 实例含 workspace A + B 数据 | workspace A 请求搜索 | 结果不含 workspace B 的 claim |
| AC-WS-4 | CLI 不受影响 | CLI 模式 | `saw query "test"` | 行为与 v1.17.0 一致（用 default workspace） |
| AC-WS-5 | 构造签名不变 | 代码审查 | 检查 QueryEngine.__init__ | 参数列表与 v1.17.0 一致，无 breaking change |
| AC-O4-1 | tag 指向 release commit | 06 ship 完成 | `git log --oneline v1.18.0` | 指向 release commit（含 ship artifacts + archive），非 reconcile commit |
| AC-O4-2 | GitHub Release 关联 | GitHub Release 创建 | 查看 Release tag | 指向 release commit |

## 7. 排期估算

| 阶段 | 预估工作量 | 依赖 | 风险 |
|---|---|---|---|
| 02 需求拆解 | [TBD] | 01 PRD done | — |
| 03 技术方案 | [TBD] | 02 done | contextvar 在 ThreadPoolExecutor 中的传播须验证 |
| 04 任务拆解 | [TBD] | 03 done | — |
| 05 实施 | [TBD] | 04 done | 子服务 contextvar fallback 改造范围 |
| 06 审查·发布 | [TBD] | 05 done | O4 流程首次执行，须仔细核对 |

## 8. 风险与依赖

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| V1 — .dmg 未签名/公证（v1.17.0 续留 P3） | 已知 | macOS Gatekeeper 拦截 | 后续 Apple Developer ID + notarization |
| V2 — 仅 mac aarch64 包（v1.17.0 续留 P3） | 已知 | 跨平台无原生包 | 后续跨平台 CI matrix |
| V3 — sidecar defer（v1.17.0 续留 P3） | 已知 | prod 仍需外部 saw server | v2.0+ 评估 |
| S1-S4 — semantic perf 续留（P3） | 低 | ANN 小规模慢 / scale_curve 维度 / COVERAGE-REPORT / engine.py god-file | 后续专项 |
| T1-T4 — agent/link 续留（P3） | 低 | activity 不持久化 / links 无 undo / 角色无分享 / CLI 结构 | 后续专项 |
| U1-U6 — dashboard 续留（P3） | 低 | 视觉 E2E / polling 延迟 / vLLM skip / 测试路径偏离 | 后续专项 |
| contextvar 在 ThreadPoolExecutor 中传播 | 低 | contextvar 默认不跨线程传播 | 03 技术方案验证（`copy_context` 或显式传递） |

## 附录

### ground 自源码

| claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|
| QueryEngine 构造签名有 workspace_id="default" | `src/saw/engines/query/engine.py:59` | `workspace_id: str = "default"` | TRUE |
| QueryEngine 存储 self._workspace_id | `src/saw/engines/query/engine.py:87` | `self._workspace_id = workspace_id` | TRUE |
| QueryEngine propagate workspace to sub-services via set_workspace_id | `src/saw/engines/query/engine.py:92-95` | `for _sub in (self._tree_mode, self._compiler, self._graph): _setter(workspace_id)` | TRUE |
| create_app_from_config 创建 QueryEngine 不传 workspace_id（用默认） | `src/saw/drivers/web/app.py` create_app_from_config | `QueryEngine(search=..., workspace_id not passed)` — engine.py:59 default kicks in | TRUE |
| observability middleware 已有 contextvars 先例 | `src/saw/drivers/web/middleware/observability.py:18,30` | `import contextvars` + `request_id_var: contextvars.ContextVar[str]` | TRUE |
| 无 workspace_id contextvar 存在 | `src/saw/drivers/web/` grep workspace_id | 零匹配（仅 observability.py 有 contextvars） | TRUE |
| collaborate REST 读 DB 无 per-request workspace 过滤 | `src/saw/api/routes/collaborate.py` list_workflows | SQL 无 `WHERE workspace_id = ?`（workflow_executions 表无 ws 列） | TRUE |
| v1.17.0 tag @e391611 = reconcile commit | `git log --oneline v1.17.0` | `e391611 chore(csp): v1.17.0 reconcile planning artifacts` | TRUE |
| release commit 1cca7dc 在 tag 之后 | `git log --oneline -10` | `1cca7dc release: v1.17.0` 在 e391611 之后 | TRUE |
| QueryEngine cache key 已含 workspace_id | `src/saw/engines/query/engine.py:234` | `"workspace_id": self._workspace_id` in cache params | TRUE |
| embedding_store query 按 workspace_id 过滤 | `src/saw/engines/query/engine.py:528-529` | `WHERE workspace_id = ?` | TRUE |

### 下一步建议

- [ ] 进入需求拆解 → 把功能模块翻成 Feature 清单 + 依赖图 + NFR，落 `.csp/decomposition/`
- [ ] 需求规模合理（2 模块），不需拆分 MVP
- [ ] 进入 03 技术方案（含选型）→ contextvar 传播机制 + ThreadPoolExecutor 兼容性验证

当前产物：`docs/prd/PRD-per-request-ws-v1.18.0.md`（status: Approved）+ `.csp/product-spec/PMS-per-request-ws.md`（PMS）+ `docs/prd/PRD-INDEX.md` 已登记。已写 `.csp/lifecycle-state.json`：01 done，current_stage=02-decomposition。
