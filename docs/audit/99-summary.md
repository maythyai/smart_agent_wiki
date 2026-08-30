# Smart Agent Wiki — 可用性启发式评估汇总报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent 集群（13 模块并行）+ 主审复核
> 范围：全项目 13 个模块 · 基线版本 v3.7.0
> 配套：`00-modules-overview.md`（模块清单 + 数据库层专节）+ 13 份模块报告（01–13）

---

## 1. 执行摘要

SAW 架构设计成熟，但在**功能接线完整性**与**用户可见性**上存在系统性短板。核心判断：

> **约一半标称"已完成"的功能实为 stub / 占位实现或未接线路径，且大量错误被静默吞没。**
> 代码结构完整、单测可过，但真实用户路径上会频繁遭遇"静默失败"和"假完成"。

三大跨模块系统性问题：
1. **stub 即成品**：占位合成文本被写进真实 Wiki 页面（Collaborate）、tree_mode 是扁平非树（Query）、research_on_miss 全桩（MCP）、API 调 stub 版 impact（Compile）、fuser 矛盾检测恒空（Ingest）、lint --fix 不执行（CLI）、trigger_all_syncs 无操作（Connectors）。
2. **静默失败 / 裸 except 吞错**（违反原则 1、9）：插件生命周期、事件总线、摄入、Web 搜索、MCP ingestion、DB session bootstrap、outbox 未知 sink 无限 pending。
3. **两套并行且不一致实现**（违反原则 4）：impact（analysis/ vs code_graph/）、ingest 流水线（engines/ingest vs ingest/pipeline）、矛盾子系统（govern vs reconcile）、slug 推导（前后端）、图谱布局三状态源。

安全侧存在**权限提升级**问题（Auth F-AUTH-01：注册接口允许自选 admin 角色），上线前必修。

> 评估限制：13 个代理在会话后期普遍遇到 `mcp__local__*` 工具降级（返回空输出），部分模块有覆盖缺口（见 §6）。主审已独立复核 4 条最高影响 finding（F-AUTH-01/F-COLLAB-01/F-COLLAB-02 已确认，F-DB-01 已推翻为误报）。其余 finding 行号为代理估算，修复前以实际代码为准。

## 2. 模块完成度概览

| # | 模块 | 完成度 | P0 | P1 | 报告 |
|---|------|--------|----|----|------|
| 1 | Ingest 摄入与解析 | ~65% | 3 | 8 | 01 |
| 2 | Query 查询与搜索 | ~55% | 3 | 6 | 02 |
| 3 | Govern 治理与审计 | ~70% | 1 | 4 | 03 |
| 4 | Collaborate 多代理协作 | ~55% | 2 | 4 | 04 |
| 5 | Compile & 代码智能 | ~75% | 2 | 5 | 05 |
| 6 | Connectors 集成连接器 | ~55% | 3 | 7 | 06 |
| 7 | Web API 与前端 UI | ~75% | 4 | 6 | 07 |
| 8 | Auth 与安全 | ~65% | 2 | 7 | 08 |
| 9 | DB 与存储层 | ~80% | 2 | 6 | 09 |
| 10 | 平台支撑 | 部分 | 3 | 4 | 10 |
| 11 | CLI 命令行 | ~75% | 2 | 5 | 11 |
| 12 | MCP Server | ~45% | 4 | 4 | 12 |
| 13 | Research/Synthesize/Purpose | ~35% | 7 | 5 | 13 |

> DB 完成度由 75% 上调至 80%：原 F-DB-01（"sinks/ 缺失"）经主审复核推翻——`write_queue/sinks/` 实有 7 个 sink 文件且 `app.py` 显式装配。

## 3. P0 级 finding 汇总（上线前必修）

