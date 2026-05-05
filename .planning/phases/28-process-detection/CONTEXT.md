# Phase 28: Process Detection — CONTEXT.md

**Phase:** 28
**Milestone:** v3.4 Code Intelligence
**Status:** Planning
**Created:** 2026-05-04

## Problem Statement

Smart Agent Wiki 有知识图谱，但缺少一个核心功能：**执行流程自动检测**。

**问题：**
1. 用户不知道代码的入口点在哪里
2. 难以理解请求如何从入口到数据库的完整路径
3. 缺乏自动化的调用链分析
4. 需要手动追踪复杂的执行流程

**GitNexus 的设计：**
GitNexus 的 `process` 工具可以自动检测执行流程：
```python
process({entry: "handleRequest", depth: 3})

EXECUTION FLOW:
  handleRequest (entry)
    → validateInput (depth 1)
      → parseJSON (depth 2)
    → processData (depth 1)
      → transformPayload (depth 2)
        → applyRules (depth 3)
    → saveToDatabase (depth 1)
```

## Goal

实现 Process Detection Engine：
1. 从入口点自动追踪调用链
2. 深度分层的执行流程展示
3. 识别关键路径和分支
4. MCP 工具 `saw_process()`

## Scope

### In Scope

- 从指定入口点追踪调用链
- 深度限制和分支检测
- 关键节点标注
- MCP 工具实现

### Out of Scope

- 动态执行分析
- 性能分析
- 外部系统集成

## Technical Design

### Process Detection Algorithm

```python
async def detect_process(
    graph: KnowledgeGraph,
    entry: str,
    max_depth: int = 5,
    relation_types: list[str] = None,
    include_loops: bool = False
) -> ProcessResult:
    """
    Detect execution flow from entry point.

    Algorithm:
    1. Find entry node
    2. DFS traverse CALLS edges
    3. Build call tree with depth
    4. Detect branches and loops
    5. Return structured flow
    """
    relation_types = relation_types or ['CALLS']

    entry_node = find_node(graph, entry)
    if not entry_node:
        raise NodeNotFoundError(entry)

    # Build call tree
    tree = ProcessNode(
        uid=entry_node['uid'],
        name=entry_node['name'],
        depth=0,
        children=[]
    )

    visited = set()
    _build_call_tree(graph, tree, visited, max_depth, relation_types, include_loops)

    return ProcessResult(
        entry=entry,
        tree=tree,
        summary=get_process_summary(tree)
    )
```

### MCP Tool

```python
@mcp.tool()
async def saw_process(
    entry: str,
    max_depth: int = 5,
    include_loops: bool = False
) -> ProcessResult:
    """
    Detect execution flow from an entry point.

    Args:
        entry: Entry point name or UID
        max_depth: Maximum traversal depth (1-10)
        include_loops: Include recursive calls

    Returns:
        ProcessResult with call tree and summary
    """
```

## Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | 用户可查询任意入口点的执行流程 | CLI 测试 |
| 2 | 结果按深度分层 | 单元测试 |
| 3 | 分支路径清晰标注 | 输出验证 |
| 4 | 循环调用正确处理 | 单元测试 |
| 5 | 提供 MCP 工具 | 集成测试 |

## Dependencies

- Depends on: Phase 27 complete
- Blocks: Phase 29

---

*Created: 2026-05-04*