# Phase 27: Impact Analysis Engine — CONTEXT.md

**Phase:** 27
**Milestone:** v3.4 Code Intelligence
**Status:** Planning
**Created:** 2026-05-04

## Problem Statement

Smart Agent Wiki 有知识图谱，但缺少一个核心功能：**代码修改影响分析**。

**问题：**
1. 用户修改代码前不知道会影响哪些依赖
2. 缺乏风险评估（高风险 vs 低风险）
3. 无法追踪上下游依赖链
4. 重构时容易破坏依赖方

**GitNexus 的设计：**
GitNexus 的 `impact` 工具是其核心价值之一：
```python
impact({target: "UserService", direction: "upstream", minConfidence: 0.8})

UPSTREAM (what depends on this):
  Depth 1 (WILL BREAK):
    handleLogin [CALLS 90%]
    handleRegister [CALLS 90%]
  Depth 2 (LIKELY AFFECTED):
    authRouter [IMPORTS]
```

## Goal

实现 Impact Analysis Engine：
1. 图遍历算法（BFS/DFS）
2. 深度分层（d=1/2/3）
3. 风险标签（WILL BREAK / LIKELY AFFECTED / MAY NEED TESTING）
4. 置信度过滤
5. MCP 工具 `saw_impact()`

## Scope

### In Scope

- 核心图遍历算法
- 深度分组和风险标注
- 置信度计算和过滤
- MCP 工具实现
- CLI 命令

### Out of Scope

- Web UI 可视化（Phase 27-03）
- 实时更新
- 外部系统集成

## Key Context

### Knowledge Graph Schema (现有)

```python
# saw/graph/models.py
class Node(TypedDict):
    uid: str
    kind: str  # File, Class, Method, Function, Variable
    name: str
    filePath: str
    startLine: int
    endLine: int

class Edge(TypedDict):
    uid: str
    type: str  # CALLS, IMPORTS, EXTENDS, IMPLEMENTS
    source: str
    target: str
    confidence: float  # 0.0 - 1.0
```

### Graph Traversal API

```python
# 现有图数据库接口
class GraphDatabase:
    def get_outgoing_edges(
        self, 
        node_id: str, 
        edge_types: list[str] = None
    ) -> list[Edge]:
        """获取出边（下游依赖）"""
        
    def get_incoming_edges(
        self, 
        node_id: str, 
        edge_types: list[str] = None
    ) -> list[Edge]:
        """获取入边（上游依赖）"""
```

## Technical Design

### Impact Result Structure

```python
from typing import TypedDict, Literal

RiskLevel = Literal['WILL_BREAK', 'LIKELY_AFFECTED', 'MAY_NEED_TESTING']

class ImpactNode(TypedDict):
    """单个受影响节点"""
    uid: str
    name: str
    kind: str
    filePath: str
    startLine: int
    depth: int
    risk_level: RiskLevel
    relation_type: str  # CALLS, IMPORTS, EXTENDS, IMPLEMENTS
    confidence: float

class ImpactResult(TypedDict):
    """Impact 分析结果"""
    target: str
    target_node: Node
    direction: str  # 'upstream' | 'downstream'
    impacts: list[ImpactNode]
    summary: dict  # {depth_1_count, depth_2_count, depth_3_count, high_risk_count}
    execution_time_ms: float
```

### Core Algorithm