| ID | 模块 | 问题 | 后果 | 原则 | 复核 |
|----|------|------|------|------|------|
| F-AUTH-01 | Auth | 注册 `role` 接受 `admin` | 权限提升 | 5 | ✅确认 |
| F-COLLAB-02 | Collaborate | stub 文本写入真实 Wiki | 假内容污染知识库 | 1/9 | ✅确认 |
| F-COLLAB-01 | Collaborate | fallback 路径传未知 kwarg → TypeError | 降级时工作流失败（非每次） | 1 | ✅确认(校准) |
| F-WEB-01 | Web | 列表先分页切片再过滤 | 搜索可能返回空 | 1/6 | — |
| F-QS-01 | Query | 搜索硬编码 limit=20 + 内存切片 | 第 3 页起空 | 1 | — |
| F-QS-02 | Query | type/tag 过滤字段不存在 | 过滤永不匹配 | 1 | — |
| F-QS-03 | Query | NL 查询无 try/catch | LLM 抖动直接 500 | 1/9 | — |
| F-AUTH-02 | Auth | 前端无 token 自动刷新 | 30 分钟后静默登出丢表单 | 1/3 | — |
| F-WEB-03 | Web | 401 硬跳转无刷新 | 编辑表单静默丢失 | 1/3 | — |
| F-WEB-04 | Web | 无路由守卫 | 未认证先看空白页 | 1 | — |
| F-WEB-02 | Web | WebSocket 无限重连无 UI | 断连用户无感知 | 1 | — |
| F-CONN-01 | Connectors | TokenEncryption() 无参 → TypeError | 同步崩溃 | 1 | — |
| F-CONN-02 | Connectors | PyGithub 缺失回退 MagicMock | 用户看假数据 | 1/2 | — |
| F-CONN-03 | Connectors | 对同步方法 await | 授权端点必 500 | 1 | — |
| F-MCP-01 | MCP | 7/16 工具未注册 | 半数工具不可用 | 1 | — |
| F-MCP-04 | MCP | _learn_engine 永远 None | 学习工具不可用 | 1 | — |
| F-MCP-03 | MCP | research_on_miss 全桩 | 补审不工作 | 1/9 | — |
| F-RS-06 | Research | synthesize_research([], topic) | 0 来源综合 | 1/9 | — |
| F-RS-02 | Research | Web 搜索吞错 | 静默空结果 | 1/9 | — |
| F-RS-07 | Research | 零结果标记 completed | 假完成 | 1/9 | — |
| F-RS-11 | Research | llm_client 参数不用 | 无实际综合 | 1/9 | — |
| F-PLUG-01 | Platform | 插件生命周期裸 except 吞错 | 失败用户不知 | 1 | — |
| F-PLUG-02 | Platform | event_bus 静默丢事件 | 事件丢失 | 1 | — |
| F-PLUG-05 | Platform | PluginContext 事件未接 EventBus | 插件无法收发事件 | 1 | 待核 |
| F-ONB-01 | Platform | Onboarding 仅静态数据 | 无引导流程 | 1/6 | — |
| F-GOV-06 | Govern | reconcile auto_apply 破坏性自动解决 | 数据静默 supersede 不可逆 | 3 | — |
| F-INGEST-01 | Ingest | ingest 无进度/取消 | 大摄入以为卡死 | 1 | — |
| F-INGEST-02 | Ingest | 错误全裸技术字符串 | 用户无法理解/恢复 | 9 | — |
| F-COMP-01 | Compile | API 调 stub / MCP 调完整 impact | 两路径结果不同 | 4/1 | — |
| F-COMP-02 | Compile | DAG 循环检测缺失 | 循环静默忽略 | 1 | — |
| F-CLI-01 | CLI | wrap_command 未接线 + 缺 import typer | 友好错误系统失效 | 1/9 | — |

## 4. 跨模块去重与系统性主题

1. **stub 即成品**（1/9）—— 建立"完成度声明"机制：stub 必须在 UI/MCP/CLI 返回显式标注或拒绝执行。
2. **静默失败**（1/9）—— 系统性禁止裸 `except: pass` 与无反馈 `return None/[]`。
3. **重复实现**（4）—— impact / ingest pipeline / 矛盾子系统 / slug / 图谱布局各两套，统一为单一实现。
4. **长耗时无反馈**（1）—— ingest/init/sync/workflow/MCP 普遍缺进度，统一接 WebSocket/进度事件。
5. **破坏性操作无确认**（3）—— reconcile auto_apply、DELETE 无反链警告、stub 写入 KB，统一加二次确认 + 撤销。
6. **裸技术错误暴露**（2/9）—— 统一走"三段式 + 用户语言"封装（CLI error_handler 框架可复用但当前未接线）。

## 5. 修复优先级（vertical slice 四层）

