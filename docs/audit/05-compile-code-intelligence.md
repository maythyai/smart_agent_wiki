# Compile 与代码智能 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/engines/compile/*`、`src/saw/analysis/*`、`src/saw/code_graph/*`、`src/saw/api/routes/impact.py`、`drivers/mcp/tools/{code_graph,impact}.py`
> 覆盖说明: 审查 23 文件（engines/compile 7、analysis 4、code_graph 16、impact 路由、MCP 工具 2）。

## 1. 执行摘要
- code_graph 引擎（build/postprocess/impact/flows/communities/context）实现扎实，但存在两套并行 impact 实现（API 调 stub、MCP 调完整），DAG 循环检测缺失，编译产出状态反馈不充分。
- 核心功能完成度约 **75%**。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| code_graph 引擎 | 完整 | code_graph/engine.py |
| impact 分析（API 路径） | stub | F-COMP-01 |
| impact 分析（MCP 路径） | 完整 | code_graph/engine.py |
| DAG 循环检测 | 缺失 | F-COMP-02 |
| 编译产出状态反馈 | 不足 | F-COMP-03 |

## 4. Findings 列表

### F-COMP-01 — 两套并行 impact 实现
- **P0** | 严重度 4 | 置信度 high | **原则** #4/#1
- **位置**: `analysis/impact.py`（stub：`_get_node`/`_get_edges` 标注 placeholder）vs `code_graph/engine.py`（完整 `impact_analysis`）
- **问题**: API 路由调用 stub 版本，MCP 调用完整版本，用户在两条路径得到完全不同结果。
- **修复**: 统一为 code_graph 实现，删除 analysis/impact.py stub。

### F-COMP-02 — DAG 循环检测缺失
- **P0** | 严重度 4 | 置信度 high | **原则** #1
- **位置**: `analysis/impact.py` + `analysis/process.py`
- **问题**: BFS/DFS 用 `visited` 防重但遇循环边静默跳过；`process.py` 的 `include_loops` 仅追加 `"(loop)"` 子节点，不报告循环路径。
- **后果**: 循环依赖被静默忽略。

### F-COMP-03 — 编译产出状态反馈不充分
- **P1** | 严重度 3 | **原则** #1
- **位置**: `engines/compile/compiler.py`
- **问题**: LLM 合成失败仅 `logging.warning` 静默降级；`_cascade_update` 为空 `pass`；`CompileResult` 不记录降级页面。

### F-COMP-04 — 风险分级标签是裸字符串
- **P1** | 严重度 3 | **原则** #2/#6
- **问题**: `WILL_BREAK` 等在返回 JSON 中是裸字符串无说明，用户可能误解为"必定编译错误"。

### F-COMP-06 — code_wiki status() bug
- **P1** | 严重度 3 | **原则** #1
- **位置**: `engines/compile/code_wiki.py`（`status()` 方法）
- **问题**: `.status` 文件存了真实时间戳，但代码 `status.last_generated = utcnow()` 硬编码为当前时间而非读文件。

> 其余 P2/P3：concept_graph 可视化、archiver 反馈、linter 输出、parsers 错误等（6 条 P2、1 条 P3）。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 2 |
| 3 | 4 |
| 2 | 6 |
| 1 | 1 |
（注：编号 5/7-14 为 P2/P3 细项）
| 优先级 | P0×2 P1×5 P2×6 P3×1 |

## 6. 修复优先级
- **Foundation**: F-COMP-01/02
- **Core UI**: F-COMP-03/04/06
- **Interactions & States**: concept_graph/archiver/linter
- **Polish**: parsers 细项

## 7. 下一步建议
- 统一 impact 实现；实现循环检测并报告路径；编译降级需对用户可见。
