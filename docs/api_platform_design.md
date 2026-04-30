# API Platform — 设计规范

> Phase 6: API Platform 实现规范

**Created:** 2026-04-30
**Milestone:** v2.0
**Status:** Design Complete

---

## 一、概述

### 1.1 目标

开放 Smart Agent Wiki 的 API 供第三方集成，支持 RESTful API、API Key 认证、速率限制、Swagger 文档、Webhook 推送、GraphQL 端点和批量操作。

### 1.2 范围

- RESTful API（所有 CRUD 操作）
- API Key 认证
- 速率限制（每 Key）
- OpenAPI/Swagger 文档
- Webhook 事件推送
- 批量导入导出
- GraphQL 端点
- API 版本控制

---

## 二、API 架构

### 2.1 版本化路由

```
/api/v1/
├── auth/           # 用户认证
│   ├── register
│   ├── login
│   └── refresh
├── vaults/         # 知识库管理
│   ├── GET /       # 列表
│   ├── POST /      # 创建
│   ├── GET /{id}   # 详情
│   ├── PUT /{id}   # 更新
│   └── DELETE /{id} # 删除
├── claims/         # 知识主张
│   ├── GET /       # 列表
│   ├── POST /      # 创建
│   └── GET /{id}
├── api-keys/       # API Key 管理
│   ├── POST /      # 创建
│   ├── GET /       # 列表
│   └── DELETE /{id}
├── webhooks/       # Webhook 管理
│   ├── POST /      # 创建
│   ├── GET /       # 列表
│   ├── POST /{id}/test
│   └── DELETE /{id}
├── bulk/           # 批量操作
│   ├── POST /import/vaults
│   ├── POST /import/claims/{vault_id}
│   ├── POST /export/vaults
│   └── GET /import/{task_id}/status
└── health/         # 健康检查
    ├── GET /health
    ├── GET /health/ready
    └── GET /metrics
```

### 2.2 认证流程

```
┌─────────────────────────────────────────────────────────────┐
│                    API Authentication                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  方式一: API Key (第三方集成)                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Authorization: ApiKey saw_abc123...                   │ │
│  │                                                        │ │
│  │  特点:                                                 │ │
│  │  - 长期有效（可设置过期）                              │ │
│  │  - 速率限制独立                                        │ │
│  │  - 权限控制更精细                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  方式二: JWT (用户登录)                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Authorization: Bearer eyJhbGc...                      │ │
│  │                                                        │ │
│  │  特点:                                                 │ │
│  │  - 短期有效（30分钟）                                  │ │
│  │  - Refresh Token 续期                                  │ │
│  │  - 与用户角色关联                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、速率限制

### 3.1 算法设计

使用 Redis 滑动窗口计数器：

```python
# Redis Key 格式
ratelimit:{api_key_id}:hour:{hour_timestamp}
ratelimit:{api_key_id}:day:{day_timestamp}

# 每次请求
hour_count = INCR ratelimit:{key}:hour:{ts}
day_count = INCR ratelimit:{key}:day:{ts}

# 设置过期
EXPIRE ratelimit:{key}:hour:{ts} 3600  # 1小时
EXPIRE ratelimit:{key}:day:{ts} 86400  # 1天
```

### 3.2 配置选项

| API Key 类型 | 每小时 | 每天 | 适用场景 |
|-------------|--------|------|---------|
| Default | 100 | 1000 | 一般用户 |
| Premium | 1000 | 10000 | 高频用户 |
| Enterprise | 无限制 | 无限制 | 企业客户 |

### 3.3 响应头

```http
X-RateLimit-Limit-Hour: 100
X-RateLimit-Remaining-Hour: 95
X-RateLimit-Limit-Day: 1000
X-RateLimit-Remaining-Day: 950
X-RateLimit-Reset-Hour: 1700000000
X-RateLimit-Reset-Day: 1700086400
```

---

## 四、Webhook 设计

### 4.1 事件类型

| 事件 | 描述 | 数据 |
|------|------|------|
| `ingest.complete` | 摄入完成 | vault_id, claim_ids |
| `claim.create` | Claim 创建 | claim_id, content |
| `claim.update` | Claim 更新 | claim_id, changes |
| `vault.create` | Vault 创建 | vault_id |
| `vault.delete` | Vault 删除 | vault_id |

### 4.2 签名验证

```python
# 服务端签名
signature = HMAC-SHA256(payload_json, webhook_secret)

