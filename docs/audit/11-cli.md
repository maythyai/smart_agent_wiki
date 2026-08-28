# CLI 命令行 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/drivers/cli/*`
> 覆盖缺口: 12 个命令文件（freshness/review/conflicts/audit/compile/feed/plugin/tutorial/docs/mcp/web/ingest_media）未读（工具降级），完成度可能随补审变化。

## 1. 执行摘要
- 主要入口（init/ingest/query/search/status/lint/verify）功能完整可用，但 error_handler 未接线（友好错误系统失效）、lint --fix 为 stub、completion 脚本过时。
- 核心功能完成度约 **75%**。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| init/ingest/query/search/status | 完整 | commands/*_cmd.py |
| 友好错误处理 | 失效 | F-CLI-01 |
| lint --fix | stub | F-CLI-04 |
| shell 补全 | 过时 | F-CLI-05 |

## 4. Findings 列表

### F-CLI-01 — wrap_command 未接线 + 缺 import typer
- **P0** | 严重度 3 | **原则** #1/#9
- **位置**: `drivers/cli/error_handler.py` + `drivers/cli/main.py`
- **问题**: `wrap_command` 装饰器定义但从未接线到任何命令，且 error_handler.py 缺 `import typer`（若调用会 NameError），友好错误处理系统完全失效。

### F-CLI-02 — 错误信息缺 f 前缀
- **P0** | 严重度 3 | **原则** #9
- **位置**: `commands/ingest_cmd.py:57`
- **问题**: `"Wiki not initialized at {path}"` 缺 f 前缀，`{path}` 作为字面量输出给用户。

### F-CLI-03 — init 无进度反馈
- **P1** | 严重度 3 | **原则** #1
- **问题**: 密钥生成/DB 创建/迁移期间静默。

### F-CLI-04 — lint --fix 为 stub
- **P1** | 严重度 3 | **原则** #1/#9
- **问题**: `--fix` 参数定义但函数体未引用，用户以为会自动修复。

### F-CLI-05 — completion 脚本硬编码命令列表过时
- **P1** | 严重度 2 | **原则** #4
- **位置**: `drivers/cli/completion.py`
- **问题**: 缺 feed/docs/compile/plugin 等。

### F-CLI-06 — error_handler 缺"为什么"环节
- **P1** | 严重度 2 | **原则** #9
- **问题**: fallback 对所有未知异常统一建议 "Run saw --help"。

### F-CLI-07 — ingest 无进度反馈
- **P1** | 严重度 3 | **原则** #1
- **问题**: 大目录摄入时用户以为卡死。

> P2/P3：config TUI 输入校验、query LLM 静默降级、search 空结果引导、status DB 错误静默吞、init Git 失败静默、别名覆盖不全、连接泄漏、UUID 显示不可读、配置解析静默回退、错误格式不统一、ingest 缺 --dry-run。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 3 | 5 |
| 2 | 8 |
| 1 | 5 |
| 优先级 | P0×2 P1×5 P2×7 P3×4 |

## 6. 修复优先级
- **Foundation**: F-CLI-01/02
- **Core UI**: F-CLI-03/04/06/07
- **Interactions & States**: F-CLI-05 + 长耗时进度
- **Polish**: 其余

## 7. 下一步建议
- 补审 12 命令文件；接线 error_handler（复用其三段式框架）；lint --fix 实现或显式标注不可用；completion 动态生成。
