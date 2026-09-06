# TMS Delta — v1.15.0（2026-09-06）

> 03 测试规约 delta。agent/link 能力轮：自定义 agent 角色注册 + L2 links auto-apply + M2 agent 活动聚合。
> 基线：v1.14.0 = 2192 passed / 3 skipped / 4 deselected (benchmark_e2e) / ruff 0 / coverage 67.34% / smoke 11/11。
> 全部用 mock（临时 .saw/agents/ 目录 + mock event_bus + mock compute_related_pages），不依赖 vLLM/embedding，CI 始终跑。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-A-1（自定义角色注册并出现在 roster） | F-T-1 | `tests/unit/test_custom_agents.py`（新建）：创建 `.saw/agents/expert.yaml`（name=MedicalExpert, model_tier=sonnet, system_prompt 非空）→ `build_agent_roster(llm_router=None)` → roster 含 MedicalExpert + `custom` 标记 | mapped |
| AC-A-2（自定义角色被 workflow 引用） | F-T-1 | `test_custom_agents.py`：MedicalExpert 已注册 → 构造 workflow YAML（step.agent=MedicalExpert）→ `WorkflowParser.validate()` → 无错误 | mapped |
| AC-A-3（重名角色被拒绝） | F-T-1 | `test_custom_agents.py`：创建 `.saw/agents/dup.yaml`（name=Librarian，与内置重名）→ `load_custom_agents()` → 该角色被跳过 | mapped |
| AC-A-4（REST 端点返回自定义角色） | F-T-1 | `tests/unit/test_agents_rest.py`（新建或扩）：注册 MedicalExpert → `GET /api/v1/agents` → 响应含 MedicalExpert + `custom: true` | mapped |
| AC-B-1（dry-run 预览不写回） | F-T-2 | `tests/unit/test_links_apply.py`（新建）：创建 3 页面 wiki → `saw links apply A --path .`（无 `--confirm`）→ 打印 3 条将应用链接 + 文件未修改 | mapped |
| AC-B-2（confirm 写回） | F-T-2 | `test_links_apply.py`：`saw links apply A --path . --confirm` → 页面 A 文件新增 `## Related` 段落含 `[[link]]` + frontmatter `related` 同步更新 | mapped |
| AC-B-3（已有链接不重复） | F-T-2 | `test_links_apply.py`：页面 A 已含 `[[page-b]]` → `saw links apply A --confirm` → `[[page-b]]` 不重复插入，提示 skipped | mapped |
| AC-B-4（apply 后 audit 无新断链） | F-T-2 | `test_links_apply.py`：apply 后 `saw links audit` → 插入的链接目标都存在，无新断链 | mapped |
| AC-C-1（activity 端点返回聚合数据） | F-T-3 | `tests/unit/test_agent_activity.py`（新建）：创建 `AgentActivityTracker` → 模拟发布 WorkflowStep 事件 `{"step":"Scholar.synthesize","status":"completed"}` → `tracker.get_activity("Scholar")` → calls≥1, last_action="synthesize", last_active_at 非空 | mapped |
| AC-C-2（无活动的 agent 返回空活动） | F-T-3 | `test_agent_activity.py`：`tracker.get_activity("Guardian")`（从未发布 Guardian 事件）→ calls=0, last_active_at=null | mapped |
| AC-C-3（不存在的 agent 返回 404） | F-T-3 | `tests/unit/test_agents_rest.py`（扩）：`GET /api/v1/agents/NonExistent/activity` → 返回 404 "Agent not found" | mapped |
| AC-C-4（agents 端点含 activity_summary） | F-T-3 | `test_agents_rest.py`：发布 3 次 Scholar 事件 → `GET /api/v1/agents` → Scholar 行含 `activity_summary: {calls: 3, last_active_at: "..."}` | mapped |

## 约定

- **自定义角色注册测试**（`test_custom_agents.py`，新建）：用 `tmp_path` fixture 创建临时 `.saw/agents/` 目录 + YAML 角色定义文件。`build_agent_roster(llm_router=None)` 不依赖 LLM。重名/非法 model_tier/空 prompt/YAML 格式错误 → 跳过 + 日志 warning 验证。CI 始终跑。
- **自定义角色 REST 测试**（`test_agents_rest.py`，新建或扩）：用 FastAPI `TestClient` + mock `build_agent_roster` 返回含自定义角色。验证 `GET /api/v1/agents` 响应含 `custom: true` 标记。CI 始终跑。
- **links apply 测试**（`test_links_apply.py`，新建）：用 `tmp_path` fixture 创建临时 wiki 目录 + 3 页面。mock `compute_related_pages` 返回固定建议列表。验证 dry-run（文件不变）+ confirm（`## Related` 段落 + frontmatter related 同步）+ 去重 + audit 无断链。CI 始终跑。不依赖 embedding/vLLM。
- **agent activity 测试**（`test_agent_activity.py`，新建）：直接调用 `AgentActivityTracker._handle_event(event)` 模拟 WorkflowStep 事件。验证计数器更新 + get_activity/get_summary 返回值。CI 始终跑。不依赖真实 workflow 执行。
- **agent activity REST 测试**（`test_agents_rest.py`，扩）：用 FastAPI `TestClient` + mock `get_activity_tracker()` 返回预设 tracker。验证 `GET /api/v1/agents/{name}/activity` 200/404 响应 + `GET /api/v1/agents` activity_summary 字段。CI 始终跑。

