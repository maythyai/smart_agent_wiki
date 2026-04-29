# Smart Agent Wiki — 设计方案

> 集百家之长的下一代智能多代理知识平台

---

## 一、设计哲学

### 核心信念

1. **知识是编译的结果，不是检索的对象** — 继承 Knowledge Pipeline 和 Karpathy 的核心理念
2. **可信是第一公民** — 继承 Multi-Agent Wiki 的完整性治理，没有可信度的知识不如没有知识
3. **人是知识的终审者** — AI 编译、人审核、系统验证，三层信任链
4. **零信息损失** — 继承 MemPalace 的逐字存储信条，原始记录永不丢弃
5. **渐进增强** — 5 分钟可用，5 天有价值，5 个月不可替代

### 与现有项目的本质区别

| 维度 | 现有项目 | Smart Agent Wiki |
|------|---------|-----------------|
| 知识可信度 | 依赖 LLM 自律 | 4 层置信度 + 溯源链 + 矛盾检测 + 密码审计 + 人工审核 |
| 多代理协作 | 无/弱 | 角色化 Agent + A2A 协议 + YAML 工作流 + 签名收据 |
| 规模扩展 | 150 页后索引失效 | 自适应索引 + 分层导航 + 上下文编译 + 结构感知搜索 |
| 隐私 | 云端 API | 本地优先 + 可选 API + 混合部署 + Cedar 策略 + 路径沙箱 |
| 学习能力 | 无 | 训练期自适应 + 间隔重复 + 认知蒸馏 + 知识过期 + 趋势感知 |
| 多端访问 | 单一入口 | CLI + MCP(23工具) + Web + Obsidian 插件 |
| 会话连续性 | 无 | WIP 动量文件 + 渐进记忆深度(L0/L1/L2) |
| 成本控制 | 全量 LLM | 零 LLM 结构化提取 + 19/20 任务纯 bash + 按范围模型路由 |

---

## 二、功能架构

### 2.1 总体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层                              │
│  CLI (Typer)  │  MCP Server  │  Web UI  │  Obsidian 插件  │
└───────┬───────┴──────┬───────┴────┬─────┴──────┬─────────┘
        │              │            │            │
┌───────▼──────────────▼────────────▼────────────▼─────────┐
│                    API 网关层                              │
│    认证 │ 限流 │ 路由 │ 上下文编译 │ 密码审计(Ed25519)     │
└───┬───────┬──────────┬──────────┬──────────┬─────────────┘
    │       │          │          │          │
┌───▼──┐┌───▼───┐┌─────▼────┐┌───▼──────┐┌──▼──────────┐
│摄入  ││查询    ││治理      ││学习      ││协作          │
│Ingest││Query   ││Govern   ││Learn     ││Collaborate  │
│      ││       ││+Cedar   ││+Distill  ││+A2A/YAML    │
└───┬──┘└───┬───┘└────┬─────┘└────┬─────┘└──┬──────────┘
    │       │          │           │         │
┌───▼──────────────────────────────────────────────────────▼─┐
│                  Write Queue (Outbox)                       │
│         持久化写入队列 → 多 Sink 并行分发                     │
└───┬──────────┬──────────┬──────────┬──────────┬────────────┘
    │          │          │          │          │
┌───▼──────┐┌──▼──────┐┌──▼──────┐┌──▼──────┐┌──▼──────┐
│逐字存储   ││主张数据库││知识图谱  ││上下文索引││WIP 动量  │
│(Vault)   ││(Claims) ││(Graph)  ││(Index)  ││(WIP)    │
└──────────┘└─────────┘└─────────┘└─────────┘└─────────┘
┌──────────────────────────────────────────────────────────┐
│                 存储与检索层                                │
│ Markdown/Git │ SQLite │ 向量索引(可选) │ 图数据库          │
└──────────────────────────────────────────────────────────┘
```

### 2.2 五大引擎

#### 引擎一：摄入引擎 (Ingest Engine)

**设计灵感**: Knowledge Pipeline 的编译范式 + MemRAG 的 4 阶段管线 + codesight 的 AST 零 LLM 提取 + Graphify 的 tree-sitter/faster-whisper 实现

**核心流程**:

```
原始输入 → 分类 → 提取 → 融合 → 验证 → 入库
   │        │       │       │       │       │
   │        │       │       │       │       ├─ 逐字存入 Vault (不可变)
   │        │       │       │       │       ├─ 主张写入 Claims DB
   │        │       │       │       │       ├─ 实体/关系更新 Graph
   │        │       │       │       │       └─ 索引自动更新
   │        │       │       │       │
   │        │       │       │       └─ 矛盾检测 + 置信度评估
   │        │       │       └─ 新旧知识融合 (3 策略: Historical/Disputed/Superseded)
   │        │       └─ 多 Agent 并行提取 (Writer + Linker)
   │        └─ 格式识别 + 结构化/非结构化分流
   │            ├─ 结构化(AST/JSON/表格): 零 LLM 提取
   │            │   ├─ 代码: tree-sitter AST 解析 (A.24)
   │            │   └─ JSON/表格: schema 解析
   │            └─ 非结构化(文本/PDF/视频): LLM 提取
   │                └─ 视频: faster-whisper 转录 (A.25)
   └─ PDF/URL/视频/音频/代码/Markdown/Office/Audio
```

**支持的输入源**:
- 文档：PDF, Word, Excel, PPT, Markdown, HTML, EPUB
- 多媒体：视频(faster-whisper 转写), 音频(faster-whisper 转写), 图片(OCR/VLM)
- 在线：URL 抓取, Chrome 剪藏扩展, RSS 订阅, arXiv/GitHub/YouTube 直接摄入 (A.30)
- 对话：Claude Code 会话同步, API 对话转储
- 代码：tree-sitter AST 解析 (A.24), Git 仓库扫描
- 实时：会议转写(Soniox/faster-whisper), 剪贴板监听(OpenWiki 模式)

**关键设计决策**:
- **结构化数据零 LLM 提取**: 代码用 tree-sitter AST (A.24)，JSON/表格用 schema 解析，不浪费 token — 借鉴 codesight + Graphify
- **非结构化数据多 LLM 竞争**: 同一文档由 2 个不同 LLM 独立提取，交叉验证减少幻觉 — 借鉴 Multi-Agent Wiki 的"验证优先于断言"
- **摄入即溯源**: 每条主张追溯到原始文档的精确位置(页码/时间戳/代码行号) — 借鉴 Memex 的 `[^src-*]` 引用和 Agentic Wiki Builder 的 git blame 溯源
- **增量更新优化**: SHA256 文件级缓存，同一文件仅提取一次 (A.27) — 借鉴 Graphify

#### 引擎二：查询引擎 (Query Engine)

**设计灵感**: Knowledge Pipeline 的 BFS 推理链 + ScholarAIO 的分层阅读 + llm_wiki 的 4 信号关联

**查询模式**:

| 模式 | 描述 | 适用场景 |
|------|------|---------|
| **直接检索** | BM25 + 向量混合搜索 | 已知关键词的事实查询 |
| **图谱遍历** | 沿实体关系图 BFS/DFS 探索 | 探索性研究、发现隐含关联 |
| **推理链** | 在概念网络中推理出无直接文档的答案 | 跨领域综合、创新洞察 |
| **对比分析** | 两页/多页内容的相似度与差异 | 观点比较、版本追踪 |
| **综述生成** | 从多源自动生成综述页面 | 文献综述、领域概览 |

**4 信号关联度模型** (借鉴 llm_wiki):
1. 直接链接 (Wikilink)
2. 来源重叠 (共享原始文档)
3. Adamic-Adar 指数 (共同邻居加权)
4. 类型亲和 (同类型实体增强)

**分层输出** (借鉴 ScholarAIO):
- L1: 标题 + 元数据 (扫描用)
- L2: 摘要 (快速理解)
- L3: 结论 + 关键主张 (深度理解)
- L4: 全文 + 原始引用 (完整证据)

**上下文编译** (借鉴 Multi-Agent Wiki):
- 按查询意图自动编译相关 wiki 页面
- Token 预算感知：优先加载高置信度、高相关度内容
- 热缓存机制：高频查询页面预编译 (借鉴 claude-obsidian 的 hot cache)

#### 引擎三：治理引擎 (Govern Engine)

**设计灵感**: Multi-Agent Wiki 的 [APPLE] 欺骗分类学 + Knowledge Pipeline 的矛盾检测 + Memex 的 3 策略冲突处理

**4 层置信度体系**:

```
┌────────────────────────────────────────────┐
│ Layer 4: 人工确认 (Human Verified)          │
│ 人审核通过，最高可信度，金色徽章              │
├────────────────────────────────────────────┤
│ Layer 3: 交叉验证 (Cross-Validated)         │
│ 多 LLM 或多源一致，高可信度，银色徽章        │
├────────────────────────────────────────────┤
│ Layer 2: 单源主张 (Single Source)           │
│ 单一来源，中等可信度，铜色徽章               │
├────────────────────────────────────────────┤
│ Layer 1: 未验证 (Unverified)                │
│ LLM 刚生成，未经任何验证，灰色徽章           │
└────────────────────────────────────────────┘
```

**矛盾检测与处理**:

```
新主张入库
    │
    ▼
