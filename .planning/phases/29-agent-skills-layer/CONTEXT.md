# Phase 29: Agent Skills Layer — CONTEXT.md

**Phase:** 29
**Milestone:** v3.4 Code Intelligence
**Status:** Planning
**Created:** 2026-05-04

## Problem Statement

Smart Agent Wiki 有 MCP 工具，但用户不知道如何有效使用它们。

**问题：**
1. 用户不了解 MCP 工具的能力和限制
2. 缺乏工具使用指南和最佳实践
3. 没有上下文感知的工具推荐
4. 需要手动查阅文档才能知道如何调用工具

**Claude Code Skills 设计：**
Claude Code 的 Skills 系统提供了：
- 上下文感知的工具调用指导
- 自动化的最佳实践检查
- 工作流集成
- 智能提示

## Goal

实现 Agent Skills Layer：
1. MCP 工具使用指南 Skills
2. 上下文感知的工具推荐
3. 自动化的最佳实践检查
4. 工作流集成

## Scope

### In Scope

- MCP 工具 Skills 定义
- 工具推荐引擎
- 最佳实践检查
- 工作流集成

### Out of Scope

- 动态工具生成
- 外部 Skills 集成
- 多语言支持

## Technical Design

### Skills Structure

```yaml
# .claude/skills/saw-tools.md
name: saw-tools
description: Smart Agent Wiki MCP tools guide
triggers:
  - "saw"
  - "impact analysis"
  - "knowledge graph"
  - "ingest"

guidelines:
  impact_analysis:
    - "Use saw_impact BEFORE modifying code"
    - "Check high_risk_count for dangerous changes"
    - "Include tests for depth > 1 changes"

  knowledge_graph:
    - "Use graph queries for dependency analysis"
    - "Check staleness before using cached data"

  ingest:
    - "Run full pipeline for new sources"
    - "Check validation errors before storing"

recommendations:
  before_code_change:
    - saw_impact
    - saw_staleness

  after_code_change:
    - saw_ingest
```

## Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Skills 自动触发工具推荐 | 功能测试 |
| 2 | 最佳实践检查工作 | 单元测试 |
| 3 | 工作流集成正常 | 集成测试 |
| 4 | 用户文档完整 | 文档审核 |

## Dependencies

- Depends on: Phase 28 complete
- Blocks: Phase 30

---

*Created: 2026-05-04*