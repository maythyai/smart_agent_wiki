# Team Deployment Architecture — 设计规范

> Phase 5: Team Deployment 实现规范

**Created:** 2026-04-30
**Milestone:** v2.0
**Status:** Design Complete

---

## 一、概述

### 1.1 目标

将 Smart Agent Wiki 从单用户本地应用扩展为多用户团队协作平台，支持 Docker Compose 部署、PostgreSQL 数据库、Redis 缓存、用户认证和权限管理。

### 1.2 范围

- Docker Compose 一键部署
- PostgreSQL 数据库支持（替代 SQLite）
- Redis 缓存层
- 多用户注册/登录
- 角色权限系统（Admin/Editor/Viewer）
- 私有/共享 Vault
- 审计日志
- 备份恢复
- 健康检查端点

### 1.3 核心设计原则

1. **渐进迁移** — 保持 SQLite 支持（开发），PostgreSQL 支持（生产）
2. **最小权限** — 用户默认 Viewer 角色，逐步授权
3. **审计透明** — 所有操作记录审计日志，Ed25519 签名保证不可篡改
4. **容器化部署** — Docker Compose 单命令启动完整系统
5. **健康可观测** — Kubernetes 探针兼容的健康检查端点

---

## 二、架构设计

### 2.1 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Deployment                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Nginx (反向代理)                    │   │
│  │  端口: 80 (HTTP → HTTPS), 443 (HTTPS)                 │   │
│  │  WebSocket: /ws 路径                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    App Container                      │   │
│  │  FastAPI + WebSocket                                  │   │
│  │  端口: 8000 (内部)                                    │   │
│  │  健康检查: /health, /health/live, /health/ready       │   │
│  └──────────────────────────────────────────────────────┘   │
│              │                       │                       │
│              ▼                       ▼                       │
│  ┌────────────────────┐    ┌────────────────────┐           │
│  │   PostgreSQL 16    │    │      Redis 7       │           │
│  │   主数据库         │    │   缓存 + 会话      │           │
│  │   数据持久化       │    │   减少数据库压力   │           │
│  └────────────────────┘    └────────────────────┘           │
│                                                              │
│  数据持久化:                                                │
│  - postgres_data volume (数据库)                            │
│  - redis_data volume (Redis AOF)                            │
│  - /app/data/vaults (Vault 文件)                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 认证架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Authentication Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐                                                │
│  │  用户    │                                                │
│  │  POST    │                                                │
│  │ /register│──────────────► 创建用户 (Viewer 角色)         │
│  └──────────┘                                                │
│                                                              │
│  ┌──────────┐                                                │
│  │  用户    │                                                │
│  │  POST    │                                                │
│  │ /login   │──────────────► 验证密码                        │
│  └──────────┘                    │                           │
│                                  ▼                           │
│                         ┌────────────────┐                   │
│                         │  JWT Token     │                   │
│                         │  Access (30min)│                   │
│                         │  Refresh (7d)  │                   │
│                         └────────────────┘                   │
│                                  │                           │
│                                  ▼                           │
│  ┌──────────┐     ┌──────────────────────────────────┐      │
│  │  API请求 │────►│ Authorization: Bearer <token>    │      │
│  │          │     │                                  │      │
│  │          │     │  ┌─────────────────────────────┐ │      │
│  │          │     │  │ 1. 解码 JWT                 │ │      │
│  │          │     │  │ 2. 查询 User 表            │ │      │
│  │          │     │  │ 3. 检查 is_active          │ │      │
│  │          │     │  │ 4. 检查 role (require_role)│ │      │
│  │          │     │  │ 5. 返回 User 对象          │ │      │
│  │          │     │  └─────────────────────────────┘ │      │
│  └──────────┘     └──────────────────────────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 权限模型

```
┌─────────────────────────────────────────────────────────────┐
│                    Permission Model                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  用户角色:                                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Role        │  Read  │  Write │  Delete │  Admin    │  │
│  ├──────────────┼────────┼────────┼─────────┼───────────┤  │
│  │  Admin       │   ✓    │   ✓    │    ✓    │     ✓     │  │
│  │  Editor      │   ✓    │   ✓    │    ✗    │     ✗     │  │
│  │  Viewer      │   ✓    │   ✗    │    ✗    │     ✗     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Vault 类型:                                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  类型        │  访问控制                               │  │
│  ├──────────────┼────────────────────────────────────────┤  │
│  │  Private     │  仅 Owner 可访问                        │  │
│  │  Shared      │  需显式授权 (vault_permissions 表)      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Cedar 策略:                                                  │
│  - Owner 自动拥有所有权限                                    │
│  - 权限通过 Cedar 策略引擎验证                               │
│  - Vault 级权限存储在 vault_permissions 表                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、核心组件设计

### 3.1 数据库层

#### SQLAlchemy 模型

```python
# src/saw/db/models.py

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class Vault(Base):
    __tablename__ = "vaults"
    id = Column(String, primary_key=True)
    name = Column(String)
    owner_id = Column(String, ForeignKey("users.id"))
    is_shared = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # ... 其他现有字段