与已有主张对比 ──→ 无冲突 ──→ 直接入库
    │
    ▼ 有冲突
矛盾分类
    ├─ 时序性矛盾 (新数据取代旧数据) → Superseded 策略
    ├─ 观点性矛盾 (不同视角)         → Disputed 策略
    └─ 事实性矛盾 (硬性冲突)         → Historical 策略 + 触发人工审核
```

**多代理治理** (借鉴 Multi-Agent Wiki):
- **能力令牌**: 基于文件的 Agent 身份认证和 RBAC 访问控制
- **文件锁**: 签出/锁定机制，TTL 过期自动释放
- **Spark 字段**: 发现矛盾时强制生成候选解决方案
- **二次规则**: 同类问题第二次出现即触发自动化防御

**9 级新鲜度系统** (借鉴 llm-wiki1):
| 级别 | 描述 | 颜色 | 行动 |
|------|------|------|------|
| 0 | 刚创建 | 🟢 绿 | 无需行动 |
| 1 | 1 天内 | 🟢 绿 | 无需行动 |
| 2 | 3 天内 | 🟢 绿 | 无需行动 |
| 3 | 1 周内 | 🟡 黄 | 建议复查 |
| 4 | 2 周内 | 🟡 黄 | 建议复查 |
| 5 | 1 月内 | 🟠 橙 | 需要验证 |
| 6 | 3 月内 | 🟠 橙 | 需要验证 |
| 7 | 半年内 | 🔴 红 | 需要更新 |
| 8 | 超过半年 | 🔴 红 | 强烈建议重写 |

#### 引擎四：学习引擎 (Learn Engine)

**设计灵感**: llm-context-base 的训练期自适应 + llm-wiki1 的 FSRS 间隔重复 + ScholarAIO 的 GPU 自适应 + Graphify 的 Leiden 社区发现 (A.26)

**三大学习机制**:

1. **训练期自适应** (前 30 天)
   - 系统主动学习用户的知识组织偏好
   - 自动发现用户的隐含分类法
   - 逐步从"主动询问"过渡到"安静执行"
   - 用户的修正操作自动转化为未来规则

2. **间隔重复复习** (FSRS 算法)
   - 高新鲜度(7-8 级)的页面自动进入复习队列
   - 复习时触发：重新验证主张 + 更新新鲜度 + 必要时重新编译
   - 复习间隔根据页面类型和重要性动态调整
   - 与治理引擎联动：复习中发现的矛盾自动触发矛盾处理流程

3. **趋势感知 + 社区发现**
   - Leiden 算法发现知识库的自然分组 (A.26)
   - 聚类结果 + FSRS 时间衰减 → 热点社区发现
   - 自动建议创建综述页面 (基于大型社区)
   - 检测知识缺口(高查询但低覆盖的社区)
   - Level 3 降级模式: 无嵌入模型时替代向量聚类

**自适应索引演进** (借鉴 Memex + Graphify):

```
flat (≤50 页)        → 简单列表索引
hierarchical (≤200 页) → 分类树 + 子索引
indexed (>200 页)     → 概念聚类 + 综述路由 + 语义搜索
                       → Leiden 社区发现增强 (A.26)
```

#### 引擎五：协作引擎 (Collaborate Engine)

**设计灵感**: Multi-Agent Wiki 的多代理架构 + DPC Messenger 的 P2P 共享 + llm-wiki1 的 10 Agent 分工

**Agent 角色**:

| 角色 | 职责 | 模型建议 |
|------|------|---------|
| **Librarian** | 索引维护、分类、搜索优化 | Haiku (高频低成本) |
| **Writer** | 页面创作、摘要生成 | Sonnet (质量与成本平衡) |
| **Critic** | 矛盾检测、质量审核 | Sonnet (需理解力) |
| **Linker** | 交叉链接发现、图谱维护 | Haiku (模式匹配) |
| **Scholar** | 深度推理、综述生成 | Opus (最高能力) |
| **Guardian** | 安全检查、权限控制 | 规则引擎 (零 LLM) |

**协作模式**:

- **单用户模式**: Guardian(规则) + Librarian(Haiku) + Writer(Sonnet)，日运行成本 < $0.5
- **深度研究模式**: 追加 Scholar(Opus) + Critic(Sonnet)，按需启用
- **团队模式**: 追加能力令牌 + 文件锁 + 冲突解决，支持多人同时操作

---

## 三、知识表示体系

### 3.1 四层存储架构

```
Layer 0: Vault (不可变原始层)
  - 逐字存储原始文档内容
  - Git 版本控制，永不修改
  - 每个文档一个 UUID 目录: vault/{uuid}/
    ├── original.pdf        # 原始文件
    ├── transcript.md       # 转写/提取的文本
    └── meta.yaml           # 元数据(来源、日期、格式)

Layer 1: Claims (主张层)
  - 结构化的知识主张数据库 (SQLite)
  - 每条主张: {id, content, source_uuid, page_loc, confidence, freshness, created, updated}
  - 主张之间可有关联: 支持/反驳/补充/修正

Layer 2: Wiki (可变综合层)
  - Markdown 页面，可被 Agent 修改
  - 每个页面有 YAML frontmatter: type, tags, related, confidence_avg, freshness
  - 页面类型: concept, entity, debate, synthesis, project, howto, reference
  - 内联引用: [^claim:uuid] 指向 Claims 层

Layer 3: Index (索引层)
  - 全文索引: SQLite FTS5
  - 向量索引: 可选 (ChromaDB / LanceDB / FAISS)
  - 图索引: 实体-关系图 (SQLite JSONL)
  - 自适应索引: 随规模自动升级
```

### 3.2 知识溯源链

```
查询回答 → Wiki 页面 [L2] → 主张 [L1] → 原始文档 [L0]
           ↑                  ↑              ↑
         可变综合           结构化断言       不可变证据
