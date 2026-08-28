# Ingest 摄入与解析 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/engines/ingest/*`、`src/saw/ingest/pipeline/*`、`src/saw/adapters/parsers/*`
> 覆盖说明: 审查了 24 个关键文件；`ingest/pipeline/phases/{validate,store}.py`、`adapters/parsers/*` 因工具降级未读，行为已由调用方代码推断。

## 1. 执行摘要
- 摄入流水线五格式（Markdown/PDF/URL/Code/Media）主路径完整且有离线降级，但 JSON/TABLE 路由断裂、Fuser 矛盾检测为 stub、批量失败计数有 bug、无进度/取消/重试机制、存在两套未统一的流水线实现。
- 核心功能完成度约 **65%**。

## 2. 审查范围
| 路径 | 职责 |
|---|---|
| engines/ingest/pipeline.py | 摄入主编排 |
| engines/ingest/classifier.py | 格式分类 |
| engines/ingest/{fuser,batch,scheduler,preview,feed_manager,validator}.py | 合并/批/调度/预览/订阅/校验 |
| engines/ingest/extractors/{markdown,pdf,url,code_ast,media,llm_extract}.py | 内容抽取 |
| ingest/pipeline/{runner,types,validator,errors}.py + phases/{classify,parse,extract,merge}.py | DAG 流水线第二套实现 |

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| 五格式抽取 | 完整 | extractors/*.py |
| JSON/TABLE 路由 | 缺失 | F-INGEST-03 |
| 矛盾检测 | stub | fuser.py:50-59 |
| 批量失败计数 | bug | batch.py:216 |
| 进度/取消/重试 | 缺失 | F-INGEST-01/10 |
| 流水线统一 | 部分 | 两套实现 F-INGEST-09 |

## 4. Findings 列表

### F-INGEST-01 — 摄入无进度反馈/取消
- **优先级** P0 | **严重度** 4 | **置信度** high | **违反原则** #1
- **位置**: `engines/ingest/pipeline.py:96-236`
- **问题**: `ingest()` 全程无进度/取消机制，大目录摄入时用户无任何反馈。
- **后果**: 用户摄入大目录时以为卡死，无法判断是否在运行或已失败。
- **修复**: 接入进度回调 + WebSocket 进度事件 + 取消标志。

### F-INGEST-02 — 错误全为裸技术字符串
- **优先级** P0 | **严重度** 4 | **置信度** high | **原则** #9
- **位置**: `pipeline.py:114,164,174,189,219`
- **问题**: 错误信息为裸技术字符串，无"发生了什么+为什么+怎么办"三段式，无恢复路径。
- **后果**: 用户无法理解摄入失败原因，也不知道如何修复。
- **修复**: 统一走 CLI error_handler 三段式封装。

### F-INGEST-03 — JSON/TABLE 分类后无 extractor
- **优先级** P0 | **严重度** 3 | **置信度** high | **原则** #5
- **位置**: `classifier.py:103-114` + `pipeline.py:163-171`
- **问题**: classifier 能产出 JSON/TABLE 分类，但无对应 extractor，必然报错。
- **后果**: 这些格式的文件摄入必然失败且错误不友好。

### F-INGEST-04 — 批量失败计数恒为 0
- **优先级** P1 | **严重度** 3 | **原则** #1
- **位置**: `batch.py:216`
- **问题**: `results.count(lambda)` 用法错误，永远返回 0，失败计数偏低。
- **后果**: 批量摄入报告显示 0 失败，掩盖真实失败。

### F-INGEST-05 — 调度重试逻辑反转
- **优先级** P1 | **严重度** 3 | **原则** #1
- **位置**: `scheduler.py:209-214`
- **问题**: 失败重置条件逻辑反转，指数退避失效。

### F-INGEST-06 — naive/aware datetime 混用
- **优先级** P1 | **严重度** 2 | **原则** #4
- **位置**: `scheduler.py:193`

### F-INGEST-07 — 矛盾检测为 stub
- **优先级** P1 | **严重度** 3 | **原则** #1
- **位置**: `fuser.py:50-59`
- **问题**: contradictions 恒为空。

### F-INGEST-08 — 预览用 :memory: DB
- **优先级** P1 | **严重度** 2 | **原则** #1
- **位置**: `preview.py:67`
- **问题**: 默认内存 DB，重启丢失所有预览。

### F-INGEST-09 — 两套并行流水线实现
- **优先级** P1 | **严重度** 2 | **原则** #4
- **位置**: `pipeline.py` vs `ingest/pipeline/`
- **问题**: 后者多处 placeholder，入口分歧。

### F-INGEST-10 — 无重试机制
- **优先级** P1 | **严重度** 2 | **原则** #3
- **位置**: `pipeline.py:173-181,218-226`
- **问题**: 瞬时错误需手动重新提交。

### F-INGEST-11 — vault_uuid 存为 placeholder
- **优先级** P1 | **严重度** 2 | **原则** #9
- **位置**: `feed_manager.py:355-360`

### F-INGEST-12 — 目录路径传文件级 extractor
- **优先级** P2 | **严重度** 2 | **原则** #5
- **位置**: `classifier.py:132-142`

### F-INGEST-13 — 错误暴露 UUID/字段名
- **优先级** P2 | **严重度** 2 | **原则** #2
- **位置**: `validator.py:41,47,53`

### F-INGEST-14 — 异常结果 file_path="unknown"
- **优先级** P2 | **严重度** 2 | **原则** #1
- **位置**: `batch.py:200-202`

### F-INGEST-15 — 离线模式静默截断段落
- **优先级** P2 | **严重度** 1 | **原则** #8
- **位置**: `markdown.py:82`, `pdf.py:72`, `url.py:66`

### F-INGEST-16 — naive datetime 与规范不一致
- **优先级** P3 | **严重度** 1 | **原则** #4
- **位置**: `types.py:20-21`

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 2 |
| 3 | 4 |
| 2 | 7 |
| 1 | 3 |
| 优先级 | P0×3 P1×8 P2×4 P3×1 |

## 6. 修复优先级（四层）
- **Foundation**: F-INGEST-01/02/03
- **Core UI**: F-INGEST-04/05/07/09
- **Interactions & States**: F-INGEST-08/10/11/13/14
- **Polish**: F-INGEST-06/12/15/16

## 7. 下一步建议
- 补审 `phases/{validate,store}.py` 与 `parsers/*`。
- 统一为单一流水线实现；接入进度/取消/重试；stub 治理（fuser 矛盾检测）。
