# Smart Agent Wiki

**下一代智能多代理知识平台** — 知识可信、可溯源、可进化

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v3.4.0-blue.svg)](https://github.com/chensaics/smart_agent_wiki/releases/tag/v3.4.0)

## 简介

Smart Agent Wiki 是一个本地优先的知识管理平台，将知识视为「编译」的结果而非检索的对象。它通过四层存储架构（Vault → Claims → Wiki → Index）和五大引擎（摄入、查询、治理、学习、协作），实现知识从摄入到过期修剪的全生命周期管理。

**核心特性：**
- 🔍 **四层存储架构** — 每条主张可溯源到原始文档的具体位置
- 🤖 **6 个专业化 Agent** — Librarian/Writer/Critic/Linker/Scholar/Guardian 协作编排
- 🛡️ **治理引擎** — 4 层置信度、9 级新鲜度、矛盾检测、Ed25519 审计收据
- 🌐 **Web UI** — React + Cytoscape.js 知识图谱可视化 + Milkdown 编辑器
- 🔌 **MCP Server** — 24+ 工具，Claude Code/Cursor/Copilot 兼容
- 🧠 **Code Intelligence** — 代码知识图谱分析（v3.4 新增）

## v3.4 新功能：Code Intelligence

借鉴 GitNexus（35K+ stars）的代码智能功能，Smart Agent Wiki 现具备代码知识图谱分析能力：

### DAG Pipeline Validation
类型安全的摄入管线架构，确保阶段依赖正确：
- Kahn 拓扑排序算法
- 循环检测与精确错误报告
- 6 阶段摄入流程：Classify → Parse → Extract → Merge → Validate → Store

### Impact Analysis Engine
代码修改影响分析，修改前了解破坏范围：
```bash
saw impact UserService
# 输出：
# Summary:
#   Total affected: 5
#   Depth 1 (will break): 2
#   Depth 2 (likely affected): 3
# ⚠ HIGH RISK: 2 direct dependents will break!
```

风险分级：
- **WILL_BREAK** — 直接依赖，修改必破
- **LIKELY_AFFECTED** — 二级依赖，可能受影响
- **MAY_NEED_TESTING** — 三级依赖，建议测试

### Process Detection
从入口点追踪执行流程：
```bash
saw process handleRequest
# 输出：
# Execution flow:
#   handleRequest
#     → validateInput
#       → parseJSON
#     → processData
#       → saveToDatabase
```

### Staleness Detection
知识库过期检测，判断数据可信度：
```bash
saw staleness
# 输出：
# Stale nodes: 3
# - UserService (10 days old, 12 commits behind)
# - OldService (8 days old, 5 commits behind)
# Recommendation: Run ingest to update 3 stale nodes
```

## 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/chensaics/smart_agent_wiki.git
cd smart-agent-wiki

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# 安装核心依赖
pip install -e .

# 安装 PDF 解析支持（可选）
pip install -e ".[pdf]"

# 安装开发依赖（可选）
pip install -e ".[dev]"
```

### 2. 初始化 Wiki

```bash
# 在当前目录创建新的 Wiki
saw init

# 生成 Agent 配置文件
saw init --agent claude-code  # 生成 CLAUDE.md
saw init --agent cursor       # 生成 .cursorrules
```

### 3. 摄入文档

```bash
# 摄入单个文件
saw ingest document.pdf
saw ingest notes.md
saw ingest https://example.com/article

# 摄入整个目录
saw ingest ./documents/

# 离线模式（仅提取结构）
saw ingest document.pdf --no-llm
```

支持的格式：
- **Markdown** (`.md`) — LLM 提取实体、概念、主张
- **PDF** (`.pdf`) — Docling → PyMuPDF 解析
- **URL** — trafilatura 内容提取
- **代码** (`.py`, `.js`, `.ts` 等) — AST 解析，零 LLM 调用

### 4. Code Intelligence 使用

```bash
# 分析代码修改影响（上游：依赖者）
saw impact UserService

# 分析下游依赖
saw impact handleLogin --direction downstream

# 深度限制
saw impact AuthModule --max-depth 5

# 置信度过滤
saw impact UserService --min-confidence 0.9

# JSON 输出
saw impact UserService --json

# 检测执行流程
saw process handleRequest --max-depth 5

# 检测过期节点
saw staleness --threshold-days 7
```

### 5. 查询知识库

```bash
# 自然语言查询
saw query "这个项目的主要设计决策是什么？"

# 关键词搜索（BM25 + FTS5）
saw search "entity resolution"

# 查看知识库状态
saw status
```

### 6. 启动 Web UI

```bash
saw web
# 访问: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 7. 启动 MCP Server

```bash
saw mcp
```

在 Claude Desktop 配置：
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
| `saw impact <symbol>` | 代码修改影响分析 ⭐ |
| `saw process <entry>` | 执行流程检测 ⭐ |
| `saw staleness` | 知识库过期检测 ⭐ |
| `saw lint` | 健康检查 |
| `saw conflicts` | 列出矛盾冲突 |
| `saw freshness` | 新鲜度报告 |
| `saw mcp` | 启动 MCP Server |
| `saw web` | 启动 Web UI |

⭐ v3.4 新增命令

## MCP 工具列表

**摄入工具 (2)**
- `saw_ingest` — 摄入文档
- `saw_reparse` — 重新解析

**查询工具 (7)**
- `saw_query` — 自然语言查询
- `saw_search` — BM25 搜索
- `saw_tree_search` — 结构感知搜索
- `saw_graph` — 知识图谱遍历
- `saw_compare` — 页面对比
- `saw_compile` — 上下文编译
- `saw_coverage` — 覆盖度分析

**治理工具 (7)**
- `saw_lint` — 健康检查
- `saw_conflicts` — 矛盾列表
- `saw_verify` — 验证溯源
- `saw_freshness` — 新鲜度报告
- `saw_review` — 人工审核
- `saw_audit` — 审计链验证
- `saw_blast_radius` — 影响范围

**Code Intelligence 工具 (3) ⭐**
- `saw_impact` — 代码修改影响分析
- `saw_process` — 执行流程检测
- `saw_staleness` — 知识库过期检测

**学习工具 (5)**
- `saw_status` — 知识库状态
- `saw_learn` — 触发学习周期
- `saw_distill` — 认知蒸馏
- `saw_suggest` — 知识缺口建议
- `saw_wip` — 工作进度

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
│ (DAG v3.4)  │             │             │                   │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────┬─────────┘
       │             │             │                │
       ▼             ▼             ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                       存储层                                 │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│    Vault    │ Claims (DB) │ Wiki Pages  │ FTS5 + Graph      │
│  (不可变)   │  (SQLite)   │ (Markdown)  │ (索引层)          │
└─────────────┴─────────────┴─────────────┴───────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Code Intelligence (v3.4)                   │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│ DAG Pipeline│ Impact Eng. │Process Det. │ Staleness Det.    │
│ Validation  │ (BFS trav.) │ (DFS tree)  │ (Git compare)     │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

## 置信度与新鲜度

### 4 层置信度体系

| 级别 | 名称 | 说明 |
|------|------|------|
| 1 | Unverified | 单来源，未验证 |
| 2 | Single Source | 单来源，已验证 |
| 3 | Cross-Validated | 多来源交叉验证 |
| 4 | Human Verified | 人工确认 |

### 9 级新鲜度系统

| 级别 | 颜色 | 说明 |
|------|------|------|
| 0-2 | 🟢 绿色 | 新鲜 |
| 3-5 | 🟡 黄色 | 较新 |
| 6-7 | 🟠 橙色 | 较旧 |
| 8 | 🔴 红色 | 过期 |

## 项目状态

**当前版本：v3.4.0**

**已完成：**
- ✅ 四层存储架构
- ✅ DAG Pipeline Validation（Kahn 拓扑排序）
- ✅ Impact Analysis Engine（BFS 风险分级）
- ✅ Process Detection（DFS 调用树）
- ✅ Staleness Detection（Git 提交比较）
- ✅ MCP Server 24+ 工具
- ✅ CLI 16 命令
- ✅ Web UI（搜索/图谱/编辑/Dashboard）
- ✅ 24 单元测试通过

**路线图 (v3.5)：**
- Web UI Impact 可视化（D3.js 图）
- Tree-sitter AST 零 LLM 解析
- LadybugDB/KuzuDB 图数据库
- Agent Skills Layer（Claude Code Skills）

## 开发

```bash
# 运行测试
pytest tests/unit/ingest/ tests/unit/analysis/ -v

# 运行覆盖率测试
pytest --cov=src/saw

# 前端开发
cd web && npm run dev
```

## 许可证

MIT License

## 致谢

本项目受到 Karpathy 的 LLM Wiki 概念启发，特别感谢：

- GitNexus — DAG Pipeline、Impact Analysis 架构参考
- Knowledge Pipeline — 编译范式、矛盾检测
- Multi-Agent Wiki — 多代理治理
- codesight — AST 零 LLM 提取
- llm-wiki1 — FSRS 间隔重复
- unified-memory-ai-agents — 三层认知、WIP 动量