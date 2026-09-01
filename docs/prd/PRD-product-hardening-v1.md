---
id: PRD-product-hardening-v1
title: 产品形态补全与基础加固
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
product_type: platform
feature_count: 5
mvp_scope: [e2e-usability, security-hardening, test-gate]
thin_sections: [7]
upstream_source: ".csp/code-spec/saw/CODE-MODULE-SPEC.md + 实机核验(2026-09-01)"
related_pms:
  - .csp/product-spec/PMS-e2e-usability.md
  - .csp/product-spec/PMS-claim-alignment.md
  - .csp/product-spec/PMS-security-hardening.md
  - .csp/product-spec/PMS-observability.md
  - .csp/product-spec/PMS-test-gate.md
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
related_specs:
  - .csp/specs/SPEC-F-A-1.md
  - .csp/specs/SPEC-F-A-2.md
  - .csp/specs/SPEC-F-A-3.md
  - .csp/specs/SPEC-F-A-4.md
  - .csp/specs/SPEC-F-A-5.md
  - .csp/specs/SPEC-F-A-6.md
  - .csp/specs/SPEC-F-B-1.md
  - .csp/specs/SPEC-F-B-2.md
  - .csp/specs/SPEC-F-B-3.md
  - .csp/specs/SPEC-F-C-1.md
  - .csp/specs/SPEC-F-C-2.md
  - .csp/specs/SPEC-F-C-3.md
  - .csp/specs/SPEC-F-C-4.md
  - .csp/specs/SPEC-F-C-5.md
  - .csp/specs/SPEC-F-D-1.md
  - .csp/specs/SPEC-F-D-2.md
  - .csp/specs/SPEC-F-D-3.md
  - .csp/specs/SPEC-F-E-1.md
  - .csp/specs/SPEC-F-E-2.md
  - .csp/specs/SPEC-F-E-3.md
---

# PRD: 产品形态补全与基础加固

**Version**: v1.0 | **Author**: [TBD] | **Date**: 2026-09-01 | **Status**: Draft

> 本 PRD 不新增对外功能，聚焦把"可运行代码"打磨为"可用、可信、可维护的产品"。所有"现状"断言基于 2026-09-01 实机核验（见 `实现度现状`），非历史审计。历史审计 `docs/smart_agent_wiki_deep_audit.md`（2026-06-23）大面积过时，不作依据。

## 实现度现状（实机核验，2026-09-01）

| 维度 | 历史审计断言（2026-06-23） | 实机核验现状 |
|---|---|---|
| 6 Agent | execute() 为空实现 | **已实装**：`agents/*.py` 6 文件共 ~1000 LOC，`LibrarianAgent.execute`（`librarian.py:46`）含 LLM 调用 + 规则 fallback + 解析，无 `pass`/`NotImplemented` 桩 |
| 连接器 | 9 个宣称 2 个完全不存在 | **7 平台均有代码**：github/notion(10 文件)/logseq + IM(discord/feishu/slack/wecom)，notion 已全实现 |
| MCP 工具 | 宣称 24+ 实际 6 | **实际 61 个** `@mcp.tool`，README "56+ tools" 准确 |
| 前后端认证 | 互不通信 | **后端已统一**：`drivers/web/routes/auth.py:13` 复用 `auth.jwt_auth.AuthService/JWTHandler`；前端 token 互通 `[TBD]` 待验 |
| RBAC/限流/审计 | 缺失 | **已存在**：`auth/permissions.py`（Permission/Role/Cedar）、`api/rate_limit.py`、`adapters/crypto/ed25519.py`（Receipt/ReceiptSigner） |
| 可观测性 | 无 | **middleware 已在**：`middleware/observability.py`（RequestId/JsonFormatter/init_observability），跨模块一致性 `[TBD]` |
| 测试 | — | 128 个 `test_*.py`，CI（`ci.yml`+`release.yml`）在，覆盖率 `[TBD]` |

