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
