---
id: SPEC-F-T-1
title: 自定义 agent 角色注册（.saw/agents/*.yaml 加载 + build_default_agents 合并 + CLI/REST 可见）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-agent-link-v1.15.0.md
pms_ref: .csp/product-spec/PMS-agent-link.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-T-1
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-015-agent-role-registry-activity.md
adr_ref: .csp/tech-decisions/ADR/ADR-015-agent-role-registry-activity.md
ac_coverage: 4/4
related_tasks: [.csp/tasks/TASKS-DELTA-v1.15.0.md#T-F-T-1]
---

# SPEC-F-T-1: 自定义 agent 角色注册

## 实现 delta（ground 自源码）

> ADR-015 决策一：YAML 配置文件 + build_default_agents 合并。
> 不修改 `build_default_agents()` 源码/签名/返回结构（PMS 明确约束，additive 合并）。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `src/saw/engines/collaborate/agents/__init__.py` L35 | `build_default_agents(llm_router, feedback_engine)` 硬编码 6 角色返回 dict，无外部注册入口 | 新增 `load_custom_agents(llm_router)` + `build_agent_roster(llm_router, feedback_engine)` 函数；`build_default_agents` 不改 |
| `src/saw/api/routes/collaborate.py` L426 `list_agents()` | 调用 `build_default_agents(llm_router=None)` 返回静态 roster | 改调 `build_agent_roster(llm_router=None)`，返回含自定义角色 + `custom: true` 标记 |
| `src/saw/drivers/cli/commands/`（saw agents CLI） | 调用 `build_default_agents` 返回内置角色 | 改调 `build_agent_roster`，输出含自定义角色（标注 `custom`） |
| `src/saw/engines/collaborate/workflow_parser.py` `validate()` | `available_agents` 集合仅含内置 6 角色 | `available_agents` 集合含 `build_agent_roster` 返回的所有角色（含自定义） |

### 不改动

- `src/saw/engines/collaborate/agents/base.py`——`BaseAgent.__init__` 签名不变，自定义角色直接复用 `BaseAgent(name, model_tier, system_prompt, tools_allowed)` 构造。
- `build_default_agents()` 函数体——不改源码/签名/返回结构。
- 内置 6 角色行为——additive 合并，内置角色不受影响。

## 后端架构

### YAML 角色定义文件 schema（`.saw/agents/*.yaml`）

```yaml
# 示例：.saw/agents/medical_expert.yaml
name: MedicalExpert          # 必填，string，不得与内置 6 角色重名
model_tier: sonnet            # 必填，enum: haiku|sonnet|opus|rule
system_prompt: >             # 必填，非空 string
  You are a medical expert agent. Analyze medical knowledge
  pages and provide domain-specific insights.
tools_allowed:               # 选填，list[str]，可为空
  - search
  - read
constraints:                 # 选填，dict，可为空
  max_tokens: 4096
```

**字段定义**：

| 字段 | 类型 | 必填 | 约束 | 校验失败处理 |
|---|---|---|---|---|
| `name` | str | 是 | 不得与内置 6 角色（Librarian/Writer/Critic/Linker/Scholar/Guardian）重名 | 跳过注册 + 日志 warning `"Agent role '{name}' conflicts with built-in, skipped"` |
| `model_tier` | str | 是 | 枚举值 `haiku` / `sonnet` / `opus` / `rule`（复用 `BaseAgent.__init__` Literal 约束） | 跳过注册 + 日志 warning `"Invalid model_tier '{value}' for agent '{name}', must be haiku/sonnet/opus/rule"` |
| `system_prompt` | str | 是 | 非空（`len(system_prompt.strip()) > 0`） | 跳过注册 + 日志 warning `"Agent '{name}' missing system_prompt, skipped"` |
| `tools_allowed` | list[str] | 否 | 列表格式（可为空列表 `[]`），默认 `[]` | 非 list → 设为 `[]` + 日志 warning |
| `constraints` | dict | 否 | dict 格式（可为空 `{}`），默认 `{}` | 非 dict → 设为 `{}` + 日志 warning |

**YAML 解析异常处理**：
- YAML 格式错误（`yaml.YAMLError`）→ 跳过该文件 + 日志 error `"Failed to parse agent definition '{file}': {error}"`
- 文件读取失败（`OSError`）→ 跳过该文件 + 日志 error
- `.saw/agents/` 目录不存在 → 仅返回内置角色（不报错，正常降级）

### `load_custom_agents()` 函数（`agents/__init__.py` 新增）

```python
def load_custom_agents(
    llm_router: "LLMRouter | None",
    agents_dir: Path | None = None,
) -> dict[str, BaseAgent]:
    """Scan .saw/agents/*.yaml and build custom agent instances.

    Additive to build_default_agents() — does not modify it.
    Invalid definitions are skipped with a warning, never blocking startup.
    """
    import yaml
    from pathlib import Path
    import logging

    logger = logging.getLogger(__name__)
    if agents_dir is None:
        agents_dir = Path(".saw/agents")

    custom: dict[str, BaseAgent] = {}
    if not agents_dir.is_dir():
        return custom  # no .saw/agents/ → only built-in agents

    BUILTIN_NAMES = {"Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian"}
    VALID_TIERS = {"haiku", "sonnet", "opus", "rule"}

    for yaml_file in sorted(agents_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                logger.warning("Agent definition '%s' is not a mapping, skipped", yaml_file)
                continue
        except (yaml.YAMLError, OSError) as e:
            logger.error("Failed to parse agent definition '%s': %s", yaml_file, e)
            continue

        name = data.get("name", "")
        if not name or name in BUILTIN_NAMES:
            logger.warning("Agent role '%s' conflicts with built-in, skipped", name)
            continue

        model_tier = data.get("model_tier", "")
        if model_tier not in VALID_TIERS:
            logger.warning("Invalid model_tier '%s' for agent '%s', must be haiku/sonnet/opus/rule", model_tier, name)
            continue

        system_prompt = data.get("system_prompt", "")
        if not system_prompt or not system_prompt.strip():
            logger.warning("Agent '%s' missing system_prompt, skipped", name)
            continue

        tools_allowed = data.get("tools_allowed", [])
        if not isinstance(tools_allowed, list):
            logger.warning("tools_allowed for '%s' is not a list, defaulting to []", name)
            tools_allowed = []

        constraints = data.get("constraints", {})
        if not isinstance(constraints, dict):
            constraints = {}

        custom[name] = BaseAgent(
            name=name,
            model_tier=model_tier,
            system_prompt=system_prompt,
            tools_allowed=tools_allowed,
            constraints=constraints or None,
        )
        logger.info("Loaded custom agent '%s' from %s", name, yaml_file)

    return custom
```

### `build_agent_roster()` 函数（`agents/__init__.py` 新增）

```python
def build_agent_roster(
    llm_router: "LLMRouter | None",
    feedback_engine=None,
) -> dict[str, BaseAgent]:
    """Build the full agent roster: built-in 6 + custom from .saw/agents/*.yaml.

    Additive merge — build_default_agents() is called unchanged, then
    custom agents are merged in. Built-in agents are never overwritten.
    """
    roster = build_default_agents(llm_router, feedback_engine=feedback_engine)
    custom = load_custom_agents(llm_router)
    roster.update(custom)  # custom agents added additively
    return roster
```

### REST `list_agents()` 改动（`collaborate.py` L426）

```python
@router.get("/agents")
async def list_agents() -> dict[str, Any]:
    """List the agent roster (built-in + custom, with custom flag)."""
    from saw.engines.collaborate.agents import build_agent_roster

    BUILTIN_NAMES = {"Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian"}
    roster = build_agent_roster(llm_router=None)
    agents = []
    for name in sorted(roster):
        a = roster[name]
        agents.append({
            "name": a.name,
            "model_tier": a.model_tier,
            "tools_allowed": list(getattr(a, "_tools_allowed", []) or []),
            "rule": a.model_tier == "rule",
            "custom": name not in BUILTIN_NAMES,
        })
    return {"agents": agents, "total": len(agents)}
```

### `WorkflowParser.validate()` 改动

`available_agents` 集合从 `build_agent_roster()` 获取（含自定义角色名），而非仅内置 6 角色。

### 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 自定义角色 name 与内置角色重名 | 跳过注册 | 日志 warning `"Agent role '{name}' conflicts with built-in, skipped"` |
| model_tier 值非法 | 跳过注册 | 日志 warning `"Invalid model_tier ..."` |
| YAML 格式错误 | 跳过该文件 | 日志 error `"Failed to parse agent definition '{file}': {error}"` |
| system_prompt 为空 | 跳过注册 | 日志 warning `"Agent '{name}' missing system_prompt, skipped"` |
| `.saw/agents/` 目录不存在 | 正常降级，仅返回内置角色 | 无提示（正常行为） |

## 数据库 Schema

无 schema 变更。角色定义存储在 `.saw/agents/*.yaml` 文件（file storage），不持久化到 DB。

## API 契约

### `GET /api/v1/agents`（既有端点扩展）

**响应 200**（新增 `custom` 字段）：
```json
{
  "agents": [
    {
      "name": "Librarian",
      "model_tier": "sonnet",
      "tools_allowed": ["search", "read"],
      "rule": false,
      "custom": false
    },
    {
      "name": "MedicalExpert",
      "model_tier": "sonnet",
      "tools_allowed": ["search", "read"],
      "rule": false,
      "custom": true
    }
  ],
  "total": 7
}
```

### CLI `saw agents`

```
Agent Roster (7)
┌─────────────────┬────────────┬──────────────────┬────────┐
│ name            │ model_tier │ tools_allowed    │ custom │
├─────────────────┼────────────┼──────────────────┼────────┤
│ Librarian       │ sonnet     │ search, read     │        │
│ MedicalExpert   │ sonnet     │ search, read     │ custom │
│ ...             │ ...        │ ...              │ ...    │
└─────────────────┴────────────┴──────────────────┴────────┘
```

## 测试策略（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-A-1 | `tests/unit/test_custom_agents.py`（新建）：创建 `.saw/agents/expert.yaml`（name=MedicalExpert, model_tier=sonnet, system_prompt 非空）→ 调用 `build_agent_roster(llm_router=None)` → roster 含 MedicalExpert | `"MedicalExpert" in roster`，`roster["MedicalExpert"].model_tier == "sonnet"` |
| AC-A-2 | `test_custom_agents.py`：MedicalExpert 已注册 → 构造 workflow YAML（step.agent=MedicalExpert）→ `WorkflowParser.validate()` → 无错误 | `validate()` 返回无错误 |
| AC-A-3 | `test_custom_agents.py`：创建 `.saw/agents/dup.yaml`（name=Librarian，与内置重名）→ `load_custom_agents()` → 该角色被跳过 | `"Librarian"` 在 `load_custom_agents` 返回中不存在（或重名被跳过） |
| AC-A-4 | `tests/unit/test_agents_rest.py`（新建或扩）：注册 MedicalExpert → `GET /api/v1/agents` → 响应含 MedicalExpert + `custom: true` | 响应 JSON 含 `"name": "MedicalExpert"` 且 `"custom": true` |

**CI 兼容**：全部用临时 `.saw/agents/` 目录（`tmp_path` fixture），不依赖真实文件。无 LLM 调用（`llm_router=None`）。

## 安全考量

- 角色定义文件来自 `.saw/agents/` 本地目录，无远程输入注入风险。
- `model_tier` 受 `Literal["haiku","sonnet","opus","rule"]` 约束，非法值跳过。
- `system_prompt` 作为 LLM system message，用户自行管理内容安全性（同内置角色范式）。
- `yaml.safe_load` 解析（非 `yaml.load`），防止 YAML 反序列化攻击。

## 实现就绪度

- [x] YAML schema 字段定义明确（name/model_tier/system_prompt/tools_allowed/constraints）
- [x] `load_custom_agents()` 伪代码完整（扫描 + 解析 + 校验 + 构造 BaseAgent）
- [x] `build_agent_roster()` additive 合并（不改 build_default_agents）
- [x] CLI/REST 改调 `build_agent_roster()` + `custom` 标记
- [x] WorkflowParser.validate() available_agents 含自定义角色
- [x] 异常处理覆盖（重名/非法 model_tier/YAML 错误/空 prompt/目录不存在）
- [x] AC 覆盖 4/4
- [ ] 05 实施后 CI 验证 `saw agents` 输出含自定义角色行