**结论**：代码骨架已较完整，真正缺口在**端到端验证、宣称-实现一致性、深化加固、测试门禁、上手可用**，与历史审计相反。故本 PRD 聚焦"加固/补全/可用"，不重建已有能力。

## 1. 背景与目标

### 1.1 背景：为什么现在做？不做会怎样？做了会怎样？

- **为什么现在做**：代码已具备四层存储、五引擎、6 agent、7 连接器、61 MCP 工具的完整骨架，但"可运行"≠"可用"——端到端链路缺统一验收基线、宣称与实现存在漂移（含过时文档）、安全/可观测/测试虽存在但未深化闭环。需在 v3.7（安全/测试/文档）与 v3.8（实现度对齐）窗口收口。
- **不做会怎样**：用户/开发者按 README 宣称试用会在未验证路径上踩坑；历史审计与代码实际背离，下游设计与开发据错误前提决策；安全/可观测/测试停留在"有模块"而非"有保障"。
- **做了会怎样**：建立端到端可用性基线与冒烟门禁；宣称与实现一一对齐（过时文档修正）；安全/可观测/测试形成可验收闭环；为 02 需求拆解与 03 技术方案提供可信 ground。

### 1.2 目标用户

| 用户角色 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|
| 知识工作者（KW） | 个人研究者/写作者，local-first 偏好 | 导入资料→查询→得到可溯源答案 | 日常知识沉淀、文献综述 |
| 开发者（DEV） | 扩展/集成 SAW 的工程师 | 清晰能力边界、可复现 API/CLI/MCP、可扩展插件 | 二次开发、连接器集成、MCP 接入 |
| 平台运维者（OPS） | 自托管团队部署者 | 可观测、可审计、可限流、可健康巡检 | 部署、监控、安全合规 |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| 端到端可用 | 核心链路冒烟通过率 | 100%（ingest→compile→query→govern→learn） | CI 冒烟 job |
| 宣称一致 | README/docs 宣称项与代码一致率 | 100% | 自动 diff 校验脚本 |
| 安全闭环 | 高危操作 100% 产出审计 receipt | 100% | receipt 覆盖率统计 |
| 测试门禁 | 核心引擎链路覆盖率 | ≥80% [TBD 基线] | CI coverage 报告 |
| 上手可用 | `saw tutorial` 端到端跑通 | 一次通过 | 冒烟用例 |

> 业务量级（DAU/装机量）`[TBD]`——开源项目未提供，不编造。

## 2. 需求概述

把已具备完整骨架的 SAW 打磨为端到端可用、宣称一致、安全可审计、可观测、测试有门禁的可用产品。

## 3. 详细功能设计

### 3.1 端到端可用性闭环与冒烟基线（e2e-usability）
- **描述**：为五引擎主链路（Ingest→Compile→Query→Govern→Learn）建立可复跑的端到端冒烟基线与验收形态，确保任意 commit 后主链路可用。
- **用户故事**：作为 DEV，我想一条命令跑通端到端冒烟，以便每次变更后确认主链路未回归。
- **优先级**：P0
- **业务规则**：
  1. 冒烟覆盖：ingest（含至少 2 种提取器：markdown + url）、compile（wiki 增量）、query（关键词 + 自然语言）、govern（lint + verify）、learn（distill 一次）。
  2. 冒烟须在干净库（fresh `saw.db`）上从 0 起跑，不依赖外部 LLM 时代码路径仍可验证（规则 fallback / mock）。
  3. 冒烟产出的每条 claim 必须可溯源到原文位置（四层存储不变量）。
  4. 失败必须定位到具体链路节点 + 退出码非 0。
  5. 冒烟用例本身纳入 CI（`ci.yml`），非手动。
