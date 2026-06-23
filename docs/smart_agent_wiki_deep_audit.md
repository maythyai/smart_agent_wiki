# Smart Agent Wiki 深度审计报告

**审计日期**: 2026-06-23  
**项目版本**: v3.7.0  
**审计范围**: 后端架构、前端体验、连接器/插件/MCP、竞品对标

---

## 一、总体评估

Smart Agent Wiki 定位精准——local-first 的多代理知识管理平台，在架构理念上具有前瞻性（四层存储、六边形架构、Agent-as-knowledge-worker）。但从"一个用户打开这个工具"的视角审视，**当前版本更像是一个架构设计文档的可运行骨架，而非一个可用的产品**。

核心矛盾在于：**文档描述的能力远大于实际实现的能力**。README 宣称的 24+ MCP 工具实际只有 6 个、6 个 Agent 的 `execute()` 为空实现、9 个连接器有 2 个完全不存在、前后端认证体系各自独立互不通信。

以下按"用户旅程"组织问题——从安装、首次使用、核心功能到高级特性。

---

## 二、致命问题（系统无法正常工作）

### 2.1 前端是一个"只读查看器"，核心交互全部断裂

这是用户最直接的体感问题。打开 Web UI 后：

| 问题 | 影响 |
|------|------|
| **没有登录/注册页面** | 后端有完整 JWT 认证，前端零 auth UI，API 请求不带 Authorization header |
| **没有页面列表/浏览页** | `GET /api/pages` 存在，但 Home 页只有 3 张静态卡片，无法浏览任何 wiki 内容 |
| **没有新建页面入口** | 整个 UI 找不到"新建"按钮，用户无法创建任何内容 |
| **编辑器保存按钮无效** | `Page.tsx` 的 Save 按钮只切换 mode 为 view，从未调用 `handleSave()` |
| **没有 404 页面** | 任何未知 URL 渲染空白，无反馈 |
| **没有删除页面 UI** | `useDeletePage` hook 完整实现但从未被任何页面引用 |

**用户视角**：打开 Web UI → 看到首页 → 点不进任何内容 → 想新建找不到按钮 → 编辑现有页面点保存没反应 → 关闭浏览器。整个流程不超过 2 分钟就会让用户判定"这个工具不能用"。

### 2.2 后端多个核心功能为空壳或完全失效

| 问题 | 文件位置 | 影响 |
|------|----------|------|
| **SSTI 模板注入漏洞** | `workflow_executor.py:382` | Jinja2 渲染用户条件表达式，可远程代码执行 |
| **所有 mutation API 无认证** | `routes/pages.py` | 任何人可创建/修改/删除页面 |
| **Ingest 去重完全失效** | `pipeline.py:239` | `_get_existing_claims()` 直接返回空列表，产生大量重复数据 |
| **矛盾检测是占位符** | `fuser.py:50` | contradictions 列表永远为空 |
| **ContextCompiler 参数不匹配** | `app.py:213` | 传 3 个参数但构造函数要 4 个，启动即崩溃 |
| **collaborate 引擎为 None** | `app.py` | `create_app_from_config()` 传入 `collaborate=None`，工作流端点全崩 |
| **BaseAgent.execute() 为空** | `agents/base.py` | 6 个 Agent 的 execute 返回空结果，多 Agent 协作完全无效 |
| **用户数据存于内存** | `routes/auth.py` | UserStore 用内存字典，重启即丢失所有用户 |

### 2.3 连接器与 MCP 名不副实

README 宣称"9 个连接器"和"24+ MCP 工具"，实际情况：

| 宣称 | 实际 |
|------|------|
| Obsidian 连接器 | **不存在**（只有一个客户端 Obsidian 插件） |
| RSS/Atom 连接器 | **不存在**（代码库中无任何 RSS 相关文件） |
| 24+ MCP 工具 | **只有 6 个**，且没有 MCP Server 入口点（工具是孤立的 Python 函数） |
| Notion 双向同步 | 拉取时 content 永远为空，推送只映射 Title 属性 |
| GitHub Discussions | GraphQL client 完整实现但从未被 connector 调用 |
| 冲突检测与解决 | `ConflictResolver` 完整实现但 `SyncEngine.sync()` 从未调用它 |

---

## 三、主要设计缺陷

### 3.1 前后端割裂——两个独立项目而非一个产品

前后端之间缺乏统一的契约：

