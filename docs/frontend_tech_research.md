# Smart Agent Wiki — 前端技术选型研究报告

> 针对 Smart Agent Wiki 项目的五项前端关键技术选型，基于项目实际需求进行深度对比分析并给出明确推荐。

---

## 0. 项目需求摘要

| 需求维度 | 具体要求 |
|---------|---------|
| 后端 | Python FastAPI + FastMCP |
| 核心功能 | 知识图谱可视化、WYSIWYG Markdown 编辑、Wiki 页面浏览、搜索界面、仪表盘 |
| 桌面端 | 可能采用 Tauri v2 打包桌面客户端 |
| 数据架构 | 4 层存储 (Vault -> Claims -> Wiki -> Index) |
| 图谱规模 | 1000+ 节点，需要路径高亮、拖拽/缩放交互 |
| 多端访问 | CLI + MCP + Web + 桌面端 |

---

## 1. 前端框架选型

### 候选方案对比

| 维度 | React 19 | Vue 3 | Svelte 5 | Solid.js |
|------|----------|-------|-----------|----------|
| **图谱库兼容性** | G6 官方支持 React；Cytoscape.js/sigma.js 均有 React 封装 | 需要手动封装或使用第三方适配器 | 生态较新，图谱库适配器少 | 无成熟图谱适配器 |
| **Markdown 编辑器生态** | Tiptap/Milkdown/Plate 均原生支持 | Tiptap 有 Vue 版本；Milkdown 框架无关 | 需手动封装 | 需手动封装 |
| **Tauri v2 集成** | 完全兼容，官方示例首选 | 完全兼容 | 完全兼容 | 完全兼容 |
| **SSR/SSG** | Next.js（生态最大） | Nuxt.js（成熟稳定） | SvelteKit（优秀体验） | SolidStart（较新） |
| **Bundle 大小** | 中等 (~45KB gzip) | 中等 (~34KB gzip) | 极小 (~2KB，编译时框架) | 极小 (~7KB) |
| **运行时性能** | 良好（并发特性改进） | 良好 | 优秀（无虚拟 DOM） | 优秀（细粒度响应式） |
| **社区与招人** | 最大生态，组件库丰富 | 国内生态强，中文文档完善 | 增长快但整体较小 | 最小社区 |
| **npm 周下载量** | ~25M | ~5M | ~800K | ~400K |

### 关键分析

**图谱可视化是本次选型的硬约束。** @antv/G6 官方提供 React 组件 `@antv/g6-react`，且 G6 的 12,085 GitHub Stars 和蚂蚁集团的持续维护使其成为中文知识管理工具的自然选择。Cytoscape.js 的 `react-cytoscapejs` 和 sigma.js 的 `@sigmajs/react` 同样成熟。而 Svelte 和 Solid.js 在图谱库方面缺少官方适配器，需要自行编写大量胶水代码。

**Markdown 编辑器生态同样以 React 最为丰富。** Plate 是 React-only 方案（基于 Slate），Tiptap 提供官方 React 集成，Milkdown 虽然框架无关但 React 示例最完善。如果选择 Vue，Tiptap 有 Vue 版本但 Plate 完全不可用。

**Tauri v2 对所有框架一视同仁。** Tauri 使用系统原生 WebView 渲染前端，任何编译为 HTML/CSS/JS 的框架都可以工作，因此这不是差异化因素。

**Bundle 大小对桌面应用影响有限。** Tauri v2 的桌面端不依赖网络加载，React 的 ~45KB gzip 与 Svelte 的 ~2KB 差异在本地应用中用户无法感知。

### 推荐：React 19 + TypeScript

**理由：**

1. **图谱库首选用 @antv/G6，其官方 React 适配器直接可用**，无需额外封装工作。选择其他框架意味着要为 G6 写适配层，增加维护负担。
2. **Markdown 编辑器选择面最宽**，Tiptap（官方 React 支持）、Milkdown（框架无关但 React 文档最好）、Plate（React-only）全部可用，可以在实际开发阶段做二次筛选。
3. **UI 组件库 shadcn/ui 基于 React**，这是下文 UI 库推荐的配套选择。
4. **社区规模和长期维护风险最低**。npm 2500 万周下载量意味着遇到问题能快速找到解决方案，招人也最容易。
5. **状态管理方案最丰富**，Zustand/Jotai/Valtio 都是 React 生态的原生选择。