- **交互流程**：`saw <smoke-cmd>` → 初始化临时库 → 逐引擎执行 → 每步打印 PASS/FAIL 与耗时 → 全过退出 0 / 任一失败退出 1 并附节点。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| LLM 不可达 | 走规则 fallback 路径，标记降级 | "LLM offline, using rule fallback; NL query degraded" |
| 提取器对某输入失败 | 跳过该条并计数，不中断整链 | "extractor X failed on Y: <reason>; 1 skipped" |
| 溯源链断裂（claim 无原文锚点） | 标 FAIL，列出 claim id | "provenance break: claim <id> has no source anchor" |

### 3.2 实现-宣称一致性校准与能力清单（claim-alignment）
- **描述**：以代码为单一事实源，自动比对 README/docs 的能力宣称与实际实现，修正过时宣称，产出可信能力清单。
- **用户故事**：作为 KW，我想 README 列的能力都真实可用，以便按文档试用不踩坑。
- **优先级**：P1
- **业务规则**：
  1. 能力清单来源：`entry-points.jsonl`（61 MCP / 117 web / 37 CLI）+ `knowledge-graph.json`，不靠手写宣称。
  2. 比对维度：MCP 工具数、连接器数、agent 数、入口数；与 README/docs 文本宣称 diff。
  3. 过时文档（如 `docs/smart_agent_wiki_deep_audit.md` v3.7.0 旧断言、`README_CN` 已修 badge）按"事实源=代码"修正或加"历史快照"标注，不删历史。
  4. 能力清单落 `docs/CAPABILITIES.md`（人或 agent 可读），每条带 file:line 入口。
  5. 任何"宣称能力"在代码中 grep 不到 → 标 `[unverified]`，不写"已支持"。
- **交互流程**：跑 diff 脚本 → 输出 added/changed/removed 宣称项 → 人工/自动修正文档 → 重跑至 0 diff。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 宣称能力无代码对应 | 标 `[unverified]` 入清单 | "claim X has no code anchor, marked unverified" |
| 代码有能力但文档未宣称 | 加入能力清单 | "capability Y exists but undocumented, added" |

### 3.3 安全基础深化（security-hardening）
- **描述**：把已存在的 RBAC/限流/审计 receipts 从"有模块"深化为"全链路闭环可验收"。
- **用户故事**：作为 OPS，我想每个高危操作都有可验证的权限校验与审计 receipt，以便合规巡检。
- **优先级**：P0
- **业务规则**：
  1. 权限矩阵（角色×功能×数据范围）全链路覆盖：所有 write/敏感 read 路由必须挂 `auth_dep`，禁止裸路由（以 `app.py` include_router 为校验源）。
  2. 审计 receipt：所有 agent 操作 + write_queue 变更必须产出 Ed25519 签名 receipt，链式 `prev_receipt_id` 不断裂。
  3. 限流：按 API key + 匿名双轨，超限返回 429 + Retry-After，边界值见配置（默认 100/h、1000/d，可 env 覆盖）。
  4. 输入消毒：URL 守卫（`url_guard`）覆盖所有外部 URL 入口，阻断内网/协议混淆。
  5. 前后端 token 互通：前端 token 与后端 `AuthService` 同源（现状后端已统一，前端 `[TBD]` 待验后补）。
- **交互流程**：运维触发安全自检 → 逐项校验权限/receipt/限流/消毒 → 报告覆盖度 + 缺口清单。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 裸路由（未挂 auth_dep） | 标 FAIL，列路由 | "unprotected route: <method> <path>" |
| receipt 链断裂 | 标 FAIL，列断点 | "receipt chain break at op <id>" |
| 限流边界被绕过 | 标 FAIL | "rate-limit bypass on <key>" |

