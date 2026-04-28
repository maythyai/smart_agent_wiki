---
phase: 03-01-multi-agent-foundation
reviewed: 2026-04-28T12:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - src/saw/adapters/crypto/cedar_policy.py
  - src/saw/domain/agent.py
  - src/saw/domain/protocols.py
  - src/saw/engines/collaborate/__init__.py
  - src/saw/engines/collaborate/a2a_protocol.py
  - src/saw/engines/collaborate/agents/base.py
  - src/saw/engines/collaborate/agents/critic.py
  - src/saw/engines/collaborate/agents/guardian.py
  - src/saw/engines/collaborate/agents/librarian.py
  - src/saw/engines/collaborate/agents/linker.py
  - src/saw/engines/collaborate/agents/scholar.py
  - src/saw/engines/collaborate/agents/writer.py
  - src/saw/engines/collaborate/dispatcher.py
  - src/saw/engines/collaborate/orchestrator.py
  - src/saw/engines/collaborate/workflow_executor.py
  - src/saw/engines/collaborate/workflow_parser.py
findings:
  critical: 2
  warning: 8
  info: 5
  total: 15
status: issues_found
---

# Phase 03-01: Code Review Report

**Reviewed:** 2026-04-28T12:00:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

对 Multi-Agent Foundation 阶段的 16 个源文件进行了标准深度代码审查。发现了 2 个关键问题和 8 个警告，主要涉及安全策略执行逻辑缺陷、临时文件安全隐患、未使用变量、以及重复导入等问题。

## Critical Issues

### CR-01: Guardian Agent 默认拒绝策略实现不一致

**File:** `src/saw/engines/collaborate/agents/guardian.py:102-120`
**Issue:** 文档注释声称遵循 D-14 "Default deny policy"，但实际实现逻辑与此矛盾。当 `_rules` 为空时（新安装场景），系统返回 `allowed=True`（允许），这违背了"默认拒绝"的安全原则。更严重的是，当存在规则但没有任何 permit 规则匹配时，才返回拒绝——这意味着即使只有 forbid 规则且未匹配，也不会默认拒绝。

```python
# 行 102-120 的逻辑问题：
# 1. 当 _rules 为空时，返回 allowed=True
# 2. 当 _rules 非空但无 permit 匹配时，返回 allowed=False
# 这与"默认拒绝"原则矛盾——正确的默认拒绝应该在没有显式 permit 时就拒绝
```

**Fix:**
```python
async def execute(
    self,
    task: AgentTask,
    context: AgentContext,
    tools: list,
) -> AgentResult:
    action = task.payload.get("action", "*")
    resource = task.payload.get("resource", "*")
    calling_agent = context.calling_agent or "unknown"

    # Evaluate all rules - deny rules take precedence
    for rule in self._rules:
        if self._rule_matches(rule, calling_agent, action, resource):
            if rule.effect == "forbid":
                return AgentResult(
                    success=False,
                    payload={
                        "allowed": False,
                        "reason": rule.reason,
                        "rule_id": rule.id,
                    },
                    error=f"Policy denied by rule {rule.id}",
                )

    # Per D-14: Default deny - must have explicit permit to allow
    has_permit_rule = any(
        self._rule_matches(r, calling_agent, action, resource)
        and r.effect == "permit"
        for r in self._rules
    )

    if has_permit_rule:
        return AgentResult(
            success=True,
            payload={"allowed": True, "reason": "Permit rule matched"},
        )
    
    # D-14: Default deny - NO permit matched means deny
    return AgentResult(
        success=False,
        payload={"allowed": False, "reason": "No permit rule matched (default deny)"},
        error="Default deny policy",
    )
```

### CR-02: Cedar CLI 临时文件存在竞态条件漏洞

**File:** `src/saw/adapters/crypto/cedar_policy.py:225-277`
**Issue:** 使用 `NamedTemporaryFile` 创建临时文件时设置了 `delete=False`，随后在 `finally` 块中手动删除。这存在 TOCTOU (Time-of-Check-Time-of-Use) 竞态条件风险：攻击者可能在文件创建和删除之间的窗口期访问或替换文件内容。此外，如果进程在 `finally` 块执行前被强制终止，临时文件会残留。

