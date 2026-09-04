# Smart Agent Wiki

**下一代智能多代理知识平台** — 知识可信、可溯源、可进化

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v1.8.0-blue.svg)](https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.8.0)
[![Tests](https://img.shields.io/badge/tests-1898+%20passing-brightgreen.svg)](tests/)
[![MCP](https://img.shields.io/badge/MCP-64+%20tools-purple.svg)](src/saw/drivers/mcp/)
[![GitHub Stars](https://img.shields.io/github/stars/chensaics/smart_agent_wiki?style=social)](https://github.com/chensaics/smart_agent_wiki)
[![GitHub Issues](https://img.shields.io/github/issues/chensaics/smart_agent_wiki)](https://github.com/chensaics/smart_agent_wiki/issues)

[English](README.md)

> **说明：** `saw` 是 **Smart Agent Wiki** 的 CLI 命令缩写。可以把它想象成一把"锯子"，锯开知识混沌，构建结构化的智慧。

## 简介

Smart Agent Wiki 是一个本地优先的知识管理平台，将知识视为「编译」的结果而非检索的对象。它通过四层存储架构（Vault → Claims → Wiki → Index）和五大引擎（摄入、查询、治理、学习、协作），实现知识从摄入到过期修剪的全生命周期管理。

**亮点：**

- 🔍 **四层存储架构** — 每条主张可溯源到原始文档的具体位置
- 🤖 **6 个专业化 Agent** — Librarian / Writer / Critic / Linker / Scholar / Guardian
- 🛡️ **治理引擎** — 4 层置信度、9 级新鲜度、矛盾检测、Ed25519 审计收据
- 🧠 **代码智能** — 影响分析、执行流检测、过期检测，基于知识图谱
- 🔐 **安全体系** — JWT 认证、RBAC、速率限制、输入清洗、审计日志
- 🧩 **插件系统** — 可扩展 SDK，事件驱动钩子，沙箱隔离
- 💰 **Token 优化** — 减少 LLM token 消耗 65%+
- 🌐 **Web UI** — React + Cytoscape.js 知识图谱 + Milkdown 编辑器
- 🔌 **MCP Server** — 24+ 工具，兼容 Claude Code / Cursor / Copilot

## 快速开始

### 1. 安装

```bash
# Linux/macOS
curl -fsSL https://get.saw.sh | bash

# Windows (PowerShell)
iwr -useb https://get.saw.sh | iex
```

其他方式：`pipx install smart-agent-wiki`、`brew install chensaics/tap/saw`、或 Docker。

<details>
<summary>手动安装（开发环境）</summary>

```bash
git clone https://github.com/chensaics/smart_agent_wiki.git
cd smart_agent_wiki
python -m venv .venv && source .venv/bin/activate
pip install -e .            # 核心
pip install -e ".[pdf]"     # + PDF 解析
pip install -e ".[dev]"     # + 开发工具
```
</details>

### 2. 初始化与摄入

```bash
saw init                          # 在当前目录创建 Wiki
saw init --agent claude-code      # 同时生成 CLAUDE.md

saw ingest document.pdf           # 单个文件
saw ingest ./documents/           # 整个目录
saw ingest https://example.com    # URL
saw ingest doc.pdf --no-llm       # 离线模式（仅提取结构）
```

支持格式：**Markdown**、**PDF**（Docling/PyMuPDF）、**URL**（trafilatura）、**代码**（AST 解析，零 LLM 调用）。

### 3. 查询与搜索

```bash
saw query "这个项目的主要设计决策是什么？"   # 自然语言查询
saw search "entity resolution"               # BM25 关键词搜索
saw status                                   # 知识库概览
```

### 4. Web UI 与 MCP

```bash
saw web    # → http://localhost:8000  (API 文档: /docs)
saw mcp    # 启动 MCP Server
```

Claude Desktop MCP 配置：
```json
{ "mcpServers": { "smart-agent-wiki": { "command": "saw", "args": ["mcp"] } } }
```

## 功能详解

### 知识治理

- **4 层置信度** — 未验证 → 单来源 → 交叉验证 → 人工确认
- **9 级新鲜度** — 🟢 新鲜 → 🟡 较新 → 🟠 较旧 → 🔴 过期
- **矛盾检测** — 自动发现跨来源的冲突主张
- **Ed25519 审计收据** — 数据溯源的密码学证明
- **Write Queue** — SQLite outbox 模式，单一变更网关

### 代码智能

通过知识图谱分析代码库：

```bash
saw impact UserService                  # 修改影响分析（BFS 风险分级）
saw impact handleLogin --direction downstream
saw process handleRequest               # 执行流检测（DFS 调用树）
saw staleness --threshold-days 7        # 知识库新鲜度检查
```

风险分级：**WILL_BREAK**（直接依赖）→ **LIKELY_AFFECTED**（二级）→ **MAY_NEED_TESTING**（三级）。

摄入管线使用 Kahn 拓扑排序进行 DAG 验证，含循环检测，跨 6 个阶段：Classify → Parse → Extract → Merge → Validate → Store。

### 安全

内置生产级安全能力：

- **JWT 认证** — Access/refresh token 对，可配置过期时间
- **RBAC** — 基于角色的访问控制（admin / editor / viewer）
- **速率限制** — 按用户、按端点的请求节流
- **输入清洗** — SQL 注入和 XSS 模式检测
- **安全头** — CSP、HSTS、X-Frame-Options、X-Content-Type-Options
- **审计日志** — 所有写操作记录时间戳和用户上下文

### 插件系统

通过自定义插件扩展 SAW：

```bash
saw plugin list                  # 列出已安装插件
saw plugin install my-plugin     # 从仓库安装
saw plugin enable my-plugin      # 启用/禁用
```

- **Plugin SDK** — `PluginBase`、`PluginContext`、事件钩子
- **事件系统** — `PageCreated`、`PageUpdated`、`PageDeleted`、`ClaimCreated`、`IngestCompleted`、`QueryExecuted`
- **沙箱隔离** — 每个插件拥有独立的 `data_dir`

详见[插件开发指南](docs/PLUGIN_DEVELOPMENT.md)。

### Token 优化

减少 LLM token 消耗高达 65%：

| 模块 | 用途 |
|------|------|
| **Anatomy Index** | 项目结构索引，含文件描述和 token 估算 |
| **Cerebrum** | 跨会话学习记忆 — 积累偏好，防止重复错误 |
| **Bug Log** | 修复记忆 — 防止重新发现已知解决方案 |
| **Session Tracker** | 检测重复文件读取并提供警告 |
| **Token Ledger** | 跨会话追踪 token 消耗并估算节省 |

```python
from saw.token_optimizer import AnatomyIndex, TokenLedger

index = AnatomyIndex(project_root="./my_project")
index.scan_directory()
entry = index.get_entry("src/main.py")
print(f"{entry.description} (~{entry.estimated_tokens} tokens)")
```

### 开发者体验

- **一行安装** — `curl -fsSL https://get.saw.sh | bash`
- **交互式教程** — `saw tutorial`（5 步引导，含演示内容）
- **简短别名** — `saw i`（ingest）、`saw q`（query）、`saw s`（status）、`saw w`（web）
- **友好错误** — 可操作的建议，而非原始 traceback
- **Shell 补全** — `saw completion bash|zsh|fish --install`
- **离线文档** — `saw docs --output ./docs-offline/`
- **查询缓存** — LRU + TTL（默认 300 秒，最多 1000 条目）
- **Dashboard 统计** — 实时指标：总页面数、最近编辑、活跃 Agent、运行时间

## CLI 命令参考

| 命令 | 别名 | 说明 |
|------|------|------|
| `saw init` | — | 初始化新的 Wiki |
| `saw status` | `saw s` | 显示知识库状态 |
| `saw ingest <source>` | `saw i` | 摄入文档/URL/目录 |
| `saw query <question>` | `saw q` | 自然语言查询 |
| `saw search <keywords>` | — | BM25 关键词搜索 |
| `saw impact <symbol>` | — | 代码修改影响分析 |
| `saw process <entry>` | — | 执行流检测 |
| `saw staleness` | — | 知识库过期检测 |
| `saw lint` | `saw l` | 健康检查 |
| `saw conflicts` | — | 列出矛盾冲突 |
| `saw freshness` | — | 新鲜度报告 |
| `saw plugin <action>` | — | 插件管理（list/install/enable/disable） |
| `saw mcp` | — | 启动 MCP Server |
| `saw web` | `saw w` | 启动 Web UI |
| `saw tutorial` | — | 交互式教程 |
| `saw config` | — | TUI 配置界面 |
| `saw completion` | — | Shell 补全 |
| `saw docs` | — | 离线文档 |

## MCP 工具（24+）

**摄入（2）：** `saw_ingest`、`saw_reparse`

**查询（7）：** `saw_query`、`saw_search`、`saw_tree_search`、`saw_graph`、`saw_compare`、`saw_compile`、`saw_coverage`

**治理（7）：** `saw_lint`、`saw_conflicts`、`saw_verify`、`saw_freshness`、`saw_review`、`saw_audit`、`saw_blast_radius`

**代码智能（3）：** `saw_impact`、`saw_process`、`saw_staleness`

**学习（5）：** `saw_status`、`saw_learn`、`saw_distill`、`saw_suggest`、`saw_wip`

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
│ (DAG pipe)  │ (+ Cache)   │ (+ RBAC)    │                   │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────┬─────────┘
       │             │             │                │
       ▼             ▼             ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                       存储层                                 │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│    Vault    │ Claims (DB) │ Wiki Pages  │ FTS5 + Graph      │
│  (不可变)   │  (SQLite)   │ (Markdown)  │ (索引层)          │
└─────────────┴─────────────┴─────────────┴───────────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│      代码智能         │  │     Token 优化        │
├──────────────────────┤  ├──────────────────────┤
│ Impact · Process     │  │ Anatomy · Cerebrum   │
│ Staleness · DAG      │  │ BugLog · Tracker     │
└──────────────────────┘  └──────────────────────┘
```

六边形架构：`domain/`（纯 Python）→ `engines/`（业务逻辑）→ `adapters/`（基础设施）→ `drivers/`（CLI/Web/MCP）。六个专业化 Agent — Librarian、Writer、Critic、Linker、Scholar、Guardian — 协作处理知识。

## 路线图

- Web UI Impact 可视化（D3.js 图）
- Tree-sitter AST 零 LLM 解析
- LadybugDB / KuzuDB 图数据库
- Agent Skills Layer（Claude Code Skills）

## 开发

```bash
pytest tests/ -v              # 运行所有测试
pytest --cov=src/saw          # 含覆盖率
cd web && npm run dev         # 前端开发服务器
```

## 许可证

[MIT 许可证](LICENSE)

## 致谢

本项目受到 Karpathy 的 LLM Wiki 概念启发，特别感谢：

- GitNexus — DAG Pipeline、Impact Analysis 架构参考
- Knowledge Pipeline — 编译范式、矛盾检测
- Multi-Agent Wiki — 多代理治理
- codesight — AST 零 LLM 提取
- llm-wiki1 — FSRS 间隔重复
- unified-memory-ai-agents — 三层认知、WIP 动量
