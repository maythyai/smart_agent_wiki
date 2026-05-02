# GitHub Connector Guide

GitHub 是代码托管和协作平台。SAW 的 GitHub 连接器支持 Issues 和 Discussions 同步，提供 OAuth App 和 GitHub App 两种认证方式。

## 前提条件

- GitHub 账户
- 仓库管理权限
- SAW Web 服务器运行中

## 选择认证方式

| 方式 | 适用场景 | 权限范围 |
|------|----------|----------|
| OAuth App | 个人账户，少量仓库 | 用户级别 |
| GitHub App | 团队/组织，多仓库 | 细粒度权限 |

推荐使用 GitHub App 以获得更细粒度的权限控制。

## 方式一: OAuth App

### 步骤 1: 创建 OAuth App

1. 访问 [GitHub Developer Settings](https://github.com/settings/developers)
2. 点击 "New OAuth App"
3. 填写信息：
   - Application name: `Smart Agent Wiki`
   - Homepage URL: `https://your-saw-domain`
   - Authorization callback URL: `https://your-saw-domain/api/v1/oauth/callback/github`
4. 记录 **Client ID** 和 **Client Secret**

### 步骤 2: 配置 SAW

```bash
export GITHUB_CLIENT_ID="Iv1.xxxxx"
export GITHUB_CLIENT_SECRET="xxxxx"
```

### 步骤 3: 连接

```bash
saw github connect --method oauth
```

## 方式二: GitHub App (推荐)

### 步骤 1: 创建 GitHub App

1. 访问 [GitHub App Settings](https://github.com/settings/apps)
2. 点击 "New GitHub App"
3. 填写基本信息：
   - GitHub App name: `Smart Agent Wiki`
   - Homepage URL: `https://your-saw-domain`
   - Callback URL: `https://your-saw-domain/api/v1/oauth/callback/github`
   - Setup URL: (留空)

### 步骤 2: 配置权限

在 "Repository permissions" 部分：

| 权限 | 访问级别 | 说明 |
|------|----------|------|
| Issues | Read | 读取 Issues |
| Discussions | Read | 读取 Discussions |
| Metadata | Read | 基础访问 |
| Webhooks | Read | 接收事件 |

### 步骤 3: 配置 Webhook

在 "Webhook" 部分：

- Webhook URL: `https://your-saw-domain/api/v1/webhooks/github`
- Webhook secret: 生成一个安全密钥

订阅事件：

| 事件 | 说明 |
|------|------|
| issues | Issue 创建/更新/关闭 |
| discussion | Discussion 创建/更新 |
| issue_comment | Issue 评论 |
| discussion_comment | Discussion 评论 |

### 步骤 4: 生成私钥

1. 在 GitHub App 设置页面点击 "Generate a private key"
2. 下载 .pem 文件
3. 记录 **App ID**

### 步骤 5: 配置 SAW

```bash
export GITHUB_APP_ID="123456"
export GITHUB_APP_PRIVATE_KEY_PATH="/path/to/private-key.pem"
export GITHUB_WEBHOOK_SECRET="your_webhook_secret"
```

### 步骤 6: 安装应用

1. 在 GitHub App 设置页面点击 "Install App"
2. 选择仓库或组织
3. 授权安装

### 步骤 7: 连接

```bash
saw github connect --method github-app
```

## 选择仓库

```bash
# 列出可用仓库
saw github list-repos

# 选择仓库
saw github select-repos --owner octocat --repo hello-world
```

或在 Web UI `/integrations` 中选择仓库。

## 内容同步

### Issues 同步

- Issue 标题映射为条目标题
- Issue 内容映射为条目内容
- 标签 (Labels) 映射为标签
- 评论作为条目的附属信息

### Discussions 同步

- Discussion 标题和内容
- 分类 (Category) 作为标签
- 回复作为附属信息

### 标签映射

自定义 GitHub 标签到 SAW 字段：

```bash
saw github map-labels \
  --confidence "High Priority:4,Low Priority:1" \
  --tags "bug:bug-type,enhancement:enhancement-type"
```

## Webhook 调和

当收到 Webhook 事件时，SAW 会：

1. 验证签名 (HMAC-SHA256)
2. 解析事件内容
3. 更新对应条目

### HMAC 签名验证

Webhook 使用 HMAC-SHA256 签名：

```bash
# 验证签名配置
saw github verify-webhook
```

## 故障排除

### Webhook 未收到

检查签名密钥：

```bash
saw github test-webhook --repo owner/repo
```

确保 GitHub Webhook 显示 "Last delivery was successful"。

### 速率限制

GitHub API 速率限制：

| 认证方式 | 限制 |
|----------|------|
| 未认证 | 60 req/hr |
| OAuth Token | 5000 req/hr |
| GitHub App | 15000 req/hr |

查看状态：

```bash
saw github rate-limit-status
```

### GraphQL 分页错误

Issues/Discussions 使用 GraphQL API，如果遇到分页问题：

```bash
saw github config --page-size 100 --max-pages 50
```

## 配置参考

```bash
saw github config --help
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--sync-issues` | true | 同步 Issues |
| `--sync-discussions` | true | 同步 Discussions |
| `--sync-comments` | true | 同步评论 |
| `--include-states` | open | 包含的 Issue 状态 (open,closed,all) |
| `--label-mapping` | - | 标签映射 |
| `--page-size` | 100 | GraphQL 分页大小 |

---

*最后更新: 2026-05-02*