# TMS Delta — v1.18.0（2026-09-07）

> 03 测试规约 delta。per-request workspace 注入 + O4 tag 流程修复。
> 基线：v1.17.0 = pytest 2267 passed / ruff 0 / coverage ≥ 67% / smoke 6/6。
> 后端测试用 pytest（middleware contextvar + QueryEngine 跨 workspace 隔离 + 构造签名不变 + O4 文档验证 + 06 时 tag 验证）。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-WS-1（contextvar 注入生效，X-Workspace-Id: team-a → 返回 team-a 数据） | F-W-1 | `tests/test_workspace_contextvar.py::test_middleware_sets_contextvar`（新建）：FastAPI TestClient + WorkspaceContextMiddleware + X-Workspace-Id header → 断言 QueryEngine._effective_workspace_id() == "team-a" | [TBD-impl] |
| AC-WS-2（fallback 默认值，无 header → default） | F-W-1 | `tests/test_workspace_contextvar.py::test_middleware_default_fallback`（新建）：TestClient 不带 header → 断言 QueryEngine._effective_workspace_id() == "default" | [TBD-impl] |
| AC-WS-3（跨 workspace 不泄漏） | F-W-1 | `tests/test_workspace_isolation.py::test_cross_workspace_no_leak`（新建）：2 workspace（team-a + team-b）各写入 claim → workspace A 请求搜索 → 断言不含 workspace B claim | [TBD-impl] |
| AC-WS-4（CLI 不受影响） | F-W-1 | `tests/test_workspace_cli_compat.py::test_cli_unchanged`（新建）：CLI 模式下 QueryEngine.query → 断言使用 default workspace | [TBD-impl] |
| AC-WS-5（构造签名不变） | F-W-1 | `tests/test_workspace_signature.py::test_queryengine_init_signature`（新建）：`inspect.signature(QueryEngine.__init__)` → 断言参数列表含 `workspace_id: str = "default"` | [TBD-impl] |
| AC-O4-1（tag 指向 release commit） | F-W-2 | `tests/test_o4_tag_flow.py::test_tag_points_to_release_commit`（06 ship 时执行）：`git log --oneline v1.18.0 -1` → 断言输出含 `release: v1.18.0` | [TBD-impl, 06 时执行] |
| AC-O4-2（GitHub Release 关联） | F-W-2 | `tests/test_o4_tag_flow.py::test_github_release_association`（06 ship 时执行）：`gh release view v1.18.0` → 断言 tag_name = v1.18.0 | [TBD-impl, 06 时执行] |

> AC-WS-1..5→F-W-1, AC-O4-1/2→F-W-2。PRD §6 共 7 条 AC 全归属 Feature，无丢失。

## 补充测试用例

| 用例 | 类型 | AC 覆盖 | Feature |
|---|---|---|---|
| `tests/test_workspace_validation.py::test_invalid_chars_400`（workspace_id 非法字符 → 400） | unit | AC-WS-1（补充） | F-W-1 |
| `tests/test_workspace_validation.py::test_too_long_400`（workspace_id 超长 → 400） | unit | AC-WS-1（补充） | F-W-1 |
| `tests/test_workspace_validation.py::test_valid_64_chars`（合法 64 字符边界） | unit | AC-WS-1（补充） | F-W-1 |
| `tests/test_workspace_contextvar.py::test_reset_after_request`（middleware finally reset） | integration | AC-WS-1（补充） | F-W-1 |
| `tests/test_workspace_thread_propagation.py::test_contextvar_in_thread`（asyncio.to_thread 传播） | unit | AC-WS-1（补充） | F-W-1 |
| `tests/test_release_flow_docs.py::test_release_manager_mentions_tag_order`（release-manager.md 含 tag 顺序） | unit（grep） | AC-O4-1（文档） | F-W-2 |
| `tests/test_release_flow_docs.py::test_release_flow_exists`（scripts/RELEASE-FLOW.md 存在） | unit（文件检查） | AC-O4-1（文档） | F-W-2 |
| `tests/test_release_flow_docs.py::test_release_flow_steps`（RELEASE-FLOW.md 含 5 step） | unit（text parse） | AC-O4-1（文档） | F-W-2 |

## 约定

