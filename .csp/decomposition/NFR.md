# NFR — 非功能性需求补全

> 来源：PRD §4（不重写，补全隐藏项）。系统级 NFR + Feature 级下沉见各 yaml `nfr`。

## 性能
- 单文档 ingest（<1MB md）P99 < 3s；query（关键词）P99 < 500ms；冒烟全链路 < [TBD]s
- 并发：[TBD]（开源本地工具，单机为主；自托管多用户并发量级未提供）
- 数据量：单库 claims 量级 [TBD]，FTS5 检索须在上述 SLA 内

## 安全
- 认证：JWT + refresh（`auth/jwt_auth.py`），RBAC（`permissions.py` + Cedar）
- 加密：Ed25519 审计 receipt（`adapters/crypto/ed25519.py`）；密码 bcrypt
- 合规：操作可审计（receipt 链式）、URL 守卫防内网/协议混淆
- 限流：API key + 匿名双轨（默认 100/h、1000/d，env 可覆盖）

## 可用性
- SLA：[TBD]（自托管，无明确 SLA）；local 模式无需 LLM 可跑通核心路径（降级不宕）
- 容灾：write_queue outbox 保证 mutation 不丢；SQLite 单库 → 备份策略 [TBD]
- 降级：LLM 不可达走规则 fallback；FTS5 不可用降级关键词检索

## 可观测性
- 日志：结构化 JSON 默认（`JsonFormatter`），trace_id 贯穿
- 监控：`/health`/`/health/ready`/`/metrics` 反映 engine 真实状态
- 告警：[TBD]（开源项目未提供告警通道）

## 国际化
- 多语言：README 已双语（EN/CN）；UI/CLI i18n 框架 [TBD]（未声明）
- 多时区：freshness 9 级含时间衰减，时区处理 [TBD]
- 本地化：[TBD]

## 其他隐藏项（逐域验证后状态）
- 数据校验：前后端双重 — 后端 Pydantic schemas（`drivers/web/schemas/`）已在；前端 [TBD]
- 分页/搜索：列表类端点（pages/feeds）已在；冒烟覆盖 [TBD]
- 导入/导出：feeds OPML import/export 在；markdown/zip import 在
- 操作日志/审计：receipt（F-C-2）+ observability（F-D-1/2）
- 配置管理：`saw config` TUI + env + `.env`
- 文件上传/存储：vault 层；media ingestion 在
- 备份/恢复：[TBD] 策略未声明
- 无障碍/移动端/SEO：[TBD]（本地工具，非公开 Web 优先项）
- 分析/埋点：PRD §5 定义 5 事件

> 命中项若 PRD 未声明 → 标 [TBD] 并记入对应 Feature `assumptions`，不擅自塞进已确认需求。

## v1.10.0 NFR delta（embedding track）

> 来源：PRD-embedding-v1.10.0 §4。Feature 级下沉见 F-N-1..4 各 yaml `nfr`。

### 性能
- 向量检索 P99 延迟 [TBD]（须优于或接近 BM25 的毫秒级）——本地 benchmark 测量
- F-N-3 smart-linking O(pages²) 相似度计算——须限 top N + 缓存策略 [TBD]
- 向量索引存储开销 [TBD]（每 claim/wiki 页面向量大小 × 总量）——磁盘测量

### 降级策略
- 无 `[learn]` extra（tier=LIGHTWEIGHT/OFFLINE）时全功能回退 BM25：
  - F-N-1：skip 向量入库，日志提示 "embeddings unavailable, skipping vector index"
  - F-N-2：语义检索降级到 BM25，meta 标注 `semantic_fallback: true`
  - F-N-3：smart-linking 保持原有 3-signal 启发式，行为与 v1.8.0 一致
- 模型下载失败（网络/OOM）：`embed_texts()` 已有 try/except 返回 None，调用方降级
- 查询文本 embedding 失败：降级到 BM25，meta 标注 `embedding_error`

### workspace 隔离
- 向量索引须含 workspace_id（claim 表已有 `workspace_id` 列，ADR-008/009）
- 语义检索、smart-linking suggest 均须透传 workspace_id，跨 workspace 查询不泄漏
- 参照既有 QueryEngine 已透传 workspace_id 范式（`engine.py:58,86`）

