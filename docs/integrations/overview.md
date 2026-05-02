# Integrations Overview

Smart Agent Wiki supports multiple third-party platforms for knowledge synchronization. This guide covers common setup steps and platform-specific configurations.

## Dashboard

The Integration Dashboard at `/integrations` provides unified visibility into all connected platforms:

- **Health Status**: Green (healthy), Yellow (degraded), Red (unhealthy)
- **Sync State**: idle, syncing, paused, error
- **Actions**: Sync Now, Disconnect, Re-authorize

## Common Setup

### 1. Start the Web Server

```bash
saw web start
```

The dashboard is available at `http://localhost:8000/integrations`.

### 2. Environment Variables

OAuth-based connectors require environment variables for credentials:

```bash
# Notion
NOTION_CLIENT_ID=your_client_id
NOTION_CLIENT_SECRET=your_client_secret

# Slack
SLACK_CLIENT_ID=your_client_id
SLACK_CLIENT_SECRET=your_client_secret

# GitHub
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

### 3. Connect Platforms

Use the CLI or web dashboard:

```bash
# Connect via CLI
saw notion connect
saw slack connect
saw github connect
```

Or navigate to `/integrations` in the web UI and click "Connect" for each platform.

## Platform Comparison

| Platform | Auth Type | Sync Direction | Special Features |
|----------|-----------|----------------|------------------|
| Notion | OAuth 2.0 | Bidirectional | Database selection, property mapping |
| Logseq | Local path | Bidirectional | File watching, block parsing |
| Slack | OAuth 2.0 | Pull | Events API, thread context |
| Discord | Bot token | Pull | Gateway WebSocket, embeds |
| Feishu | App ID/Secret | Pull | Webhooks, multi-tenant |
| WeCom | Corp ID/Secret | Pull | Webhooks, AES encryption |
| GitHub | OAuth/App | Pull | Issues/Discussions, webhooks |

## Troubleshooting

### Common Issues

1. **"Token expired"**: Click "Re-authorize" on the dashboard or run `saw {platform} reconnect`

2. **"Rate limit exceeded"**: Sync will pause automatically. Wait a few minutes and retry.

3. **"Connection timeout"**: Check network connectivity and platform availability.

4. **"Permission denied"**: Ensure OAuth scopes include required permissions.

### Logs

View connector logs:

```bash
saw logs connector --platform notion
saw logs sync --last 10
```

## Connector Guides

- [Notion Setup Guide](./notion.md)
- [Logseq Setup Guide](./logseq.md)
- [Slack Setup Guide](./slack.md)
- [Discord Setup Guide](./discord.md)
- [Feishu Setup Guide](./feishu.md)
- [WeCom Setup Guide](./wecom.md)
- [GitHub Setup Guide](./github.md)

---

*Last updated: 2026-05-02*