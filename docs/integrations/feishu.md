# Feishu Connector Guide

飞书（Feishu/Lark）是字节跳动的企业协作平台。SAW 的飞书连接器通过 Webhook 接收文档和消息事件，支持多租户模式。

## 前提条件

- 飞书企业租户管理员权限
- SAW Web 服务器运行中
- 公网可访问的 Webhook URL

## 步骤 1: 创建飞书应用

1. 访问 [飞书开发者控制台](https://open.feishu.cn/app)
2. 点击 "创建企业自建应用"
3. 输入应用名称: `Smart Agent Wiki`
4. 选择应用图标
5. 记录 **App ID** 和 **App Secret**

## 步骤 2: 配置权限

在 "权限管理" 页面，添加以下权限：

| 权限 | 说明 |
|------|------|
| `docx:doc` | 读取文档 |
| `docx:doc:readonly` | 只读访问文档 |
| `contact:user.base:readonly` | 读取用户基本信息 |
| `wiki:wiki:readonly` | 读取知识库 |

## 步骤 3: 配置事件订阅

在 "事件订阅" 页面：

1. 输入 Request URL: `https://your-saw-domain/api/v1/webhooks/feishu`
2. 等待 URL 验证通过

订阅以下事件：

| 事件 | 说明 |
|------|------|
| `docx.doc.created_v1` | 文档创建 |
| `docx.doc.modified_v1` | 文档修改 |
| `docx.doc.deleted_v1` | 文档删除 |

## 步骤 4: 配置加密

飞书使用 AES-256-CBC 加密 Webhook 事件：

1. 在 "事件订阅" 页面生成 **Encrypt Key**
2. 配置到 SAW：

```bash
export FEISHU_ENCRYPT_KEY="your_encrypt_key"
```

## 步骤 5: 配置 SAW

设置环境变量：

```bash
export FEISHU_APP_ID="cli_xxxxxxxxx"
export FEISHU_APP_SECRET="xxxxxxxxxx"
export FEISHU_ENCRYPT_KEY="xxxxxxxxxx"
```

### 通过 CLI 连接

```bash
saw feishu connect
```

### 通过 Web UI

访问 `/integrations`，找到飞书卡片点击 Connect。

## 步骤 6: 发布应用

在应用管理页面：

1. 点击 "版本管理与发布"
2. 创建版本并申请发布
3. 管理员审批后应用生效

## 多租户模式

飞书支持多租户访问（用户授权）：

### 租户授权流程

1. 用户点击 "授权飞书"
2. 跳转到飞书授权页面
3. 用户同意后获取租户 token
4. 使用租户 token 访问用户数据

配置多租户：

```bash
saw feishu config --multi-tenant true
```

### 租户 Token 刷新

租户 token 会自动刷新，确保持续访问：

```bash
saw feishu token-refresh --tenant-id <tenant_id>
```

## 中文内容处理

飞书主要处理中文内容，SAW 会：

- 正确解析 UTF-8 编码
- 保留中文格式（标点、空格）
- 支持中文分词（可选）

## 故障排除

### 签名验证失败

检查 Encrypt Key 配置：

```bash
saw feishu verify-signature --test
```

### Token 刷新失败

手动刷新 App Access Token：

```bash
saw feishu refresh-app-token
```

### 编码问题

如果遇到中文乱码：

```bash
# 检查编码设置
saw feishu config --encoding utf-8

# 重新同步
saw feishu sync --force
```

## 配置参考

```bash
saw feishu config --help
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--multi-tenant` | false | 多租户模式 |
| `--sync-docs` | true | 同步文档 |
| `--sync-wiki` | true | 同步知识库 |
| `--encoding` | utf-8 | 编码方式 |
| `--batch-size` | 50 | 批量处理数 |

---

*最后更新: 2026-05-02*