### 3.4 可观测性与日志一致性（observability）
- **描述**：统一跨模块 logger 规约与 trace_id 贯穿，使端到端链路可追踪。
- **用户故事**：作为 OPS，我想一次请求的 trace_id 贯穿 CLI/engines/write_queue，以便快速定位问题。
- **优先级**：P1
- **业务规则**：
  1. `init_observability` 为唯一 logger 初始化点，所有模块经它获取 logger，禁散落 `logging.basicConfig`。
  2. trace_id（request_id）从 drivers 层注入 context，贯穿 engines→write_queue→sinks，日志带同一 id。
  3. 结构化 JSON 日志（`JsonFormatter`）为生产默认；本地可切可读模式。
  4. 健康度 `/health`/`/health/ready`/`/metrics` 反映 engines 真实状态（非恒 200）。
- **交互流程**：请求入 → middleware 注 trace_id → 各层日志带 id → 异常时按 trace_id 聚合定位。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 模块绕过统一 logger | 标 lint FAIL | "module X uses raw logging, route via init_observability" |
| trace_id 丢失 | 记录并降级 | "trace_id missing at <node>, degraded correlation" |

### 3.5 测试覆盖门禁（test-gate）
- **描述**：为核心引擎链路建立覆盖率门禁与回归基线，CI 不达门禁则阻断合并。
- **用户故事**：作为 DEV，我想 CI 在覆盖率回归时拦住我，以便不引入未测变更。
- **优先级**：P0
- **业务规则**：
  1. 门禁范围：engines/{ingest,query,govern,collaborate,compile} + write_queue 核心路径。
  2. 覆盖率阈值：核心引擎链路 ≥80%（基线 `[TBD]` 首次实测后定），非核心 ≥60%。
  3. 冒烟用例（3.1）必须随每次 CI 跑且全过。
  4. 覆盖率报告入产物，趋势可查。
  5. 门禁失败 → CI 退出非 0，阻断合并。
- **交互流程**：CI 拉起 → 跑单测 + 冒烟 + coverage → 比对阈值 → 过则绿 / 不过则红并指未达模块。
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 覆盖率低于阈值 | CI 红，列未达模块 | "coverage <80% on engines/query (actual 72%)" |
| 冒烟失败 | CI 红，附节点 | "smoke failed at <engine>" |

## 4. 非功能要求

| 类别 | 要求 | 验收标准 |
|---|---|---|
| 性能 | 单文档 ingest（<1MB markdown）P99 < 3s | 冒烟基线内含性能断言 |
| 性能 | query（关键词）P99 < 500ms | 同上 |
| 可靠性 | 端到端冒烟在 fresh 库 100% 通过 | CI 连续 10 次构建全绿 |
| 安全 | 无裸 write 路由 | 安全自检 0 FAIL |
| 可维护 | 模块边界与 PMS 一致 | 下游拆解不越界 PMS |
| 兼容 | local 模式无需 LLM 可跑通核心路径 | 离线冒烟通过 |

> 不指定 DB/语言/框架（已知为 SQLite/Python/FastAPI 等属既有实现事实，非本 PRD 约束）。

## 5. 数据需求（埋点/事件）

| 事件名 | 触发条件 | 关键属性 | 用途 |
|---|---|---|---|
| ingest.completed | 文档入库成功 | doc_uuid, extractor, claim_count, duration | 链路健康 |
| query.answered | 查询返回 | mode(nl/keyword/graph), latency, citation_count | 查询质量 |
| receipt.signed | 操作产出 receipt | op_id, prev_receipt_id, agent | 审计闭环 |
| smoke.run | 冒烟执行 | pass_count, fail_count, node | 可用性门禁 |
| ratelimit.exceeded | 触发限流 | key, route, limit | 安全监控 |

> 埋点实现细节（存储/导出）属 HOW，不在本 PRD；事件名与属性稳定即可。

