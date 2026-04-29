# Smart Agent Wiki

**下一代智能多代理知识平台** — 知识可信、可溯源、可进化

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 简介

Smart Agent Wiki 是一个本地优先的知识管理平台，将知识视为「编译」的结果而非检索的对象。它通过四层存储架构（Vault → Claims → Wiki → Index）和五大引擎（摄入、查询、治理、学习、协作），实现知识从摄入到过期修剪的全生命周期管理。

**核心特性：**
- 🔍 **四层存储架构** — 每条主张可溯源到原始文档的具体位置
- 🤖 **6 个专业化 Agent** — Librarian/Writer/Critic/Linker/Scholar/Guardian 协作编排
- 🛡️ **治理引擎** — 4 层置信度、9 级新鲜度、矛盾检测、Ed25519 审计收据
- 🌐 **Web UI** — React + Cytoscape.js 知识图谱可视化 + Milkdown 编辑器
- 🔌 **MCP Server** — 23 个工具，Claude Code/Cursor/Copilot 兼容

## 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/smart-agent-wiki.git
cd smart-agent-wiki

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装核心依赖
pip install -e .

# 安装 PDF 解析支持（可选，推荐）
pip install -e ".[pdf]"

# 安装开发依赖（可选）
pip install -e ".[dev]"
```

### 2. 初始化 Wiki

```bash
# 在当前目录创建新的 Wiki
saw init

# 或指定路径
saw init /path/to/wiki

# 生成特定 Agent 的配置文件
saw init --agent claude-code  # 生成 CLAUDE.md
saw init --agent cursor       # 生成 .cursorrules
saw init --agent copilot      # 生成 .github/copilot-instructions.md
```

初始化后目录结构：
```
my-wiki/
├── .saw/
│   ├── config.yaml           # Wiki 配置
│   ├── claims.db             # SQLite 主张数据库
│   ├── fsrs_cards.yaml       # FSRS 间隔重复状态
│   ├── training.yaml         # 训练期状态
│   ├── wip.yaml              # 工作进度文件
│   └── feedback/
│       ├── approved.yaml     # 正向行为模式
│       └── rejected.yaml     # 负向行为模式
├── vault/                    # 原始文档存储（不可变）
│   └── {uuid}/
│       ├── original          # 原始文件
│       ├── transcript        # 文本转录
│       └── metadata.json     # 元数据
├── wiki/                     # Wiki 页面（可变）
│   ├── entities/
│   └── concepts/
└── index/
    └── l0_summary.md         # L0 索引（最多 100 行）
```

### 3. 摄入文档

```bash
# 摄入单个文件
saw ingest document.pdf
saw ingest notes.md
saw ingest https://example.com/article

# 摄入整个目录
saw ingest ./documents/

# 离线模式（不调用 LLM，仅提取结构）
saw ingest document.pdf --no-llm
```

支持的格式：
- **Markdown** (`.md`) — LLM 提取实体、概念、主张
- **PDF** (`.pdf`) — 三级降级解析：Docling → PyMuPDF
- **URL** — trafilatura 内容提取
- **代码** (`.py`, `.js`, `.ts` 等) — AST 解析，零 LLM 调用
- **JSON/YAML** — Schema 解析，零 LLM 调用

### 4. 查询知识库

```bash
# 自然语言查询
saw query "这个项目的主要设计决策是什么？"

# 关键词搜索（BM25 + FTS5）
saw search "entity resolution"

# 查看知识库状态
saw status
```

### 5. 治理与健康检查

```bash
# 健康检查
saw lint

# 查看矛盾冲突
saw conflicts

# 查看新鲜度报告
saw freshness

# 验证主张溯源
saw verify <claim-uuid>

# 验证审计收据链
saw audit

# 触发人工审核流程
saw review
```

### 6. 启动 Web UI

```bash
# 启动后端 API 服务器
saw web

# 指定端口和主机
saw web --port 3000 --host 0.0.0.0

# 启用热重载（开发模式）
saw web --reload

# 启用 CORS（用于前端开发）
saw web --cors
```

然后访问：
- **Web UI**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **搜索页面**: http://localhost:5173/search
- **知识图谱**: http://localhost:5173/graph
- **Agent Dashboard**: http://localhost:5173/dashboard

### 7. 启动 MCP Server

```bash
# 标准输入/输出模式（默认）
saw mcp

# SSE 模式（用于 HTTP 传输）
saw mcp --transport sse --port 8080
```

在 Claude Desktop 配置中添加：
```json
{
  "mcpServers": {
    "smart-agent-wiki": {
      "command": "saw",
      "args": ["mcp"]
    }
  }
}
```

## CLI 命令参考

| 命令 | 说明 |
|------|------|
| `saw init` | 初始化新的 Wiki |
| `saw status` | 显示知识库状态概览 |
| `saw ingest <source>` | 摄入文档/URL/目录 |
| `saw query <question>` | 自然语言查询 |
| `saw search <keywords>` | BM25 关键词搜索 |
| `saw lint` | 健康检查 |
| `saw verify <claim>` | 验证主张溯源链 |
| `saw conflicts` | 列出矛盾冲突 |
| `saw freshness` | 新鲜度报告 |
| `saw review` | 触发人工审核 |
| `saw audit` | 验证 Ed25519 审计收据链 |
| `saw mcp` | 启动 MCP Server |
| `saw web` | 启动 Web UI |

每个命令支持 `--help` 查看详细选项：
```bash
saw ingest --help
saw web --help
```

## 配置

### 环境变量

```bash
# LLM API 密钥（任选其一）
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# 可选：使用本地 LLM
export LITELLM_MODEL="ollama/llama3"
```

### 配置文件 `.saw/config.yaml`

```yaml
# Wiki 基本信息
wiki_name: "我的知识库"