class VaultPermission(Base):
    __tablename__ = "vault_permissions"
    vault_id = Column(String, ForeignKey("vaults.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    permission = Column(String, default="read")  # read, write, admin

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    signature = Column(String)  # Ed25519 签名
```

#### 数据库配置

```python
# src/saw/config.py

@dataclass
class DatabaseConfig:
    url: str = "sqlite:///saw.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

    @property
    def async_url(self) -> str:
        if self.url.startswith("postgresql"):
            return self.url.replace("postgresql://", "postgresql+asyncpg://")
        return self.url
```

### 3.2 认证系统

#### JWT 配置

```python
# src/saw/config.py

@dataclass
class AuthConfig:
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
```

#### Token 结构

```json
{
  "sub": "user_abc123",
  "exp": 1700000000,
  "iat": 1699999000,
  "role": "editor"
}
```

### 3.3 缓存层

#### Redis 使用场景

| 场景 | TTL | 示例 Key |
|------|-----|---------|
| 查询缓存 | 5 分钟 | `saw:query:user_abc:page_1` |
| 会话存储 | 1 小时 | `saw:session:user_abc` |
| Vault 元数据缓存 | 10 分钟 | `saw:vault:vault_123:meta` |
| 热点 Claims | 30 分钟 | `saw:claim:claim_789` |

#### 缓存装饰器

```python
@cache_result(ttl=timedelta(minutes=5))
async def get_vault_claims(self, vault_id: str) -> List[Claim]:
    # 自动缓存结果
    pass
```

---

## 四、Docker 配置

### 4.1 docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://saw:saw@db:5432/saw
      - REDIS_URL=redis://redis:6379/0
      - AUTH_SECRET_KEY=${AUTH_SECRET_KEY}
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: saw
      POSTGRES_PASSWORD: saw
      POSTGRES_DB: saw
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### 4.2 启动命令

```bash
# 开发环境
docker compose -f docker/docker-compose.yml up -d

# 生产环境
docker compose -f docker/docker-compose.prod.yml up -d
```

---

## 五、健康检查

### 5.1 端点定义

| 端点 | 用途 | 检查项 |
|------|------|--------|
| `/health` | 基础检查 | 应用存活 |
| `/health/live` | Kubernetes 存活探针 | 进程存活 |
| `/health/ready` | Kubernetes 就绪探针 | 数据库 + Redis |
| `/metrics` | Prometheus 指标 | 用户数/Vault数/Claims数 |

### 5.2 响应示例

```json
// GET /health
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-04-30T00:00:00Z"
}

// GET /health/ready
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

---

## 六、备份策略

### 6.1 备份内容

| 内容 | 方法 | 频率 |
|------|------|------|
| PostgreSQL 数据库 | `pg_dump` | 每日 2:00 AM |
| Redis 数据 | `redis-cli SAVE` | 每日 2:00 AM |
| Vault 文件 | `tar` 归档 | 每日 2:00 AM |

### 6.2 保留策略

- 保留最近 7 天的备份
- 自动清理超过 7 天的备份文件
- 备份文件命名格式: `saw_backup_YYYYMMDD_HHMMSS.tar.gz`

---

## 七、审计日志

### 7.1 记录内容

| 字段 | 说明 |
|------|------|
| user_id | 操作用户 ID |
| action | 操作类型 (create, read, update, delete) |
| resource_type | 资源类型 (vault, claim, user) |
| resource_id | 资源 ID |
| timestamp | 操作时间 |
| ip_address | 用户 IP |
| signature | Ed25519 签名（防篡改） |

### 7.2 关键操作记录

- 用户注册/登录
- Vault 创建/删除
- Claim 写入
- 权限授予/撤销
- 备份恢复操作

---

## 八、迁移指南

### 8.1 从 SQLite 迁移到 PostgreSQL

1. 导出 SQLite 数据：
   ```bash
   sqlite3 saw.db .dump > saw_dump.sql
   ```

2. 转换 SQL：
   ```bash
   # 修改 SQLite 特有语法为 PostgreSQL 语法
   sed -i 's/AUTOINCREMENT/SERIAL/' saw_dump.sql
   sed -i 's/INTEGER PRIMARY KEY/SERIAL PRIMARY KEY/' saw_dump.sql
   ```

3. 导入 PostgreSQL：
   ```bash
   psql -U saw -d saw -f saw_dump.sql
   ```

### 8.2 配置切换

```python
# 开发环境 (SQLite)
DATABASE_URL = "sqlite:///saw.db"

# 生产环境 (PostgreSQL)
DATABASE_URL = "postgresql://saw:password@db:5432/saw"
```

---

## 九、测试策略

### 9.1 单元测试

- 认证模块测试
- 权限检查测试
- 缓存操作测试

### 9.2 集成测试

- Docker Compose 启动测试
- 健康检查端点测试
- 备份恢复流程测试

### 9.3 性能测试

- PostgreSQL 连接池测试
- Redis 缓存命中率测试
- 多用户并发测试

---

## 十、安全性考虑

### 10.1 认证安全

- 密码使用 bcrypt 哈希（防止彩虹表）
- JWT 签名验证（防止伪造）
- Refresh Token 单独存储（防止泄露）

### 10.2 权限安全

- Cedar 策略引擎（防止绕过）
- 最小权限原则（防止滥用）
- Owner 自动全权限（防止意外拒绝）

### 10.3 数据安全

- PostgreSQL SSL 连接（防止监听）
- Redis 访问控制（防止未授权）
- Vault 文件加密（可选）

---

*Design document created: 2026-04-30*
*Milestone: v2.0 — Phase 5: Team Deployment*