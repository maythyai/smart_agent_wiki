# ADR-008: Workspace 写入策略（insert 持久化 + ingest 透传）

## 状态：Accepted
## 上下文
v1.5.0（T-F-Z-7）把 workspace scope 注入到 claims **读取**路径（search/get_by_id + QueryEngine + cache key）。但**写入**路径有缺陷：`Claim` domain 模型有 `workspace_id: str = "default"` 字段（T-F-P-4），但 `SQLiteClaimsRepository.insert` 的 INSERT SQL **不写 workspace_id 列**（仅靠表的列默认 'default'）→ 无论 Claim.workspace_id 设何值，落库总是 'default'。IngestPipeline 也不持 workspace_id。结果：多 workspace 写入实际不生效，所有 claim 落 default。
## 决策
1. **insert SQL 补 workspace_id 列**：`INSERT OR IGNORE INTO claim (..., workspace_id) VALUES (..., ?)`，值取 `claim.workspace_id`。既有调用 Claim.workspace_id 默认 'default' → 行为不变（backward compat）。
2. **upsert 同步**：upsert 的 UPDATE 分支也带 workspace_id（防 default 覆盖已设值——只在 INSERT 分支写，UPDATE 不动 workspace_id 以免覆盖）。
3. **IngestPipeline 持 workspace_id**：`ingest(workspace_id="default")` 透传到 `_build_write_ops` → Claim 构建带 workspace_id。
4. 不新 migration（v8 已有 workspace_id 列）。
## 备选方案
| 方案 | 优势 | 劣势 | 适用 |
|---|---|---|---|
| insert 补列（选） | 复用既有列，零迁移，backward compat | — | 本轮 ✓ |
| set_workspace 后置 | 不改 insert | 双写（insert + UPDATE），竞态 + 性能 | 不可接受 |
| 新 migration 加列 | — | 列已存在（v8），无意义 | 不适用 |
## 理由
workspace_id 列已存（v8），缺陷仅在 insert SQL 漏写。补列是最小修复，零迁移，默认值保单机兼容。复用既有 Claim.workspace_id 字段（domain 已有）。
## 后果
- 正：多 workspace 写入生效（claim 落指定 ws）；读取隔离（v1.5.0）+ 写入隔离（本轮）闭环。
- 负：既有测试若依赖"insert 后 workspace_id 总是 default"可能受影响——但 Claim 默认 'default'，行为不变。
- 风险：upsert UPDATE 分支若覆盖 workspace_id 会破坏隔离 → 决策只在 INSERT 写，UPDATE 不动。
## 关联 Feature
F-J-2（AC-WS-5）。依赖 ADR-005（workspace 原语）+ ADR-007（读取注入）。