- **API 路径不一致**：前端 `integrationsStore` 硬编码 `/api/v1/integrations`，但 proxy 配置的是 `/api`，请求会 404
- **两个独立 Zustand store 不通信**：`useStore`（主）和 `useIntegrationsStore` 完全独立
- **Dashboard 绕过 React Query**：用原生 `fetch` + `setInterval` 拉数据，无重试/缓存/去重
- **Tailwind v4 用了 v3 的 config 文件**：自定义 `confidence`/`freshness` 颜色可能被 v4 引擎静默忽略

### 3.2 治理引擎——设计精良但实现空洞

置信度、新鲜度、矛盾检测、审计收据——这些概念设计很好，但实现层面：

| 功能 | 状态 |
|------|------|
| `trigger_review()` | no-op |
| `get_review_queue()` | 返回空列表 |
| `apply_resolution()` | no-op |
| `upgrade_confidence()` | 不持久化 |
| `get_confidence_distribution()` | 全返回零 |
| `refresh_on_access()` | 不更新任何数据 |
| `detect_gaps()` / `get_growth_patterns()` | 占位符 |

**用户视角**：`saw conflicts` 永远返回空、`saw freshness` 永远显示全绿、`saw lint` 永远说一切正常。治理系统给了用户"虚假的安全感"。

### 3.3 插件系统——无沙箱、无事件、无示例

- **沙箱是幻觉**：插件通过 `importlib` 加载到同一进程，`PluginContext` 只是一个 dataclass，插件完全可以忽略它直接 `import os`
- **事件系统从未触发**：定义了 6 种事件类型，但代码库中没有任何地方 emit 这些事件
- **模块命名污染**：`sys.modules[f"plugin_{name}"]` 可被恶意插件利用来 shadow 标准库
- **零个示例插件**：用户无法参考任何 working example 来开发插件

### 3.4 LLM 集成——裸调用无任何防护

`LLMRouter` 直接调用 LiteLLM，缺少：
- 速率限制（可能触发上游 429）
- Response 缓存（重复查询浪费 token）
- Fallback model（主模型不可用时直接失败）
- `_check_available()` 方法已定义但从未被调用

### 3.5 知识图谱可视化——控件全部失灵

Cytoscape.js 集成是"看起来有但用不了"的典型：

- **缩放按钮无效**：`onZoomIn/Out/Fit` 回调全是空函数
- **布局选择器脱节**：侧边栏的 layout select 用 local state，GraphControls 用 store，两者不同步，且 KnowledgeGraph 组件忽略 layout prop
- **关系类型过滤器无效**：UI 存在但 `relationTypeFilter` 从未发送给 API
- **每次数据变化重建 Cytoscape 实例**：丢失动画状态、滚动位置、选中状态

---

## 四、用户体验差距（对标同类项目）

以 Obsidian / Notion / Logseq / Heptabase 等成熟知识管理工具的标杆来衡量，SAW 缺少以下用户"理所当然"期待的功能：

### 4.1 导航与发现

| 缺失功能 | 对标项目 | 用户影响 |
|----------|----------|----------|
| 侧边栏页面树 | Obsidian / Notion | 用户无法浏览层级内容，只能靠搜索或知道 URL |
| 面包屑导航 | 所有 wiki 类工具 | 用户不知道当前页面在知识体系中的位置 |
| 最近浏览/历史 | 所有 KM 工具 | 无法快速回到刚看过的页面 |
| 反向链接面板 | Obsidian / Logseq / Roam | **这是 wiki 类工具的核心功能**，缺失意味着知识之间无法自然形成网络 |
| 命令面板 (Cmd+K) | Obsidian / VS Code | 高级用户没有快速操作入口 |

### 4.2 内容创作

| 缺失功能 | 对标项目 | 用户影响 |
|----------|----------|----------|
| 新建页面 UI | 所有工具 | 用户无法通过 UI 添加内容 |
| `[[` 内部链接自动补全 | Obsidian / Logseq | Wiki 核心交互缺失 |
| 图片/附件嵌入 | 所有工具 | 无法创建富媒体内容 |
| 页面模板 | Notion / Obsidian | 无法快速启动常见页面类型 |
| 目录/大纲面板 | Notion / GitBook | 长页面无法快速导航 |
| 版本历史/Diff 视图 | Obsidian (Git) / Notion | 无法查看变更或回滚 |

### 4.3 搜索与查询

| 缺失功能 | 对标项目 | 用户影响 |
|----------|----------|----------|
| 语义+关键词混合搜索 | Mem.ai / Reflect | 只有 BM25 关键词搜索，缺少 embedding 语义搜索 |
| 搜索建议/自动补全 | 所有现代工具 | SearchBar 有 suggestions 下拉但无 ARIA 属性、无键盘导航 |
| 搜索结果高亮 | 所有搜索工具 | 无法直观看到匹配位置 |

