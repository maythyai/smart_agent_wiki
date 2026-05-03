# Phase 16: Real-Time Dashboard - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning
**Mode:** Smart discuss (autonomous)

<domain>
## Phase Boundary

实现 WebSocket 实时推送，让 Integration Dashboard 无需页面刷新即可显示连接器状态更新。用户可以看到同步进度、健康状态变化实时更新。

此阶段依赖 Phase 15 的 Integration Dashboard 作为 UI 基础，扩展其 API 和前端组件以支持 WebSocket 实时更新。

**In scope:**
- WebSocket 服务端点和连接管理
- 实时状态广播（健康状态、同步进度）
- 前端 WebSocket 集成和重连机制
- 按连接器开关实时更新

**Out of scope:**
- 移动端适配（Phase 17）
- 连接器设置页面（Phase 18）
- 发送消息到 IM 平台

</domain>

<decisions>
## Implementation Decisions

### WebSocket Server Architecture
- **D-01:** 使用 FastAPI WebSocket 端点 `/ws/integrations` 处理连接
- **D-02:** 连接管理器维护活跃连接列表，支持广播消息
- **D-03:** 心跳检测（30秒间隔），超时断开后自动重连
- **D-04:** 消息格式：JSON `{ "type": "connector_health"|"sync_progress", "platform": "...", "data": {...} }`

### Event Broadcasting
- **D-05:** HealthMonitor 状态变化触发广播
- **D-06:** SyncEngine 同步进度实时推送（items_synced, completion%）
- **D-07:** 用户可按连接器订阅/取消订阅更新

### Frontend Integration
- **D-08:** 使用原生 WebSocket API（浏览器原生支持）
- **D-09:** 自动重连机制（指数退避：1s→2s→4s→8s，最大 30s）
- **D-10:** 连接状态指示器（connected/connecting/disconnected）
- **D-11:** 更新 Zustand store 时乐观更新 UI

### Claude's Discretion
- WebSocket 连接池具体实现方式
- 消息类型详细定义
- 前端 Hook 封装方式
- 错误处理和重试策略细节

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 15)
- **IntegrationCard.tsx** — 显示连接器状态卡片，可扩展显示实时更新
- **integrationsStore.ts** — Zustand store，可添加 WebSocket 连接状态
- **Dashboard API** — `/api/v1/integrations/dashboard` 返回聚合状态

### Reusable Assets (from Phase 03-02)
- **WebSocket 基础** — `/ws` 端点用于 agent_status、workflow_progress
- **WebSocket 连接管理器** — 已有连接池和广播机制

### Established Patterns
- FastAPI WebSocket 路由和依赖注入
- Zustand store 状态管理
- React 组件乐观更新模式

### Integration Points
- **HealthMonitor** — 状态变化时触发广播
- **SyncStatusTracker** — 同步进度更新时触发广播
- **IntegrationCard** — 接收实时更新并重新渲染

</code_context>

<specifics>
## Specific Ideas

### WebSocket Message Types

```json
// Connector health change
{
  "type": "connector_health",
  "platform": "notion",
  "data": {
    "status": "healthy",
    "last_success_at": "2026-05-03T10:30:00Z",
    "consecutive_failures": 0
  }
}

// Sync progress update
{
  "type": "sync_progress",
  "platform": "slack",
  "data": {
    "state": "syncing",
    "items_synced": 45,
    "items_total": 100,
    "completion_percent": 45,
    "errors": []
  }
}

// Connection status
{
  "type": "connection_status",
  "data": {
    "connected": true,
    "server_time": "2026-05-03T10:30:00Z"
  }
}
```

### Frontend Hook Pattern

```typescript
// web/src/hooks/useIntegrationWebSocket.ts
export function useIntegrationWebSocket(platforms?: string[]) {
  const [status, setStatus] = useState<'connected'|'connecting'|'disconnected'>('connecting');
  const updateConnector = useIntegrationsStore(s => s.updateConnector);
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/integrations`);
    ws.onopen = () => setStatus('connected');
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (!platforms || platforms.includes(msg.platform)) {
        updateConnector(msg.platform, msg.data);
      }
    };
    ws.onclose = () => setStatus('disconnected');
    return () => ws.close();
  }, [platforms?.join(',')]);
  
  return { status };
}
```

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 16 requirements are in scope.

</deferred>

---

*Phase: 16-real-time-dashboard*
*Context gathered: 2026-05-03 via smart discuss*