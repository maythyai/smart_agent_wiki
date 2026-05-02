# Discord Connector Guide

Discord 是游戏和社区沟通平台。SAW 的 Discord 连接器通过 Gateway WebSocket 接收消息，支持嵌入内容解析和线程上下文。

## 前提条件

- Discord 服务器管理员权限
- SAW Web 服务器运行中

## 步骤 1: 创建 Discord Application

1. 访问 [Discord Developer Portal](https://discord.com/developers/applications)
2. 点击 "New Application"
3. 输入名称: `Smart Agent Wiki`
4. 记录 **Application ID**

## 步骤 2: 创建 Bot

1. 在左侧菜单选择 "Bot"
2. 点击 "Add Bot"
3. 记录 **Bot Token** (点击 Reset Token 获取)

### 配置 Bot 权限

在 "Privileged Gateway Intents" 部分，启用：

| Intent | 说明 |
|--------|------|
| MESSAGE CONTENT INTENT | 读取消息内容 |
| SERVER MEMBERS INTENT | 读取成员信息（可选） |

## 步骤 3: 配置 Bot 权限

在 "OAuth2" → "URL Generator" 页面：

1. Scopes: 选择 `bot`
2. Bot Permissions:
   - Read Messages/View Channels
   - Read Message History
   - Send Messages (可选，用于测试)

复制生成的 OAuth2 URL。

## 步骤 4: 添加 Bot 到服务器

1. 在浏览器打开生成的 OAuth2 URL
2. 选择要添加 Bot 的服务器
3. 授权权限

## 步骤 5: 配置 SAW

设置环境变量：

```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
```

### 通过 CLI 连接

```bash
saw discord connect
```

### 通过 Web UI

访问 `/integrations`，找到 Discord 卡片点击 Connect。

## 步骤 6: 选择频道

```bash
# 列出可用频道
saw discord list-channels

# 选择频道
saw discord select-channels --ids 123456789,987654321
```

## Gateway 连接

Discord 连接器使用 Gateway WebSocket 接收实时消息：

- 自动重连 (带退避策略)
- 心跳保活
- Resume 断点续传

查看连接状态：

```bash
saw discord gateway-status
```

## 嵌入内容解析

Discord 消息支持 Embed（嵌入内容），SAW 会解析：

| Embed 字段 | 处理方式 |
|------------|----------|
| title | 作为标题 |
| description | 作为内容 |
| url | 作为来源链接 |
| fields | 解析为键值对 |
| image/video | 保存链接 |

## 线程处理

Discord 的线程（Thread）会被捕获：

- 线程消息带有 `thread_id` 和 `thread_name`
- 父消息引用会被保留

## 故障排除

### Gateway 连接失败

检查网络连接和 Bot Token：

```bash
saw discord test-connection
```

### 消息未接收

确认 Bot 有正确权限：

1. 在 Discord 服务器设置中检查 Bot 角色
2. 确认 MESSAGE CONTENT INTENT 已启用

### 速率限制

Discord Gateway 有速率限制：

| 事件 | 限制 |
|------|------|
| 连接 | 1/5min (同一 session) |
| 心跳 | 由 Discord 指定 |

查看速率限制状态：

```bash
saw discord rate-limit-status
```

## 配置参考

```bash
saw discord config --help
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--sync-history` | true | 是否同步历史消息 |
| `--max-messages` | 1000 | 最大消息数 |
| `--include-threads` | true | 是否包含线程 |
| `--include-embeds` | true | 是否解析嵌入 |

---

*最后更新: 2026-05-02*