Vue 3 是合理的第二选择（尤其如果团队更熟悉 Vue），但 G6 和 shadcn/ui 的 React 倾向使得 React 成为整体技术栈的最优解。

---

## 2. 图谱可视化库选型

### 候选方案对比

| 维度 | @antv/G6 | sigma.js | Cytoscape.js | vis-network |
|------|----------|----------|--------------|-------------|
| **GitHub Stars** | 12,085 | 11,998 | 10,951 | 3,556 |
| **渲染引擎** | Canvas/SVG/WebGL | WebGL | Canvas/SVG | Canvas |
| **1000+ 节点性能** | 支持（GPU + Rust 并行计算布局） | 优秀（WebGL 原生优势） | 一般（Canvas 瓶颈） | 勉强（官方说"few thousand"） |
| **布局算法** | 10+ 内置（力导向、层次、环形、辐射、Dagre 等） | 依赖 graphology 布局插件 | 丰富（学术级图论库） | 4 种基础布局 |
| **交互能力** | 拖拽/缩放/框选/路径分析/子图提取 | 拖拽/缩放/悬停 | 拖拽/缩放/70+ 扩展插件 | 拖拽/缩放/聚类 |
| **React 集成** | 官方 `@antv/g6-react` | 社区 `@sigmajs/react` | `react-cytoscapejs` | 第三方封装 |
| **中文文档** | 完善（蚂蚁集团出品） | 无 | 无 | 无 |
| **定制化程度** | 高（自定义节点/边/交互） | 中等 | 高（CSS-like 样式） | 低 |
| **维护状态** | 活跃（蚂蚁数据可视化团队） | 活跃 | 活跃（学术支持） | 维护模式 |

### 关键分析

**渲染技术决定性能天花板。** sigma.js 使用纯 WebGL 渲染，天然适合数千节点的大规模图，但其交互能力相对有限（主要做网络可视化，不是图分析工具）。G6 v5 引入了 GPU 加速布局和 Rust 并行计算，在 1000+ 节点场景下的性能已接近 WebGL 方案。Cytoscape.js 使用 Canvas，在没有 WebGL 加速的情况下，超过 1000 节点会出现明显卡顿。vis-network 性能最弱。

**Smart Agent Wiki 的图谱不是纯可视化，而是交互式知识管理工具。** 用户需要：点击节点跳转 Wiki 页面、高亮两个概念之间的路径、拖拽重新布局、展开/折叠子图。这要求图谱库具备丰富的事件系统和自定义能力。G6 和 Cytoscape.js 在这方面优于 sigma.js。

**中文生态是实际生产力因素。** G6 的中文文档、中文社区、蚂蚁团队的持续维护，对于中文知识管理项目来说是巨大的实际优势。调试时能看懂文档比学术级别的图论能力更重要。

**graphology 是 sigma.js 的隐藏优势。** sigma.js 底层使用 graphology 作为图数据结构，这意味着你可以用 graphology 的算法库（最短路径、中心性、社区检测等）做后端分析，然后传给 sigma.js 前端渲染。但 Smart Agent Wiki 的图算法在后端用 Python (NetworkX/igraph) 处理更自然，这个优势被抵消。

### 推荐：@antv/G6 v5（主力）+ sigma.js（大规模场景备选）

**理由：**

1. **1000+ 节点性能达标。** G6 v5 的 GPU 布局 + Rust 并行计算使其在知识图谱场景下性能足够。如果后续规模增长到 5000+，可以在特定视图切换到 sigma.js 的 WebGL 渲染。
2. **交互能力最强。** 路径高亮、节点展开/折叠、子图提取、自定义节点渲染（渲染 Markdown 摘要、置信度标签等）都是 G6 的强项。
3. **React 原生集成。** `@antv/g6-react` 提供声明式组件 API，与 React 状态管理无缝对接。
4. **中文文档完善。** 开发效率显著高于需要反复查英文文档的替代方案。
5. **蚂蚁集团持续维护。** 12,085 Stars，商业公司背书，不会出现维护者流失的风险。