```python
async def analyze_impact(
    graph: GraphDatabase,
    target: str,
    direction: str = 'upstream',
    max_depth: int = 3,
    min_confidence: float = 0.5,
    relation_types: list[str] = None,
    include_tests: bool = False
) -> ImpactResult:
    """
    GitNexus-style impact analysis.
    
    Algorithm:
    1. Find target node by name or UID
    2. BFS traverse along specified edges
    3. Group by depth with risk labels
    4. Filter by confidence threshold
    5. Return structured result
    """
    relation_types = relation_types or ['CALLS', 'IMPORTS', 'EXTENDS', 'IMPLEMENTS']
    
    # Find target
    target_node = await find_node(graph, target)
    if not target_node:
        raise NodeNotFoundError(target)
    
    # BFS traversal
    visited = set()
    impacts = []
    queue = [(target_node['uid'], 0)]
    
    while queue:
        node_id, depth = queue.pop(0)
        
        if depth > max_depth:
            continue
            
        if node_id in visited:
            continue
            
        visited.add(node_id)
        
        # Get edges based on direction
        if direction == 'upstream':
            edges = graph.get_incoming_edges(node_id, relation_types)
        else:
            edges = graph.get_outgoing_edges(node_id, relation_types)
        
        for edge in edges:
            if edge['confidence'] < min_confidence:
                continue
            
            # Get the dependent node
            dep_id = edge['source'] if direction == 'upstream' else edge['target']
            dep_node = graph.get_node(dep_id)
            
            # Filter tests if needed
            if not include_tests and is_test_node(dep_node):
                continue
            
            # Add to results
            impacts.append(ImpactNode(
                uid=dep_id,
                name=dep_node['name'],
                kind=dep_node['kind'],
                filePath=dep_node['filePath'],
                startLine=dep_node['startLine'],
                depth=depth + 1,
                risk_level=get_risk_level(depth + 1),
                relation_type=edge['type'],
                confidence=edge['confidence']
            ))
            
            queue.append((dep_id, depth + 1))
    
    # Sort by depth, then confidence
    impacts.sort(key=lambda x: (x['depth'], -x['confidence']))
    
    return ImpactResult(
        target=target,
        target_node=target_node,
        direction=direction,
        impacts=impacts,
        summary=get_summary(impacts),
        execution_time_ms=0  # Filled by caller
    )


def get_risk_level(depth: int) -> RiskLevel:
    """Map depth to risk level."""
    if depth == 1:
        return 'WILL_BREAK'
    elif depth == 2:
        return 'LIKELY_AFFECTED'
    else:
        return 'MAY_NEED_TESTING'


def get_summary(impacts: list[ImpactNode]) -> dict:
    """Generate summary statistics."""
    return {
        'depth_1_count': sum(1 for i in impacts if i['depth'] == 1),
        'depth_2_count': sum(1 for i in impacts if i['depth'] == 2),
        'depth_3_count': sum(1 for i in impacts if i['depth'] == 3),
        'high_risk_count': sum(1 for i in impacts if i['risk_level'] == 'WILL_BREAK'),
        'total_affected': len(impacts)
    }
```

### MCP Tool

```python
# saw/mcp/tools.py

@mcp.tool()
async def saw_impact(
    target: str,
    direction: str = 'upstream',
    max_depth: int = 3,
    min_confidence: float = 0.8,
    relation_types: list[str] = None,
    include_tests: bool = False
) -> ImpactResult:
    """
    Analyze code modification impact.
    
    Args:
        target: Symbol name or UID to analyze
        direction: 'upstream' (what depends on this) or 'downstream' (what this depends on)
        max_depth: Maximum traversal depth (1-5)
        min_confidence: Minimum edge confidence (0.0-1.0)
        relation_types: Filter by relation types (CALLS, IMPORTS, EXTENDS, IMPLEMENTS)
        include_tests: Include test files in results
    
    Returns:
        ImpactResult with affected nodes grouped by depth and risk level
    """
    graph = get_current_graph()
    
    start = time.time()
    result = await analyze_impact(
        graph, target, direction, max_depth, min_confidence, relation_types, include_tests
    )
    result['execution_time_ms'] = (time.time() - start) * 1000
    
    # Warning for high-risk modifications
    if result['summary']['high_risk_count'] > 0:
        logger.warning(
            f"HIGH RISK: Modifying {target} will break {result['summary']['high_risk_count']} direct dependents"
        )
    
    return result
```

### CLI Command

```python
# saw/cli/impact.py

@app.command()
def impact(
    target: str,
    direction: str = 'upstream',
    max_depth: int = 3,
    min_confidence: float = 0.8,
    output_format: str = 'text'
):
    """
    Analyze code modification impact.
    
    Examples:
        saw impact UserService
        saw impact handleLogin --direction downstream
        saw impact AuthModule --max-depth 5 --min-confidence 0.9
    """
    result = asyncio.run(analyze_impact(...))
    
    if output_format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print_impact_report(result)
```

## Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | 用户可查询任意符号的上下游依赖 | CLI 测试 |
| 2 | 结果按深度分层并标注风险 | 单元测试 |
| 3 | 每条边显示置信度分数 | 输出验证 |
| 4 | 支持关系类型过滤 | 单元测试 |
| 5 | 提供 MCP 工具 | 集成测试 |
| 6 | 高风险修改触发警告 | 单元测试 |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| 图遍历性能（大型代码库） | Medium | High | 实现深度限制、懒加载 |
| 节点查找失败 | Low | Medium | 模糊匹配、建议列表 |
| 置信度不准确 | Low | Medium | 从 GitNexus 借鉴评分模型 |

## Dependencies

- Depends on: Phase 26 complete
- Blocks: Phase 28, Phase 29

---

*Created: 2026-05-04*