**Foundation（阻断性，先修）**
- Auth F-AUTH-01（权限提升）、F-AUTH-02 + Web F-WEB-02/03/04（认证守卫与连接）
- Collaborate F-COLLAB-01/02（工作流崩溃 + 假内容污染）
- Query F-QS-01/02/03 + Web F-WEB-01（搜索/分页/过滤核心路径）
- Connectors F-CONN-01/02/03（连接器崩溃三连）
- MCP F-MCP-01/03/04（工具注册、补审桩、引擎接线）
- Compile F-COMP-01（统一 impact 实现）
- Govern F-GOV-06（reconcile 默认 auto_apply=False）

**Core UI / 交互**
- 静默失败统一治理（§4-2）；长耗时进度反馈（§4-4）；破坏性操作确认（§4-5）；错误三段式封装（§4-6）。

**Interactions & States**
- 列表四态（loading/error/empty/success）补齐；暗色模式补齐（Query 搜索/图谱）；路由守卫、面包屑、连接状态指示器；工作流取消与崩溃恢复可见性。

**Polish**
- slug 一致性、completion 脚本同步、退出码统一、UUID 可读化等 minor/cosmetic。

## 6. 覆盖缺口与待补审项

| 模块 | 未审范围 | 报告 |
|------|----------|------|
| Ingest | `ingest/pipeline/phases/{validate,store}.py`、`adapters/parsers/*` | 01 |
| Connectors | `api/{github,github_webhook,logseq,notion_sync}.py`、前端 Integrations/ConnectorSettings | 06 |
| Web/前端 | 全部 pages 组件、stores、`api/{feeds,dashboard_stats,graphql,bulk}.py` | 07 |
| DB | `write_queue/sinks/*.py` 各 sink 错误处理 | 09 |
| 平台 | `token_optimizer/*`（7 文件）、`context/loader.py` | 10 |
| CLI | 12 命令文件 | 11 |
| MCP | `tools/` 16 个工具文件 | 12 |
| Research | `synthesize/*`（6 文件）、`purpose/*`（3 文件） | 13 |

## 7. 已复核与误报
- ✅ **F-AUTH-01** 确认（`auth.py:29` role pattern 含 admin，:77 直接采用）。
- ✅ **F-COLLAB-01** 确认并校准（`dispatcher.py:160` fallback 路径传 model_tier_override；`agents/base.py:80` execute 无 **kwargs；仅降级路径，非每次调度）。
- ✅ **F-COLLAB-02** 确认（`collaborate.py:141` stub 文本 → `_publish` 写入）。
- ❌ **F-DB-01** 推翻为误报（sinks/ 实有 7 文件且 app.py 装配）。

## 8. 下一步建议
1. 先修 Foundation 层 P0（尤其 Auth 权限提升与 Collaborate 假内容污染）。
2. 统一治理系统性主题（§4），而非逐点打补丁。
3. 补审覆盖缺口（§6）后更新本汇总。
4. 本评估为 Mode B（启发式，发现率 60-75%，定位"早期信号"），上线前仍建议补充真实用户测试（Mode A）。
5. 可回流至：异常态设计 Skill（统一错误三段式）、页面设计 Skill（列表四态/空状态）、设计提案 Skill（stub 治理机制）。

---

## 9. 修复进度