## 6. 验收标准

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-E2E-1 | 端到端冒烟 | fresh 库 | 跑冒烟命令 | 五引擎全 PASS，退出 0 |
| AC-E2E-2 | 离线降级 | LLM 不可达 | 跑冒烟 | 走 fallback，核心路径仍 PASS |
| AC-ALIGN-1 | 宣称一致 | 代码 61 MCP | 跑 diff 脚本 | README 宣称与代码一致，0 diff |
| AC-ALIGN-2 | 未验证项 | 宣称无代码对应 | 生成能力清单 | 标 `[unverified]`，不写"已支持" |
| AC-SEC-1 | 权限全覆盖 | 任意 write 路由 | 安全自检 | 0 裸路由 |
| AC-SEC-2 | receipt 闭环 | agent + write 变更 | 查 receipt 链 | 链式 prev_id 不断裂 |
| AC-SEC-3 | 限流生效 | 超 100/h | 再请求 | 429 + Retry-After |
| AC-OBS-1 | trace 贯穿 | 一次请求 | 查各层日志 | 同 trace_id |
| AC-OBS-2 | 健康真实 | engine 异常 | GET /health/ready | 反映非 200 |
| AC-TEST-1 | 覆盖门禁 | 核心引擎 | CI 跑 coverage | ≥80% 否则红 |
| AC-TEST-2 | 冒烟在 CI | push | CI 跑 | 冒烟全过 |

## 7. 排期估算

| 阶段 | 预估工作量 | 依赖 | 风险 |
|---|---|---|---|
| 端到端冒烟基线（3.1） | M [TBD] | CMS ground | 离线 fallback 路径完整性 |
| 实现-宣称校准（3.2） | S–M | 3.1 entry-points | 历史文档修正范围 |
| 安全深化（3.3） | M | 现有 RBAC/receipt | 前端 token 互通待验 |
| 可观测一致（3.4） | S | 现有 observability | 跨模块 logger 收敛量 |
| 测试门禁（3.5） | M | 3.1 冒烟 | 覆盖率基线未定 |

> 工作量粒度 S/M/L，数值人日 `[TBD]`（未提供团队规模与速率）。

## 8. 风险与依赖

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 前端 token 与后端未互通 | 中 | 中 | 3.3 实机核验后定，标 [TBD] |
| 覆盖率基线过低致门禁难达 | 中 | 中 | 首次实测后定阈值，分阶段提 |
| 历史审计/文档过时误导下游 | 高 | 高 | 以代码为事实源，3.2 校准 |
| 离线 fallback 路径不完整 | 中 | 中 | 3.1 冒烟暴露，逐项补 |
| 团队规模/速率未知 | 高 | 低 | 排期标 [TBD]，02 拆解补 |

## 附录

- 关联文档：`.csp/code-spec/saw/CODE-MODULE-SPEC.md`（13 模块边界+入口图）、`.csp/AGENTS.md`（路由契约）、`docs/ARCHITECTURE.md`、`CLAUDE.md`、`.planning/REQUIREMENTS.md`（v3.5 DX 需求）、`.planning/ROADMAP.md`（v3.7/v3.8）。
- 历史审计：`docs/smart_agent_wiki_deep_audit.md`（2026-06-23，**过时，不作依据**）、`docs/remote_project_audit_findings.md`（竞品分析，非本项目）。
- 设计资产清单：无上游 `.tsx`（非设计链路模式）。
- thin_sections：Section 7（排期数值 [TBD]，团队规模/速率未提供）。

### 下一步建议
- [ ] 进入 02 需求拆解 → 把 5 模块翻成 Feature 清单 + 依赖图 + NFR，落 `.csp/decomposition/`（不越出本 PMS 边界）。
- [ ] 需求过大 → 先圈定 MVP（P0：e2e-usability/security-hardening/test-gate）再拆。
- [ ] 进入 03 技术方案 → 读本 PRD + decomposition + PMS + CMS，按既有实现（六角架构/write_queue/observability）做选型与 TDD，不重造已存在能力。
- 当前产物：`docs/prd/PRD-product-hardening-v1.md` + `.csp/product-spec/`（5 PMS + INDEX）+ `docs/prd/PRD-INDEX.md` 已登记；`lifecycle-state.json` 将置 01 done，current_stage=02-decomposition。