# LLM 配置
llm:
  extraction_model: "gpt-4o-mini"  # 提取模型
  query_model: "gpt-4o"            # 查询模型
  max_retries: 3

# 摄入配置
ingest:
  supported_extensions:
    - ".md"
    - ".pdf"
    - ".py"
    - ".js"
    - ".ts"
  max_file_size_mb: 50

# 治理配置
governance:
  training_period_days: 30  # 训练期天数
  expiry_tactical_days: 30  # 战术知识过期天数

# Web 配置
web:
  host: "127.0.0.1"
  port: 8000
```

## 置信度与新鲜度

### 4 层置信度体系

| 级别 | 名称 | 说明 |
|------|------|------|
| 1 | Unverified | 单来源，未验证 |
| 2 | Single Source | 单来源，已验证 |
| 3 | Cross-Validated | 多来源交叉验证（≥2 独立来源） |
| 4 | Human Verified | 人工确认 |

### 9 级新鲜度系统

| 级别 | 颜色 | 说明 |
|------|------|------|
| 0-2 | 🟢 绿色 | 新鲜 |
| 3-5 | 🟡 黄色 | 较新 |
| 6-7 | 🟠 橙色 | 较旧 |
| 8 | 🔴 红色 | 过期 |

## MCP 工具列表

MCP Server 暴露 23 个工具，按功能分组：

**摄入工具 (2)**
- `saw_ingest` — 摄入文档
- `saw_reparse` — 重新解析已摄入文档

**查询工具 (7)**
- `saw_query` — 自然语言查询
- `saw_search` — BM25 搜索
- `saw_tree_search` — 结构感知搜索
- `saw_graph` — 知识图谱遍历
- `saw_compare` — 页面对比分析
- `saw_compile` — 上下文编译
- `saw_coverage` — 查询覆盖度分析

**治理工具 (7)**
- `saw_lint` — 健康检查
- `saw_conflicts` — 矛盾列表
- `saw_verify` — 验证溯源
- `saw_freshness` — 新鲜度报告
- `saw_review` — 人工审核
- `saw_audit` — 审计链验证
- `saw_blast_radius` — 影响范围分析

**学习工具 (5)**
- `saw_status` — 知识库状态
- `saw_learn` — 触发学习周期
- `saw_distill` — 认知蒸馏
- `saw_suggest` — 知识缺口建议
- `saw_wip` — 工作进度

**协作工具 (2)**
- `saw_workflow` — 执行 YAML 工作流
- `saw_feedback` — 提交反馈

## 工作流示例

创建 `workflows/literature_review.yaml`：

```yaml
name: Literature Review Workflow

steps:
  - id: ingest
    agent: Librarian
    action: ingest
    input: "{{ paper_url }}"
    output: paper_uuid

  - id: analyze
    agent: Scholar
    action: synthesize
    input: "{{ paper_uuid }}"
    output: analysis
    gates:
      - condition: "confidence >= 2"
        on_fail: escalate_to_human

  - id: critique
    agent: Critic
    action: review
    input: "{{ analysis }}"
    output: review_notes

  - id: link
    agent: Linker
    action: find_connections
    input: "{{ paper_uuid }}"
    output: related_entities

fallback:
  - action: retry
    max_retries: 3
  - action: escalate_to_human
```

执行：
```bash
saw workflow workflows/literature_review.yaml --input paper_url=https://arxiv.org/abs/...
```

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│   CLI (Typer)   │  Web UI (React) │  MCP Server (FastMCP)   │
└────────┬────────┴────────┬────────┴────────────┬────────────┘
         │                 │                      │
         └─────────────────┼──────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       引擎层                                 │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│ IngestEngine│ QueryEngine │GovernEngine │ CollaborateEngine │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────┬─────────┘
       │             │             │                │
       ▼             ▼             ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                       存储层                                 │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│    Vault    │ Claims (DB) │ Wiki Pages  │ FTS5 + Graph      │
│  (不可变)   │  (SQLite)   │ (Markdown)  │ (索引层)          │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

## 开发

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=src/saw
```

### 前端开发

```bash
cd web
npm install
npm run dev      # 开发服务器 http://localhost:5173
npm run build    # 生产构建
```

## 项目状态

**当前版本：v1.1**

- ✅ 四层存储架构
- ✅ 摄入引擎（PDF/MD/URL/代码）
- ✅ 查询引擎（NL + BM25 + 图遍历）
- ✅ 治理引擎（置信度/新鲜度/矛盾检测/审计）
- ✅ 学习引擎（训练期自适应 + FSRS + 认知蒸馏）
- ✅ MCP Server 23 工具
- ✅ CLI 13 命令
- ✅ Web UI（搜索/图谱/编辑/Dashboard）
- ✅ 6 Agent 协作架构

**路线图 (v2)：**
- Video/Audio ingestion (Whisper)
- Chrome 剪藏扩展
- RSS feed 订阅
- Obsidian 插件
- Tauri 桌面应用
- P2P 知识共享
- 团队部署模式

## 许可证

MIT License

## 致谢

本项目受到 Karpathy 的 LLM Wiki 概念启发，分析了社区 666 条评论和 181 个衍生项目，特别感谢以下参考项目：

- Knowledge Pipeline — 编译范式、矛盾检测
- Multi-Agent Wiki — 多代理治理
- Memex — 冲突处理策略
- codesight — AST 零 LLM 提取
- llm-wiki1 — FSRS 间隔重复
- scopeblind-gateway — Ed25519 + Cedar 审计
- unified-memory-ai-agents — 三层认知、WIP 动量
- MindOS — A2A 协议、YAML 工作流