```

每一条回答都可以追溯到原始文档的具体位置，且原始文档永不被修改。

---

## 四、技术架构

### 4.1 技术选型

| 层次 | 技术 | 选择理由 |
|------|------|---------|
| **核心语言** | Python 3.11+ | 生态最丰富、AI 库最全 |
| **CLI 框架** | Typer | 类型安全、自动文档、异步支持 |
| **Web 框架** | FastAPI | 异步、自动 OpenAPI、WebSocket |
| **数据库** | SQLite (默认) / PostgreSQL (团队) | 单用户零配置 / 团队级并发 |
| **向量存储** | 可选: LanceDB(本地) / ChromaDB / FAISS | 渐进增强，本地优先 |
| **全文搜索** | SQLite FTS5 | 零依赖，内建 |
| **知识图谱** | SQLite + NetworkX | 轻量图存储 + 复杂图算法 |
| **PDF 解析** | MinerU(优先) → Docling → PyMuPDF | 多级降级保证成功率 |
| **LLM 路由** | LiteLLM | 统一接口，100+ 模型支持 |
| **嵌入模型** | 本地优先: all-MiniLM-L6-v2 (80MB) | 零 API、隐私安全 |
| **MCP 协议** | FastMCP | 标准 MCP 服务器实现 |
| **前端** | React + Cytoscape.js + Milkdown | 图谱可视化 + WYSIWYG 编辑 |
| **桌面应用** | Tauri v2 (可选) | 跨平台、轻量、Rust 安全 |
| **版本控制** | Git | 审计追踪 + 协作基础 |
| **配置** | YAML + CLAUDE.md 兼容 | 与现有生态无缝对接 |
| **测试** | pytest + 2368+ 测试目标 (参考 llm-wiki) | 质量保障 |

### 4.2 部署模式

```
模式 A: 纯本地 (最简)
  ┌─────────────────┐
  │  Smart Agent Wiki│
  │  CLI + 本地 LLM  │
  │  SQLite + FTS5   │
  │  Git 版本控制     │
  └─────────────────┘
  依赖: Python 3.11 + Ollama(可选)
  安装: pip install smart-agent-wiki && saw init

模式 B: 本地 + 云 LLM (推荐)
  ┌─────────────────┐     ┌──────────┐
  │  Smart Agent Wiki│────→│ LLM API  │
  │  CLI + MCP + Web │     │(Claude/  │
  │  SQLite + 向量    │     │ GPT/Gemini)│
  │  Git 版本控制     │     └──────────┘
  └─────────────────┘
  依赖: Python 3.11 + LLM API Key
  安装: pip install smart-agent-wiki && saw init --api

模式 C: 团队部署
  ┌─────────────────┐     ┌──────────┐
  │  Smart Agent Wiki│────→│ LLM API  │
  │  CLI + MCP + Web │     └──────────┘
  │  PostgreSQL +    │     ┌──────────┐
  │  ChromaDB +      │────→│ 对象存储  │
  │  Redis 缓存      │     │ (S3/MinIO)│
  └─────────────────┘     └──────────┘
  依赖: Docker Compose
  安装: docker compose up
```

### 4.3 MCP 工具清单

| 工具 | 描述 | 对应引擎 |
|------|------|---------|
| `saw_ingest` | 摄入文档/URL/对话 | 摄入引擎 |
| `saw_query` | 查询知识库 | 查询引擎 |
| `saw_search` | 关键词/语义搜索 | 查询引擎 |
| `saw_tree_search` | 结构感知搜索(Tree Mode) | 查询引擎 |
| `saw_graph` | 查询知识图谱 | 查询引擎 |
| `saw_compare` | 对比两个页面 | 查询引擎 |
| `saw_lint` | 健康检查 | 治理引擎 |
| `saw_conflicts` | 列出矛盾/冲突 | 治理引擎 |
| `saw_verify` | 验证特定主张 | 治理引擎 |
| `saw_freshness` | 新鲜度报告 | 治理引擎 |
| `saw_review` | 触发人工审核 | 治理引擎 |
| `saw_audit` | 验证 Ed25519 收据链完整性 | 治理引擎 |
| `saw_schema_validate` | 知识库结构验证 | 治理引擎 |
| `saw_prune` | 触发知识过期/修剪 | 学习引擎 |
| `saw_status` | 知识库状态概览 | 学习引擎 |
| `saw_learn` | 触发学习/适应 | 学习引擎 |
| `saw_distill` | 触发认知蒸馏/SOP 提取 | 学习引擎 |
| `saw_suggest` | 获取改进建议 | 学习引擎 |
| `saw_wip` | 读取/更新跨会话工作动量 | 学习引擎 |
| `saw_compile` | 编译上下文 | 查询引擎 |
| `saw_workflow` | 执行 YAML 定义的工作流 | 协作引擎 |
| `saw_blast_radius` | 查看修改影响范围 | 治理引擎 |
| `saw_feedback` | 提交正/负行为强化模式 | 学习引擎 |

---

## 五、核心工作流

### 5.1 摄入工作流

```
用户: saw ingest research_paper.pdf

1. [分类] 识别为 PDF 学术论文
2. [解析] MinerU → 结构化文本(保留公式/图表/布局)
3. [提取] 并行:
   ├── Librarian(Haiku): 提取元数据(标题/作者/日期/关键词)
   ├── Writer(Sonnet): 提取实体、概念、主张
   └── Linker(Haiku): 发现与已有wiki的关联
4. [融合] 合并提取结果
   ├── 新主张 → 写入 Claims DB
   ├── 已有主张 → 对比，触发矛盾检测
   └── 新实体 → 创建 Wiki 页面草稿
5. [验证] Critic(Sonnet) 审核草稿
   ├── 检查与原始文档的一致性
   ├── 检查与已有知识的矛盾
   └── 评估置信度
6. [入库] 全部写入
   ├── Vault: 原始 PDF + 转写文本
   ├── Claims: 结构化主张
   ├── Wiki: 综合页面(标注置信度)
   ├── Graph: 实体关系更新
   └── Git: 自动 commit
7. [通知] 报告: 摄入 N 个新主张, M 个新实体, K 个矛盾, 耗时/费用
```

### 5.2 查询工作流

```
用户: saw query "为什么 Transformer 取代了 RNN？"

1. [意图] 识别为"原因解释"类查询
2. [编译] 上下文编译
   ├── 从 Index 找到相关页面: Transformer, RNN, Seq2Seq
   ├── Token 预算内加载 L2-L3 内容
   └── 高置信度内容优先
3. [推理] Scholar(Opus) 基于编译上下文回答
   ├── 引用 wiki 页面 [^wiki:transformer]
   ├── 引用具体主张 [^claim:uuid]
   └── 标注未验证部分
4. [输出] 分层回答
   ├── L2: 一句话摘要
   ├── L3: 详细解释 + 证据链
   └── L4: 完整引用 + 原始文档链接
5. [学习] 记录查询模式，更新热缓存
```

### 5.3 治理工作流

```
定时触发: saw lint --full

1. [新鲜度] 扫描所有页面新鲜度
   ├── 级别 7-8: 加入复习队列
   └── 级别 5-6: 标记为需验证
2. [矛盾] 检测跨源声明冲突
   ├── 事实性矛盾 → 触发人工审核
   ├── 观点性矛盾 → 标记为 Disputed
   └── 时序性矛盾 → 自动 Superseded
3. [完整性] 检查
   ├── 孤立页面(无入站链接)
   ├── 断链(指向不存在的页面)
   ├── 缺失元数据
   └── 空页面(有链接但无内容)
4. [索引] 自适应索引升级检查
   ├── 页面数 > 50 → 建议升级到 hierarchical
   └── 页面数 > 200 → 建议升级到 indexed
5. [报告] 输出健康报告
   └── 矛盾数、孤立页面、平均新鲜度、置信度分布
