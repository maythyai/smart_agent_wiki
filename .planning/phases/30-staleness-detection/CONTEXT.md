# Phase 30: Staleness Detection — CONTEXT.md

**Phase:** 30
**Milestone:** v3.4 Code Intelligence
**Status:** Planning
**Created:** 2026-05-04

## Problem Statement

Smart Agent Wiki 的知识图谱可能过时，用户不知道数据是否可信。

**问题：**
1. 代码修改后知识图谱未更新
2. 用户使用过时的依赖信息
3. 缺乏自动化的过期检测
4. 无法判断数据的时效性

**GitNexus 的设计：**
GitNexus 的 staleness 检测：
```python
staleness({threshold: 7 days})

STALE NODES:
  UserService (last_indexed: 15 days ago, commits_behind: 12)
  handleLogin (last_indexed: 8 days ago, commits_behind: 5)

  Recommendation: Run ingest to update 23 stale nodes
```

## Goal

实现 Staleness Detection：
1. 比较 last_indexed_commit 与 HEAD
2. 计算 commits_behind
3. 识别过期节点
4. MCP 工具 `saw_staleness()`

## Scope

### In Scope

- Git commit 比较算法
- 过期节点识别
- 更新建议生成
- MCP 工具实现

### Out of Scope

- 自动更新触发
- 外部系统集成
- 实时监控

## Technical Design

### Staleness Detection Algorithm

```python
async def detect_staleness(
    graph: KnowledgeGraph,
    threshold_days: int = 7,
    min_commits_behind: int = 1
) -> StalenessResult:
    """
    Detect stale nodes in knowledge graph.

    Algorithm:
    1. Get HEAD commit
    2. For each indexed node:
       - Get last_indexed_commit
       - Calculate commits_behind
       - Check if exceeds threshold
    3. Group stale nodes by severity
    4. Return structured result
    """
    head_commit = get_head_commit()

    stale_nodes = []
    for node in graph.get_all_nodes():
        indexed_commit = node.get('last_indexed_commit')
        indexed_date = node.get('last_indexed_date')

        if indexed_commit and indexed_commit != head_commit:
            commits_behind = count_commits_between(indexed_commit, head_commit)
            days_old = days_since(indexed_date)

            if days_old > threshold_days or commits_behind >= min_commits_behind:
                stale_nodes.append(StaleNode(
                    uid=node['uid'],
                    name=node['name'],
                    days_old=days_old,
                    commits_behind=commits_behind,
                    severity=get_staleness_severity(days_old)
                ))

    return StalenessResult(
        total_stale=len(stale_nodes),
        nodes=stale_nodes,
        recommendation=generate_update_recommendation(stale_nodes)
    )
```

## Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | 正确检测过期节点 | 单元测试 |
| 2 | commits_behind 计算准确 | 单元测试 |
| 3 | severity 分级正确 | 单元测试 |
| 4 | 提供 MCP 工具 | 集成测试 |

## Dependencies

- Depends on: Phase 29 complete
- Blocks: None (final phase)

---

*Created: 2026-05-04*