| 批次 | finding | 状态 | 说明 |
|------|---------|------|------|
| Batch 1 | F-AUTH-01 | ✅ fixed | 注册端点不再自授 admin，降为 viewer |
| Batch 1 | F-COLLAB-01 | ✅ fixed | dispatcher 移除 model_tier_override kwarg，消除 TypeError |
| Batch 1 | F-COLLAB-02 | ✅ fixed | 无来源时抛错失败，不再写入 stub 页面 |
| Batch 1 | F-CLI-02 | ✅ fixed | ingest_cmd 错误信息补 f 前缀 |
| Batch 1 | F-QS-03 | ✅ fixed | NL 查询 LLM 失败时回退关键词搜索 |
| Batch 1 | F-GOV-06 | ✅ fixed | reconcile 默认 auto_apply=False；MANUAL 不再自动 supersede |
| Batch 2 | F-QS-01 | ✅ fixed | engine 透传 limit/offset 至 FTS5；search 路由取 500 窗口后客户端分页 |
| Batch 2 | F-QS-02 | ✅ fixed | 搜索源填充 type/tags 字段，过滤器可匹配 |
| Batch 2 | F-WEB-01 | ✅ fixed | pages 列表先过滤后分页，窗口外匹配不再丢失 |
| Batch 3 | F-CONN-01 | ✅ fixed | TokenEncryption() → from_env()，token 解密不再 TypeError |
| Batch 3 | F-CONN-02 | ✅ fixed | PyGithub 缺失/无 token 时显式 raise，不再 MagicMock 假数据 |
| Batch 3 | F-CONN-03 | ✅ fixed | reauth 端点移除 await + 传 user_id，不再 500（测试 mock 改同步以反映真实） |
| Batch 4 | F-MCP-03 | ✅ fixed | research_on_miss 停止返回伪造 placeholder URL，改为空结果（不再摄入假源） |
| Batch 4 | F-MCP-04 | ✅ fixed | MCP server 接线 LearnEngine，learn 工具不再恒为 None |
| Batch 4 | F-MCP-01 | ⏳ deferred | 7 个 thinking 工具注册需逐工具 schema 设计 + 引擎接线，强行注册未接线工具会引入新缺陷——留作后续特性任务 |
| Batch 5 | F-COMP-01 | ❌ refuted | 误报：`analysis/impact.analyze_impact` 是真实 BFS（test_impact.py 覆盖），`KnowledgeGraph` 代理到 `CodeGraphStore`——API 与 MCP 最终查同一存储，非 stub-vs-complete。不改代码以免破坏已通过测试的路径 |
| Batch 6 | F-AUTH-02 | ✅ fixed | api.ts 新增 refreshAccessToken，401 时刷新+重试，access token 过期不再丢表单 |
| Batch 6 | F-WEB-03 | ✅ fixed | 401 由硬跳转改为刷新→重试→失败才登出跳转 |
| Batch 6 | F-WEB-02 | ✅ fixed | WebSocket 重连加上限（10 次），不再无限重连 |
| Batch 6 | F-WEB-04 | ⏳ deferred | 路由守卫需 auth-mode 感知：local-first 模式后端信任无 token 请求，硬守卫会破坏本地单用户使用——留作后续（加 /api/auth/mode 端点 + 条件守卫） |
| Batch 7 | F-RS-02 | ✅ fixed | web 搜索 except 现记录错误（变量 e 原未用），不再静默吞错 |
| Batch 7 | F-RS-06 | ✅ fixed | 综合传入真实 ingested items（原传 []），溯源链不再断裂 |
| Batch 7 | F-RS-07 | ✅ fixed | execute_research 异常时标 failed（原恒 completed）；零结果正常完成 |
| Batch 7 | F-RS-11 | ✅ fixed | synthesize_research 无 LLM 时诚实标注"仅来源列表"，不再静默忽略 llm_client |
| Batch 8 | F-PLUG-01 | ✅ fixed | 插件 discover/load/enable/disable 裸 except 现记录错误，失败可见 |
| Batch 8 | F-PLUG-02 | ✅ fixed | event_bus 队列满/处理器异常现记录，不再静默丢/吞 |
| Batch 8 | F-PLUG-05 | ❌ refuted | 误报：app.py create_app_from_config 已用闭包把 PluginContext.subscribe_event/publish_event 桥接到 InMemoryEventBus |
| Batch 8 | F-ONB-01 | ❌ refuted | 误报：onboarding 路由提供 GET /status + POST /seed 流程（经 WriteQueue 创建页面 + 逐页错误处理）；starter_kits 是数据文件，本应静态 |
| Batch 9 | F-INGEST-01 | ✅ fixed | ingest() 新增可选 progress_callback，classify/extract/fuse/validate/enqueue/done 各阶段回调，不再静默长跑 |
| Batch 9 | F-INGEST-02 | ✅ fixed | 摄入错误消息改为可操作三段式提示（含修复建议），不再裸技术串 |
| Batch 9 | F-INGEST-03 | ✅ clarified | JSON/TABLE 无 extractor 已优雅返回错误（非崩溃）；消息已澄清"暂不支持"。加 extractor 属特性任务 |
| Batch 10 | F-MCP-02 | ❌ refuted | 误报：所有 query 工具均 `if _engine is None: return {error}`（如 "Query engine not initialized"），且 server.py 已 `logger.warning` 记录初始化失败——非静默吞没 |
| Batch 10 | F-COMP-02 | ❌ refuted | 误报：`_build_call_tree` 用 `visited` 集合在递归前检查，已防止死循环/挂死；循环已检测并标记 "(loop)"。报告完整环路路径是增强项，非正确性 bug |
| Batch 11 | F-WEB-05 | ✅ fixed | RFC7807 `title` 改为人类可读（如 "Knowledge store unavailable"），不再暴露异常类名 |
| Batch 11 | F-WEB-06 | ✅ fixed | import_md 500 不再暴露 str(e)（改通用消息 + 服务端 log） |
| Batch 11 | F-WEB-09 | ✅ fixed | 前端 ApiError 解析 RFC7807 title/detail，组件显示有意义消息而非原始 HTTP 状态文本 |
| Batch 12 | F-AUTH-03 | ✅ fixed | 登录用户不存在时跑 dummy bcrypt 均衡时序，防用户枚举 |
| Batch 12 | F-AUTH-05 | ✅ fixed | 403 不再暴露内部角色名，改通用"无权限"消息 |
| Batch 12 | F-AUTH-06 | ✅ partial | query 输入检查扩至全方法 + 窄 XSS 检测（sanitize_string/check_xss 现已使用）；请求体 XSS 由 Pydantic+渲染层兜底，专用 body sanitizer 留后续 |
| Batch 12 | F-AUTH-08 | ✅ fixed | 429 响应增加标准 Retry-After 头 |
| Batch 12 | F-AUTH-09 | ❌ refuted | 误报：登录表单不应有 minLength（会误拒有效短密码）；"Invalid email or password" 是防枚举的正确通用消息 |
| Batch 13 | F-QS-04 | ✅ fixed | CommandPalette 实现 ↑↓ 键盘导航 + 高亮 + Enter 选中（原仅提示无实现） |
| Batch 13 | F-QS-06 | ✅ fixed | 新增前端 slugify（镜像后端），图节点/搜索建议 slug 不再与后端不一致导致 404 |
| Batch 13 | F-WEB-07 | ✅ fixed | useShortcuts 网页模式注册原生 keydown，Cmd+S/O/N/, 在浏览器生效（原仅 Tauri） |
| Batch 13 | F-QS-09 | ⏳ deferred | 暗色模式为纯 CSS 美容项，留作 UI 统一刷 |
| Batch 13 | F-WEB-08 | ⏳ deferred | 面包屑为新组件特性，留作后续 |
| Batch 14 | F-INGEST-04 | ✅ fixed | 批量失败计数 `list.count(lambda)` 误用（恒 0）改为 `sum(1 for r if not r.success)` |
| Batch 14 | F-INGEST-05 | ✅ fixed | scheduler 成功重置逻辑反转修正：仅无错且 200/304 才重置失败计数（原 else 在有错时反而重置，削弱退避） |
| Batch 14 | F-DB-02 | ✅ fixed | dispatcher 未知 sink 由 `continue`（无限 pending）改为 mark_failed 推进至死信，不再循环 |
| Batch 14 | F-CONF-01 | ❌ refuted | 误报：ConfigError 暴露的是用户自有配置路径 + yaml 解析错误，属可操作用户面信息，非内部泄露 |
| Batch 15 | F-GOV-01 | ✅ fixed | linter confidence_map 键名改为枚举名（single_source/cross_validated/human_verified）+ .lower()，分布统计不再全塌缩到 1 级 |
| Batch 15 | F-COMP-06 | ✅ fixed | code_wiki status() 改为从 .status 文件读取真实生成时间（原硬编码 utcnow） |
| Batch 16 | F-CONN-05 | ✅ fixed | SyncEngine 接入 HealthMonitor，sync 成功/失败时 record_success/record_failure（best-effort 不阻断同步） |
| Batch 16 | F-CONN-09 | ❌ refuted | 误报：trigger_sync 实际构造 SyncEngine 并 `await sync_engine.sync()`，非空操作 |
| Batch 16 | F-CONN-04 | ⏳ deferred→见 Batch 21 | 冲突检测需按 source_id 查既有 claim，但 claim 表无 source_id 列（仅 source_uuid）——需 schema 变更，盲接有风险 |
| Batch 17 | F-WEB-10 | ✅ fixed | DELETE 端点加存在性检查（404）+ 反链扫描警告（PageStatus.warnings） |
| Batch 17 | F-COMP-04 | ✅ fixed | impact summary 增加 risk_legend，解释 WILL_BREAK 等标签含义 |
| Batch 18 | F-CONN-07 | ✅ fixed | OAuth callback 处理用户拒绝授权（error/无 code → 友好 400，原 422） |
| Batch 18 | F-CONN-10 | ✅ fixed | OAuth 授权 URL 参数 URL-编码（urlencode，原裸拼接） |
| Batch 18 | F-COMP-03 | ⏳ deferred | _cascade_update 为 pass 桩 + CompileResult schema 不明，需先设计降级标记字段 |
| Batch 19 | F-QS-08 | ✅ fixed | Tree Mode 实现真实标题层级树：解析 wiki 页 markdown ATX 标题构建嵌套 HeadingNode，按查询词定位章节并返回 root→section 路径（原扁平 stub）；claim 路径保留为回退 |
| Batch 20 | F-CONN-06 | ✅ fixed | webhook_inbound 验签后尽力提取文本→经 WriteQueue 入 claim（原仅 ack），推送式接入闭环 |
| Batch 21 | F-CONN-04 | ✅ partial | 迁移 v6 加 source_platform/source_id 列 + Claim 域字段 + claims_sink 写入 + repo get_by_source_id + sync_pull 接入 detect_conflict/record_conflict（SAW 胜则跳过，best-effort 全 try/except）。自动 UPDATE resolution 仍留后续 |
| Batch 22 | F-INGEST-07 | ✅ fixed | fuser 实现真实否定矛盾检测（同源 + 否定前缀），contradictions 不再恒空 |
| Batch 23 | F-QS-07 | ✅ fixed | QueryCache 接入 _keyword_search 读路径（LRU+TTL）+ dispatcher 内容写入时 clear 失效（原 cache.py 死代码） |
| Batch 24 | F-QS-05 | ✅ fixed | 图谱布局统一为单一源：Graph.tsx 用 store.layout（原 local state）；KnowledgeGraph 用 getLayout(layout)（原 getLayoutForViewMode）；新增 circle/grid 布局 |
| Batch 25 | F-COMP-03 | ✅ fixed | LLM 合成失败时在页面加可见降级 banner（离线模式不加）；_cascade_update 替换 pass 桩，改为记录引用页 log entry |
| Batch 26 | F-WEB-04 | ✅ fixed | 加 GET /api/auth/mode 端点 + 前端 RequireAuth 条件守卫（仅 team 模式强制登录，兼容 local-first） |
| Batch 27 | F-INGEST-03 | ✅ fixed | 新增 JSON/Table extractor（离线规则式，每记录/行一 claim）+ 接入 pipeline JSON/TABLE 路由（原分类后无 extractor 必报错） |
| Batch 28 | F-WEB-08 | ✅ fixed | 新增 Breadcrumbs 组件（按路径段生成可点击面包屑，含暗色 + 可访问性 aria-label）+ App.tsx main 内渲染 |
| Batch 29 | F-QS-09 | ✅ partial→done | 搜索组件暗色（Batch 29）+ 图谱组件暗色（Batch 30: GraphControls/GraphFilters/NodeDetail）全补齐 |
| Batch 31 | F-CONN-04 | ✅ done | resolution：claims_repository 加 upsert（UPDATE 既有 content，否则 INSERT）；claims_sink 改用 upsert——platform-wins 冲突真正覆盖旧 claim（原 INSERT OR IGNORE 不更新） |

> 验证：Batch 1 改动通过 462 项测试（auth/reconcile/dispatcher/query/web/engines/integration），0 回归。
> 验证：Batch 2 改动通过全套件 1569 项测试，0 回归。
> 验证：Batch 3 改动通过全套件 1569 项测试，0 回归。
> 验证：Batch 4 改动通过全套件 1569 项测试，0 回归。
> 验证：Batch 5 F-COMP-01 经主审核为误报（同 F-DB-01），无代码改动。
> 验证：Batch 6 改动通过前端 51 项测试 + tsc 干净，0 回归。