```

---

## 六、差异化竞争优势

### 与每个第一梯队项目的对比

| 我比它更好的地方 | 对比项目 |
|----------------|---------|
| **4 层置信度 + 人工审核** vs 无置信度体系 | claude-obsidian, OpenWiki, llm-wiki |
| **跨平台 (CLI+MCP+Web+Obsidian)** vs 单一入口 | OpenWiki (macOS only), claude-obsidian (Claude Code only) |
| **矛盾检测 + 3 策略处理** vs 无/弱矛盾检测 | llm-wiki, llm_wiki(nashsu), llm-wiki-agent |
| **学习引擎 (训练期+间隔重复)** vs 无学习能力 | 全部现有项目 |
| **结构化零 LLM 提取** vs 全量 LLM 处理 | Knowledge Pipeline, Memex |
| **多模型路由 + 本地优先** vs 单一 LLM 锁定 | MemRAG (Gemini only), Memex (Claude only) |
| **逐字存储 + 主张数据库双轨** vs 单一表示 | 几乎所有项目 |
| **自适应索引升级** vs 固定索引 | Memex (有但单一) |
| **Blast Radius 修改影响分析** vs 无 | codesight 之外的所有项目 |
| **部署渐进增强** vs 单一部署模式 | MemRAG (仅 AWS), Memex (仅本地) |
| **认知蒸馏 + SOP 自动提取** vs 无行为学习 | MindOS (有Echo但无SOP闭环) |
| **密码学审计 (Ed25519 + Cedar)** vs 无审计 | scopeblind-gateway (有但仅做安全) |
| **知识过期修剪** vs 永久保留一切 | unified-memory-ai-agents (有但无分层) |
| **结构感知搜索 (Tree Mode)** vs 纯 BM25 | TreeSearch (有但仅做搜索) |
| **跨会话工作动量 (WIP)** vs 无会话连续性 | unified-memory-ai-agents (有但单功能) |
| **YAML 工作流编排** vs 硬编码流程 | MindOS (有但不可编程) |
| **三层认知记忆映射** vs 扁平存储 | unified-memory-ai-agents (有但未整合到wiki) |

### 独有的创新特性

1. **4 层置信度体系** — 现有项目没有任何一个实现完整的置信度分层
2. **学习引擎** — 训练期自适应 + 间隔重复 + 趋势感知 + 认知蒸馏的四位一体
3. **结构化零 LLM 提取** — 在 LLM Wiki 领域首次引入 codesight 的 AST 理念
4. **4 层存储架构** — Vault→Claims→Wiki→Index，兼顾溯源与可用性
5. **矛盾检测 + 3 策略自动处理** — 从检测到解决的完整闭环
6. **多 Agent 角色化协作** — 按需调度不同模型，成本可控
7. **密码学治理层** — Ed25519 签名 + Cedar 策略 + CVE 策略包 (scopeblind 启发)
8. **认知记忆分层** — 三层认知模型 + 渐进深度 + WIP 动量保持 (unified-memory 启发)
9. **多 Sink 持久化写入** — 单入口 → outbox → 多 sink 并行分发 (ContextLattice 启发)
10. **知识全生命周期管理** — 从摄入到过期修剪的完整生命周期 (unified-memory 启发)

---

## 七、路线图

### Phase 1: 核心基座 (6 周)
- Vault 存储 + Claims 数据库
- 摄入引擎 (PDF/Markdown/URL)
- 查询引擎 (BM25 + FTS5 + Tree Mode)
- CLI 命令: init, ingest, query, lint
- Git 版本控制集成
- Write Queue (Outbox) + 多 Sink 架构
- WIP 跨会话动量文件
- **里程碑**: 5 分钟内创建第一个 wiki 并摄入查询

### Phase 2: 智能增强 (4 周)
- 治理引擎: 矛盾检测 + 置信度体系 + 密码审计(Ed25519)
- 治理引擎: Cedar 策略引擎 + CVE 策略包
- 学习引擎: 训练期自适应 + 认知蒸馏(Echo)
- 学习引擎: 知识过期修剪 + 双反馈强化
- Schema 治理系统 (infer/validate/diff)
- MCP Server (23 个工具)
- 多 LLM 支持 (LiteLLM) + 按范围模型路由
- **里程碑**: 知识库达到 200 页仍可高效查询

### Phase 3: 协作进化 (4 周)
- 多 Agent 角色化协作 + A2A 协议
- YAML 工作流编排引擎
- 知识图谱可视化
- 间隔重复复习系统(FSRS)
- Chrome 剪藏扩展
- 向量搜索 (可选)
- Web UI (React + Cytoscape.js)
- **里程碑**: 多人协作场景验证

### Phase 4: 生态完善 (持续)
- Obsidian 插件
- Tauri 桌面应用
- 视频转写 + 会议记录
- P2P 知识共享
- 团队部署模式 (Docker Compose + PostgreSQL)
- API 开放平台
- 多语言支持 (EN/中文/日本語, 借鉴 llmbase)
- OWL-RL 本体推理 (借鉴 Venn)

---

## 八、成功指标

| 指标 | 目标 | 衡量方式 |
|------|------|---------|
| 5 分钟上手 | init → ingest → query < 5 分钟 | 计时测试 |
| 日运行成本 | 单用户 < $0.5/天 | LLM API 费用统计 |
| 矛盾检出率 | > 90% | 人工标注测试集 |
| 查询准确率 | L3 回答 > 85% 准确 | 对照原始文档验证 |
| 规模扩展 | 1000 页查询 < 3 秒 | 性能基准测试 |
| 用户留存 | 7 天留存 > 60% | 使用统计 |
| 认知蒸馏质量 | SOP 提取准确率 > 80% | 用户反馈验证 |
| 知识修剪准确性 | 战略/战术分类准确率 > 85% | 人工审核样本 |
| 多 Sink 写入可靠性 | Outbox 持久化率 > 99.9% | Sink 同步率监控 |
| 密码审计覆盖度 | > 95% 操作有签名收据 | 收据链完整性检查 |
| 跨会话恢复成功率 | WIP 动量恢复 > 90% | 会话接续测试 |
| 降级搜索质量 | Level 2 相对 Level 1 > 75% MRR | 对照基准测试 |

---

## 附录 A：从 Group 1 分析中补充的关键设计决策

### A.1 拒绝反馈循环 (借鉴 obsidian-llm-wiki-local)

**核心机制**: 用户拒绝草稿时，必须说明原因。原因被注入到下次编译的上下文中，逐步提高自动生成质量。5 次拒绝后自动阻塞该页面，等待人工处理。

**在 Smart Agent Wiki 中的实现**:
- Writer Agent 生成的草稿进入"待审核"状态
- 用户可 Approve / Reject(附原因) / Edit
- 拒绝原因写入 `.feedback/{page_id}.yaml`，下次编译自动注入
- 手动编辑后的页面获得"人工编辑保护"标记，后续编译跳过

### A.2 三层优雅降级 (借鉴 agentic-local-brain)

**降级策略**:

```
Level 1: 全功能模式 (有 LLM API + 有嵌入模型)
  → 完整摄入、语义搜索、矛盾检测、综述生成

Level 2: 轻量模式 (有 LLM API + 无嵌入模型)
  → 完整摄入、BM25 搜索、矛盾检测(无语义)
  → 自动降级：向量搜索不可用时用 BM25 替代

Level 3: 离线模式 (无 LLM API + 无嵌入模型)
  → BM25 搜索、手动摄入、结构化 Lint(零 LLM)
  → TF-IDF 抽取式摘要替代 LLM 摘要
```

**设计原则**: 系统在任何降级级别都必须可用，只是精度和自动化程度不同。这保证了即使在无网络环境下，知识库也不会变成"只读废墟"。

### A.3 16+ 代理兼容层 (借鉴 obsidian-wiki)

**设计目标**: 同一个知识库可被 Claude Code、Cursor、Copilot、Codex、Gemini CLI、Windsurf、Cline 等所有主流 AI 编码代理操作。

**实现方式**:
- 核心逻辑在 CLI/MCP 层，不绑定任何特定代理
- 每个代理只需一个配置文件(CLAUDE.md / .cursorrules / AGENTS.md / GEMINI.md)
- `saw init --agent <name>` 自动生成对应代理的配置文件
- 所有配置文件引用同一套核心指令，避免分歧
- 代理特定的行为通过 `agents/<name>.yaml` 覆盖

### A.4 来源可信度三级标记 (借鉴 obsidian-wiki)

每条主张标注来源可信度：
- **extracted** — 从原始文档直接提取，最高可信
- **inferred** — LLM 从上下文推断，中等可信
- **ambiguous** — 含糊或有争议，最低可信，需人工确认

这比我之前设计的 4 层置信度更精细——4 层置信度是页面级别，三级标记是主张级别，两者正交组合。

### A.5 Research-on-Miss 自动研究闭环 (借鉴 llm-wiki1)

**核心机制**: 当查询引擎无法从现有知识库中找到满意答案时，自动触发多渠道并行研究，然后将研究结果写回知识库。

**在查询工作流中的补充**:

```
用户: saw query "XXX?"