**架构建议：** 封装一个 `GraphRenderer` 抽象层，内部默认使用 G6，但接口设计允许未来替换为 sigma.js。这样在大规模图谱场景下可以灵活切换，而不影响业务逻辑。

---

## 3. Markdown 编辑器选型

### 候选方案对比

| 维度 | Tiptap | Milkdown | Plate |
|------|--------|----------|-------|
| **底层引擎** | ProseMirror | ProseMirror | Slate.js |
| **GitHub Stars** | 33,000+ | 9,000+ | 12,000+ |
| **npm 月下载** | 12.8M | ~200K | ~600K |
| **框架支持** | React/Vue/Nuxt/Svelte（官方适配） | 框架无关 | React-only |
| **编辑模式** | WYSIWYG + Markdown 快捷键 | WYSIWYG + Markdown 插件 | WYSIWYG |
| **扩展性** | 100+ 官方扩展，社区扩展丰富 | 插件化架构，自定义 headless 组件 | 50+ 插件，AI Copilot |
| **协作编辑** | 付费（Tiptap Collab，SOC 2 认证） | 需自行实现 | 需自行实现 |
| **AI 集成** | 付费（Tiptap AI） | 无官方方案 | AI Copilot 插件（免费） |
| **数学公式** | KaTeX 扩展 | LaTeX 插件 | 需自行集成 |
| **代码高亮** | CodeBlockLowlight 扩展 | 内置 | 内置 |
| **表格支持** | 扩展支持 | 插件支持 | 插件支持 |
| **移动端适配** | 良好 | 良好 | 良好 |
| **License** | MIT（核心）/ 商业（Collab/AI） | MIT | MIT |
| **定制难度** | 中等（ProseMirror 学习曲线） | 中低（headless 设计降低门槛） | 中等（Slate 学习曲线） |

### 关键分析

**Smart Agent Wiki 对编辑器的核心需求：**

- 支持 Markdown 语法输入 + 所见即所得渲染
- 知识主张标注（置信度标签、来源溯源）
- 代码块 + 数学公式（知识管理刚需）
- 未来可能需要多人协作编辑
- 需要深度定制工具栏（插入知识主张、关联图谱节点等）

**Tiptap 的付费陷阱需要注意。** 协作编辑（Collab）和 AI 功能是付费商业服务，不是开源的。如果 Smart Agent Wiki 需要协作编辑，要么付费，要么基于 ProseMirror 的 Yjs 方案自行实现。但 Tiptap 核心编辑器（包含 100+ 扩展）是 MIT 协议，完全免费。

**Milkdown 的 headless 设计理念适合本项目。** Smart Agent Wiki 不是通用文档编辑器，而是知识管理工具中的编辑组件。Milkdown 的 headless 设计意味着 UI 完全由你控制，编辑器只负责编辑逻辑，这与本项目需要深度定制编辑体验的需求高度匹配。但 Milkdown 的社区规模（200K 月下载 vs Tiptap 的 12.8M）意味着遇到问题时解决方案更少。

**Plate 的 AI Copilot 值得关注但不构成决定性优势。** Smart Agent Wiki 的 AI 功能在后端通过 FastMCP 实现，不依赖编辑器内置 AI。Plate 的 React-only 限制也意味着与 Vue/Svelte 完全不兼容。

### 推荐：Tiptap（核心编辑引擎）

**理由：**

1. **生态最大，问题解决效率最高。** 12.8M 月下载量，StackOverflow 上大量 Q&A，遇到问题 10 分钟内能找到答案。相比之下，Milkdown 的问题可能需要翻源码。
2. **100+ 扩展覆盖本项目 90% 的编辑需求。** Markdown 快捷键、代码高亮（CodeBlockLowlight）、数学公式（KaTeX）、表格、任务列表、链接、图片等开箱即用。
3. **ProseMirror 底层提供最深度的定制能力。** Smart Agent Wiki 需要自定义"知识主张"节点类型（包含置信度、来源、审核状态），ProseMirror 的 Node/Mark 系统天然支持这种扩展。
4. **协作编辑的 Plan B 明确。** 如果未来需要协作，可以使用 Tiptap Collab（付费），或者基于 Yjs + ProseMirror 自行实现（开源方案成熟）。
5. **React 官方适配器成熟。** `@tiptap/react` 提供了 `useEditor` hook 和 `EditorContent` 组件，与 React 状态管理无缝集成。

