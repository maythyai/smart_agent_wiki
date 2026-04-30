# Phase 6: API Platform - Context

**Gathered:** 2026-04-30
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous mode with Claude discretion)

<domain>
## Phase Boundary

**Goal:** 开放 API 供第三方集成

**Requirements:**
- APIP-01: RESTful API for CRUD operations
- APIP-02: API key authentication
- APIP-03: Rate limiting per API key
- APIP-04: OpenAPI/Swagger auto-documentation
- APIP-05: Webhook support for ingestion events
- APIP-06: Bulk import/export via API
- APIP-07: GraphQL endpoint
- APIP-08: API versioning (v1/ prefix)

**In Scope:**
- RESTful API 端点
- API Key 认证
- 速率限制
- Swagger 文档自动生成
- Webhook 事件推送
- 批量导入导出
- GraphQL 端点
- API 版本控制

**Out of Scope:**
- OAuth2 认证（延迟到 v2.1）
- API 管理平台（延迟到 v3.0）
- GraphQL 订阅（延迟到 v2.1）

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion — 技术架构决策

**1. API 认证策略**
- **决策:** API Key + JWT 双模式认证
- **理由:** API Key 适用于第三方集成，JWT 适用于用户登录
- **实现:** 请求头 `Authorization: ApiKey xxx` 或 `Bearer xxx`

**2. 速率限制实现**
- **决策:** 使用 Redis 计数器 + 滑动窗口算法
- **理由:** Redis 高性能，滑动窗口精确控制
- **实现:** 每个 API Key 配置独立速率限制

**3. Swagger 文档**
- **决策:** 使用 FastAPI 内置 OpenAPI 支持
- **理由:** FastAPI 自动生成文档，无需额外配置
- **实现:** `/docs` Swagger UI, `/redoc` ReDoc UI

**4. Webhook 设计**
- **决策:** 异步推送 + 重试机制 + 签名验证
- **理由:** 确保 Webhook 可靠送达，防止伪造
- **实现:** 任务队列 + 3 次重试 + HMAC-SHA256 签名

**5. GraphQL 实现**
- **决策:** 使用 strawberry 库
- **理由:** strawberry 是现代 Python GraphQL 库，FastAPI 集成良好
- **实现:** `/graphql` 端点 + Apollo 格式兼容

**6. API 版本控制**
- **决策:** URL 路径版本控制 `/api/v1/`
- **理由:** 简单明确，便于缓存和路由
- **实现:** 版本路由器分离

</decisions>

<code_context>
## Existing Code Insights

### 现有 API (v1.1)

**文件:**
- `src/saw/api/server.py` — FastAPI 应用
- `src/saw/api/routes/` — API 路由目录

**现有端点:**
- MCP Server (23 个工具)
- CLI 命令行入口
- Web UI 后端接口

**认证:**
- Phase 5 添加的 JWT 认证

### 集成点

1. **API Key 表**
   - 新增 `api_keys` 表存储 API Key
   - 关联到用户或团队

2. **速率限制中间件**
   - 使用 Redis 计数器
   - 配置可按 API Key 定制

3. **Webhook 任务队列**
   - 使用 Redis 作为任务队列
   - 或集成 Celery（可选）

4. **GraphQL Schema**
   - 定义 Vault, Claim, User 类型
   - 查询和 Mutation 操作

</code_context>

<specifics>
## Specific Ideas

### 1. API Key 数据模型

```python
@dataclass
class APIKey:
    id: str
    key: str  # hashed
    name: str
    user_id: str
    rate_limit: int  # requests per hour
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    permissions: List[str]  # read, write, admin
```

### 2. 速率限制配置

```python
@dataclass
class RateLimitConfig:
    requests_per_hour: int = 100
    requests_per_day: int = 1000
    burst_size: int = 10
```

### 3. Webhook 配置

```python
@dataclass
class WebhookConfig:
    url: str
    events: List[str]  # ingest.complete, claim.create, etc.
    secret: str  # HMAC 签名密钥
    retry_count: int = 3
    retry_delay_seconds: int = 5
```

### 4. GraphQL Schema

```python
import strawberry

@strawberry.type
class VaultType:
    id: str
    name: str
    owner_id: str
    is_shared: bool
    claims: List[ClaimType]

@strawberry.type
class Query:
    @strawberry.field
    async def vault(self, id: str) -> VaultType:
        ...

    @strawberry.field
    async def vaults(self, limit: int = 10) -> List[VaultType]:
        ...

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_vault(self, name: str) -> VaultType:
        ...
```

### 5. Webhook 签名验证

```python
def generate_webhook_signature(payload: dict, secret: str) -> str:
    import hmac
    import hashlib
    body = json.dumps(payload, sort_keys=True)
    return hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_webhook_signature(
    payload: dict,
    signature: str,
    secret: str
) -> bool:
    expected = generate_webhook_signature(payload, secret)
    return hmac.compare_digest(signature, expected)
```

</specifics>

<deferred>
## Deferred Ideas

### OAuth2 认证
- 支持第三方 OAuth2 Provider
- 延迟到 v2.1

### GraphQL 订阅
- 实时更新推送
- 需要 WebSocket 集成
- 延迟到 v2.1

### API 管理平台
- API 使用分析
- 计费系统
- 延迟到 v3.0+

### SDK 生成
- 自动生成 Python/JS SDK
- 延迟到 v2.2+

</deferred>