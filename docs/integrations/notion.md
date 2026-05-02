# Notion Connector Guide

Notion 是一款流行的知识管理和协作工具。SAW 的 Notion 连接器支持双向同步，可以将 Notion 数据库中的页面同步到知识库，并支持属性映射和增量同步。

## 前提条件

- Notion 账户
- SAW Web 服务器运行中 (`saw web start`)
- 要同步的数据库的管理权限

## 步骤 1: 创建 Notion 集成

1. 访问 [Notion Developers](https://www.notion.so/my-integrations)
2. 点击 "+ New integration"
3. 填写集成信息：
   - Name: `Smart Agent Wiki` (或任意名称)
   - Logo: 可选
   - Associated workspace: 选择你的工作区
4. 点击 "Submit" 创建集成
5. 记录以下信息：
   - **Client ID** (OAuth 客户端 ID)
   - **Client Secret** (OAuth 客户端密钥)

## 步骤 2: 配置 OAuth 凭证

设置环境变量：

```bash
export NOTION_CLIENT_ID="your_client_id_here"
export NOTION_CLIENT_SECRET="your_client_secret_here"
```

或在 `.env` 文件中：

```
NOTION_CLIENT_ID=your_client_id_here
NOTION_CLIENT_SECRET=your_client_secret_here
```

## 步骤 3: 连接工作区

### 通过 Web UI

1. 访问 `http://localhost:8000/integrations`
2. 找到 "Notion" 卡片
3. 点击 "Connect"
4. 在弹出窗口中授权 SAW 访问你的 Notion 工作区
5. 选择要同步的数据库

### 通过 CLI

```bash
saw notion connect
```

这将打开浏览器进行 OAuth 授权流程。

## 步骤 4: 选择数据库

授权完成后，选择要同步的数据库：

```bash
# 列出可用数据库
saw notion list-databases

# 选择数据库
saw notion select-database --id <database_id>
```

在 Web UI 中，数据库选择界面会显示所有可用的数据库及其属性。

## 步骤 5: 配置属性映射

Notion 数据库属性可以映射到 SAW 字段：

| Notion 属性类型 | SAW 字段 | 说明 |
|----------------|----------|------|
| Title | title | 页面标题 (必需) |
| Rich Text | content | 页面内容 |
| Select | confidence | 置信度等级 |
| Date | freshness | 新鲜度时间戳 |
| URL | source_url | 来源链接 |
| Multi-select | tags | 标签列表 |

配置映射：

```bash
saw notion map-properties \
  --title "Name" \
  --content "Content" \
  --confidence "Confidence" \
  --freshness "Updated"
```

## 步骤 6: 测试同步

执行手动同步测试：

```bash
saw notion sync --dry-run
```

查看同步预览，确认无误后执行实际同步：

```bash
saw notion sync
```

## 双向同步

Notion 连接器支持双向同步：

- **Pull**: 从 Notion 拉取新页面和更新
- **Push**: 将 SAW 中的更改推送到 Notion

启用双向同步：

```bash
saw notion config --sync-direction bidirectional
```

### 冲突处理

当同一页面在两边都被修改时：

- 默认策略: **最后修改者胜出** (last_modified_wins)
- 可配置策略: `platform_wins`, `saw_wins`, `manual`

```bash
saw notion config --conflict-resolution last_modified_wins
```

## 定时同步

配置自动同步间隔（最小 60 秒）：

```bash
saw notion config --poll-interval 3600  # 每小时同步
```

## 故障排除

### Token 过期

错误信息: `Token expired` 或 `Unauthorized`

解决方案: 重新授权

```bash
saw notion reconnect
```

或在 Web UI 中点击 "Re-authorize" 按钮。

### 速率限制

Notion API 限制为 3 请求/秒。SAW 自动处理速率限制，但如果遇到 `rate_limited` 错误：

```bash
# 查看速率限制状态
saw notion rate-limit-status

# 等待后重试
saw notion sync --retry-after 60
```

### 属性类型变更

如果 Notion 数据库中的属性类型发生变更：

1. SAW 会检测到类型变更
2. 同步会暂停并显示警告
3. 更新属性映射后恢复同步

```bash
saw notion detect-schema-changes
saw notion update-mapping
```

## 配置参考

完整配置选项：

```bash
saw notion config --help
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--poll-interval` | 3600 | 同步间隔 (秒) |
| `--sync-direction` | bidirectional | 同步方向 |
| `--conflict-resolution` | last_modified_wins | 冲突解决策略 |
| `--batch-size` | 100 | 每批同步页面数 |
| `--include-archived` | false | 是否包含已归档页面 |

---

*最后更新: 2026-05-02*