### 4.4 协作与社交

| 缺失功能 | 对标项目 | 用户影响 |
|----------|----------|----------|
| 用户账户/头像 | 所有协作工具 | 无多用户支持 |
| 评论/批注 | Notion / Google Docs | 无协作审阅流程 |
| Agent 活动可视化 | 无直接对标（SAW 独有概念） | 6 个 Agent 在做什么完全不可见，Dashboard 只有静态卡片 |

### 4.5 数据导入导出

| 缺失功能 | 对标项目 | 用户影响 |
|----------|----------|----------|
| Obsidian vault 导入 | Obsidian | 用户迁移路径断裂 |
| Notion 导出导入 | Notion | 连接器声称支持但 content 为空 |
| Markdown 批量导入 | 所有工具 | `saw ingest` CLI 存在但无 UI |
| 导出功能 | 所有工具 | ExportDialog 使用不存在的 CSS 类，完全无法使用 |

---

## 五、代码质量与工程问题

### 5.1 安全漏洞

| 严重度 | 问题 | 位置 |
|--------|------|------|
| **CRITICAL** | SSTI 模板注入 → RCE | `workflow_executor.py:382` |
| **CRITICAL** | 所有 mutation API 无认证 | `routes/pages.py` |
| **HIGH** | CSP 包含 `unsafe-inline` | `middleware/security.py` |
| **HIGH** | `require_role()` 默认值可绕过 | `middleware/security.py` |
| **HIGH** | InputSanitizer 不检查 GET 参数 | `middleware/security.py` |
| **MEDIUM** | vault merge 用 `git add .` 可能泄露密钥 | `vault_repository.py` |

### 5.2 代码 Bug

| 问题 | 位置 |
|------|------|
| `list.count(lambda)` 永远返回 0 | `batch.py:221` |
| 三元表达式优先级错误 | `scheduler.py:249` |
| Dispatcher 传入不存在的参数 | `dispatcher.py:160` |
| FSRS 路径双重 `.saw/.saw/` | `fsrs_scheduler.py` |
| `reconcile run` 覆盖 facts 为空列表 | `cli/reconcile.py:172` |
| SQLite event listener 用错 API | `sqlite_connection.py:45` |

### 5.3 前端工程问题

| 问题 | 影响 |
|------|------|
| 5 个 hooks 导入 `@tauri-apps/api` 但不在 package.json 中 | 构建时如果引用即崩溃 |
| ExportDialog / DropZone 使用不存在的 CSS 类 | 组件完全无样式 |
| `@/*` 路径别名定义但零使用 | 代码规范不一致 |
| 同一常量 (CONFIDENCE_LABELS) 在 3 个文件重复定义 | 维护成本高 |
| 编辑器无 undo/redo 按钮 | 用户必须知道 Markdown 语法或快捷键 |

---

## 六、改进方案（按优先级排序）

### Phase 1：让产品"能用"（1-2 周）

目标：修复阻断用户基本使用的问题。

**1.1 补全前端核心交互**
- 添加页面列表/浏览页（sidebar + 主内容区）
- 添加新建页面 UI（表单 + 编辑器）
- 修复编辑器保存按钮（确保 mode 切换前调用 handleSave）
- 添加 404 catch-all 路由
- 添加面包屑导航

**1.2 补全认证链路**
- 前端添加 Login/Register 页面
- API client 注入 Authorization header
- 添加 protected route guard
- 后端 mutation API 挂载认证依赖

**1.3 修复致命后端 Bug**
- 修复 SSTI 漏洞（用安全的表达式求值替代 Jinja2 模板渲染）
- 修复 ContextCompiler 参数不匹配
- 修复 collaborate=None 导致的工作流崩溃
- 修复 Ingest 去重（实现 `_get_existing_claims()` 的实际查询）
- 修复 `batch.py` 的 `list.count(lambda)` bug
- 修复 `reconcile.py` facts 被覆盖的 bug

### Phase 2：让产品"可信"（2-4 周）

目标：让核心功能真正工作，而非空壳。

**2.1 激活治理引擎**
- 实现矛盾检测的实际逻辑（基于 embedding 相似度 + 关键词重叠）
- 实现置信度评估的持久化
- 实现新鲜度的自动衰减和访问刷新
- 让 `saw conflicts` / `saw freshness` / `saw lint` 返回真实数据