**关于付费功能的说明：** Tiptap Collab 和 Tiptap AI 是付费服务，但 Smart Agent Wiki 的协作需求可以通过 Yjs（开源 CRDT 库）+ ProseMirror 自行实现，AI 功能已在后端通过 FastMCP 提供。核心编辑能力完全免费，无需担心供应商锁定。

---

## 4. UI 组件库选型

### 候选方案对比

| 维度 | shadcn/ui | Ant Design 5 | Naive UI |
|------|-----------|--------------|----------|
| **GitHub Stars** | 113,000+ | 93,000+ | 16,000+ |
| **技术基础** | Radix UI + Tailwind CSS | 自研组件 + CSS-in-JS | 自研组件 + CSS-in-JS |
| **设计风格** | 极简、高度可定制 | 企业级、规范完善 | 简约、Vue 原生 |
| **包管理方式** | 复制粘贴（非 npm 依赖） | npm 依赖 | npm 依赖 |
| **Bundle 大小** | 按需（只用复制需要的） | 较大（全量引入或配置按需） | 中等（Tree-shaking） |
| **暗色模式** | 内置 CSS 变量切换 | 内置 | 内置 |
| **框架绑定** | React | React | Vue 3-only |
| **Tailwind 依赖** | 是 | 否 | 否 |
| **定制自由度** | 极高（源码在你项目里） | 中等（Token/主题系统） | 中等（主题变量） |
| **组件丰富度** | 40+ 基础组件 | 60+ 企业级组件 | 80+ 组件 |
| **国际化** | 需自行处理 | 完善的 i18n 方案 | 内置 i18n |
| **表格/表单** | 基础（需搭配 TanStack Table 等） | 企业级（ProComponents） | 完善 |

### 关键分析

**shadcn/ui 不是传统组件库，是"组件源码生成器"。** 你不安装 npm 包，而是把组件代码直接复制到项目中。这意味着你拥有完全的源码控制权，可以任意修改组件行为和样式。缺点是组件升级需要手动同步。

**Smart Agent Wiki 不是企业后台管理系统。** Ant Design 的优势在于表格、表单、权限管理、数据展示等企业级场景。Smart Agent Wiki 是知识管理工具，核心界面是：图谱可视化、Markdown 阅读/编辑、搜索、仪表盘。这些场景更看重视觉品质和定制自由度，而不是开箱即用的企业组件。

**Naive UI 排除。** Naive UI 是 Vue 3 专属组件库，与本文推荐的 React 方案不兼容。

**shadcn/ui 与 Tailwind CSS 的组合提供了最佳的定制体验。** Smart Agent Wiki 的知识图谱界面、Wiki 页面、搜索界面都需要高度定制化的 UI，shadcn/ui 的"源码在你手里"模式允许你把组件改成任何样子，不受组件库 API 限制。

### 推荐：shadcn/ui + Tailwind CSS v4

**理由：**

1. **完全的可定制性。** Smart Agent Wiki 的 UI 不是标准后台管理界面，需要大量定制（知识主张卡片、置信度可视化、图谱控制面板等）。shadcn/ui 的组件源码直接在你的项目中，修改零阻力。
2. **无依赖锁定风险。** 组件代码复制到项目中后，即使 shadcn/ui 停止维护，你的代码不受任何影响。这与其他组件库形成鲜明对比（Ant Design 大版本升级经常导致 Breaking Changes）。
3. **与 Tailwind CSS 的完美配合。** 知识图谱界面的样式需要精细控制（节点颜色、边的样式、路径高亮），Tailwind 的 utility-first 模式非常适合这种场景。
4. **Bundle 大小最优。** 只复制你实际使用的组件代码，没有一行多余的 JavaScript。
5. **视觉品质高。** shadcn/ui 的设计审美偏现代极简，适合知识管理工具的调性。