1. [编译] 上下文编译 → 相关页面
2. [评估] 知识覆盖率评估
   ├── 覆盖率 ≥ 阈值 → 正常回答
   └── 覆盖率 < 阈值 → 触发 Research-on-Miss
3. [研究] Research-on-Miss 流程 (可选，需用户确认)
   ├── Web 搜索 (Tavily/Serper)
   ├── 学术搜索 (Semantic Scholar/arXiv)
   └── 代码搜索 (GitHub)
4. [整合] 研究结果自动摄入 → 更新知识库
5. [回答] 基于增强后的知识库回答
```

这使知识库形成**查询→缺口发现→自动研究→知识增长→更好回答**的正反馈闭环。

### A.6 模型安全切换顾问 (借鉴 obsidian-llm-wiki-local)

**核心功能**: `saw compare` 命令在隔离环境中对比不同 LLM 模型处理相同笔记的效果，用用户自己的知识库作为基准测试数据集。

**工作流**:
1. 选择要对比的两个模型 (如 Sonnet vs Gemini)
2. 从知识库中抽取 10 个代表性页面作为测试集
3. 在隔离分支中分别用两个模型重新编译
4. 对比: 准确性、遗漏信息、幻觉率、Token 消耗
5. 输出对比报告 + 切换建议

### A.7 关于设计矛盾的澄清

**逐字存储 vs 主张提取的矛盾**:
- Vault 层存储逐字原文（零损失），Claims 层存储提取的主张（有损但有结构）
- 两者**不互斥**：Vault 是证据，Claims 是索引，回答问题时两者结合使用
- 回答中的每个主张都通过 `[^claim:uuid]` 链接到 Claims，Claims 又通过 `source_uuid` 链接到 Vault 中的逐字原文

**来源三级标记 × 4 层置信度的交互**:
- 来源标记(主张级): extracted/inferred/ambiguous — 描述"这条主张是怎么来的"
- 置信度(页面级): Layer 1-4 — 描述"这个页面的整体可信度"
- 页面置信度 = 聚合其所有主张的来源标记: 全 extracted → Layer 3，含 inferred → Layer 2，含 ambiguous → Layer 1，人工审核通过 → Layer 4

### A.8 5 分钟上手承诺的修正

**Phase 1 实际安装体验**:

```bash
# 最简安装 (无本地 LLM)
pip install smart-agent-wiki
saw init                        # 创建空 wiki，配置 LLM API Key
saw ingest ~/paper.pdf          # 摄入第一个文档
saw query "论文核心观点是什么"   # 查询

# 离线安装 (有本地 LLM)
pip install smart-agent-wiki[local]
saw init --local                # 自动下载嵌入模型 (~80MB)
saw ingest ~/paper.pdf
saw query "论文核心观点是什么"
```

**5 分钟承诺仅适用于 "最简安装" 模式**（需要 LLM API Key）。离线模式因需下载模型，首次约需 10-15 分钟。

### A.9 路线图修正

Phase 1 从 4 周调整为 6 周，聚焦最小可行产品：

- **Week 1-2**: Vault 存储 + SQLite Claims DB + Git 集成
- **Week 3-4**: 摄入引擎 (PDF/Markdown/URL) + BM25 搜索
- **Week 5-6**: CLI (init/ingest/query/lint) + 基础 Web UI + MCP Server

### A.10 认知蒸馏与 SOP 提取 (借鉴 MindOS)

**核心机制**: Echo 认知蒸馏 — 从每次用户交互中自动提取修正、偏好和行为模式，转化为可复用的标准操作流程(SOP)。

**在 Smart Agent Wiki 中的实现**:
- 每次查询后的用户反馈（接受/拒绝/修改）自动进入 `distill/` 目录
- Echo Agent 定期扫描反馈，提取重复模式，生成 `sops/{category}.yaml`
- SOP 作为未来 Writer/Critic Agent 的上下文注入，逐步提高自动生成质量
- 与 A.1 的拒绝反馈循环互补：A.1 是页面级反馈，A.10 是跨页面行为模式学习

### A.11 三层认知记忆架构 (借鉴 unified-memory-ai-agents)

**设计灵感**: 潜意识(Subconscious) → 意识(Conscious) → 持久(Persistent) 三层认知模型

**映射到 Smart Agent Wiki 四层存储**:

| 认知层 | Smart Agent Wiki 对应 | 特点 |
|--------|----------------------|------|
| 潜意识 | Vault (L0) | 自动捕获，无需意识参与 |
| 意识 | Claims (L1) + Wiki (L2) | 策展工作空间，结构化断言 |
| 持久 | Index (L3) + SOPs | 行为身份文件，长期模式 |

**渐进式记忆深度 (L0/L1/L2)** — 借鉴 unified-memory-ai-agents:
- L0: 始终加载的索引 (~85 行) — wiki 的 TABLE OF CONTENTS
- L1: 摘要索引，列出最近 ~15 个主题 — 快速上下文
- L2: 完整内容，按需加载 — 深度查询时触发
- **目标**: 将 boot tokens 从 ~20K 降至 ~8-10K，同时保持对所有知识的感知

### A.12 知识过期与自动修剪 (借鉴 unified-memory-ai-agents)

**核心机制**: 知识有生命周期，不是所有知识都应永久保留。

**在治理引擎中的补充**:

```
知识生命周期:
├── 战术性知识 (⏳): 自动过期，30 天后降级
│   → 如临时工作流、短期任务状态、WIP 文件
│   → 与 9 级新鲜度系统联动：新鲜度 7-8 + 战术标记 → 自动归档
│
├── 战略性知识 (🔒): 永久保留
│   → 如核心概念、验证过的主张、人工审核页面
│   → 过期修剪器跳过此类知识
│
└── 过期修剪规则:
    ├── 战术 → 战略 去重: 60% 词重叠则删除战术版本
    ├── WIP 文件: 每次自动编译覆盖，只保留最新状态
    └── 健康检查: 零 token 检测 6 类不一致(矛盾/重复/过期/缺索引/WIP过期/膨胀)
```

### A.13 结构感知零向量搜索 (借鉴 TreeSearch)

**核心创新**: TreeSearch 证明了结构感知的 FTS5 搜索可以**无需向量嵌入**达到接近语义搜索的效果（QASPER MRR 0.50），且毫秒级延迟。

**在查询引擎中的补充**:
- **Tree Mode**: 对学术论文、技术文档等层级结构内容，使用 anchor retrieval → tree walk → path aggregation
- **Flat Mode**: 对代码、关键词密集查询，使用传统 FTS5
- **Auto Mode**: 三层智能选择（类型映射 + 深度验证 + 比例阈值）
- **价值**: 在 Level 2/3 降级模式下（无嵌入模型），Tree Mode 可提供比纯 BM25 更好的搜索质量
- **与现有设计的关系**: 作为查询引擎第 5 种查询模式 "结构感知搜索" 的补充

### A.14 多 Sink 持久化写入架构 (借鉴 ContextLattice)

**核心机制**: 单一写入入口 `/memory/write` → 持久化 outbox → 多个专用 sink 并行分发。

**在 Smart Agent Wiki 中的映射**:

```
当前设计:
  摄入引擎 → Vault + Claims + Wiki + Graph + Index (直接写入)

增强为:
  摄入引擎 → Write Queue (outbox)
    ├── Sink 1: Vault Storage (原始文档持久化)
    ├── Sink 2: Claims DB (结构化主张)
    ├── Sink 3: Wiki Pages (可变综合层)
    ├── Sink 4: Graph Index (实体关系)
    ├── Sink 5: FTS5 Index (全文搜索)
    └── Sink 6: Vector Index (可选，语义搜索)