### 可测性
- CI 无 `[learn]` extra 时：embedding 相关测试 `pytest.importorskip("sentence_transformers")` 自动 skip，不 fail，不需 `--ignore`
- 本地有 `[learn]` extra 时：embedding 测试正常运行并 pass
- coverage 不因 embedding 测试 skip 而下降（沿用 `--ignore learn` → `importorskip` 策略）

### 安全
- 向量索引与 claim 数据同源（同 SQLite 生态），workspace_id 隔离参照既有 RBAC 范式
- 向量数据不含额外 PII（embedding 输入为 claim/wiki 内容文本，非用户数据）

## v1.11.0 NFR delta（debt-closure IV track）

> 来源：PRD-debt-closure-v1.11.0 §4。Feature 级下沉见 F-O-1..4 各 yaml `nfr`。

### 性能
- semantic cache 命中后查询延迟 ≤ keyword cache 命中延迟（同量级）——复用 F-QS-07 cache 路径，命中时跳过 embed_texts() + 全量 cosine
- cache 命中率 [TBD]（须 benchmark 后定基线，PRD §1.3 标 [TBD]）
- REST /workflows 查询延迟 [TBD]（DB SELECT + merge live，须与 CLI 同量级）

### 测试覆盖
- 全量 coverage ≥65%，fail_under 从 64 提升到 65（AC-COV-2）
- compile/compiler.py 覆盖率 17%→[TBD]（须实施后测量，PRD §6 AC-COV-1 标 [TBD]）
- 测试不依赖 [learn] extra（compiler 不涉及 embedding）

### 不回归
- passed ≥1993（v1.10.0 基线 1993）
- ruff 0 errors
- smoke 6/6

### 兼容
- 无 breaking API 变更（additive MINOR）
- REST schema 不变（`{"workflows": [...], "total": N}`）
- CLI 命令不变（仅加 cache 层，不改命令接口）

### workspace 隔离
- semantic cache key 须含 workspace_id（与 _keyword_search 对称），防跨 workspace 泄漏
- workflow REST /workflows 须透传 workspace_id（参照既有范式）

## v1.12.0 NFR delta（embedding API pivot track）

> 来源：PRD-embedding-api-v1.12.0 §4。Feature 级下沉见 F-Q-1..4 各 yaml `nfr`。

### 性能
- API embedding P99 延迟 [TBD]（须优于或接近 BM25 的毫秒级）——benchmark 对比（真实 API key 可选 E2E）
- semantic vs BM25 召回率 [TBD]——须用同义查询集 benchmark 后定 baseline
- 全量重建延迟 [TBD]（取决于 claim/wiki 总量 × API embedding 单次延迟）

### 无本地 torch 加载
- runner 进程不 import torch——API 为默认路径，不要求 [learn] extra
- CI 日志 + `pip show torch` 不存在
- [learn] extra 装了可用作 fallback（不装不影响功能）

### 降级策略
- API 配置可用 → 走 litellm API（默认路径，无需本地 ST）
- API 不可用但 [learn] 已装（本地 ST 可 import）→ 走本地 ST fallback（日志 info "API unavailable, falling back to local ST"）
- 两者都不可用 → embed_texts() 返回 None，语义检索降级到 BM25（semantic_fallback: true），不报错不中断
- detect_tier() FULL 条件：API 配置可用 OR 本地 ST 可 import

### 测试覆盖
- CI 无 [learn] extra 时：embedding 测试不再 importorskip skip，改 API mock 全 pass
- coverage 不因 embedding 测试改 mock 而下降（去掉 importorskip 后测试从 skip 变 pass，coverage 应升不降）

### 不回归
- passed ≥2064（v1.11.0 基线）
- ruff 0 errors
- smoke 6/6

### workspace 隔离
- embedding 索引须遵守 workspace_id 隔离（embedding_store PK (doc_id, workspace_id) 既有，不变）
- 维度变更重建须全 workspace 生效（DELETE FROM embedding_store 全量 wipe）

### 向量索引存储开销
- [TBD]（API dim 如 1536 > 本地 384，每 claim/wiki 页面向量大小 × 总量）——磁盘测量

