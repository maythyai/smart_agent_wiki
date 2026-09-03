# Quick Start Guide

Get started with Smart Agent Wiki in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- pip or pipx

## Step 1: Install (1 minute)

**Linux/macOS:**
```bash
curl -fsSL https://get.saw.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr -useb https://get.saw.sh | iex
```

**Alternative methods:**
```bash
# pipx (recommended for isolation)
pipx install smart-agent-wiki

# Homebrew (macOS)
brew install chensaics/tap/saw

# Docker
docker run -it chensaics/saw:latest saw init
```

## Step 2: Initialize (1 minute)

Create a new wiki in your current directory:

```bash
saw init
```

This creates:
```
wiki.db          # SQLite database
vault/           # Document storage
claims/          # Extracted claims
wiki/            # Synthesized pages
saw.yaml         # Configuration
```

## Step 3: Ingest Documents (2 minutes)

Add your documents to the knowledge base:

```bash
# Single file
saw ingest document.pdf
saw ingest notes.md

# URL (extracts content automatically)
saw ingest https://example.com/article

# Directory
saw ingest ./documents/

# Offline mode (structure only, no LLM calls)
saw ingest document.pdf --no-llm
```

**Supported formats:**
- Markdown (`.md`)
- PDF (`.pdf`)
- URLs (web pages)
- Code (`.py`, `.js`, `.ts`, etc.) — zero LLM, AST parsing

## Step 4: Query Your Wiki (1 minute)

Search your knowledge base:

```bash
# Basic search
saw query "machine learning"

# Different query modes
saw query "project X" --mode direct     # Direct retrieval
saw query "team decisions" --mode graph  # Graph traversal
saw query "why did we choose Y?" --mode reasoning  # Reasoning chain

# Show source citations
saw query "budget" --citations
```

## Step 5: Web UI (Optional)

Launch the web interface:

```bash
saw web
```

Opens http://localhost:8000 with:
- 🔍 Search interface
- 📊 Knowledge graph visualization
- ✏️ Wiki page editor
- 📋 Dashboard

## Verification

Check everything is working:

```bash
saw --version
# Output: saw 1.4.0

saw status
# Output:
#   Documents: 15
#   Claims: 142
#   Wiki Pages: 23
#   Last Ingest: 2026-05-05
```

## What's Next?

- 📖 Read the [full documentation](https://github.com/chensaics/smart_agent_wiki#documentation)
- 🎯 Try the [examples](../examples/)
- 🔧 Configure [integrations](https://github.com/chensaics/smart_agent_wiki/wiki/Integrations)
- 💬 Join [discussions](https://github.com/chensaics/smart_agent_wiki/discussions)

## Logging

> **v1.2.0+**: 生产环境默认输出 JSON 结构化日志。本地开发如需可读文本日志，设置环境变量：
> ```bash
> export SAW_PRETTY_LOGS=1   # 切回纯文本可读日志
> # 或显式关闭 JSON 日志：
> export SAW_JSON_LOGS=0
> ```
> team 模式下 JSON 日志强制开启，以上变量不生效。详见 [Migration Guide — v1.2.0 行为变更](MIGRATION.md#v120-行为变更)。

## Troubleshooting

**Python not found:**
```bash
# Install Python 3.11+
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
# Windows: https://www.python.org/downloads/
```

**pip not found:**
```bash
curl -fsSL https://bootstrap.pypa.io/get-pip.py | python3
```

**Command 'saw' not found:**
- Restart your terminal
- Or add `~/.local/bin` to your PATH:
  ```bash
  export PATH="$PATH:$HOME/.local/bin"
  ```

---

*Need more help? Open an [issue](https://github.com/chensaics/smart_agent_wiki/issues).*
