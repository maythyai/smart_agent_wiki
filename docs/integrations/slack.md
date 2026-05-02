# Slack Connector Guide

Slack 是企业团队沟通平台。SAW 的 Slack 连接器通过 Events API 接收消息，支持线程上下文捕获和反应信号。

## 前提条件

- Slack 工作区管理员权限
- SAW Web 服务器运行中
- 公网可访问的 Webhook URL（或使用 ngrok 进行本地测试）

## 步骤 1: 创建 Slack App

1. 访问 [Slack API Dashboard](https://api.slack.com/apps)
2. 点击 "Create New App"
3. 选择 "From scratch"
4. 输入 App 名称: `Smart Agent Wiki`
5. 选择你的工作区

## 步骤 2: 配置 OAuth Scopes

在 "OAuth & Permissions" 页面，添加以下 Bot Token Scopes：

| Scope | 说明 |
|-------|------|
| `channels:history` | 读取频道消息历史 |
| `channels:read` | 读取频道列表 |
| `groups:history` | 读取私有频道消息 |
| `groups:read` | 读取私有频道列表 |
| `reactions:read` | 读取消息反应 |
| `users:read` | 读取用户信息 |
| `team:read` | 读取工作区信息 |

## 步骤 3: 启用 Events API

在 "Event Subscriptions" 页面：

1. 启用 Events: On
2. 输入 Request URL: `https://your-saw-domain/api/v1/webhooks/slack`
3. 等待 URL 验证通过

订阅以下 Bot Events：

| Event | 说明 |
|-------|------|
| `message.channels` | 频道消息 |
| `message.groups` | 私有频道消息 |
| `reaction_added` | 反应添加 |
| `reaction_removed` | 反应移除 |

## 步骤 4: 安装 App

1. 在 "OAuth & Permissions" 页面点击 "Install to Workspace"
2. 授权 App 权限
3. 记录 **Bot User OAuth Token** (xoxb-...)

## 步骤 5: 配置 SAW

设置环境变量：

```bash
export SLACK_CLIENT_ID="your_client_id"
export SLACK_CLIENT_SECRET="your_client_secret"
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_SIGNING_SECRET="your_signing_secret"
```

### 通过 CLI 连接

```bash
saw slack connect
```

### 通过 Web UI

访问 `/integrations`，找到 Slack 卡片点击 Connect。

## 步骤 6: 选择频道

选择要同步的频道：

```bash
# 列出可用频道
saw slack list-channels

# 选择频道
saw slack select-channels --ids C12345,C67890
```

## 线程上下文捕获

Slack 连接器会捕获消息的线程上下文：

- 父消息内容
- 线程回复
- 反应信号（表示重要性）

线程中的消息会带有 `thread_parent_id` 标记，方便追溯完整对话。

## 反应信号

用户反应可以作为重要性信号：

```yaml
reaction_signals:
  thumbsup: confidence_boost  # 👍 提升置信度
  star: important             # ⭐ 标记重要
  bookmark: reference         # 🔖 标记参考
```

配置反应信号处理：

```bash
saw slack config --reaction-signals thumbsup:confidence_boost,star:important
```

## 故障排除

### Event 未接收

检查 Events API 配置：

1. 确保 Request URL 已验证
2. 检查 Signing Secret 配置
3. 验证订阅的 Event 类型

```bash
saw slack verify-webhook
```

### Token 过期

Slack Bot Token 通常不会过期，但如果遇到认证问题：

```bash
saw slack reconnect
```

### 速率限制

Slack API 有 tiered rate limits：

| Tier | 限制 |
|------|------|
| Tier 1 | 1 req/min |
| Tier 2 | 20 req/min |
| Tier 3 | 100 req/min |
| Tier 4 | 100 req/sec |

SAW 自动处理速率限制。查看当前状态：

```bash
saw slack rate-limit-status
```

## 本地测试

如果 SAW 运行在本地，使用 ngrok 提供 Webhook URL：

```bash
ngrok http 8000
```

使用 ngrok 提供的 URL 作为 Webhook Request URL：
`https://xxx.ngrok.io/api/v1/webhooks/slack`

## 配置参考

```bash
saw slack config --help
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--sync-interval` | 300 | 历史同步间隔 (秒) |
| `--include-threads` | true | 是否包含线程回复 |
| `--include-reactions` | true | 是否包含反应 |
| `--max-messages-per-channel` | 1000 | 每频道最大消息数 |
| `--reaction-signals` | - | 反应信号映射 |

---

*最后更新: 2026-05-02*