**2.2 激活 Agent 系统**
- 实现 BaseAgent.execute() 的实际 LLM 调用
- 为每个 Agent 定义清晰的 system prompt 和工具集
- 在 Dashboard 添加 Agent 活动实时面板（用户在做什么、Agent 在做什么）

**2.3 修复知识图谱可视化**
- 修复缩放/布局/过滤控件的连接
- 避免每次数据变化重建 Cytoscape 实例（用 diff 更新）
- 添加节点搜索、边标签、minimap

**2.4 LLM 路由加固**
- 添加 response 缓存（LRU + TTL）
- 添加 fallback model 链
- 添加速率限制和指数退避

### Phase 3：让产品"好用"（4-8 周）

目标：补齐与同类产品的体验差距。

**3.1 导航与发现**
- 侧边栏页面树（支持折叠/展开层级）
- 反向链接面板（"What links here"）
- 最近浏览历史
- 命令面板 (Cmd+K)
- 全文搜索 + embedding 语义混合搜索

**3.2 内容创作增强**
- `[[` 内部链接自动补全
- 图片/附件拖拽上传
- 页面模板系统
- 目录/大纲面板
- 版本历史与 Diff 视图

**3.3 数据导入导出**
- Obsidian vault 导入（读取 Markdown + frontmatter）
- Notion 完整内容同步（修复 content 为空的问题）
- Markdown/PDF/HTML 导出
- 修复 ExportDialog 的 CSS 问题

**3.4 连接器补全**
- 实现 RSS/Atom 连接器
- 实现 Obsidian Python 连接器（或明确说明只通过 Obsidian 插件交互）
- 将 GitHub Discussions GraphQL client 接入 connector
- 修复 Notion 双向同步（content + 完整属性映射）

### Phase 4：差异化竞争力（长期）

目标：发挥 SAW 独有的多 Agent 架构优势。

**4.1 Agent-as-Knowledge-Worker**
- Agent 主动整理：自动发现未分类页面、建议标签、发现孤立知识
- Agent 主动关联：自动发现可链接的页面、建议新的知识关系
- Agent 主动摘要：为新摄入的文档自动生成摘要和关键主张
- Agent 活动流：用户可以看到"Librarian 刚刚为 3 个页面添加了标签"

**4.2 插件生态**
- 实现真正的事件总线（emit 事件 → 分发到订阅插件）
- 实现进程级沙箱（subprocess + restricted Python）
- 提供 3-5 个示例插件
- 建立插件注册/分发机制

**4.3 MCP Server 完善**
- 实现真正的 MCP Server 入口（stdio/SSE transport）
- 补全缺失的 18 个工具
- 确保与 Claude Code / Cursor / Copilot 的兼容性

**4.4 移动端**
- PWA 支持（至少支持移动端查看和搜索）
- 离线模式（Service Worker + IndexedDB 缓存）

---

## 七、SAW 的独特优势（值得坚守）

尽管存在大量实现缺口，SAW 的架构设计有几个真正独特的差异化点，是市面上没有竞品能匹配的：

1. **知识编译范式**：知识是"编译"的结果而非检索的对象。四层存储（Vault → Claims → Wiki → Index）+ 可溯源到原始文档位置——这在所有 KM 工具中独一无二。

2. **多 Agent 知识治理**：6 个专业化 Agent 各司其职（Librarian/Writer/Critic/Linker/Scholar/Guardian），市面上没有第二个产品做到这个程度的 Agent 分工。

3. **三层入口模型**：CLI + Web UI + MCP Server 覆盖不同用户群——开发者用 CLI、管理者用 Web UI、AI 工具用 MCP。

4. **代码智能**：影响分析、执行流检测、过期检测——将知识管理直接与代码开发打通，这是 GitNexus 等工具都没有完全做到的。

5. **Token 优化体系**：Anatomy Index + Cerebrum + Bug Log + Session Tracker 的组合，在 LLM 成本日益增长的背景下非常有价值。

---

## 八、总结

SAW 目前处于"架构 80 分、实现 30 分"的状态。设计文档描绘的愿景令人兴奋，但用户实际触达的功能远少于承诺。最紧迫的不是增加新功能，而是**让已有功能真正工作**。

建议的优先级排序：

```
让核心交互不断裂 > 让治理/Agent 真正运行 > 补齐体验差距 > 发挥差异化优势
```

从用户视角说：一个知识管理工具，如果用户连"新建一个页面并保存"都做不到，那再精妙的架构设计也无法产生价值。

---

*报告生成于 2026-06-23，基于 smart_agent_wiki v3.7.0 源码审计*
