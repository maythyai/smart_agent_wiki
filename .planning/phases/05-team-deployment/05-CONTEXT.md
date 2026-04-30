# Phase 5: Team Deployment - Context

**Gathered:** 2026-04-30
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous mode with Claude discretion)

<domain>
## Phase Boundary

**Goal:** 支持多用户团队协作部署模式

**Requirements:**
- TEAM-01: Docker Compose single-command deployment
- TEAM-02: PostgreSQL database support
- TEAM-03: Redis caching and session management
- TEAM-04: Multi-user registration and authentication
- TEAM-05: User roles (Admin, Editor, Viewer)
- TEAM-06: Per-user private vaults
- TEAM-07: Shared team vaults with permissions
- TEAM-08: Audit logs for all actions
- TEAM-09: Backup and restore functionality
- TEAM-10: Health check endpoints

**In Scope:**
- Docker Compose 部署配置
- PostgreSQL 数据库适配
- Redis 缓存层
- 用户认证系统
- 角色权限系统
- 私有/共享 Vault
- 审计日志
- 备份恢复
- 健康检查端点

**Out of Scope:**
- Kubernetes 部署（延迟到 v2.2+）
- SaaS 多租户模式
- SSO 集成（延迟到 v2.1）

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion — 技术架构决策

**1. 数据库迁移策略**
- **决策:** 使用 SQLAlchemy 2.0 + Alembic 进行数据库迁移
- **理由:** SQLAlchemy 是 Python 生态最成熟的 ORM，Alembic 提供可靠的迁移管理
- **实现:** 抽象数据库层，支持 SQLite（开发）和 PostgreSQL（生产）双模式

**2. 认证系统**
- **决策:** 使用 JWT + Refresh Token 模式
- **理由:** 无状态认证，适合分布式部署；Refresh Token 增强安全性
- **实现:** fastapi-users 库提供完整的用户管理

**3. 权限模型**
- **决策:** 扩展 Cedar 策略引擎支持用户角色
- **理由:** v1.1 已引入 Cedar，扩展而非替换保持一致性
- **实现:** Admin/Editor/Viewer 三角色 + 资源级权限控制

**4. Vault 隔离策略**
- **决策:** 每个用户有私有 Vault，团队有共享 Vault
- **理由:** 兼顾隐私和协作需求
- **实现:** Vault 表添加 owner_id 和 is_shared 字段

**5. Redis 使用场景**
- **决策:** 会话存储、查询缓存、任务队列
- **理由:** 减少数据库压力，加速常见查询
- **实现:** 使用 Redis 作为缓存层，数据库作为持久层

**6. Docker Compose 结构**
- **决策:** 分离服务容器：app, db, redis, nginx
- **理由:** 职责分离，便于扩展和维护
- **实现:** docker-compose.yml + docker-compose.prod.yml

</decisions>

<code_context>
## Existing Code Insights

### 现有架构 (v1.1)

**存储层:**
- `src/saw/storage/vault.py` — Vault 存储
- `src/saw/storage/claims.py` — Claims 存储
- `src/saw/storage/write_queue.py` — 写入队列

**认证相关 (v1.1 已有):**
- `src/saw/governance/cedar_policy.py` — Cedar 策略引擎
- `src/saw/governance/audit.py` — 审计日志（Ed25519 签名）

**Web API:**
- `src/saw/api/server.py` — FastAPI 应用
- `src/saw/api/routes/` — API 路由

**配置:**
- `src/saw/config.py` — 配置管理

### 集成点

1. **数据库抽象**
   - 当前使用 SQLite
   - 需要抽象为 SQLAlchemy Engine
   - 支持连接池（PostgreSQL）

2. **认证扩展**
   - 添加用户表
   - 添加 JWT 认证中间件
   - 扩展 API 路由需要认证

3. **Vault 扩展**
   - 添加 owner_id 字段
   - 添加 is_shared 字段
   - 添加权限检查

4. **缓存层**
   - 查询结果缓存
   - 会话存储
   - 任务队列（可选 Celery）

</code_context>

<specifics>
## Specific Ideas

### 1. 用户数据模型

```python
@dataclass
class User:
    id: str
    email: str
    hashed_password: str
    role: UserRole  # admin, editor, viewer
    created_at: datetime
    last_login: datetime
    is_active: bool

class UserRole(Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
```

### 2. Vault 权限模型

```sql
-- Vault 表扩展
ALTER TABLE vaults ADD COLUMN owner_id TEXT;
ALTER TABLE vaults ADD COLUMN is_shared BOOLEAN DEFAULT FALSE;

-- Vault 权限表
CREATE TABLE vault_permissions (
    vault_id TEXT,
    user_id TEXT,
    permission TEXT,  -- read, write, admin
    PRIMARY KEY (vault_id, user_id)
);
```

### 3. Docker Compose 结构

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379

  db:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
```

### 4. 审计日志扩展

```python
@dataclass
class AuditLog:
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    signature: str  # Ed25519 签名
```

### 5. 健康检查端点

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "version": __version__
    }

@app.get("/health/ready")
async def readiness_check():
    # 检查所有依赖是否就绪
    pass
```

</specifics>

<deferred>
## Deferred Ideas

### Kubernetes 部署
- 需要 Helm charts
- 需要 Ingress 配置
- 延迟到 v2.2+

### SSO 集成
- OAuth2 / OIDC
- LDAP / Active Directory
- 延迟到 v2.1

### SaaS 多租户
- 租户隔离
- 计费系统
- 延迟到 v3.0+

### 高可用配置
- 数据库主从复制
- Redis Sentinel
- 延迟到 v2.2+

</deferred>