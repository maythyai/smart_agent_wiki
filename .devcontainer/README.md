# GitHub Codespaces Setup

This configuration allows you to try Smart Agent Wiki in the cloud without any local installation.

## Quick Start

1. Click the "Code" button on GitHub
2. Select "Open with Codespaces"
3. Click "New codespace"
4. Wait ~2 minutes for setup
5. Run `saw tutorial` to start the interactive guide

## What's Included

- Python 3.11 environment
- Smart Agent Wiki pre-installed
- Sample wiki initialized
- Ports forwarded for web UI

## Commands to Try

```bash
# Check wiki status
saw status

# Search knowledge base
saw query "project"

# Launch web UI
saw web
```

## Ports

| Port | Purpose |
|------|---------|
| 8000 | Web UI Backend |
| 3000 | Web UI Frontend |

Both ports auto-forward when you run `saw web`.

## Clean Up

When done, close the codespace or let it expire automatically (default: 30 days).

---

*No data is persisted after codespace deletion.*