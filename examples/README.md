# Smart Agent Wiki Examples

This directory contains examples demonstrating how to use Smart Agent Wiki in various scenarios.

## Quick Start

The fastest way to get started:

```bash
# Install SAW
curl -fsSL https://get.saw.sh | bash

# Initialize a wiki
saw init

# Ingest documents
saw ingest ./my-documents/*.md

# Query your knowledge
saw query "project planning"
```

## Example Categories

### 📚 [Basic Usage](./basic-usage/)
Start here if you're new to Smart Agent Wiki.

- [01-initialization.md](./basic-usage/01-initialization.md) — Creating and configuring your first wiki
- [02-ingest.md](./basic-usage/02-ingest.md) — Adding documents to your knowledge base
- [03-query.md](./basic-usage/03-query.md) — Searching and retrieving information

### 🚀 [Advanced](./advanced/)
For power users and integrations.

- [mcp-integration.md](./advanced/mcp-integration.md) — Using with Claude Code / Cursor
- [web-ui.md](./advanced/web-ui.md) — Web interface and visualization
- [team-deployment.md](./advanced/team-deployment.md) — Multi-user team setup

### 🎯 [Demo](./demo/)
Pre-configured demo to explore SAW features.

- [sample-documents/](./demo/sample-documents/) — Sample PDF and Markdown files
- Run `saw tutorial` for interactive guided tour

## Running Examples

Each example directory contains:
- 📄 Step-by-step instructions
- 📁 Sample files (where applicable)
- ✅ Expected output

## Need Help?

- 📖 [Documentation](https://github.com/chensaics/smart_agent_wiki#documentation)
- 💬 [Discussions](https://github.com/chensaics/smart_agent_wiki/discussions)
- 🐛 [Issue Tracker](https://github.com/chensaics/smart_agent_wiki/issues)