**补充建议：** 对于 shadcn/ui 不覆盖的企业级组件（如高级表格），搭配 TanStack Table（虚拟滚动表格）和 cmdk（命令面板）等专注型库。这种"组合最优单品"的策略比使用一个全家桶组件库更灵活。

---

## 5. 状态管理选型

### 候选方案对比

| 维度 | Zustand | Jotai | Valtio | Pinia |
|------|---------|-------|--------|-------|
| **范式** | 单一 Store + Selector | 原子化（Atom） | 代理响应式（Proxy） | 单一 Store + Module |
| **框架** | React | React | React | Vue 3-only |
| **Bundle 大小** | ~1.1KB | ~2.5KB | ~3.5KB | ~1.5KB |
| **学习曲线** | 低（接近原生 JS） | 中低（原子化思维） | 低（直接 mutate） | 低（Vue 风格） |
| **TypeScript 支持** | 优秀 | 优秀 | 良好 | 优秀 |
| **中间件** | 内置（persist/devtools/immer） | 通过插件 | 通过插件 | 内置插件系统 |
| **异步处理** | 直接在 action 中 async/await | 通过 atom 的 async 定义 | 直接在 action 中 | async action |
| **DevTools** | Redux DevTools 兼容 | Redux DevTools 兼容 | Redux DevTools 兼容 | Vue DevTools |
| **适用场景** | 中大型应用 | 组件级细粒度状态 | 需要可变数据 | Vue 应用 |

### 关键分析

**Pinia 排除。** Pinia 是 Vue 3 官方状态管理方案，与本文推荐的 React 方案不兼容。

**Smart Agent Wiki 的状态特征分析：**

- **全局状态少**：用户认证状态、主题偏好、当前 Wiki 页面
- **图谱状态复杂**：当前选中节点、路径高亮状态、布局模式、缩放级别
- **编辑器状态独立**：由 Tiptap/ProseMirror 内部管理
- **搜索状态瞬态**：搜索关键词、过滤条件、结果列表
- **WebSocket 实时更新**：FastMCP 推送的知识主张更新

**Zustand vs Jotai 的核心区别是架构哲学。** Zustand 是集中的 Store 模式（类似简化的 Redux），适合在应用层管理全局状态。Jotai 是原子化模式（类似 Recoil），适合在组件级管理细粒度状态。Smart Agent Wiki 需要两者：全局状态（用户/主题）用 Zustand，组件级状态（图谱交互）用 Jotai。但引入两个状态管理库增加了团队认知负担。

**推荐 Zustand 作为唯一状态管理方案。** Zustand 的灵活性允许你同时处理全局状态和局部状态。通过 `create` 创建多个 Store，每个 Store 职责单一：

```typescript
// 全局 Store
const useAuthStore = create<AuthState>((set) => ({ ... }));

// 图谱 Store
const useGraphStore = create<GraphState>((set) => ({ ... }));

// 搜索 Store
const useSearchStore = create<SearchState>((set) => ({ ... }));
```

Zustand 的 `persist` 中间件可以直接将用户偏好、图谱布局等持久化到 localStorage 或 IndexedDB，这对 Tauri 桌面应用特别有用。

### 推荐：Zustand

**理由：**

1. **API 极简，团队上手零成本。** 一个 `create` 函数，一个 `useStore` hook，没有 Reducer/Action/Dispatch 的概念负担。
2. **多 Store 模式天然匹配 Smart Agent Wiki 的模块化架构。** 图谱状态、搜索状态、编辑状态各自独立，互不干扰。
3. **内置中间件覆盖核心需求。** `persist`（持久化到 localStorage）、`devtools`（Redux DevTools 调试）、`immer`（不可变数据更新）、`subscribeWithSelector`（细粒度订阅）全部开箱即用。
4. **与 Tauri 桌面应用配合良好。** `persist` 中间件可以将状态持久化到本地文件系统，实现桌面应用的"关闭后再打开恢复上次状态"。
5. **1.1KB 极小体积。** 在 Tauri 桌面应用和 Web 应用中都不是性能瓶颈。
6. **TypeScript 体验优秀。** Store 类型推导完整，不需要手写复杂类型声明。

---

## 6. 推荐技术栈总结