```

**关键优势**:
- **持久性**: outbox 机制确保写入不丢失，即使某个 sink 暂时不可用
- **检索学习循环**: 从多源召回合并结果，通过反馈循环改善排名
- **运行时锁定**: 严格的运行时配置锁定，防止重启间调优漂移

### A.15 密码审计与策略治理 (借鉴 scopeblind-gateway)

**核心机制**: Ed25519 签名收据 + Cedar 策略引擎，为多 Agent 环境提供密码学级别的操作审计。

**在 Smart Agent Wiki 治理引擎中的补充**:

```
操作审计层:
├── 签名收据: 每个 Agent 操作生成 Ed25519 签名收据
│   → 收据包含: agent_id, operation, target, timestamp, signature
│   → 离线可验证：无需服务器即可验证收据链完整性
│
├── 策略引擎: 基于 Cedar 的 Agent 访问控制
│   → permit/forbid 规则按工具粒度定义
│   → 例: "permit(Librarian, saw_ingest) when confidence >= 2"
│   → 例: "forbid(Writer, saw_verify) — Writer 不能自行验证"
│
├── 攻击防御策略包:
│   → CVE 锚定的策略模板，防御已知的 Agent 攻击模式
│   → 借鉴 [APPLE] 欺骗分类学 + 二次规则自动防御
│
└── Swarms 拓扑追踪:
    → 11 个 hook 事件追踪 Agent 拓扑变化
    → 可视化 Agent 调用链 (Receipt DAG)
```

### A.16 跨会话工作动量保持 (借鉴 unified-memory-ai-agents)

**核心机制**: WIP (Work-in-Progress) 文件 — 捕获会话间的"工作动量"，而不仅仅是知识制品。

**在 Smart Agent Wiki 中的实现**:

```yaml
# .saw/wip.yaml — 每次自动编译更新
active_tasks:
  - task: "正在分析 Transformer vs RNN 的论文对比"
    status: "进行中"
    next_step: "需要提取 RNN 系列论文的核心主张"
    context_pages: ["transformer", "rnn", "seq2seq"]
    started: "2026-04-25T10:00:00Z"

pending_questions:
  - question: "用户对知识图谱可视化的偏好还需确认"
    priority: medium
    asked_count: 0
```

**设计价值**: 大多数知识系统忽略"会话之间发生了什么"。WIP 文件确保下次启动时，系统能无缝恢复工作上下文。

### A.17 YAML 工作流编排 (借鉴 MindOS)

**核心机制**: 用 YAML 定义多步 Agent 工作流，可视化编辑，步骤执行引擎。

**在 Smart Agent Wiki 协作引擎中的补充**:

```yaml
# workflows/literature_review.yaml
name: 文献综述生成
steps:
  - agent: Librarian
    action: search
    input: "{{ query }}"
    output: related_pages

  - agent: Scholar
    action: synthesize
    input: related_pages
    output: draft_synthesis

  - agent: Critic
    action: review
    input: draft_synthesis
    gates:
      - confidence >= 3
      - contradiction_count == 0

  - agent: Writer
    action: publish
    input: reviewed_synthesis
    output: wiki_page
```

**价值**: 用户无需编程即可定义复杂的知识工作流，降低使用门槛。

### A.18 双反馈文件行为强化 (借鉴 unified-memory-ai-agents)

**核心机制**: approved.json + rejected.json 作为正负行为强化信号。

**与 A.1 拒绝反馈循环的整合**:

```
现有: .feedback/{page_id}.yaml — 页面级反馈
新增: .saw/reinforcement/
  ├── approved.yaml — 正面行为模式 (应重复)
  │   → 例: "用户喜欢表格形式的对比摘要"
  │   → 例: "用户偏好中文回答，英文技术术语保留"
  │
  └── rejected.yaml — 负面行为模式 (应避免)
      → 例: "用户不喜欢过长的引用链"
      → 例: "用户拒绝没有来源标记的回答"

注入时机:
  → 每次 Writer/Scholar Agent 调用时自动注入到 system prompt
  → 与 Echo 认知蒸馏(A.10)联动：approved/rejected 自动提炼为 SOP
```

---

## 附录 B：181 项目审计总结

### B.1 审计范围

- **本地深度分析**: 25 个项目（完整代码审查）
- **远程 README 审计**: ~40 个项目（WebFetch/WebReader）
- **项目页面扫描**: ~60 个项目（快速分类）
- **判定为 SKIP**: ~56 个项目（模板/fork/最小实现）

### B.2 独特特性来源矩阵

| 设计特性 | 来源项目数 | 主要来源 |
|----------|-----------|---------|
| 4 层置信度体系 | 0 (原创) | Smart Agent Wiki 原创 |
| 矛盾检测 + 3 策略处理 | 3 | Knowledge Pipeline, Venn, Memex |
| 训练期自适应 + 间隔重复 | 2 | llm-wiki1(FSRS), llm-context-base |
| 零 LLM 结构化提取 | 3 | codesight(AST), TreeSearch(FTS5), basic-memory(schema) |
| 多 Agent 角色化协作 | 4 | llm-wiki1(10 Agent), MindOS(A2A), Thinking-Space(55+ ops), tracecraft(S3) |
| 密码学审计 | 1 | scopeblind-gateway(Ed25519 + Cedar) |
| 认知蒸馏/SOP 提取 | 2 | MindOS(Echo), unified-memory-ai-agents(auto-precompact) |
| 渐进式记忆深度 | 2 | unified-memory-ai-agents(L0/L1/L2), AI-Context-OS |
| 知识过期修剪 | 1 | unified-memory-ai-agents(expiring lessons) |
| 跨会话动量保持 | 1 | unified-memory-ai-agents(WIP file) |
| 多 Sink 持久化 | 2 | ContextLattice(fanout), tracecraft(S3 coordination) |
| 双反馈行为强化 | 1 | unified-memory-ai-agents(approved/rejected) |
| YAML 工作流编排 | 1 | MindOS |
| 三层认知记忆 | 1 | unified-memory-ai-agents |
| OWL-RL 本体推理 | 1 | Venn |
| 三语默认 | 1 | llmbase |
| 自修改应用架构 | 1 | Thinking-Space |
| Schema 治理系统 | 1 | basic-memory |
| 温度分层检索 (hot/warm/glacier) | 1 | Cog |
| 类型化 Wiki 记录 | 1 | blink-query |
| 零 RAG 纯 Git+BM25 | 1 | sp-context |
| 反债务框架 | 1 | Compound Engineering Plugin |
| 跨模型持久记忆 | 1 | omega-memory |
| Git blame 溯源 | 1 | Agentic Wiki Builder |
| 虚拟文件系统 | 1 | grover/vfs |

### A.19 温度分层检索 (借鉴 Cog)

**核心机制**: hot/warm/glacier 三层温度检索 — 基于人类记忆显著性的分层，而非扁平化处理所有信息。

**与渐进式记忆深度 (L0/L1/L2) 的关系**:
- A.11 的 L0/L1/L2 是**加载深度**（决定加载多少内容）
- A.19 的 hot/warm/glacier 是**存储温度**（决定存储位置和检索优先级）
- 两者正交：L0 可以包含 hot 和 warm 的摘要

**在治理引擎中的实现**:
```
温度分层规则:
├── hot (<50 行): 始终加载的核心理念、常用决策、高频查询页面
│   → 自动复制到 boot sequence 的 L0 层
│   → 每周自动压缩，保持 <50 行约束
│
├── warm: 近期活跃的页面、中等频次访问
│   → L1 层自动索引，按需加载
│   → 30 天无访问自动降级为 glacier
│
└── glacier: 归档的历史记录、低频访问的原始文档
    → 仅 L2 全内容加载时检索
    → 冷存储，节省加载带宽
```

### A.20 类型化 Wiki 记录 (借鉴 blink-query)

**核心机制**: 5 种类型化记录 + namespace 组织 — 让 wiki 页面有明确的消费指令，而非无类型的 Markdown。

**在 Wiki 层 (L2) 的实现**:
```
Wiki 页面 YAML frontmatter 增加 record_type 字段:

