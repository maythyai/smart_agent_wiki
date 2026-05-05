# Phase 26: DAG Pipeline Validation — CONTEXT.md

**Phase:** 26
**Milestone:** v3.4 Code Intelligence
**Status:** Planning
**Created:** 2026-05-04

## Problem Statement

Smart Agent Wiki 的摄入引擎当前使用线性的 6 阶段流程：
```
分类 → 解析 → 提取 → 融合 → 验证 → 入库
```

**问题：**
1. 阶段之间没有显式依赖声明
2. 缺少运行时依赖验证
3. 阶段输出没有类型化定义
4. 循环依赖无法检测
5. 错误信息不够清晰

**GitNexus 的设计：**
GitNexus 使用 12 阶段 DAG 管线，每个阶段：
- 有显式 `deps` 声明
- 有类型化 `Output` 定义
- 运行时 Kahn 拓扑排序验证
- 循环依赖检测并报告精确路径
- `getPhaseOutput<T>(deps, 'name')` 类型安全访问

## Goal

为摄入引擎引入 DAG 架构：
1. 定义 `PipelinePhase[T]` 类型
2. 实现 DAG 验证器（Kahn 拓扑排序）
3. 迁移现有 6 阶段到 DAG 架构
4. 支持增量阶段添加

## Scope

### In Scope

- PipelinePhase 类型定义
- DAG 验证器和运行器
- 现有 6 阶段迁移
- 类型安全输出访问

### Out of Scope

- 新阶段添加（Phase 27+）
- 性能优化
- Web UI 改动

## Key Context

### Existing Pipeline (saw/ingest/pipeline.py)

```python
# 当前实现（简化）
async def run_pipeline(source: str) -> KnowledgeGraph:
    graph = KnowledgeGraph()
    
    # 阶段 1: 分类
    file_type = classify(source)
    
    # 阶段 2: 解析
    content = parse(source, file_type)
    
    # 阶段 3: 提取
    claims = extract(content)
    
    # ... 后续阶段
```

**问题：**
- 没有类型化的阶段输出
- 没有依赖验证
- 阶段顺序硬编码

### GitNexus Pipeline Reference

```typescript
// gitnexus/src/core/ingestion/pipeline-phases/types.ts
interface PipelinePhase<T> {
  name: string;
  deps: string[];
  execute(ctx: PipelineContext, deps: PhaseResults): Promise<T>;
}

// 运行时验证
function validateDag(phases: PipelinePhase[]): ValidationResult {
  // Kahn's topological sort
  // Detect cycles with exact path
  // Check for missing deps
}
```

## Technical Design

### Phase Types

```python
from typing import TypedDict, Generic, TypeVar, Awaitable

T = TypeVar('T')

class PhaseResult(TypedDict, Generic[T]):
    """阶段执行结果"""
    name: str
    output: T
    duration_ms: float

class PipelinePhase(TypedDict, Generic[T]):
    """管线阶段定义"""
    name: str
    deps: list[str]
    execute: Callable[[PipelineContext, PhaseResults], Awaitable[T]]

class PhaseResults:
    """阶段结果集合"""
    _results: dict[str, Any]
    
    def get_phase_output[T](self, name: str) -> T:
        """类型安全获取阶段输出"""
        if name not in self._results:
            raise PhaseNotFoundError(name)
        return self._results[name]['output']
```

### DAG Validator

```python
def validate_dag(phases: list[PipelinePhase]) -> ValidationResult:
    """
    Kahn's topological sort for DAG validation.
    
    Returns:
        ValidationResult with:
        - valid: bool
        - cycle_path: list[str] | None
        - missing_deps: list[tuple[str, str]]
    """
    # Build adjacency list
    # Kahn's algorithm
    # Detect cycles
    # Check for missing dependencies
```

### Pipeline Runner

```python
class PipelineRunner:
    def __init__(self, phases: list[PipelinePhase]):
        self.phases = phases
        self._validate()
    
    def _validate(self):
        result = validate_dag(self.phases)
        if not result['valid']:
            raise PipelineValidationError(result)
    
    async def run(self, ctx: PipelineContext) -> KnowledgeGraph:
        """Execute phases in topological order"""
        results = PhaseResults()
        
        for phase in self._sorted_phases:
            # Filter deps to declared only
            phase_deps = {k: v for k, v in results._results.items() 
                          if k in phase['deps']}
            
            start = time.time()
            output = await phase['execute'](ctx, phase_deps)
            duration = (time.time() - start) * 1000
            
            results._results[phase['name']] = PhaseResult(
                name=phase['name'],
                output=output,
                duration_ms=duration
            )
        
        return ctx.graph
```

### Migrated Phases

```python
# Phase 1: Classify
class ClassifyOutput(TypedDict):
    file_type: str
    metadata: dict

CLASSIFY_PHASE: PipelinePhase[ClassifyOutput] = {
    'name': 'classify',
    'deps': [],
    'execute': async_classify
}

# Phase 2: Parse
class ParseOutput(TypedDict):
    content: str
    sections: list[Section]

PARSE_PHASE: PipelinePhase[ParseOutput] = {
    'name': 'parse',
    'deps': ['classify'],
    'execute': async_parse
}

# Phase 3: Extract
class ExtractOutput(TypedDict):
    claims: list[Claim]
    entities: list[Entity]

EXTRACT_PHASE: PipelinePhase[ExtractOutput] = {
    'name': 'extract',
    'deps': ['parse'],
    'execute': async_extract
}

# Phase 4: Merge
class MergeOutput(TypedDict):
    merged_claims: list[Claim]
    conflicts: list[Conflict]

MERGE_PHASE: PipelinePhase[MergeOutput] = {
    'name': 'merge',
    'deps': ['extract'],
    'execute': async_merge
}

# Phase 5: Validate
class ValidateOutput(TypedDict):
    validated_claims: list[Claim]
    errors: list[ValidationError]

VALIDATE_PHASE: PipelinePhase[ValidateOutput] = {
    'name': 'validate',
    'deps': ['merge'],
    'execute': async_validate
}

# Phase 6: Store
class StoreOutput(TypedDict):
    stored_count: int
    vault_path: str

STORE_PHASE: PipelinePhase[StoreOutput] = {
    'name': 'store',
    'deps': ['validate'],
    'execute': async_store
}
```

## Success Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | 每个阶段有类型化输出 | 类型检查通过 |
| 2 | 运行时验证依赖完整性 | 单元测试 |
| 3 | 检测循环依赖并报告路径 | 单元测试 |
| 4 | 类型安全访问阶段输出 | 类型检查通过 |
| 5 | 清晰的管线错误信息 | 错误场景测试 |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| 现有功能回归 | Medium | High | 保持向后兼容，渐进迁移 |
| 性能开销 | Low | Low | 验证仅启动时执行 |

## Dependencies

- Depends on: v3.3 complete
- Blocks: Phase 27, 28, 30

---

*Created: 2026-05-04*