```python
# 行 225-231: 不安全的临时文件创建
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False
) as f:
    json.dump(request_data, f)
    request_file = f.name
# 恶意用户可能在这个窗口期修改 request_file
```

**Fix:**
```python
import os
import tempfile

def evaluate(self, principal: str, action: str, resource: str, context: dict | None = None) -> PolicyDecision:
    request_data = {
        "principal": principal,
        "action": action,
        "resource": resource,
        "context": context or {},
    }

    # 使用 TempDirectory 替代 NamedTemporaryFile 确保 atomic delete
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            request_file = os.path.join(tmpdir, "request.json")
            # 设置限制性权限
            os.makedirs(tmpdir, mode=0o700, exist_ok=True)
            with open(request_file, "w", encoding="utf-8") as f:
                os.chmod(request_file, 0o600)
                json.dump(request_data, f)
            
            # ... 执行 CLI 命令 ...
            # TemporaryDirectory 在退出时自动安全删除
    except Exception as e:
        logger.error(f"Cedar CLI error: {e}")
        return PolicyDecision(allowed=False, reason=f"CLI error: {e}")
```

## Warnings

### WR-01: Dispatcher 的 fallback 机制未实际更改模型

**File:** `src/saw/engines/collaborate/dispatcher.py:138-158`
**Issue:** fallback 循环遍历 `fallback_chain`，但每次调用都是 `agent.execute()` 而未切换模型。Agent 的 model_tier 是在构造时固定的，fallback loop 不会改变 agent 使用的模型。代码设置 `result.metadata["model_tier_used"] = fallback_tier.value` 是误导性的——它记录了 fallback tier，但实际并未使用该 tier 调用 LLM。

**Fix:**
```python
# 方案1: 在 agent.execute() 中动态传入 model
# 方案2: 完善 LLMRouter 的 completion 方法支持 fallback
# 或者明确注释这是占位逻辑，需要后续完善
```

### WR-02: A2AAdapter broadcast 模式下异常处理不完整

**File:** `src/saw/engines/collaborate/a2a_protocol.py:165-179`
**Issue:** 在 broadcast 模式下使用 `asyncio.gather(..., return_exceptions=True)`，成功判断逻辑过于宽松。`hasattr(r, "success")` 检查可能导致错误的异常对象被误判为成功。

```python
# 行 172-175: 可能错误地将异常判断为成功
all_success = all(
    not isinstance(r, Exception) and (r.success if hasattr(r, "success") else True)
    for r in results
)
```

**Fix:**
```python
all_success = all(
    not isinstance(r, Exception) and isinstance(r, A2AResult) and r.success
    for r in results
)
```

### WR-03: WorkflowExecutor gate 检查逻辑错误

**File:** `src/saw/engines/collaborate/workflow_executor.py:220-233`
**Issue:** gate 检查失败后会增加 `retry_count`，但随后 `continue` 会重新执行相同的 gate 检查（因状态未变更），导致无限循环直到 `max_retries` 耗尽。这违背了重试逻辑的本意——重试应该尝试新的执行，而不是重复检查相同的失败条件。

**Fix:**
```python
# Gate 失败应该直接执行 fallback 而非重试
if step.gates:
    gate_result = await self._check_gates(step.gates, context)
    if not gate_result.passed:
        return await self._handle_gate_failure(step, gate_result, context)

# 重试逻辑应仅针对执行失败，而非 gate 失败
```

### WR-04: WorkflowParser 模板渲染存在潜在 XSS 风险

**File:** `src/saw/engines/collaborate/workflow_parser.py:193-203`
**Issue:** 使用 Jinja2 模板进行变量渲染时未设置自动转义，如果 `context` 包含用户可控数据，可能导致模板注入攻击。虽然这是后端 Python 代码而非 Web 前端，但恶意模板表达式可能执行任意代码。

```python
# 行 198: 未启用自动转义，可能存在模板注入风险
return Template(f"{{{{ {condition} }}}}").render(**context)
```

**Fix:**
```python
from jinja2 import Environment, BaseLoader, select_autoescape

SAFE_ENV = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(enabled_extensions=('html', 'xml')),
)

def render_template(self, template: str, context: dict[str, Any]) -> str:
    # 使用沙箱环境或限制可访问的变量
    safe_context = {k: v for k, v in context.items() if k.isidentifier()}
    return SAFE_ENV.from_string(template).render(**safe_context)
```

