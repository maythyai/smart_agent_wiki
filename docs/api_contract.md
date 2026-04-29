# Smart Agent Wiki — API 合约设计

> RESTful API + WebSocket + MCP 工具映射的完整接口规范
>
> 日期：2026-04-25

---

## 一、设计原则

| 原则 | 说明 |
|------|------|
| URL 前缀版本化 | `/api/v1/`，破坏性变更递增版本号 |
| Cursor-based 分页 | 大数据集不分页用 offset，用 cursor（基于 UUID + created_at） |
| 幂等写入 | 写入操作通过 `op_id` 去重，重复请求返回相同结果 |
| 统一错误格式 | 所有错误遵循 RFC 7807 Problem Details |
| 双协议并行 | HTTP API + MCP 工具覆盖相同功能，共享核心逻辑 |

---

## 二、认证

### 模式 A：单用户桌面（默认）

```
Authorization: Bearer <api_key>
```

- `saw init` 生成随机 API Key，存储在 `.saw/config.yaml`
- CLI/Web/桌面端共用同一 Key
- 本地模式下 Key 可为空（信任本地请求）

### 模式 B：团队部署

```
Authorization: Bearer <jwt_token>
```

- JWT 签发，包含 `sub`（用户 ID）、`role`（admin/editor/viewer）、`exp`
- RBAC 映射：admin（全权限）、editor（读写）、viewer（只读）

---

## 三、统一错误格式

```json
{
  "type": "https://saw.dev/errors/{error_code}",
  "title": "Human readable title",
  "status": 400,
  "detail": "Specific error description",
  "instance": "/api/v1/ingest/abc-123",
  "request_id": "req-uuid"
}
```

### 错误码体系

| HTTP 状态码 | 业务错误码 | 含义 |
|------------|-----------|------|
| 400 | `INVALID_INPUT` | 请求参数校验失败 |
| 400 | `SCHEMA_VIOLATION` | 请求体不符合 JSON Schema |
| 401 | `UNAUTHENTICATED` | 缺少或无效的认证凭据 |
| 403 | `FORBIDDEN` | 权限不足（Cedar 策略拒绝） |
| 404 | `NOT_FOUND` | 资源不存在 |
| 409 | `CONFLICT` | 资源冲突（如重复 op_id） |
| 409 | `CONTRADICTION_DETECTED` | 摄入时检测到矛盾 |
| 422 | `UNPROCESSABLE` | 文档解析失败 |
| 422 | `LLM_ERROR` | LLM 调用失败 |
| 429 | `RATE_LIMITED` | 请求频率超限 |
| 500 | `INTERNAL_ERROR` | 服务内部错误 |
| 503 | `SINK_UNHEALTHY` | 存储后端不健康 |
| 503 | `LLM_UNAVAILABLE` | LLM 服务不可用 |

---

## 四、分页规范

### Cursor-based Pagination

```
GET /api/v1/claims?cursor=eyJjcmVhdGVkX2F0IjoiMjAyNi...
                      &limit=20
                      &order=desc
```

**响应格式：**

```json
{
  "data": [...],
  "pagination": {
    "has_more": true,
    "next_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNi0wNC0y...",
    "total_count": 1234
  }
}
```

- `cursor`：Base64 编码的 JSON `{"created_at": "...", "uuid": "..."}`
- `limit`：每页条数，默认 20，最大 100
- `order`：`asc` 或 `desc`，默认 `desc`

---

## 五、API 路由设计

### 5.1 通用接口

#### `GET /api/v1/health`

健康检查。

**响应：**

```json
{
  "status": "healthy",
  "version": "0.3.0",
  "sinks": {
    "vault": "healthy",
    "claims": "healthy",
    "fts5": "healthy",
    "vector": "not_configured"
  },
  "llm": {
    "default": "anthropic/claude-sonnet-4-20250514",
    "available": ["anthropic/claude-sonnet-4-20250514", "anthropic/claude-haiku-4-5-20251001"]
  }
}
```

#### `GET /api/v1/status`

知识库状态概览。

**响应：**

```json
{
  "vault": {"document_count": 42, "total_size_mb": 128.5},
  "claims": {"total": 1234, "by_confidence": {"1": 120, "2": 450, "3": 500, "4": 164}},
  "wiki": {"page_count": 89, "orphan_pages": 3},
  "graph": {"entities": 210, "relations": 340},
  "outbox": {"pending": 0, "failed": 0, "dead_letter": 2}
}
```

