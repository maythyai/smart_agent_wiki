# Web API 与前端 UI 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/drivers/web/*`、`src/saw/api/{feeds,dashboard_stats,graphql,bulk,health}.py`、`web/src/*`
> 覆盖缺口: 前端 pages 组件、stores、部分 API 文件未读（工具降级），需补审。本报告基于已读 22 文件。

## 1. 执行摘要
- 已审查端点完成度约 75%（CRUD/搜索/图谱/导入/模板/时间线/认证/WebSocket 均接线），但缺路由守卫、token 刷新、面包屑、连接状态 UI、网页模式快捷键，且分页先切片后过滤致搜索空结果。
- 最关键 4 条 P0。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| 页面 CRUD/搜索/图谱 | 完整 | routes/* |
| WebSocket 广播 | 完整 | websocket.py |
| 错误处理（RFC7807） | 部分 | F-WEB-05/06/09 |
| 路由守卫 | 缺失 | F-WEB-04 |
| token 自动刷新 | 缺失 | F-WEB-03 |
| 列表分页+过滤 | bug | F-WEB-01 |

## 4. Findings 列表

### F-WEB-01 — 列表先分页切片再过滤
- **P0** | 严重度 4 | 置信度 high | **原则** #1/#6
- **位置**: `drivers/web/routes/pages.py:52-100`
- **问题**: 列表端点在应用搜索过滤前对结果分页切片，导致当前窗口外的匹配不可见。搜索现有关键词可能返回空结果。

### F-WEB-02 — WebSocket 无限重连无 UI
- **P0** | 严重度 3 | **原则** #1
- **位置**: `web/src/hooks/useWebSocket.ts:138-148`
- **问题**: 断开时无限重连无最大重试，`onerror` 仅 console；App.tsx 无连接状态指示器。

### F-WEB-03 — 401 硬跳转无刷新，丢表单
- **P0** | 严重度 3 | **原则** #1/#3
- **位置**: `web/src/lib/api.ts:55-58`
- **问题**: 401 直接 `window.location.href='/login'`，无 token 刷新，编辑表单数据静默丢失。

### F-WEB-04 — 无路由守卫
- **P0** | 严重度 3 | **原则** #1
- **位置**: `web/src/routes/router.tsx:1-45`
- **问题**: 未认证用户可访问所有功能页，在 API 401 重定向前先看到空白/错误闪烁。

### F-WEB-05 — 异常类名作 RFC7807 title
- **P1** | 严重度 2 | **原则** #2/#9
- **位置**: `drivers/web/middleware/errors.py:67`
- **问题**: `StorageError`/`WriteQueueError` 作为 title 暴露，非用户语言。

### F-WEB-06 — str(e) 拼进 500
- **P1** | 严重度 3 | **原则** #2/#9
- **位置**: `drivers/web/routes/import_md.py:159`
- **问题**: `str(e)` 直接拼入 500 响应，泄露内部错误。

### F-WEB-07 — 快捷键仅 Tauri 有效
- **P1** | 严重度 2 | **原则** #7
- **位置**: `web/src/hooks/useShortcuts.ts:37-40`
- **问题**: 网页模式 Cmd+S/Cmd+O 等无效。

### F-WEB-08 — 缺面包屑导航
- **P1** | 严重度 2 | **原则** #6
- **位置**: `web/src/App.tsx`
- **问题**: 用户在页面层级中失去上下文。

### F-WEB-09 — ApiError 不解析 RFC7807
- **P1** | 严重度 2 | **原则** #9
- **位置**: `web/src/lib/api.ts:60-66`
- **问题**: 组件显示原始 HTTP 状态文本。

### F-WEB-10 — DELETE 无存在性检查/反链警告
- **P1** | 严重度 3 | **原则** #3
- **位置**: `drivers/web/routes/pages.py:225-260`

> P2/P3：命令面板触发器、refetchOnWindowFocus=false、body 未清洗、移动端登出不可达、NavLink 类名重复。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 1 |
| 3 | 5 |
| 2 | 6 |
| 1 | 3 |
| 优先级 | P0×4 P1×6 P2×4 P3×1 |

## 6. 修复优先级
- **Foundation**: F-WEB-01/02/03/04
- **Core UI**: F-WEB-05/06/09
- **Interactions & States**: F-WEB-07/08/10
- **Polish**: 其余

## 7. 下一步建议
- 补审前端 pages/stores；加分页过滤顺序修复、路由守卫、token 刷新拦截器、连接状态 UI、面包屑。