# 请求头
X-SAW-Signature: abc123...
X-SAW-Event: ingest.complete
X-SAW-Timestamp: 1700000000

# 客户端验证
expected = HMAC-SHA256(payload, secret)
if signature != expected:
    reject()
```

### 4.3 重试策略

```
首次失败 → 等待 5 秒 → 第二次尝试
第二次失败 → 等待 10 秒 → 第三次尝试
第三次失败 → 记录失败，失败计数 +1

连续 10 次失败 → 自动禁用 Webhook
```

---

## 五、GraphQL Schema

### 5.1 类型定义

```graphql
type Vault {
  id: ID!
  name: String!
  ownerId: String!
  isShared: Boolean!
  createdAt: DateTime!
  claims(limit: Int = 10): [Claim!]!
}

type Claim {
  id: ID!
  vaultId: String!
  content: String!
  confidence: Float!
  createdAt: DateTime!
  mediaTimestamp: [Float]
}

type User {
  id: ID!
  email: String!
  role: String!
  vaults: [Vault!]!
}
```

### 5.2 查询示例

```graphql
# 获取 Vault 及关联 Claims
query {
  vault(id: "vault_123") {
    name
    claims(limit: 20) {
      content
      confidence
      createdAt
    }
  }
}

# 搜索 Claims
query {
  searchClaims(query: "机器学习", limit: 10) {
    id
    content
    vaultId
  }
}
```

### 5.3 Mutation 示例

```graphql
# 创建 Vault
mutation {
  createVault(name: "我的知识库") {
    id
    name
  }
}

# 更新 Vault
mutation {
  updateVault(id: "vault_123", name: "新名称") {
    id
    name
  }
}
```

---

## 六、批量操作

### 6.1 导入格式

**JSON 格式:**
```json
[
  {
    "name": "知识库 1",
    "entries": [
      {"content": "第一条知识", "source": "url"},
      {"content": "第二条知识", "source": "pdf"}
    ]
  }
]
```

**CSV 格式:**
```csv
content,source,confidence
第一条知识,url,0.9
第二条知识,pdf,0.8
```

### 6.2 导出格式

- **JSON**: 完整结构化数据
- **CSV**: 表格格式，适合分析
- **Markdown**: 文档格式，适合阅读
- **NDJSON**: 流式格式，大数据量

### 6.3 后台处理流程

```
上传文件 → 解析内容 → 创建任务 → 后台处理
                                   │
                                   ▼
                            更新进度到 Redis
                                   │
                                   ▼
                            完成后触发 Webhook
```

---

## 七、OpenAPI 文档

### 7.1 端点

| 端点 | 用途 |
|------|------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc UI |
| `/openapi.json` | OpenAPI 规范 |

### 7.2 文档配置

```python
app = FastAPI(
    title="Smart Agent Wiki API",
    version="2.0.0",
    description="多代理知识平台 API",
    openapi_tags=[
        {"name": "vaults", "description": "知识库管理"},
        {"name": "claims", "description": "知识主张"},
        {"name": "api-keys", "description": "API Key 管理"},
    ]
)
```

---

## 八、安全性考虑

### 8.1 API Key 安全

- SHA256 哈希存储（防止泄露）
- 原始 Key 仅显示一次
- 支持过期时间
- 支持撤销

### 8.2 速率限制安全

- 防止 DoS 攻击
- 独立 Key 独立限制
- 超限返回 429

### 8.3 Webhook 安全

- HMAC 签名验证
- HTTPS 要求
- IP 白名单（可选）

---

*Design document created: 2026-04-30*
*Milestone: v2.0 — Phase 6: API Platform*