- **middleware contextvar 测试**（`test_workspace_contextvar.py`，新建）：用 FastAPI TestClient 创建带 WorkspaceContextMiddleware 的 app → 发带/不带 `X-Workspace-Id` header 的请求 → 断言 contextvar 值。pytest，CI 始终跑。
- **跨 workspace 隔离测试**（`test_workspace_isolation.py`，新建）：mock 2 workspace 的 claims（team-a + team-b）→ workspace A 请求搜索 → 断言结果不含 workspace B claim。pytest，CI 始终跑。
- **CLI 兼容测试**（`test_workspace_cli_compat.py`，新建）：CLI 模式下创建 QueryEngine（不走 middleware）→ 调 query → 断言使用 default workspace。pytest，CI 始终跑。
- **构造签名测试**（`test_workspace_signature.py`，新建）：`inspect.signature(QueryEngine.__init__)` → 断言 `workspace_id` 参数存在且 default = `"default"`。pytest，CI 始终跑。
- **workspace_id 校验测试**（`test_workspace_validation.py`，新建）：TestClient 发非法/超长/合法边界 workspace_id → 断言 400/200。pytest，CI 始终跑。
- **contextvar 线程传播测试**（`test_workspace_thread_propagation.py`，新建）：设 contextvar → asyncio.to_thread 内读 contextvar → 断言值一致。pytest，CI 始终跑。
- **O4 tag 验证测试**（`test_o4_tag_flow.py`，新建）：06 ship 时执行——`git log --oneline v1.18.0 -1` 断言 release commit + `gh release view v1.18.0` 断言关联。标记 `@pytest.mark.skipif` 不在 CI 跑（仅 06 ship 时执行）。
- **文档验证测试**（`test_release_flow_docs.py`，新建）：检查 release-manager.md 含 tag 顺序 + scripts/RELEASE-FLOW.md 存在且含 5 step。pytest，CI 始终跑。

## 测试文件矩阵

| 测试文件 | 新建/改 | mock/skip | AC 覆盖 | Feature |
|---|---|---|---|---|
| `tests/test_workspace_contextvar.py`（新建） | 新建 | TestClient mock | AC-WS-1, AC-WS-2 | F-W-1 |
| `tests/test_workspace_isolation.py`（新建） | 新建 | mock DB | AC-WS-3 | F-W-1 |
| `tests/test_workspace_cli_compat.py`（新建） | 新建 | 无 mock | AC-WS-4 | F-W-1 |
| `tests/test_workspace_signature.py`（新建） | 新建 | inspect | AC-WS-5 | F-W-1 |
| `tests/test_workspace_validation.py`（新建） | 新建 | TestClient mock | AC-WS-1（补充） | F-W-1 |
| `tests/test_workspace_thread_propagation.py`（新建） | 新建 | 无 mock | AC-WS-1（补充） | F-W-1 |
| `tests/test_o4_tag_flow.py`（新建） | 新建 | skipif not release | AC-O4-1, AC-O4-2 | F-W-2 |
| `tests/test_release_flow_docs.py`（新建） | 新建 | 无 mock | AC-O4-1（文档） | F-W-2 |

## 依赖约束

- 无新 pip 依赖（后端测试用 pytest + inspect + re + FastAPI TestClient，标准库 + 既有依赖）。
- 无新 npm 依赖（不改前端代码）。
- AC-O4-1/2（tag 验证）依赖 git tag 已打 + gh CLI 可用——仅 06 ship 时执行，CI 标记 skipif。

## CI 兼容矩阵

| AC | 依赖 git tag? | 依赖 gh CLI? | CI 行为 | marker |
|---|---|---|---|---|
| AC-WS-1 | 否 | 否 | CI 始终跑 | 无 |
| AC-WS-2 | 否 | 否 | CI 始终跑 | 无 |
| AC-WS-3 | 否 | 否 | CI 始终跑 | 无 |
| AC-WS-4 | 否 | 否 | CI 始终跑 | 无 |
| AC-WS-5 | 否 | 否 | CI 始终跑 | 无 |
| AC-O4-1 | 是 | 否 | 06 ship 时跑 | `@pytest.mark.skipif` |
| AC-O4-2 | 是 | 是 | 06 ship 时跑 | `@pytest.mark.skipif` |

## 后端不回归（系统级 NFR，PRD §4）

| AC | 验证方式 | 基线 | 状态 |
|---|---|---|---|
| 后端不回归 | pytest ≥ 2267 passed，ruff 0，coverage ≥ 67%，smoke 6/6 | v1.17.0 = 2267 passed / ruff 0 / coverage ≥ 67% / smoke 6/6 | [TBD-impl] |

> v1.18.0 后端改动为 middleware + QueryEngine contextvar fallback（不改构造签名），新增 ~10 个测试（AC-WS-1..5 + 补充），pytest 总数预期增加。
