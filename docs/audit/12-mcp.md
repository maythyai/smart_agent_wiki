# MCP Server 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/drivers/mcp/*`
> 覆盖缺口: `tools/` 下 16 个工具文件未逐一审查（工具降级），仅审 server/config/prompts/resources/research_on_miss/__init__。完成度可能随补审变化。

## 1. 执行摘要
- 9/16 工具被注册，其中 learn/collaborate 引擎未接线、govern 缺 blast_radius/audit、research_on_miss 为桩实现。错误处理多处 `pass` 吞错。
- 核心功能完成度约 **45%**。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| FastMCP server + 9 工具注册 | 部分 | server.py + tools/__init__ |
| learn/collaborate 引擎 | 未接线 | F-MCP-04 |
| govern blast_radius/audit | 缺失 | F-MCP-05 |
| research_on_miss | stub | F-MCP-03 |
| 错误返回格式 | 部分 | F-MCP-08 |

## 4. Findings 列表

### F-MCP-01 — 7/16 工具文件未导入注册
- **P0** | 严重度 3 | **原则** #1
- **位置**: `drivers/mcp/tools/__init__.py` / `server.py`
- **问题**: 7 个工具文件未在注册表导入，一半 MCP 工具不可用。

### F-MCP-02 — 引擎初始化失败静默吞没
- **P0** | 严重度 3 | **原则** #1
- **问题**: try/except 吞掉异常，工具后续调用返回空/None。

### F-MCP-03 — research_on_miss 搜索全为桩
- **P0** | 严重度 3 | **原则** #1/#9
- **位置**: `drivers/mcp/research_on_miss.py`
- **问题**: 缺失研究补审不工作。

### F-MCP-04 — _learn_engine 永远 None
- **P0** | 严重度 3 | **原则** #1
- **问题**: 学习类工具不可用。

### F-MCP-05 — blast_radius/audit 硬编码 None
- **P1** | 严重度 2 | **原则** #1
- **问题**: govern 工具缺 blast_radius/audit。

### F-MCP-06 — 资源返回空值无降级说明
- **P1** | 严重度 2 | **原则** #9

### F-MCP-07 — ingestion 异常 pass 吞没
- **P1** | 严重度 3 | **原则** #1/#9

### F-MCP-08 — 错误信息暴露技术堆栈
- **P1** | 严重度 3 | **原则** #2/#9

> P2/P3：无进度反馈、prompt 无输入校验、depth 静默降级、daily_review 非时间排序、search_resource 未用 FTS5、内容截断无标记、transport 无枚举校验、私有 API 访问、coverage_after 伪造公式、register_all_tools 不支持重注册。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 3 | 6 |
| 2 | 7 |
| 1 | 4 |
| 优先级 | P0×4 P1×4 P2×5 P3×4 |

## 6. 修复优先级
- **Foundation**: F-MCP-01/02/03/04
- **Core UI**: F-MCP-05/06/07/08
- **Interactions & States**: 进度反馈、输入校验
- **Polish**: 其余

## 7. 下一步建议
- **补审 `tools/` 16 个文件**（输入校验、错误返回格式、schema 清晰度、命名一致性）；注册全部工具；接线 learn/collaborate 引擎；错误对 LLM/用户可懂。