record_types:
├── SUMMARY: 一页摘要，快速上下文注入 (阅读指令: "先读摘要")
├── META: 结构化元数据 JSON (阅读指令: "解析 JSON 字段")
├── SOURCE: 原始文档链接 + 引用 (阅读指令: "获取原始证据")
├── ALIAS: 重定向/别名页面 (阅读指令: "跟随指向目标页面")
└── COLLECTION: 子页面集合 (阅读指令: "浏览子页面列表")

namespaces:
├── wiki/concepts/ → 概念类页面
├── decisions/ → 决策记录
├── people/ → 人物档案
├── sources/ → 原始文档
└── collections/ → 资料集
```

**价值**: Agent 不需猜测页面用途，阅读指令明确编码在类型中。

### A.21 零 RAG 纯 Git+BM25 模式 (借鉴 sp-context)

**核心机制**: 证明 114 tokens/session 的 catalog + Git + BM25 可替代向量 RAG。

**在 Level 3 降级模式中的应用**:
```
Level 3 离线模式增强:
├── 当前设计: BM25 搜索 + TF-IDF 摘要
├── 新增: Catalog 模式 — 极简 100 tokens 目录始终加载
│   → catalog.yaml: 所有页面的 title + type + tags + status
│   → Agent 先扫描 catalog，BM25 检索命中页面，再加载 L1
│   → 证明: 不需要嵌入模型也能有接近语义搜索的效果
│
└── 与 Tree Mode (A.13) 结合: 结构感知 + 目录导航 → 无向量高效检索
```

**证据**: sp-context 实现了 Git repo + BM25 + ~100 tokens/session 的跨 Agent 持久记忆。

### A.22 反债务框架与复利工程 (借鉴 Compound Engineering Plugin)

**核心机制**: "每个工程单元应让后续单元更容易，而非更难" — anti-debt philosophy。

**在学习引擎中的补充**:
```
复利工程规则:
├── 每次摄入后检查: 这是否为未来摄入创造了模板/模式？
│   → 是 → 提取为 SOP (A.10 认知蒸馏)
│   → 否 → 标记为"孤立摄入"，需人工审查
│
├── 每次查询后检查: 这是否减少了未来查询成本？
│   → 是 → 创建 shortcut/alias 页面
│   → 否 → 标记为"一次性查询"
│
└── Debt 检测: 定期扫描"孤立摄入"和"一次性查询"比例
    → 比例 > 30% → 触发治理引擎的整合建议
```

**与 Research-on-Miss (A.5) 的关系**: A.5 解决查询失败，A.22 解决知识不增值。

### A.23 Git Blame 溯源链 (借鉴 Agentic Wiki Builder)

**核心机制**: 每次摄入在独立分支处理，合并后通过 git blame 追踪原始数据动机。

**在摄入引擎中的增强**:
```
当前设计: Claims DB 中每条主张有 source_uuid
增强为:
├── 每次摄入创建 session branch: session/{timestamp}-{source_name}
├── Agent 在 session branch 上工作，更新 Wiki
├── 完成后 merge 到 main → git commit 保留 session 信息
└── 双溯源链:
    ├── Claims → Vault (主张到原始文档)
    └── git blame → session branch → raw input file (Wiki 修改到处理会话)
```

**价值**: 比 anchor-style cites 更可靠 — Agent 可能幻觉 anchor，但 git 不会。

---

## 附录 C：Agent 审计结果汇总

本次审计共启动 5 个后台 agent，受 API 429 限流影响，部分未能完成。以下是成功提取的新发现：

| Agent ID | 成功审计项目数 | 新发现 |
|----------|--------------|--------|
| ac9c877a89d6a1faa | ~15 | MindOS, unified-memory, ContextLattice 部分内容 |
| afd4bd9feeeba2484 | ~20 | TreeSearch, silverbullet, ContextLattice, sp-context |
| aed368c7eb00d8d57 | ~25 | omega-memory, Cog, blink-query, Compound Engineering |
| a736b3e4a1af247bd | ~10 | vfs/grover, beyond-token-bottleneck |
| ab7843c05642244c4 | ~5 | grover, Semantica |

**总计**: 从 agent 输出中新增约 15 个项目的独特特性分析。

### B.3 设计完整度自评

| 设计维度 | 覆盖度 | 说明 |
|----------|--------|------|
| 存储架构 | ★★★★★ | 四层存储 + 多 Sink + 三层认知 |
| 查询能力 | ★★★★★ | 5 种查询模式 + Tree Mode + Research-on-Miss |
| 治理体系 | ★★★★★ | 4 层置信度 + 矛盾检测 + 密码审计 + 策略引擎 |
| 学习能力 | ★★★★★ | 训练期 + FSRS + 认知蒸馏 + 趋势感知 + 知识过期 |
| Agent 协作 | ★★★★☆ | 6 角色分工 + A2A + YAML 工作流 + 签名收据 |
| 隐私安全 | ★★★★☆ | 本地优先 + Cedar 策略 + 沙箱 + 写保护 |
| 部署灵活性 | ★★★★★ | 三级降级 + 三种部署模式 + 多代理兼容 |
| 可扩展性 | ★★★★☆ | 自适应索引 + 多 Sink + 插件系统 |
| 用户体验 | ★★★★☆ | 5 分钟上手 + WIP 动量 + Chrome 剪藏 + Web UI |

### A.24 tree-sitter 代码解析实现 (借鉴 Graphify)

**核心机制**: 使用 tree-sitter 作为代码 AST 提取的具体实现，实现零 LLM 结构化提取。

**与现有设计的关系**: 现有摄入引擎已设计"codesight 模式 AST 零 LLM 提取"，tree-sitter 作为其后端实现。

**在摄入引擎中的实现**:

```python
# 代码解析实现
def extract_code_structure(file_path: str) -> dict:
    """
    使用 tree-sitter 提取代码结构 (零 LLM)
    
    返回: {
        "classes": [{name, methods, properties, docstring}],
        "functions": [{name, params, return_type, docstring}],
        "imports": [{module, names}],
        "calls": [{caller, callee}]
    }
    """
    import tree_sitter_languages as tsl
    parser = tsl.get_parser(language)  # 自动识别或指定
    # ... AST 遍历提取
```

**技术选型理由**:
- tree-sitter-languages 支持 25+ 种编程语言
- 纯 Python 调用，与现有技术栈无缝集成
- 性能优异（毫秒级解析）

**依赖**: `pip install tree-sitter-languages` (可选依赖，代码摄入时启用)

### A.25 faster-whisper 视频转录优化 (借鉴 Graphify)

**核心机制**: 使用 faster-whisper 替代标准 Whisper，实现更快的视频音频转录。

**与现有设计的关系**: 现有摄入引擎支持"音频(Whisper 转写)"，faster-whisper 作为加速方案。

**在摄入引擎中的实现**:

```
视频转录流程:
├── yt-dlp 下载视频 (支持 YouTube/Bilibili 等)
├── faster-whisper 本地转录
│   ├── 模型选择: tiny (最快) / base / small (平衡)
│   ├── 实时转录速度: x 0.3 (比标准 Whisper 快 3 倍)
│   └── 输出: segments [{start, end, text}] + full_text
├── 缓存: .saw/cache/transcript/{sha256_hash}/
└── 摄入: 转录文本 → Writer Agent 提取概念和主张
```

**技术选型理由**:
- faster-whisper 基于 CTranslate2，推理速度提升 3-4 倍
- 内存占用更低，适合本地运行
- 与现有 Whisper 方案兼容，可降级

**依赖**: `pip install faster-whisper yt-dlp` (可选依赖)

### A.26 Leiden 社区发现算法 (借鉴 Graphify)

**核心机制**: 基于 Leiden 算法的图拓扑聚类，无需嵌入向量即可实现知识社区发现。

**与现有设计的关系**: 增强学习引擎的"趋势感知"和"知识缺口检测"能力。

**在学习引擎中的实现**:

```python
# 社区发现
def discover_communities(graph: nx.Graph) -> dict[str, int]:
    """
    使用 Leiden 算法发现知识社区
    
    返回: {node_id: community_id}
    """
    from graspologic.partition import leiden
    communities = leiden(graph, resolution=1.0)
    return communities