### 兼容
- 无 breaking API 变更（additive MINOR）
- embed_texts() 签名不变（list[list[float]] | None）
- REST/CLI 命令不变（仅 provider 换 + dim 驱动 + fallback 路由）

## v1.14.0 NFR delta（semantic perf track）

> 来源：PRD-semantic-perf-v1.14.0 §4。Feature 级下沉见 F-S-1..3 各 yaml `nfr`。

### 性能 — ANN 加速
- ANN 检索 P99 优于全量 cosine（规模 ≥1k 时）——benchmark 输出 ANN P99 < cosine P99 @ ≥1k 文档 `[TBD]`
- 规模阈值 `SAW_ANN_THRESHOLD` 默认值 `[TBD]`——03 技术方案 benchmark 实测确定 cosine 可接受延迟的拐点

### 性能 — cache 可配
- env 配置 cache 启用/禁用后行为可验证——`SAW_SEMANTIC_CACHE_ENABLED=false` 时 `cache.stats()` 无新增 hit；`=true`（默认）时行为不变
- `SAW_SEMANTIC_CACHE_THRESHOLD_MS` 阈值跳过写入——API 响应 < 阈值时 `cache.set` 跳过，`cache.get` 仍可命中

### 不回归
- passed ≥2179（v1.13.0 基线 2179）
- ruff 0 errors
- smoke 6/6

### 覆盖率
- coverage ≥67% 不回归（CI fail_under=67）

### 依赖约束
- 不引入重依赖——不新增 faiss/torch/scikit-learn 等
- ANN 库须 pip 可装、MIT/Apache 许可（候选：sqlite-vss / hnswlib / numpy 分块矩阵乘）

### 向后兼容
- 默认行为不变——不设 env 时行为与 v1.13.0 一致（cache 始终启用 + 全量 cosine）
- 无 breaking API 变更（additive MINOR）
- `_semantic_search` 返回值结构（`QueryResult`）不变，仅影响内部 cache 命中/写入路径 + ANN 切换路径
- `embedding_store` 表结构不变（向量仍 BLOB 存储，ANN 索引为附加结构）

### workspace 隔离
- ANN 索引须遵守 workspace_id 隔离（参照既有 embedding_store PK (doc_id, workspace_id)）
- cache 配置控制不影响 `_keyword_search` 的 cache 路径（F-QS-07），两个 cache 路径独立控制

### 降级策略
- ANN 库已装 + 索引可用 + 规模 > 阈值 → 走 ANN 路径
- ANN 库未装 / 索引损坏 / 规模 ≤ 阈值 → 走全量 cosine（`ann_fallback: true` 或无 ANN 标记），不报错不中断
- cache 禁用 → 跳过 cache.get/set，直接 embedding + cosine/ANN
- cache 启用 + 阈值未达 → 正常 cache.get/set
- cache 启用 + API 响应 < 阈值 → cache.get 可命中已有，cache.set 跳过新写入

## v1.15.0 NFR delta（agent/link track）

> 来源：PRD-agent-link-v1.15.0 §4。Feature 级下沉见 F-T-1..3 各 yaml `nfr`。

### 不回归
- passed ≥2192（v1.14.0 基线 2192）
- ruff 0 errors
- smoke 11/11

### 覆盖率
- coverage ≥67% 不回归（CI fail_under=67）

### links apply 破坏性确认
- apply 命令默认 dry-run，须 `--confirm` 方写回（AC-B-1 Given-When-Then）
- 不绕过 WikiRepository.write() 安全边界
- 单页写回失败不中断，继续处理其余页面，最后汇总失败列表

### activity 聚合不阻塞 workflow
- event bus handler 轻量（仅计数器更新），不抛异常不传播
- workflow 执行时间不因聚合器增加（无可感知延迟）
- event bus 已有 try/except 不传播 handler 异常

### 自定义角色向后兼容
- 不修改 build_default_agents() 签名和返回结构
- 内置 6 角色行为不变，自定义角色是 additive
- 角色定义文件格式错误 → 跳过该文件不阻断启动

### 无新依赖
- 复用既有 event_bus / BaseAgent / WikiRepository / compute_related_pages
- 不引入新库