---

### 5.2 摄入引擎（Ingest）

#### `POST /api/v1/ingest`

摄入文档。

**请求：**

```json
{
  "source": "file",
  "path": "/path/to/paper.pdf",
  "options": {
    "extract_method": "auto",
    "llm_model": "auto",
    "skip_contradiction_check": false,
    "tags": ["paper", "transformer"],
    "session_id": "optional-session-uuid"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | string | 是 | `file` / `url` / `text` |
| `path` | string | 条件 | 文件路径（source=file） |
| `url` | string | 条件 | URL（source=url） |
| `content` | string | 条件 | 纯文本内容（source=text） |
| `options.extract_method` | string | 否 | `auto` / `ast` / `llm`，默认 auto |
| `options.llm_model` | string | 否 | `auto` / 指定模型名，默认 auto |
| `options.skip_contradiction_check` | bool | 否 | 默认 false |
| `options.tags` | string[] | 否 | 附加标签 |
| `options.session_id` | string | 否 | 会话 ID |

**响应（202 Accepted）：**

```json
{
  "job_id": "job-uuid",
  "status": "processing",
  "status_url": "/api/v1/ingest/job-uuid/status"
}
```

#### `GET /api/v1/ingest/{job_id}/status`

查询摄入进度。

**响应：**

```json
{
  "job_id": "job-uuid",
  "status": "completed",
  "stage": "validate",
  "progress": 0.85,
  "result": {
    "claims_extracted": 12,
    "entities_found": 8,
    "contradictions_detected": 1,
    "new_pages_created": 3,
    "duration_seconds": 15.3,
    "cost_usd": 0.023,
    "model_used": "claude-sonnet-4-20250514"
  }
}
```

`status` 枚举：`queued` → `parsing` → `extracting` → `fusing` → `validating` → `completed` / `failed`

#### `GET /api/v1/ingest/history`

摄入历史记录。支持 cursor 分页。

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `cursor` | string | 分页游标 |
| `limit` | int | 每页条数 |
| `status` | string | 过滤状态：`completed` / `failed` |
| `since` | string | ISO 8601，起始时间 |

---

### 5.3 查询引擎（Query）

#### `POST /api/v1/query`

查询知识库，返回带溯源链的合成回答。

**请求：**

```json
{
  "question": "为什么 Transformer 取代了 RNN？",
  "mode": "auto",
  "depth": "L3",
  "max_tokens": 2000,
  "include_sources": true,
  "session_id": "optional"
}
```

| 字段 | 说明 |
|------|------|
| `mode` | `auto` / `search` / `graph` / `reasoning` / `compare` / `synthesize` |
| `depth` | `L1`（标题）/ `L2`（摘要）/ `L3`（结论+主张）/ `L4`（全文） |
| `max_tokens` | 回答 token 上限 |
| `include_sources` | 是否包含溯源信息 |

**响应：**

```json
{
  "answer": "Transformer 通过自注意力机制...",
  "depth": "L3",
  "sources": [
    {
      "claim_uuid": "claim-uuid-1",
      "content": "Transformer 的自注意力机制允许并行计算...",
      "confidence": 3,
      "source_mark": "extracted",
      "vault_uuid": "doc-uuid-1",
      "location": {"page": 5, "paragraph": 2}
    }
  ],
  "related_pages": ["transformer", "rnn", "attention-mechanism"],
  "meta": {
    "model_used": "claude-opus-4-20250918",
    "tokens_used": 1850,
    "cost_usd": 0.012,
    "coverage_score": 0.82,
    "research_on_miss_triggered": false
  }
}
```

#### `POST /api/v1/search`

关键词/语义搜索。

**请求：**

```json
{
  "query": "transformer attention mechanism",
  "mode": "hybrid",
  "filters": {
    "claim_type": ["fact", "definition"],
    "confidence_min": 2,
    "freshness_max": 6,
    "tags": ["nlp"],
    "date_range": {"from": "2025-01-01"}
  },
  "limit": 20,
  "offset": 0
}
```

`mode` 枚举：`bm25` / `vector` / `hybrid` / `tree`

**响应：**

```json
{
  "results": [
    {
      "claim_uuid": "...",
      "content": "...",
      "score": 0.95,
      "highlights": ["<em>transformer</em> <em>attention</em>..."],
      "confidence": 3,
      "claim_type": "fact",
      "source_count": 2
    }
  ],
  "total": 45,
  "mode_used": "hybrid"
}
```

#### `GET /api/v1/graph/{node_id}`

查询知识图谱中某节点的邻居和关系。

**查询参数：**

| 参数 | 说明 |
|------|------|
| `depth` | 遍历深度，默认 1，最大 3 |
| `relation_types` | 过滤关系类型，逗号分隔 |
| `limit` | 每层最大节点数，默认 20 |

**响应：**

```json
{
  "center": {"uuid": "entity-uuid", "name": "Transformer", "type": "concept"},
  "nodes": [
    {"uuid": "...", "name": "RNN", "type": "concept", "distance": 1}
  ],
  "edges": [
    {"from": "Transformer", "to": "RNN", "type": "evolves_from", "strength": 0.8}
  ]
}
```

#### `POST /api/v1/compare`

对比两个页面或两组主张。

**请求：**

```json
{
  "targets": [
    {"type": "page", "id": "transformer"},
    {"type": "page", "id": "rnn"}
  ],
  "aspects": ["performance", "architecture", "use_cases"],
  "depth": "L3"
}
```

**响应：**

```json
{
  "comparison": {
    "summary": "Transformer 和 RNN 在架构上的核心差异...",
    "aspects": {
      "performance": {"transformer": "...", "rnn": "...", "verdict": "..."},
      "architecture": {"transformer": "...", "rnn": "...", "verdict": "..."}
    },
    "shared_claims": ["claim-uuid-1"],
    "contradicting_claims": ["claim-uuid-2", "claim-uuid-3"]
  }
}
```

#### `POST /api/v1/compile`

手动触发上下文编译。

**请求：**

```json
{
  "topic": "transformer architecture",
  "max_tokens": 4000,
  "confidence_min": 2,
  "include_relations": true
}
```

---

### 5.4 治理引擎（Govern）

#### `GET /api/v1/claims/{claim_id}`

获取主张详情。

**响应：**

```json
{
  "uuid": "claim-uuid",
  "content": "...",
  "confidence": 3,
  "source_mark": "extracted",
  "freshness": 2,
  "temperature": "warm",
  "lifecycle": "strategic",
  "review_status": "approved",
  "claim_type": "fact",
  "tags": ["nlp", "transformer"],
  "sources": [
    {"vault_uuid": "...", "page": 5, "paragraph": 2, "surrounding_text": "..."}
  ],
  "relations": [
    {"to_claim": "...", "type": "supports", "strength": 0.9}
  ],
  "entities": [
    {"uuid": "...", "name": "Transformer", "role": "subject"}
  ],
  "audit_trail": [
    {"agent": "Writer", "operation": "create", "timestamp": "..."}
  ],
  "created_at": "...",
  "updated_at": "..."
}
```

#### `PATCH /api/v1/claims/{claim_id}/confidence`

更新主张置信度。

**请求：**

```json
{
  "confidence": 4,
  "reason": "Cross-validated with 3 sources"
}
```

#### `GET /api/v1/contradictions`

列出矛盾记录。

**查询参数：**

| 参数 | 说明 |
|------|------|
| `status` | `pending` / `resolved` / `escalated` |
| `type` | `temporal` / `factual` / `opinion` |
| `cursor` | 分页游标 |
| `limit` | 每页条数 |

#### `POST /api/v1/contradictions/{id}/resolve`

处理矛盾。

**请求：**

```json
{
  "strategy": "Superseded",
  "winning_claim": "claim-uuid-b",
  "note": "Newer research supersedes earlier findings"
}
```

#### `POST /api/v1/verify`

触发主张验证。

**请求：**

```json
{
  "claim_ids": ["uuid1", "uuid2"],
  "verification_mode": "cross_source"
}
```

#### `POST /api/v1/lint`

健康检查。

**请求：**

```json
{
  "scope": "full",
  "checks": ["freshness", "contradictions", "completeness", "index", "orphans"]
}
```

**响应：**

```json
{
  "report": {
    "overall_health": 0.85,
    "total_claims": 1234,
    "freshness_distribution": {"0-2": 800, "3-5": 300, "6-8": 134},
    "contradictions": {"pending": 5, "resolved": 12},
    "orphan_pages": 3,
    "broken_links": 1,
    "missing_metadata": 8,
    "suggestions": ["Consider upgrading to hierarchical index (>50 pages)"]
  }
}
```

#### `POST /api/v1/blast-radius`

查看修改影响范围。

**请求：**

```json
{
  "target_type": "claim",
  "target_id": "claim-uuid",
  "depth": 2
}
```

**响应：**

```json
{
  "direct_impacts": 3,
  "indirect_impacts": 7,
  "affected_pages": ["transformer", "attention-mechanism"],
  "affected_claims": ["uuid1", "uuid2", "uuid3"],
  "risk_level": "medium"
}
```

---

### 5.5 学习引擎（Learn）

#### `POST /api/v1/feedback`

提交行为反馈。

**请求：**

```json
{
  "type": "approved",
  "context": {
    "page_id": "transformer",
    "action": "query_answer",
    "detail": "用户接受了带溯源链的回答格式"
  }
}
```

`type` 枚举：`approved` / `rejected`

#### `POST /api/v1/distill`

触发认知蒸馏。

**请求：**

```json
{
  "scope": "all",
  "min_pattern_occurrences": 3
}
```

**响应：**

```json
{
  "sops_extracted": 2,
  "sops": [
    {
      "category": "query_format",
      "pattern": "用户偏好表格形式的对比",
      "rule": "对比查询使用表格输出",
      "evidence_count": 5
    }
  ]
}
```

#### `GET /api/v1/sop`

列出已提取的 SOP。

#### `POST /api/v1/prune`

触发知识过期修剪。

**请求：**

```json
{
  "dry_run": true,
  "scope": "tactical_only"
}
```

**响应：**

```json
{
  "would_prune": 15,
  "items": [
    {"uuid": "...", "reason": "tactical + freshness 8 + 60% overlap with strategic claim"}
  ]
}
```

#### `GET /api/v1/trends`

知识库趋势分析。

**查询参数：**

| 参数 | 说明 |
|------|------|
| `period` | `7d` / `30d` / `90d` |
| `metric` | `growth` / `hot_topics` / `coverage_gaps` |

#### `GET /api/v1/wip`

读取跨会话工作动量。

#### `PUT /api/v1/wip`

更新工作动量文件。

---

### 5.6 协作引擎（Collaborate）

#### `POST /api/v1/workflows`

执行 YAML 工作流。

**请求：**

```json
{
  "workflow": "literature_review",
  "params": {
    "query": "transformer variants"
  },
  "async": true
}
```

**响应（202 Accepted）：**

```json
{
  "workflow_id": "wf-uuid",
  "status": "running",
  "steps_total": 4,
  "steps_completed": 0,
  "status_url": "/api/v1/workflows/wf-uuid/status"
}
```

#### `GET /api/v1/workflows/{id}/status`

查询工作流执行状态。

**响应：**

```json
{
  "workflow_id": "wf-uuid",
  "status": "running",
  "current_step": 2,
  "steps": [
    {"name": "search", "agent": "Librarian", "status": "completed"},
    {"name": "synthesize", "agent": "Scholar", "status": "running"},
    {"name": "review", "agent": "Critic", "status": "pending", "gate": "confidence >= 3"},
    {"name": "publish", "agent": "Writer", "status": "pending"}
  ]
}
```

---

### 5.7 Wiki 页面管理

#### `GET /api/v1/pages`

列出 Wiki 页面。支持 cursor 分页和过滤。

**查询参数：**

| 参数 | 说明 |
|------|------|
| `cursor` | 分页游标 |
| `limit` | 每页条数 |
| `type` | 页面类型过滤 |
| `tag` | 标签过滤 |
| `sort` | `updated` / `created` / `name` |

#### `GET /api/v1/pages/{page_id}`

获取 Wiki 页面内容。

**查询参数：**

| 参数 | 说明 |
|------|------|
| `depth` | `L1` / `L2` / `L3` / `L4` |
| `include_claims` | 是否展开内联主张，默认 true |

#### `PUT /api/v1/pages/{page_id}`

更新 Wiki 页面（人工编辑）。

**请求：**

```json
{
  "content": "Updated markdown content...",
  "message": "Human edit: corrected factual error",
  "mark_human_edited": true
}
```

---

## 六、WebSocket 协议

### 6.1 连接

```
ws://localhost:8000/api/v1/ws?token=<api_key>
```

### 6.2 消息格式

所有消息为 JSON，包含 `type` 字段标识类型。

```json
{
  "type": "message_type",
  "data": {...},
  "timestamp": "2026-04-25T10:00:00Z"
}
```

### 6.3 客户端 → 服务端

| type | 说明 | data |
|------|------|------|
| `subscribe` | 订阅事件主题 | `{"topics": ["ingest", "query", "govern"]}` |
| `unsubscribe` | 取消订阅 | `{"topics": ["ingest"]}` |
| `ping` | 心跳 | 无 |

### 6.4 服务端 → 客户端

| type | 说明 | data |
|------|------|------|
| `ingest_progress` | 摄入进度 | `{"job_id": "...", "stage": "extracting", "progress": 0.5}` |
| `ingest_complete` | 摄入完成 | `{"job_id": "...", "result": {...}}` |
| `query_result` | 查询结果 | `{"answer": "...", "sources": [...]}` |
| `claim_updated` | 主张更新 | `{"claim_uuid": "...", "changes": {...}}` |
| `contradiction_found` | 矛盾发现 | `{"uuid": "...", "type": "factual", "claims": [...]}` |
| `workflow_step` | 工作流步骤 | `{"workflow_id": "...", "step": 2, "status": "completed"}` |
| `agent_action` | Agent 操作 | `{"agent": "Writer", "action": "create_page", "target": "..."}` |
| `pong` | 心跳响应 | 无 |

### 6.5 订阅主题

| 主题 | 事件 |
|------|------|
| `ingest` | 摄入进度、完成、失败 |
| `query` | 查询结果 |
| `govern` | 主张更新、矛盾发现、审核变更 |
| `learn` | SOP 提取、知识修剪 |
| `collaborate` | 工作流步骤、Agent 操作 |
| `*` | 所有事件 |

---

## 七、MCP 工具 → HTTP API 映射

| MCP 工具 | HTTP 方法 | URL |
|----------|----------|-----|
| `saw_ingest` | POST | `/api/v1/ingest` |
| `saw_query` | POST | `/api/v1/query` |
| `saw_search` | POST | `/api/v1/search` |
| `saw_tree_search` | POST | `/api/v1/search`（mode=tree） |
| `saw_graph` | GET | `/api/v1/graph/{node_id}` |
| `saw_compare` | POST | `/api/v1/compare` |
| `saw_compile` | POST | `/api/v1/compile` |
| `saw_lint` | POST | `/api/v1/lint` |
| `saw_conflicts` | GET | `/api/v1/contradictions` |
| `saw_verify` | POST | `/api/v1/verify` |
| `saw_freshness` | GET | `/api/v1/status`（含 freshness 分布） |
| `saw_review` | PATCH | `/api/v1/claims/{id}/review` |
| `saw_audit` | GET | `/api/v1/audit/{target_type}/{target_id}` |
| `saw_schema_validate` | POST | `/api/v1/lint`（checks 含 schema） |
| `saw_prune` | POST | `/api/v1/prune` |
| `saw_status` | GET | `/api/v1/status` |
| `saw_learn` | POST | `/api/v1/feedback` |
| `saw_distill` | POST | `/api/v1/distill` |
| `saw_suggest` | GET | `/api/v1/trends` |
| `saw_wip` | GET/PUT | `/api/v1/wip` |
| `saw_workflow` | POST | `/api/v1/workflows` |
| `saw_blast_radius` | POST | `/api/v1/blast-radius` |
| `saw_feedback` | POST | `/api/v1/feedback` |

**共享逻辑层**：MCP 工具和 HTTP API 共用同一个核心引擎层，通过 Hexagonal Architecture 的 Driving Adapter 模式实现。

```
CLI Driver ──┐
MCP Driver ──┼──→ Engine Layer（纯业务逻辑）──→ Write Queue ──→ Sinks
Web Driver ──┘
```

---

## 八、CORS 配置

```python
# FastAPI CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",  # Tauri 开发模式
        "http://localhost:5173",  # Vite 开发模式
        "tauri://localhost",      # Tauri 生产模式
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

*本 API 合约与 Claims Schema、前端技术栈选型共同构成 Smart Agent Wiki 的完整接口规范*
*Last updated: 2026-04-25*