# 与 FSRS 结合实现热点社区发现
def find_hot_communities(communities, freshness_scores):
    """聚类的社区 + 时间衰减 = 热点社区"""
    # ... 实现
```

**应用场景**:
- Level 3 降级模式: 无嵌入模型时替代向量聚类
- 趋势感知: 发现知识库的自然分组 + 热点社区
- 综述建议: 大型社区触发综述生成建议

**技术选型理由**:
- 已依赖 NetworkX，graspologic 与其无缝集成
- Leiden 算法比 Louvain 更稳定，不会产生任意分割的社区
- 纯 Python 实现，跨平台兼容

**依赖**: `pip install graspologic` (在 NetworkX 基础上扩展)

### A.27 SHA256 文件级缓存 (借鉴 Graphify)

**核心机制**: 在 Write Queue 基础上增加文件级 SHA256 缓存，实现精细化增量更新。

**与现有设计的关系**: 增强 Write Queue (Outbox) 的缓存粒度。

**实现架构**:

```
现有 Write Queue:
  摄入引擎 → Write Queue → 多 Sink 分发

增强为:
  摄入引擎 → SHA256 检查 → Write Queue → 多 Sink 分发
                │
                ├─ 命中: 跳过提取，直接入库
                └─ 未命中: 执行提取，更新缓存

缓存命名空间:
.saw/cache/
  ├── ast/{sha256}/         # AST 提取结果
  ├── transcript/{sha256}/  # 视频转录结果
  └── semantic/{sha256}/    # 语义提取结果
```

**价值**: 同一文件多次摄入时，仅执行一次提取，大幅降低 LLM 调用成本。

### A.28 多代理配置安装器 (借鉴 Graphify)

**核心机制**: 增强 `saw init` 命令，自动生成多代理兼容的配置文件。

**与现有设计的关系**: 实现 A.3 "16+ 代理兼容层"的目标。

**在协作引擎中的实现**:

```bash
# 现有命令
saw init

# 增强为
saw init --agent <name>    # 生成指定代理的配置

# 示例
saw init --agent claude    # 生成 CLAUDE.md
saw init --agent cursor    # 生成 .cursorrules
saw init --agent gemini    # 生成 GEMINI.md
saw init --agent all       # 生成全部支持平台的配置
```

**生成的配置文件内容**:
- 核心指令 (统一，指向共享的 .saw/instructions.md)
- 平台特定配置 (工具映射、上下文格式等)
- skill 定义文件 (如果平台支持)

**技术选型**: 纯 Python 实现，使用 Jinja2 模板生成配置文件。

### A.29 Git 钩子自动摄入 (借鉴 Graphify)

**核心机制**: Git 钩子触发知识库增量更新。

**与现有设计的关系**: 增强摄入引擎的自动化触发机制。

**实现**:

```bash
# 安装钩子
saw hook install

# 生成钩子脚本
.git/hooks/
  ├── pre-commit   # 检测变更文件，触发增量摄入
  └── post-merge   # 合并后触发知识同步
```

**pre-commit 钩子逻辑**:
```bash
#!/bin/bash
# 获取变更文件
changed_files=$(git diff --cached --name-only)
# 计算 SHA256 检测实际变更
# 调用 saw ingest --update <files>
```

**与 A.23 的关系**: A.23 用 git blame 追溯，A.29 用 git hook 自动化，形成闭环。

### A.30 URL/视频直接摄入 (借鉴 Graphify)

**核心机制**: 从 URL 或视频链接直接摄入知识，无需手动下载。

**与现有设计的关系**: 扩展摄入引擎的输入源。

**实现**:

```bash
# arXiv 论文
saw ingest https://arxiv.org/abs/1706.03762
# → 自动下载 PDF → MinerU 解析 → 摄入

# YouTube 视频
saw ingest https://youtube.com/watch?v=XXX
# → yt-dlp 下载 → faster-whisper 转录 → 摄入

# GitHub 仓库
saw clone https://github.com/user/repo
# → 克隆 → tree-sitter AST 解析 → 图谱构建

# 通用 URL
saw ingest https://example.com/article
# → WebFetch 抓取 → 内容提取 → 摄入
```

**元数据提取**: 自动提取来源信息（标题、作者、日期、URL）存入 Claims 层的 `source_url` 字段。

---

## 附录 D：Graphify 项目审计总结

### D.1 审计来源

**项目**: Graphify (https://github.com/safishamsi/graphify)

**核心贡献**: 知识图谱构建工具，实现 71.5x 的查询 token 减少。

### D.2 整合特性清单

| Graphify 特性 | 是否整合 | Smart Agent Wiki 应用 | 技术选型 |
|--------------|---------|---------------------|---------|
| tree-sitter AST | ✅ | 代码解析实现 (A.24) | tree-sitter-languages |
| faster-whisper | ✅ | 视频转录优化 (A.25) | faster-whisper (可选) |
| Leiden 聚类 | ✅ | 社区发现算法 (A.26) | graspologic |
| SHA256 缓存 | ✅ | 增量更新机制 (A.27) | hashlib (标准库) |
| 多代理安装器 | ✅ | 兼容层实现 (A.28) | Jinja2 模板 |
| Git 钩子 | ✅ | 自动摄入触发 (A.29) | Git hooks |
| URL/视频摄入 | ✅ | 摄入源扩展 (A.30) | yt-dlp (可选) |
| vis.js 可视化 | ❌ | 已有 Cytoscape.js | 无需替换 |
| graph.json 持久化 | ❌ | 已有 SQLite 方案 | 无需替换 |
| GRAPH_REPORT.md | ❌ | 可通过 saw_suggest 实现 | 无需单独工具 |

### D.3 不整合的部分及理由

| Graphify 特性 | 不整合理由 |
|--------------|-----------|
| **vis.js 图谱可视化** | 已选 Cytoscape.js，功能更强大：支持复杂布局、TypeScript 原生、React 集成更好、支持大规模图谱 |
| **graph.json 持久化** | 已有 SQLite + NetworkX 存储方案，数据一致性更好 |
| **GRAPH_REPORT.md 自动报告** | 可通过现有 saw_suggest 工具实现，无需新增 MCP 工具 |
| **三阶段流程命名** | 保持现有摄入引擎的命名一致性（分类→解析→提取→融合→验证→入库） |

### D.4 技术选型一致性

| 新增依赖 | 与现有技术栈兼容性 | 安装方式 |
|---------|------------------|---------|
| tree-sitter-languages | ✅ Python 原生 | pip install (可选) |
| faster-whisper | ✅ Python 原生 | pip install (可选) |
| graspologic | ✅ Python 原生，依赖 NetworkX | pip install |
| yt-dlp | ✅ Python 原生 | pip install (可选) |

所有依赖均为 Python 原生，与现有技术栈完全兼容。

### D.5 设计完整度更新

| 设计维度 | 原评分 | 新评分 | 说明 |
|----------|--------|--------|------|
| 学习能力 | ★★★★★ | ★★★★★ | 新增 Leiden 社区发现 (A.26) |
| Agent 协作 | ★★★★☆ | ★★★★★ | 新增多代理配置安装器 (A.28) |
| 可扩展性 | ★★★★☆ | ★★★★★ | 新增 Git 钩子 + URL 摄入 (A.29, A.30) |
| 多媒体支持 | ★★★☆☆ | ★★★★☆ | faster-whisper 加速视频转录 (A.25) |

---

*Smart Agent Wiki — 让知识可信、可溯源、可进化*
*基于 181 个 LLM Wiki 开源项目 + Graphify 精选特性的全面审计设计*
*Last updated: 2026-04-29*