```
┌─────────────────────────────────────────────────────┐
│              Smart Agent Wiki 前端技术栈               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  框架          React 19 + TypeScript                 │
│  构建工具      Vite 6                                │
│  状态管理      Zustand (含 persist/devtools 中间件)   │
│  UI 组件库     shadcn/ui + Tailwind CSS v4           │
│  图谱可视化    @antv/G6 v5                           │
│  Markdown 编辑  Tiptap (ProseMirror)                 │
│  桌面端        Tauri v2                              │
│  路由          React Router v7                       │
│  数据请求      TanStack Query                        │
│  表格          TanStack Table                        │
│  命令面板      cmdk                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 技术栈选择的核心逻辑链

```
React 19（图谱库/编辑器/UI库生态最优解）
    │
    ├── @antv/G6 v5（React 官方适配器 + 中文文档 + GPU 布局）
    ├── Tiptap（ProseMirror 生态最大 + 100+ 扩展）
    ├── shadcn/ui（源码级控制 + 无锁定风险）
    └── Zustand（极简 API + 内置持久化）

Tauri v2（桌面端，对所有前端框架一视同仁，不构成选型约束）
```

### 风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| G6 v5 仍在快速迭代，API 可能变化 | 中 | 封装 `GraphRenderer` 抽象层，隔离 G6 API 变更 |
| Tiptap 协作编辑是付费功能 | 低 | 使用 Yjs + ProseMirror 开源方案替代 |
| shadcn/ui 组件需手动升级 | 低 | 设定月度同步周期，使用 `npx shadcn@latest diff` 检查变更 |
| React 19 并发特性增加调试复杂度 | 低 | 使用 React DevTools Profiler + Zustand DevTools 监控渲染 |

---

## 7. 项目目录结构建议

```
smart-agent-wiki-web/
├── src/
│   ├── components/
│   │   ├── ui/                    # shadcn/ui 组件（复制到此）
│   │   ├── graph/                 # 图谱可视化组件
│   │   │   ├── GraphRenderer.tsx   # G6 抽象层
│   │   │   ├── KnowledgeGraph.tsx  # 知识图谱主组件
│   │   │   └── GraphControls.tsx   # 布局/缩放控制面板
│   │   ├── editor/                # Markdown 编辑器组件
│   │   │   ├── WikiEditor.tsx      # Tiptap 编辑器封装
│   │   │   ├── extensions/         # 自定义 Tiptap 扩展
│   │   │   │   ├── claim.ts        # 知识主张节点类型
│   │   │   │   ├── confidence.ts   # 置信度标注
│   │   │   │   └── source-ref.ts   # 来源溯源链接
│   │   │   └── toolbar/            # 编辑器工具栏
│   │   ├── wiki/                  # Wiki 页面浏览组件
│   │   ├── search/                # 搜索界面组件
│   │   └── dashboard/             # 仪表盘组件
│   ├── stores/                    # Zustand stores
│   │   ├── auth.ts
│   │   ├── graph.ts
│   │   ├── search.ts
│   │   └── editor.ts
│   ├── hooks/                     # 自定义 hooks
│   ├── lib/                       # 工具函数
│   │   ├── mcp-client.ts          # FastMCP WebSocket 客户端
│   │   └── api.ts                 # FastAPI HTTP 客户端
│   ├── pages/                     # 页面路由
│   ├── types/                     # TypeScript 类型定义
│   └── styles/                    # 全局样式 + Tailwind
├── src-tauri/                     # Tauri v2 桌面端配置
│   ├── src/
│   │   └── main.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## 8. 结论

本文推荐的技术栈以 React 19 为核心，围绕其最丰富的图谱可视化生态（@antv/G6）、最成熟的 Markdown 编辑器生态（Tiptap）、以及最高定制自由度的 UI 方案（shadcn/ui）构建。Zustand 提供极简的状态管理，Tauri v2 提供桌面端能力。

这套技术栈的核心优势是**生态完整性**：每一个选型决策都强化了其他决策的合理性。G6 有 React 官方适配器，Tiptap 有 React 官方 hook，shadcn/ui 是 React 原生组件，Zustand 是 React 状态管理库。整个技术栈不存在"需要写胶水代码连接两个不兼容方案"的情况，开发效率和维护成本都是最优解。
