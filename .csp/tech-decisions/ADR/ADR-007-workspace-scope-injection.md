# ADR-007: Workspace scope 注入策略（repo 层过滤）

## 状态：Accepted
## 上下文
v1.4.0 P-4（H2 前置）建了 workspace 隔离原语：migration v8 给 `claim` 表加 `workspace_id` 列（default 'default'）+ `user_workspace_auth` 绑定表 + `repo.list_by_workspace`。但**全查询路径未注入 workspace scope**——`QueryEngine`（`engines/query/engine.py`）/`IngestPipeline`（`engines/ingest/pipeline.py`）及 claims repo 的 search/get/list 均无 workspace_id 过滤，跨 workspace 数据可互查（H2 漏过滤风险）。
## 决策
1. **注入点 = repo 层**（ClaimsRepository / WikiRepository 方法签名加可选 `workspace_id: str | None = None`），而非 engine 层。理由：repo 是数据边界，所有数据进出必经；engine 层注入会漏 MCP/direct-repo 路径。
2. 默认值 `'default'`（单机向后兼容，既有无 ws 调用不破坏）。
3. `QueryEngine` 构造时持 `workspace_id`（从 request context 注入），透传给 repo 调用。
4. e2e 守：`test_workspace_routing` 跨 ws 查询拒（A ws claim 在 B ws 查询返回空）。
## 备选方案
| 方案 | 优势 | 劣势 | 适用 |
|---|---|---|---|
| repo 层注入（选） | 数据边界单一，全覆盖含 MCP/直 repo | 多 repo 方法签名改动面广 | 本轮 ✓ |
| engine 层注入 | 改动少 | 漏 MCP/direct-repo 路径，不全 | 不安全 |
| DB 视图 per-workspace | 透明 | SQLite 视图 + session 变量复杂，local-first 过重 | SaaS 才值得 |
## 理由
security 边界须在数据层（fail-secure：漏注入=漏过滤=越权）。repo 层虽面广但 H2 的核心就是"防漏过滤"，e2e 守住。default 'default' 保单机兼容。复用既有 workspace_id 列，零新 migration。
## 后果
- 正：全路径 workspace 隔离，e2e 可验。
- 负：repo 方法签名改动面广（claims + wiki repo）；须逐方法核防漏。
- 风险：某 repo 方法漏注入→越权——mitigate：e2e 跨 ws 拒测试 + lint 核 repo 方法签名。
## 关联 Feature
F-Z-7（AC-WS-3）。依赖 ADR-005（workspace 原语）。