## 测试文件矩阵

| 测试文件 | 新建/改 | mock/skip | AC 覆盖 | Feature |
|---|---|---|---|---|
| `tests/unit/test_custom_agents.py`（新建） | 新建 | mock `.saw/agents/` 目录（tmp_path），无 LLM | AC-A-1, AC-A-2, AC-A-3 | F-T-1 |
| `tests/unit/test_agents_rest.py`（新建或扩） | 新建/扩 | mock `build_agent_roster` + TestClient | AC-A-4, AC-C-3, AC-C-4 | F-T-1, F-T-3 |
| `tests/unit/test_links_apply.py`（新建） | 新建 | mock `compute_related_pages` + tmp_path wiki | AC-B-1, AC-B-2, AC-B-3, AC-B-4 | F-T-2 |
| `tests/unit/test_agent_activity.py`（新建） | 新建 | mock event（直接调用 `_handle_event`） | AC-C-1, AC-C-2 | F-T-3 |

## 依赖约束

- 无新 pip 依赖。复用既有 `yaml`（`PyYAML`，已安装）/ `typer` / `fastapi` / `pytest`。
- 不引入 hnswlib/torch/faiss 等重依赖。
- 不依赖 vLLM/embedding/sentence_transformers。

## CI 兼容矩阵

| AC | 依赖 vLLM? | 依赖 embedding? | CI 行为 | marker |
|---|---|---|---|---|
| AC-A-1 | 否 | 否 | CI 始终跑 | 无 |
| AC-A-2 | 否 | 否 | CI 始终跑 | 无 |
| AC-A-3 | 否 | 否 | CI 始终跑 | 无 |
| AC-A-4 | 否 | 否 | CI 始终跑 | 无 |
| AC-B-1 | 否 | 否（mock compute_related_pages） | CI 始终跑 | 无 |
| AC-B-2 | 否 | 否（mock compute_related_pages） | CI 始终跑 | 无 |
| AC-B-3 | 否 | 否（mock compute_related_pages） | CI 始终跑 | 无 |
| AC-B-4 | 否 | 否（mock compute_related_pages） | CI 始终跑 | 无 |
| AC-C-1 | 否 | 否（mock event） | CI 始终跑 | 无 |
| AC-C-2 | 否 | 否（mock event） | CI 始终跑 | 无 |
| AC-C-3 | 否 | 否（mock tracker） | CI 始终跑 | 无 |
| AC-C-4 | 否 | 否（mock tracker） | CI 始终跑 | 无 |

## 落地状态（05 实施回填）

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-A-1 | F-T-1 | `test_custom_agents.py::test_ac_a_1_custom_agent_in_roster` | covered |
| AC-A-2 | F-T-1 | `test_custom_agents.py::test_ac_a_2_workflow_validate_custom_agent` | covered |
| AC-A-3 | F-T-1 | `test_custom_agents.py::test_ac_a_3_duplicate_name_skipped` | covered |
| AC-A-4 | F-T-1 | `test_agents_rest.py::test_ac_a_4_rest_returns_custom_agent` | covered |
| AC-B-1 | F-T-2 | `test_links_apply.py::test_ac_b_1_dry_run_no_write` | covered |
| AC-B-2 | F-T-2 | `test_links_apply.py::test_ac_b_2_confirm_writes_related_section` | covered |
| AC-B-3 | F-T-2 | `test_links_apply.py::test_ac_b_3_dedup_existing_link` | covered |
| AC-B-4 | F-T-2 | `test_links_apply.py::test_ac_b_4_audit_no_broken_links` | covered |
| AC-C-1 | F-T-3 | `test_agent_activity.py::test_ac_c_1_activity_returns_aggregated` | covered |
| AC-C-2 | F-T-3 | `test_agent_activity.py::test_ac_c_2_no_activity_returns_empty` | covered |
| AC-C-3 | F-T-3 | `test_agents_rest.py::test_ac_c_3_nonexistent_agent_404` | covered |
| AC-C-4 | F-T-3 | `test_agents_rest.py::test_ac_c_4_agents_endpoint_activity_summary` | covered |
