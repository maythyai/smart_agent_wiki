# WeCom Connector Guide

企业微信（WeCom）是腾讯的企业沟通平台。SAW 的企业微信连接器通过 Webhook 接收消息事件，支持 AES 加密和多种消息类型。

## 前提条件

- 企业微信企业管理员权限
- SAW Web 服务器运行中
- 公网可访问的 Webhook URL（需 HTTPS）

## 步骤 1: 创建企业微信应用

1. 登录 [企业微信管理后台](https://work.weixin.qq.com/wework_admin/frame)
2. 进入 "应用管理" → "自建应用"
3. 点击 "创建应用"
4. 填写应用信息：
   - 应用名称: `Smart Agent Wiki`
   - 应用logo: 上传图标
   - 可见范围: 选择部门或成员

5. 记录以下信息：
   - **AgentId**
   - **Secret**

## 步骤 2: 获取企业信息

在企业微信管理后台 "我的企业" 页面记录：

- **CorpID** (企业 ID)

## 步骤 3: 配置接收消息

在应用设置页面 "接收消息" 部分：

1. 设置 API 接收
2. 输入以下 URL: `https://your-saw-domain/api/v1/webhooks/wecom`
3. 生成并记录 **Token** 和 **EncodingAESKey**

### AES 加密配置

企业微信使用 AES-256-CBC 加密消息：

```bash
export WECOM_TOKEN="your_token"
export WECOM_ENCODING_AES_KEY="your_aes_key"  # 43位 Base64 编码
```

## 步骤 4: 配置可信域名

在应用设置 "企业可信IP" 部分：

1. 添加 SAW 服务器 IP
2. 或配置可信域名

## 步骤 5: 配置 SAW

设置环境变量：

```bash
export WECOM_CORP_ID="wwxxxxxxxxxxxx"
export WECOM_AGENT_ID="1000001"
export WECOM_SECRET="xxxxxxxxxx"
export WECOM_TOKEN="your_token"
export WECOM_ENCODING_AES_KEY="your_aes_key"
```

### 通过 CLI 连接

```bash
saw wecom connect
```

### 通过 Web UI

访问 `/integrations`，找到 WeCom 卡片点击 Connect。

## 步骤 6: 验证配置

```bash
saw wecom verify
```

这会验证：
- API 连接
- Token 有效性
- 加密配置

## 消息解析

### 消息类型支持

| 消息类型 | 支持 | 说明 |
|----------|------|------|
| text | ✅ | 文本消息 |
| image | ✅ | 图片（保存链接） |
| voice | ❌ | 语音 |
| video | ❌ | 视频 |
| file | ✅ | 文件（保存链接） |
| mixed | ✅ | 图文混合 |

### 消息解密

Webhook 消息解密流程：

1. 接收 Base64 编码的加密消息
2. 使用 EncodingAESKey 解密
3. 验证签名
4. 解析 XML 消息体

SAW 自动处理解密过程。

## 故障排除

### 签名验证失败

常见原因：

1. Token 或 AES Key 配置错误
2. 时间戳偏差过大
3. 消息被篡改

检查配置：

```bash
saw wecom test-encryption
```

### 加密错误

如果遇到 `AES decrypt failed`：

1. 确认 EncodingAESKey 正确（43位）
2. 检查是否使用正确的编码

```bash
saw wecom config --aes-key "your_43_char_key"
```

### 消息格式错误

企业微信消息为 XML 格式：

```bash
# 查看原始消息
saw wecom debug --show-raw
```

## 配置参考

```bash
saw wecom config --help
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--sync-messages` | true | 同步消息 |
| `--message-types` | text,image,file | 消息类型 |
| `--max-messages` | 10000 | 最大消息数 |
| `--batch-size` | 100 | 批量处理数 |

## 安全建议

1. **IP 白名单**: 在企业微信后台配置服务器 IP 白名单
2. **HTTPS**: 确保 Webhook URL 使用 HTTPS
3. **Token 轮换**: 定期更新 Token 和 AES Key
4. **日志审计**: 开启操作日志

```bash
saw wecom config --audit-logging true
```

---

*最后更新: 2026-05-02*