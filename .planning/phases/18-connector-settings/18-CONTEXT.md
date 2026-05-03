# Phase 18: Connector Settings - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning
**Mode:** Smart discuss (autonomous)

<domain>
## Phase Boundary

实现连接器配置页面，让用户可以从 Integration Dashboard 访问每个连接器的专属设置页面，配置同步间隔、同步方向、属性映射，并重新授权过期 OAuth tokens。配置需要持久化存储。

此阶段依赖 Phase 16 的 Integration Dashboard 作为入口点，扩展现有连接器架构添加配置存储层。

**In scope:**
- Settings API 端点（GET/PUT per-connector settings）
- 配置持久化存储（数据库表或配置文件）
- Settings UI 页面（每个连接器的配置表单）
- Property Mapping 编辑器（Notion/Logseq 字段映射）
- OAuth re-authorize 流程集成

**Out of scope:**
- 新连接器类型
- 批量配置操作
- 配置导入/导出

</domain>

<decisions>
## Implementation Decisions

### Settings Storage
- **D-01:** 使用 SQLite/PostgreSQL 存储配置（connector_settings 表）
- **D-02:** 配置 schema：sync_interval, sync_directions, property_mappings, oauth_status
- **D-03:** 配置通过 API 端点 CRUD 操作

### Settings API
- **D-04:** GET /api/v1/connectors/{platform}/settings — 获取配置
- **D-05:** PUT /api/v1/connectors/{platform}/settings — 更新配置
- **D-06:** POST /api/v1/connectors/{platform}/reauth — 重新授权 OAuth

### Sync Interval Options
- **D-07:** 预设选项：5min、15min、1hr、6hr、manual
- **D-08:** manual 模式只响应手动触发，不自动轮询

### Sync Directions
- **D-09:** inbound_only：只从平台摄入到 SAW
- **D-10:** outbound_only：只从 SAW 推送到平台
- **D-11:** bidirectional：双向同步（默认）

### Property Mappings (Notion/Logseq)
- **D-12:** Notion：标题属性、内容属性、置信度属性、新鲜度属性映射
- **D-13:** Logseq：block property drawer 字段映射
- **D-14:** 编辑器提供下拉选择可用属性

### OAuth Re-authorization
- **D-15:** 检测 token 过期状态，显示 re-authorize 按钮
- **D-16:** 点击按钮触发完整 OAuth flow
- **D-17:** 成功后更新 token，刷新状态

### Claude's Discretion
- Settings 页面路由结构
- Property mapping UI 布局
- 表单验证逻辑细节
- 错误提示文案

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 10-15)
- **src/saw/connectors/** — 连接器实现框架
- **src/saw/connectors/models.py** — ConnectorConfig, ConnectorHealth models
- **src/saw/api/oauth.py** — OAuth 处理逻辑
- **web/src/components/integrations/IntegrationCard.tsx** — 连接器卡片入口

### Established Patterns
- FastAPI REST 端点模式
- Zustand 状态管理
- React 表单组件
- OAuth redirect flow

### Integration Points
- **web/src/pages/Integrations.tsx** — Dashboard 入口点
- **src/saw/drivers/web/app.py** — API 路由注册
- **src/saw/connectors/registry.py** — 连接器注册表

</code_context>

<specifics>
## Specific Ideas

### Settings Database Schema

```python
# connector_settings table
class ConnectorSettings(Base):
    platform: str  # primary key
    sync_interval: str  # "5min", "15min", "1hr", "6hr", "manual"
    sync_directions: str  # "inbound_only", "outbound_only", "bidirectional"
    property_mappings: dict  # JSON: {"title": "Name", "content": "Body"...}
    updated_at: datetime
```

### Settings API Implementation

```python
# src/saw/api/settings.py
@router.get("/connectors/{platform}/settings")
async def get_settings(platform: str):
    return await get_connector_settings(platform)

@router.put("/connectors/{platform}/settings")
async def update_settings(platform: str, settings: SettingsUpdate):
    return await save_connector_settings(platform, settings)
```

### Settings Page Route

```tsx
// App.tsx
<Route path="/integrations/:platform/settings" element={<ConnectorSettings />} />
```

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 18 requirements are in scope.

</deferred>

---

*Phase: 18-connector-settings*
*Context gathered: 2026-05-03 via smart discuss*