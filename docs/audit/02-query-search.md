# Query 查询与搜索 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/engines/query/*`、`drivers/web/routes/{search,pages,graph}.py`、`web/src/pages/{Search,Pages,Graph}.tsx`、`web/src/components/{search,graph}/*`

## 1. 执行摘要
- FTS5+BM25 搜索基座完整，但分页断裂、type/tag 过滤静默失效、NL 查询无降级、Tree Mode 是 stub、查询缓存未接线、搜索/图谱组件无暗色模式。搜索核心路径基本不可用。
- 核心功能完成度约 **55%**。

## 2. 审查范围
| 路径 | 职责 |
|---|---|
| engines/query/{engine,search,compiler,graph_traverse,compare,tree_mode,wiki_graph,wiki_links,related_pages,wiki_indexer,cache,memory}.py | 查询编排/搜索/编译/图谱/对比/树/缓存/记忆 |
| drivers/web/routes/{search,pages,graph}.py | API 路由 |
| web/src/pages/{Search,Pages,Graph}.tsx + components/{search,graph} | 前端 |

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| FTS5+BM25 搜索 | 完整 | search.py |
| 分页 | 断裂 | F-QS-01 |
| type/tag 过滤 | 失效 | F-QS-02 |
| NL 查询降级 | 缺失 | F-QS-03 |
| Tree Mode | stub | F-QS-08 |
| 查询缓存 | 未接线 | F-QS-07 |

## 4. Findings 列表

### F-QS-01 — 搜索分页从根本上断裂
- **P0** | 严重度 4 | 置信度 high | **原则** #1
- **位置**: `engines/query/engine.py:169`
- **问题**: 硬编码 `limit=20`，路由在 20 条结果中做内存切片，第 3 页起返回空。FTS5Search 已支持 offset/limit 但引擎未透传。
- **后果**: 翻页到第 3 页返回空，用户以为没有更多结果。

### F-QS-02 — type/tag 过滤器静默失效
- **P0** | 严重度 4 | 置信度 high | **原则** #1
- **位置**: `engines/query/search.py:70-78` + `engine.py:197-220`
- **问题**: 过滤器检查 `source.get("type")`，但 sources dict 不含 type/tags 字段，过滤器永远不匹配。
- **后果**: 用户按类型/标签过滤得到空结果，无任何提示。

### F-QS-03 — NL 查询无降级
- **P0** | 严重度 4 | 置信度 high | **原则** #1/#9
- **位置**: `engines/query/engine.py:124`
- **问题**: `self._llm.answer_query()` 无 try/catch，LLM 临时不可用时直接 500，未回退到关键词搜索。
- **后果**: LLM 抖动时查询直接崩溃而非降级。

### F-QS-04 — 命令面板 ↑↓ 导航未实现
- **P1** | 严重度 3 | **原则** #7
- **位置**: `web/src/components/search/CommandPalette.tsx`
- **问题**: 页脚提示快捷键但无事件监听，键盘用户无法使用。

### F-QS-05 — 图谱布局三状态源脱节
- **P1** | 严重度 3 | **原则** #4
- **位置**: `web/src/pages/Graph.tsx` + `graphStore` + `KnowledgeGraph viewMode`
- **问题**: 三个状态互不同步，两个 layout 选择器对渲染无效果。

### F-QS-06 — slug 推导不一致
- **P1** | 严重度 3 | **原则** #4
- **位置**: 前端 `replace(/\s+/g,'-')` vs 后端 `slugify()`
- **问题**: 含特殊字符的标题导航 404。

### F-QS-07 — QueryCache 死代码
- **P1** | 严重度 2 | **原则** #1
- **位置**: `engines/query/cache.py`
- **问题**: 完整实现但从未被任何搜索/查询路径调用。

### F-QS-08 — Tree Mode 是 stub
- **P1** | 严重度 3 | **原则** #1
- **位置**: `engines/query/tree_mode.py:123-131`
- **问题**: 构建扁平结构而非标题层级树，注释自承"Real implementation would use heading level"。

### F-QS-09 — 搜索/图谱组件无暗色模式
- **P1** | 严重度 2 | **原则** #4
- **位置**: 6 个 search/graph 组件文件无 `dark:` 变体。

> 其余 P2/P3：search_with_snippets 死代码、空结果无引导、图谱缩放/选中无返回等。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 3 |
| 3 | 5 |
| 2 | 7 |
| 1 | 2+ |
| 优先级 | P0×3 P1×6 P2×7 P3×2 |

## 6. 修复优先级
- **Foundation**: F-QS-01/02/03
- **Core UI**: F-QS-04/05/06/08
- **Interactions & States**: F-QS-07/09 + 四态补齐 + 暗色模式
- **Polish**: 死代码清理、空结果引导

## 7. 下一步建议
- 优先修搜索分页与过滤（核心路径）；Tree Mode 要么实现要么显式标注 stub；接入 QueryCache。