### WR-05: 重复导入 json 模块

**File:** `src/saw/engines/collaborate/agents/critic.py:77`
**File:** `src/saw/engines/collaborate/agents/librarian.py:77`
**File:** `src/saw/engines/collaborate/agents/linker.py:75`
**File:** `src/saw/engines/collaborate/agents/scholar.py:75`
**File:** `src/saw/engines/collaborate/agents/writer.py:74`
**Issue:** 所有 Agent 类在模块顶部已导入 `json`（通过 base.py 的 `import json`），但在 `_parse_response` 方法中又重复导入。虽然 Python 会缓存模块，但这是一种代码异味。

**Fix:** 在各文件顶部添加 `import json`，移除方法内的重复导入。

### WR-06: CollaborateEngine 紧密耦合内部属性

**File:** `src/saw/engines/collaborate/orchestrator.py:236-237`
**Issue:** 直接访问 `self._dispatcher._agents` 私有属性，违反封装原则。如果 AgentDispatcher 的内部实现变更，此代码会失败。

```python
# 行 236: 直接访问私有属性
return list(self._dispatcher._agents.keys())
```

**Fix:**
```python
# 在 AgentDispatcher 中添加公共方法
def get_registered_agents(self) -> dict[str, AgentProtocol]:
    return dict(self._agents)

# 在 CollaborateEngine 中调用
return list(self._dispatcher.get_registered_agents().keys())
```

### WR-07: BaseAgent execute 方法未使用传参

**File:** `src/saw/engines/collaborate/agents/base.py:80-103`
**Issue:** `execute` 方法接收 `tools` 参数但完全未使用。子类也忽略此参数。这表明要么设计不完整，要么参数是多余的。

**Fix:** 如果 tools 未使用，移除参数；或者添加文档说明未来将支持。

### WR-08: WorkflowExecutor._eval_condition 异常被静默吞掉

**File:** `src/saw/engines/collaborate/workflow_executor.py:395-400`
**Issue:** Jinja2 模板渲染失败时返回 `False`，但未记录任何日志。条件表达式解析失败会静默失败，难以调试。

```python
# 行 395-400
try:
    from jinja2 import Template
    return bool(Template(f"{{{{ {condition} }}}}").render(**context))
except Exception:
    return False  # 异常被静默忽略
```

**Fix:**
```python
except Exception as e:
    logger.warning(f"Condition evaluation failed: {condition}, error: {e}")
    return False
```

## Info

### IN-01: CedarPolicyEngine 未使用的 TYPE_CHECKING 导入

**File:** `src/saw/adapters/crypto/cedar_policy.py:18-19`
**Issue:** `TYPE_CHECKING` 导入但未使用，`if TYPE_CHECKING` 块为空。

**Fix:** 移除未使用的导入。

### IN-02: cedar_policy.py 冗余的 is_authorized 方法

**File:** `src/saw/adapters/crypto/cedar_policy.py:301-312`
**Issue:** `CedarPolicyEngine.is_authorized()` 和 `CedarPythonAdapter.is_authorized()` 都只是调用 `evaluate()` 的包装，存在代码冗余。

**Fix:** Protocols 已定义接口，可以考虑使用 Mixin 或组合减少重复。

### IN-03: 魔法字符串 "unknown" 作为默认 agent 名称

**File:** `src/saw/engines/collaborate/agents/guardian.py:83`
**Issue:** `calling_agent` 为 None 时使用 "unknown" 作为默认值，这个魔法字符串可能在多处使用，应定义为常量。

**Fix:**
```python
DEFAULT_AGENT_NAME = "unknown"
calling_agent = context.calling_agent or DEFAULT_AGENT_NAME
```

### IN-04: 硬编码的模型名称

**File:** `src/saw/engines/collaborate/dispatcher.py:27-31`
**Issue:** 模型名称硬编码在字典中。日期格式解析如 `20250514` 表明这些是特定日期的模型版本。应考虑集中管理或使用配置文件。

### IN-05: WorkflowStep dataclass 缺少冻结论证

**File:** `src/saw/engines/collaborate/workflow_parser.py:21-36`
**Issue:** `WorkflowStep` 是可变 dataclass，可能在运行时被意外修改。考虑添加 `frozen=True` 使其不可变。

---

_Reviewed: 2026-04-28T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
