# Research / Synthesize / Purpose 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/research/*`、`src/saw/synthesize/*`、`src/saw/purpose/*`
> 覆盖缺口: 仅审 research/（4 文件）；synthesize/（6 文件）与 purpose/（3 文件）未审（工具降级）。

## 1. 执行摘要
- Research 模块搜索/摄入/综合骨架存在，但 LLM 集成（查询优化、内容综合）均为 stub，搜索错误处理为静默吞噬，综合步骤传入空数据。
- 核心功能完成度约 **35%**。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| research_engine 骨架 | 部分 | research_engine.py |
| Web 搜索 | stub/吞错 | F-RS-02 |
| LLM 查询优化 | stub | F-RS-11 |
| 内容综合 | stub | F-RS-06/11 |
| synthesize/ | 未审 | 覆盖缺口 |
| purpose/ | 未审 | 覆盖缺口 |

## 4. Findings 列表

### F-RS-02 — Web 搜索吞错
- **P0** | 严重度 3 | **原则** #1/#9
- **位置**: `research/web_search.py`
- **问题**: `except Exception as e` 捕获后变量 `e` 从未使用，静默返回空结果。

### F-RS-06 — 综合传入空来源
- **P0** | 严重度 4 | **原则** #1/#9
- **位置**: `research/research_engine.py`（`synthesize_research([], topic)`）
- **问题**: 综合页面 0 来源，来源溯源链断裂。

### F-RS-07 — 零结果仍标记 completed
- **P0** | 严重度 3 | **原则** #1/#9
- **问题**: 零结果时任务仍 `status="completed"`，`"failed"` 状态从未使用。

### F-RS-11 — llm_client 参数从不使用
- **P0** | 严重度 3 | **原则** #1/#9
- **位置**: `synthesize_research`
- **问题**: 接受 `llm_client` 参数但从不使用，仅列来源链接无实际综合。

> 其余 P0（共 7 条 P0）：含 1 条 catastrophic；P1×5、P2×5（详见代理原始结果）。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 1 |
| 3 | 6 |
| 2 | 5 |
| 1 | 5 |
| 优先级 | P0×7 P1×5 P2×5 |

## 6. 修复优先级
- **Foundation**: F-RS-02/06/07/11
- **Core UI**: LLM 集成实现或显式标注不可用
- **Interactions & States**: 进度/取消/错误反馈
- **Polish**: 其余

## 7. 下一步建议
- **补审 `synthesize/` 与 `purpose/`**；零结果必须标 failed 并提示；综合必须真正调用 LLM；搜索错误必须上抛或反馈。
