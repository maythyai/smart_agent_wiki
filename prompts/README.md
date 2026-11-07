# 系统提示词集（端到端交付链路）

一套自包含的系统提示词 + 一个外环战略规划，覆盖从长期规划到上线运维与整体复盘的完整链路。外环 `roadmap.md` 先于 00 跑一次（每个项目通常跑一次用很久）；内环 00-07 每版本迭代执行。八份内环 + 一份外环同源同构：统一目录约定（`docs/` + `.csp/`）、统一 slug/feature-id 命名、统一 front-matter 单向锚定（`.csp/`→`docs/`）+ manifest 双向映射、PMS/CMS/TMS 三说明书全程 living 治理、归档就绪、变更 delta 同步。

## 链路与文件

| 顺序 | 阶段 | 文件 | 产出目录 |
|---|---|---|---|
| 外环 | 产品长期规划（**方向调研**+战略锚点+版本号规则+版本序列路径+**版本功能集成必要性审视 gate**+**每版本规划级 PRD SPECs**） | [roadmap.md](./roadmap.md) | `docs/strategy/`（STRATEGY+ROADMAP）+ `docs/analysis/`（MARKET-RESEARCH/INTEGRATION-NECESSITY）+ `docs/prd/`（规划级 SPEC，01 升级） |
| 闸门 | 产品架构收敛审查（功能架构梳理+核心/次要取舍+IA 方向+迭代优先级——roadmap 与 01 PRD 之间的必经闸门） | [product-design-convergence.md](./product-design-convergence.md) | `.csp/convergence/`（CONVERGENCE-REPORT + CONVERGED-FEATURE-PLAN + IA-DIRECTION）+ `docs/analysis/`（摘要） |
| 0 | 知识中枢初始化 | [00-knowledge-hub.md](./00-knowledge-hub.md) | `.csp/AGENTS.md` + `.csp/manifest.json` |
| 1 | PRD 生成（产品需求；升级模式承接外环规划级 SPEC；评审前 11 点预设清单自查） | [01-prd.md](./01-prd.md) | `docs/prd/` + `.csp/product-spec/`（PMS） |
| 2 | 需求拆解（工程级 Feature） | [02-decomposition.md](./02-decomposition.md) | `.csp/decomposition/` |
| 3 | 技术选型 + 技术方案 + 全栈 Spec | [03-tech-design.md](./03-tech-design.md) | `.csp/tech-decisions/` + `.csp/tech-design/` + `.csp/specs/` + `.csp/test-spec/`（TMS） |
| 4 | 任务拆解 + 实施规划 | [04-task-breakdown.md](./04-task-breakdown.md) | `.csp/tasks/`（WBS/DAG/WAVE-PLAN） |
| 5 | 实施开发（多 Agent 团队） | [05-implementation.md](./05-implementation.md) | 代码（git worktree）+ `.csp/code-spec/`（CMS 增量）+ `.csp/artifacts/` |
| 6 | 审查·测试·发布交付·运维 | [06-verify-ship.md](./06-verify-ship.md) | `.csp/artifacts/{verify,review}/` + `.csp/ship/` + `.csp/ops/` + `.csp/milestones/` |
| 7 | 整体复盘审查（产品+技术，迭代探索） | [07-reviewer.md](./07-reviewer.md) | `.csp/review/` + `docs/solutions/`（摘要） |
| 独立 | 模块化审计+可用性审查+联动测试+roadmap bump | [audit.md](./audit.md) | `.csp/audit/` + `docs/analysis/`（摘要） |
| 独立 | 全链路审计 pipeline——串联六个审查提示词（体检→实机验证→UI/UX 专项→产品批评→缺口补强→演进交棒），互不重复劳动；Step 0 运行模式检测（标准 subagent fan-out / Fallback 串行+完整性硬门控）+ 0.5 环境自检会话重建 + 0.6 findings 基线回读防重复侦查 + 0.8 自动化门禁快照 | [audit-pipeline.md](./audit-pipeline.md) | 聚合 `.csp/{audit,verify,evidence,ui-review,critic,gap-analysis}/` 六步产物 + findings 交棒 roadmap |
| 独立 | 产品巡检+多角度审查主 Agent（07 复盘与外环 roadmap 之间的桥接）——巡检现有功能模块 → 增强规划/功能迭代/模块重组/界面规划 + 扩展维度 → 版本主题候选交棒 roadmap 做实证输入 | [product-audit-to-roadmap.md](./product-audit-to-roadmap.md) | `docs/audit/PRODUCT-AUDIT-{date}.md` + `REVIEW-FINDINGS-{audit-slug}.json`（交棒 roadmap） |
| 独立 | 单页面/单功能模块缺口与增强深潜（通用面+领域目录+联动） | [feature-gap-analysis.md](./feature-gap-analysis.md) | `.csp/gap-analysis/` + `docs/analysis/`（摘要） |
| 独立 | E2E 深度验证（M1 交互验证+修复 / M2 建套件 / M3 取证 / M4 全路由 sweep+按钮级点击审计+孤儿路由/隐藏后端功能审计+结构健康核查） | [e2e-deep-audit.md](./e2e-deep-audit.md) | `verify/` + `evidence/` + `gap-analysis/`（零 skill 依赖，可独立粘贴） |
| 独立 | 产品总监批评性审查（重复/冗余/IA/视觉交互一致性/用户习惯/定位/完整性/状态 七镜头，带产品 sense 给 critic judgement） | [product-critic-review.md](./product-critic-review.md) | `.csp/critic/` + `docs/analysis/`（前缀 `CRITIC-F-NN`，交棒 roadmap→Phase 2.5） |
| 独立 | UI/UX 设计总监审查——从审查方法到版本迭代的完整闭环（八镜头→提升点分级→落实到 PRD/Spec/Task→版本迭代路线图→回归验证） | [ui-review-to-iteration.md](./ui-review-to-iteration.md) | `.csp/ui-review/` + `docs/analysis/`（前缀 `UI-F-NN`，交棒 roadmap） |
| 独立 | 自动化验证层——提示词↔脚本契约（9 个机器可执行治理门禁 G-POS/G-NAV/G-DOC/G-FLAG/G-PLACEHOLDER/G-DUAL-NAV/G-CONTRACT/G-BUTTON/G-LAYER，映射五类根因 Pattern，统一 JSON 报告供提示词消费） | [automation-validation.md](./automation-validation.md) | `.csp/convergence/GATE-REPORT-{date}.json`（通用脚本 `scripts/validate_gates.py` + 配置 `gates.config.example.json`） |
| 独立 | 连续版本交付流水线——lifecycle-orchestrator 续跑全部待交付版本，含 01 前置四读、收敛闸门、findings 闭合契约、06 双闸门（findings_closure + version_integrity） | [develop_pipeline.md](./develop_pipeline.md) | 驱动 00-07 连续迭代 + `prompts/scripts/` 发布门禁 |
| 独立 | 开发期 UI 预防规范（8 条编码规范 N1-N8 + 5 个 CI 门禁 G1-G5 + 7 项审查链路增强，从历次审计根因提炼） | [prevention-norms.md](./prevention-norms.md) | 供 AGENTS.md 检查清单引用 |
| 独立 | 功能去重护栏——新功能开发前置约束通用方法论（六约束：定位查重/支柱归属/复用基础设施/元数据单源/导航准入/完成自检；防 R1 平行页面·R2 旁路实现·R3 元数据多副本·R4 语义重叠；含可粘贴 prompt 片段） | [feature-dedup-guardrails.md](./feature-dedup-guardrails.md) | 注入 `05-implementation.md` §7.0 开发期 gate |
| 独立 | Python 代码审查专家提示词——六维审查框架（正确性/复用/简化/效率/安全/可测试性）+ 硬规则 H1-H8/必须项 M1-M5 + 安全深度清单（注入/反序列化/密钥/依赖/并发）+ FastAPI/Django/Flask/Agentic 框架特化 + 对抗性与边界镜头 + 项目结构 A-D 评估矩阵 + 严重度/反馈标签/裁决标准（零 skill 依赖，可独立粘贴到任意 Agent 执行 review） | [python-code-review.md](./python-code-review.md) | 审查报告（可选落 `.csp/review/`） |
| 独立 | 数据汇报文案——五要素语境对齐+口径校验+三段叙事（绝对 pp/相对 %/可持续性）+五类叙事类型（提升/下降/稳定/突破-稳定/V 型）+反 cherry-pick+因果审慎+小样本标注，把数据翻译成老板 30 秒能看懂的结论与下一步 | [data-reporting.md](./data-reporting.md) | `docs/analysis/DATA-REPORT-{topic}-{date}.md`（IM 场景纯文本降级） |
| 独立 | 专利文档生成——从 PRD/技术方案提炼可专利化创新点（产品语言→专利技术语言转换+三问+四检查），固定模板（0-7 节+申请说明+关键词）+缺点-方案-效果闭环（第 5 节缺点 ↔ 6.3 量化效果一一对应）+竞品公开检索不编造 | [patent-doc.md](./patent-doc.md) | `docs/analysis/PATENT-{slug}.md`（提交前人工审核） |
| 独立 | 前端开发专家——TypeScript + Next.js(App Router) + Tailwind CSS + shadcn/ui 全栈前端开发与审查提示词（零 skill 依赖，可独立粘贴到任意 Agent 执行）。覆盖：Server/Client 组件边界、RSC/Server Action/API Route 选型、TypeScript strict 基线+Zod、Tailwind 设计 token 纪律、shadcn/ui Form/Table/Command 标准模式、React Query/Zustand/nuqs 状态管理、Loading/Error/Empty/Success 四态覆盖、WCAG AA a11y、LCP<2.5s 性能基线、功能去重护栏、前端特化代码审查六维框架、项目结构评估（含 Next.js + shadcn 组件目录约定） | [frontend-development.md](./frontend-development.md) | 代码产出（`src/app/` + `src/components/`）+ 审查报告（可选落 `.csp/review/`） |

| 独立 | 前后端联动审查——十一个场景（API URL 一致性/变更影响分析/常量集中管理/命名一致性/全链路 DB→API→FE 对齐/OpenAPI 文档 vs 实现/错误处理一致性），逐端点逐字段的契约缝隙审查提示词（零 skill 依赖，可独立粘贴到任意 Agent 执行） | [integration-review.md](./integration-review.md) | `.csp/review/INTEGRATION-REVIEW-{date}.md`（含差异清单 + 修复优先级） |
> **数据汇报文案 `data-reporting`**：独立支线，向人汇报的最后一公里——数据深潜归 `csp-product-metrics-review`/07，本流程只做叙事包装与沟通。五要素语境对齐（对象/目的/指标/范围/基准，缺则一次补齐）→ 数据校验（口径声明/异常值确认/小样本标注）→ 三段叙事（绝对 pp → 相对 % 口语化换算 → 可持续性判断）→ 一句话摘要（20-40 字）→ 下一步计划。五类叙事类型（提升/下降/稳定/突破-稳定/V 型）各有模板，下降型强制"影响量化→根因定位→止损恢复"三步、V 型含超额恢复分析。硬红线：不编数据、每数带时间范围与口径、绝对+相对并存、禁 cherry-pick、相关不写因果（p>0.05 不显著）、UV<100 标小样本、报忧必带方案。对象适配三档（老板/跨部门/客户）决定粒度。落 `docs/analysis/DATA-REPORT-{topic}-{date}.md` + manifest 回写；IM 场景纯文本降级（无 markdown 标题、一屏以内）。

> **专利文档生成 `patent-doc`**：独立支线，从 PRD/技术方案（01/03 产物）到专利交底书——建议 PRD Approved 后、功能公开前跑（公开披露破坏新颖性）。核心能力是"产品语言→专利技术语言"转换（"用户可以语音搜索"→"基于语音特征提取与语义向量匹配的多模态商品检索方法"）。流程：四要素提取（痛点/方案/差异/效果）→ 1-3 个创新点提炼（主+辅助，三问+四条质量检查）→ 固定模板生成（申请说明≤300 字+关键词顿号分隔+0-7 节，第 4 节历史留空）→ 两段式输出（预览→落盘）。硬红线：竞品必须公司名+产品名且公开检索不编造、详述到编号步骤级禁概念层、效果量化到技术指标（60%→82% 式）且与第 5 节缺点一一对应闭环、替代方案禁套话、不提供法律意见（提交前人工审核）。多份 PRD 独立成文不混内容。

> **前端开发专家 `frontend-development`**：独立于 00–07 链路，随时可用的 TypeScript + Next.js + Tailwind + shadcn/ui 全栈前端开发与审查提示词。综合提炼自 `05-implementation.md`（Frontend Engineer 角色）、`03-tech-design.md`（维度 1/5 前端架构）、`prevention-norms.md`（UI 编码规范 + CI 门禁）、`feature-dedup-guardrails.md`（功能去重）、`python-code-review.md`（审查方法论）、`ui-review-to-iteration.md`（八镜头审查）、`e2e-deep-audit.md`（前端测试策略）、`csp-flow-web`（Web 场景技能）。**零 skill 依赖、自包含**——全部规则/清单/命令/模板已内联，可直接复制粘贴到任意 Agent 执行。五种模式：Mode A 新页面开发 / Mode B 组件开发 / Mode C 全栈功能开发（含 Server Component + Server Action + Client Component 协同）/ Mode D PR/文件审查（五步审查法：读意图→先读测试→读实现→追踪关键路径→检查接缝）/ Mode E 全项目前端审计（含编译/类型检查/结构评估 A-D 评级）。核心资产：Next.js App Router 专项（Server/Client 组件边界、RSC/Server Action/API Route 选型、`layout/loading/error/not-found` 约定）、TypeScript 专项（`strict:true` 基线、T1-T7 禁止项、Zod 运行时校验、Discriminated Union）、Tailwind 专项（TW1-TW5 硬规则、design token 纪律、响应式断点）、shadcn/ui 专项（`<Form>` + `useForm` 标准模式、四态覆盖：Loading Skeleton/Error Alert+Retry/Empty Guide+CTA/Success）、状态管理（React Query/Zustand/nuqs 选型树）、硬规则 H1-H11 + 必须项 M1-M8、功能去重六条前端特化约束、WCAG 2.1 AA a11y 清单、LCP<2.5s 性能基线、前端安全审查（XSS/CSRF/信息泄漏/依赖安全）、16 种反模式及修复、项目结构 A-D 完备性评估。产物为生产级前端代码 + 可追溯的审查报告。

> **前后端联动审查 `integration-review`**：独立于 00–07 链路，随时可运行的全栈集成审查提示词——确保前后端之间的契约边界没有缝隙。综合提炼自 `03-tech-design.md`（维度 3 API 契约）、`06-verify-ship.md`（S6 契约测试 + S7 代码审查）、`frontend-development.md`（前端 API 调用模式）、`automation-validation.md`（G-CONTRACT 契约孤儿门禁）。**零 skill 依赖、自包含**——全部审查规则/命令/检查清单已内联，可直接复制粘贴到任意 Agent 执行。十一个场景：场景一 API URL 一致性（路径/方法/参数/字段逐条交叉对比，差异报告带 file:line 证据）/ 场景二 变更影响分析（git diff 驱动，自动检测任一端变更是否导致另一端断裂，含后端→前端影响矩阵和前端→后端影响矩阵）/ 场景三 API 常量集中管理（检测硬编码 URL、非大写命名、重复定义、缺失集中常量文件，输出应替换为常量的完整清单）/ 场景四 前后端命名一致性（全量对比 API 端点/字段名/枚举值/错误码/时间格式，按模块聚合差异报告）/ 场景五 全链路一致性 DB→API→FE（逐实体三层对比：数据库列 ↔ API DTO 字段 ↔ 前端 TypeScript 类型，检测命名漂移/类型不一致/缺失字段）/ 场景六 OpenAPI 文档 vs 代码实现（检测文档虚增、文档缺失、schema 漂移、response status code 不一致）/ 场景七 错误处理一致性（检测后端错误格式是否统一、前端是否覆盖所有错误状态码、是否存在裸 fetch 无 catch）。CRITICAL/HIGH/MEDIUM/LOW 四级严重度，每条 finding 带前后端两侧 file:line 证据 + 可执行修复 + P0/P1/P2 修复优先级。

| 棕地 | docs/→.csp/ 双轨整合（PRD→PMS、strategy→lifecycle、solutions→specs、analysis→audit） | [brownfield-doc-integration.md](./brownfield-doc-integration.md) | `.csp/product-spec/` + `.csp/manifest.json` + `docs/` 整理归位 |
| 参考 | 版本号管理规范——SemVer/CalVer 机制、tag 纪律、攒批发布 feat/fix 分轨、多平台六处一致的权威定义（roadmap/05/06 引用，冲突时以其为准） | [version-management.md](./version-management.md) | 被各提示词引用，无独立产物 |
| 参考 | PRD 预设检查清单——实证评审提炼的 11 类高频 Critical 模式（可测指标禁 [TBD]/分母一致/安全闸门治理/known-limit 上界/双模式显式/恢复路径/HOW 不具名/三处同步/信任模型/入出站对称/选型不外渗），01 升级/评审前必过；项目以 `.csp/agent-conventions/PRD-PRESET-CHECKLIST.md` overlay 叠加 | [prd-preset-checklist.md](./prd-preset-checklist.md) | 被 01/prd-writer 引用，无独立产物 |
| 模板 | 技能解耦移植任务模板——把外部借鉴的平台耦合技能解耦为目标框架原生等价物（本地 markdown+git+脚本）；A 表场景变量 + B–H 不变方法论，换场景只重填 A 表 | [skill-port-decouple.md](./skill-port-decouple.md) | 目标技能目录（按任务填充） |

> **06 vs 07**：06 是**发布前符合性验证**（实现是否满足 PRD/Spec/AC、能否上线），是门控；07 是**里程碑后整体复盘**（产品对不对、架构稳不稳、下一步做什么），探索性/战略性，不卡发布。07 从用户视角+技术视角发现 Spec 之外的新问题，findings 回流下一迭代 01-05 + 外环 roadmap。

> **外环 roadmap**：`roadmap.md` 先于 00 跑一次——四步链：**调研**（Phase R：行业扫描/竞品深潜/客户洞察/经济模型/方向可行性，落 `docs/analysis/MARKET-RESEARCH-{date}.md`）→ **规划功能版本**（战略锚点 STRATEGY.md + 版本号规则 + 版本序列路径 ROADMAP.md，每版本给版本号+主题+简要功能模块清单）→ **去除不必要功能**（Phase 2.5 集成必要性审视，净版回写 ROADMAP+FEATURES）→ **产出 PRD SPECs**（Phase 4.5：每净版版本一份规划级 SPEC 落 `docs/prd/`，`prd_depth: planning` + Draft）。01 PRD 读 ROADMAP 定位本版本主题（`roadmap_ref`/`target_version`），探测到同版本规划级 SPEC 时走**升级模式**（原文件 delta 升级为工程级，不新建）；06 release 用版本号规则；07 复盘 findings 回流更新 ROADMAP 下一版本主题。每个项目通常只跑一次，07 回流或战略调整时增量更新。

> **收敛闸门 `product-design-convergence`**：roadmap 与 01 PRD 之间的**必经硬闸门**——不通过不进入开发。核心判断："功能杂乱"不是审美问题，是治理问题；产品说的（AGENTS.md 定位）和产品做的（roadmap 功能清单）分家是根因。本流程建立**功能准入机制**：Phase 0 定位与支柱基线（AGENTS.md 最高权威）→ Phase 1 功能全景+定位对齐+支柱映射 → Phase 2 六维度收敛（D1 功能架构/D2 核心取舍/D3 IA+**导航准入三问**+导航预算/D4 迭代优先级/D5 **定位对齐与前提挑战**/D6 **系统级卫生**：后端膨胀+Feature Flag+文档权威）→ Phase 3 五类根因 Pattern 检测（A 定位漂移/B 架构无收敛/C 前端 IA 债/D 后端膨胀/E 文档权威失守）→ Phase 4 收敛后功能清单（01 PRD 唯一输入）→ Phase 5 裁决记录+交棒。导航准入三问：Q1 独立任务域？Q2 频率≥每周？Q3 导航预算内？三问不过禁止新增顶级导航。定位漂移 >30% → 整个 roadmap 回炉。产出 CONVERGED-FEATURE-PLAN + IA-DIRECTION（含导航预算）+ SYSTEM-HYGIENE。非单功能 PATCH 修复版本必跑。

> **独立审计 `audit`**：`audit.md` 独立于 00–07 链路，可随时运行——模块化拆解（含 DB 模块）→ 并行 fan-out 事实 → 需求可追溯缺口 → 跨层联动测试 → 逐模块可用性审查（Mode A/B + Nielsen 10）→ 评级 → 裁决报告 → findings 带 SemVer bump 建议回流 roadmap。产出 `.csp/audit/`（MODULE-LIST/USABILITY-REPORT/AUDIT-VERDICT/FINDINGS）。兼容 CSP 全部约定；不写 lifecycle、不改代码，只产审计+建议（修复归 05/06）。

> **全链路审计 pipeline `audit-pipeline`**：发现层一键编排——按「工程体检（audit）→ 实机验证（e2e-deep-audit）→ UI/UX 八镜头（ui-review-to-iteration）→ 产品总监批评（product-critic-review）→ 单模块缺口深潜（feature-gap-analysis）→ 演进交棒（product-audit-to-roadmap）」顺序串联六个审查提示词，互不重复劳动。四道前置保险：运行模式检测（subagent 不可用 → Fallback 串行+完整性硬门控，禁止批量文件读取替代深度分析）、环境自检+会话重建（防 E2E 依赖断裂）、findings 基线强制回读（防重复侦查）、自动化门禁快照（机器证据前置）。存量仓库"深挖问题 → 修复 → 上线"先跑它。

> **产品巡检交棒 `product-audit-to-roadmap`**：07 复盘与外环 roadmap 之间的桥接流程，任意里程碑后/版本间隙可触发——巡检现有功能模块后从四个必选角度（增强规划/功能迭代/模块重组/界面规划）+ 按项目特征裁剪的扩展角度产出审查发现，把"版本主题候选+优先级+依据"交棒 roadmap（交棒不代行：版本号/序列由 roadmap 定）。全部结论来自实际读到的模块/代码/界面/反馈，高危结论（死代码/无鉴权/从未调用）实机核验带 file:line；产出 `docs/audit/PRODUCT-AUDIT-{date}.md` + 结构化 findings JSON。

> **独立深潜 `feature-gap-analysis`**：`feature-gap-analysis.md` 独立于 00–07 链路，可随时运行——锁定**单个已实现的页面/功能模块**，做现状重建 → 通用能力面扫描（F1–F12 横切关注点）→ **UI 与产品维度深审（U1–U7：宏观定位/信息架构/散乱/视觉与交互一致性/色调/用户习惯/响应式与 a11y，结合 `csp-frontend-design`/`csp-html-prototype`/`dataviz` 等设计技能）** → 领域增强目录对照（认证/CRUD/列表/搜索/上传/支付/Dashboard/消息/设置/审批等功能原型）→ 边界联动检查 → 优先级评级 → 交棒。粒度细到单页面/单模块（如 login 缺密码大小写校验、缺验证码、缺找回流程），findings 前缀 `GAP-F-NN`，落 `.csp/gap-analysis/`。P0 直发 04 拆 fix task → 05 → 06；P1/P2 攒批进 roadmap 版本主题。与 `audit.md`（全项目体检）、`product-audit-to-roadmap.md`（产品级演进方向）互补：audit 出结构问题 → 本流程深潜增强点；多模块 GAP findings 可由 product-audit 聚合。不写 lifecycle、不改代码，只产缺口+建议（实现归 01/03/05）。文末附「全界面自动巡检」驱动提示词——不指定页面时自动发现全部界面逐个深潜 + 跨模块 UI 一致性/重组聚合。

> **E2E 深度验证 `e2e-deep-audit`**：独立于 00–07 链路，发布前/大重构后全量体检用。四种模式：M1 交互验证+修复（四类证据→失败签名→最小修复→回归循环到 complete）、M2 建套件（POM+fixture+mock+storageState+CI sharding）、M3 只取证（截图/深浅色对比，不改码）、M4 深度审计（L1 存量套件→L2 全路由文件系统自动发现 sweep→L3 按钮级点击审计带安全 deny-list+JSONL 流式续析→L4 孤儿路由/隐藏后端功能/死按钮静态交叉审计→L5 schema drift/类型检查/mock 债务结构健康核查）。诚实化处置阶梯（接线>disabled+诚实 title>演示标注>禁死 CTA）、assert 过期先判、归因局限（NONE≠死按钮）、长任务脱离执行 shell、测量竞态先排除。**零 skill 依赖**，所有命令/代码/纪律内联，可直接粘贴独立执行；产物落 `verify/`+`evidence/`+`gap-analysis/`。与 `audit.md`（结构/可用性体检）互补：audit 出结构问题，本流程做页面级行为验证+死按钮审计。

> **产品总监批评性审查 `product-critic-review`**：独立于 00–07 链路，版本间隙/发布前任意时点触发。以产品总监/资深 PM 视角带 product sense 对**已实现功能与界面挑刺**（不是找缺口增强，而是批评已有问题）。七组镜头全覆盖：A 重复与冗余（功能重复跨模块 / 配置重复多处 / 实现重复 / 入口重复——按限界上下文判归属、单一真相源）、B 信息架构与模块组织、C 视觉与交互一致性、D 用户习惯与认知（Nielsen ①⑥）、E 宏观定位与产品阶段对齐、F 功能完整性与可用性违例（F1-F12 + Nielsen 10 + 领域目录）、G 状态覆盖与边界。内置设计判定清单 M1-M8（视觉层级/交互模式/响应式/原型验证/视觉基线对比/可访问性/限界上下文判散乱/图表规范），UI 改动建议先出原型不悬空提。每条 finding 必带产品 sense rationale（论证对用户认知/效率/信任/定位的具体伤害），区分真问题 vs 审美偏好。落 `.csp/critic/`（`CRITIC-F-NN`）+ `docs/analysis/`，经 `回流阶段` 字段三路径汇入主线：P0 直发 04 fix / P1·P2 经 Phase 2.5 集成必要性审视交棒 roadmap→01 / deferred 自动承继下一版本。与 `audit`（工程结构体检）、`feature-gap`（增强深潜）互补可串联，前缀不同可并存去重。

> **UI/UX 设计总监审查 `ui-review-to-iteration`**：独立于 00–07 链路，版本间隙/发布前任意时点触发。以 UI/UX 设计总监视角对**全部界面做系统性审查**，产出从审查方法到版本迭代的完整闭环。六大 Phase 贯穿：Phase 1 审查前基线建立（产品定位+设计系统+Token 漂移对照表+界面全景）；Phase 2 八镜头逐模块审查（①视觉层级与布局 ②交互模式与反馈 ③信息架构与导航 ④视觉与交互一致性 ⑤用户习惯与认知 ⑥响应式与多端适配 ⑦可访问性 ⑧状态覆盖与边界——8 个镜头共 50+ 细粒度检查项，均内联判定标准+反模式，不依赖外部 skill）；Phase 3 跨模块聚合裁决（一致性聚合/IA 重组/Token 漂移全局治理/宏观定位复检）；Phase 4 提升点优先级矩阵（4 级严重度 + P0-P3 四级优先级 + 版本迭代路线图模板 + 按产品阶段的迭代节奏建议）；Phase 5 落实到产品文档（Finding→PRD/UI 要求、Finding→Spec/验收标准、Finding→Task/实现的具体映射格式）；Phase 6 版本迭代执行与回归验证（执行流+回归清单+闭环度量）。内置附录：审查执行快速参考卡、Nielsen 10 速查表、M1-M8 设计方法速查。落 `.csp/ui-review/`（`UI-F-NN`）+ `docs/analysis/`，交棒 roadmap。与其他提示词互补：`audit` 出结构问题 → 本流程做 UI 级分析 → `feature-gap` 出增强点 → `product-audit-to-roadmap` 聚合成产品演进方向。区别于 `product-critic-review`（产品总监挑刺已有功能，侧重定位/重复/散乱/反习惯）——本流程专注 UI/UX 层面的视觉/交互/一致性/可访问性/状态覆盖，侧重"界面怎么改、怎么排期"。

> **自动化验证层 `automation-validation`**：提示词↔脚本契约——把"判断与裁决"（提示词，需 product sense）与"确定性检测"（脚本，可机器判定）分离。定义 9 个治理门禁（G-POS 定位漂移/G-NAV 导航预算/G-DOC 文档新鲜度/G-FLAG Flag 卫生/G-PLACEHOLDER 占位增长/G-DUAL-NAV 多导航源/G-CONTRACT 契约孤儿/G-BUTTON 按钮 a11y/G-LAYER 分层违规），映射五类根因 Pattern A-E，统一编排命令 `python scripts/validate_gates.py`，退出码 0/1/2 语义，JSON 报告落 `.csp/convergence/GATE-REPORT-{date}.json` 供 convergence/audit-pipeline/ui-review 程序化消费。参考实现已在 auto_content 落地（委托既有 scan_contract.py/button_audit.py/lint_layer.py，新增 6 个治理门禁）。提示词层项目无关（引用门禁 ID + JSON schema），脚本层项目特定（路径/关键词/阈值可移植）。含 CI 集成示例 + 移植到新项目的 5 步模板化指引。

> **开发期预防规范 `prevention-norms`**：从历次 UI/UX 审计 findings 提炼的根因→机器可查约束。8 条编码规范（N1 路由必须注册/N2 导航只放目的地/N3 同域单一事实源/N4 按钮文案动作词典/N5 占位规范/N6 hex-token 纪律/N7 deprecation 带 TTL/N8 立项查重）+ 5 个 CI 门禁（G1 route_registry/G2 wording_check/G3 placeholder_gate/G4 deprecation_ttl/G5 hex_lint，含统一脚本接口约定 exit 0/1/2/3 + stdout JSON）+ 7 项审查链路增强（R1-R7）。供 AGENTS.md 检查清单引用，与 `automation-validation.md` 的 G-* 门禁互补（G1-G5 是 PR/push 级编码门禁，G-POS 等是治理级收敛门禁）。

> **功能去重护栏 `feature-dedup-guardrails`**：开发期（05 实施）功能准入护栏，与规划期 `product-design-convergence`（收敛闸门）互补——闸门裁决"该不该做"，护栏约束"怎么做不产生重复冗余"。**通用方法论，项目无关**（支柱名/基础设施通道/元数据源/次级入口均为占位符，各项目在 AGENTS.md/.csp/product-spec/ 实例化）。定义功能重复冗余四形态（R1 平行页面/R2 旁路实现/R3 元数据多副本/R4 语义重叠）+ 通用根因 + 边界判定（什么算"同一能力"，≥3 维度命中=重复候选）+ 六条开发前置约束（①定位查重 grep 域词典②支柱归属③复用统一基础设施通道④元数据单一事实源⑤导航准入三问+预算⑥完成前唯一性自检+归并/复用/新增三行清单）+ 预防措施四层级（事前规划>事中开发>事中CI>事后审计，成本递增）+ 反模式 + 边界豁免（不同支柱同名/只读vs可写/平台适配/测试mock/TTL过渡入口）+ §七可粘贴 prompt 片段。注入 `05-implementation.md` §7.0 作为每个新功能 TDD 前的强制 gate；N8 立项查重是其约束 1 的 CI 版，G-POS/G-NAV/G-DUAL-NAV 是其约束 2/5 的机器版，critic 镜头 A 是其 R1-R4 的事后兜底版。

> **Python 代码审查 `python-code-review`**：独立于 00–07 链路，随时可跑的 Python 专项 code review 提示词。综合提炼自 `csp-python-reviewer`（含 coding-standards/security-checklist/project-structure 三份 references）、`csp-code-review` 六维方法论、`csp-ruff-fixer` lint 修复纪律、`python-testing` 测试实践、`python-review` command 流程与 adversarial/edge-case 审查工具。**零 skill 依赖、自包含**——全部规则/清单/命令/模板已内联，可直接复制粘贴到任意 Agent 执行。三种模式：Mode A diff/PR 审查（默认，五步审查法：读意图→先读测试→六维读实现→追踪关键路径→检查接缝）、Mode B 文件/模块审查、Mode C 全项目审计（叠加六维工程完备性 A-D 评估矩阵 + 结构反模式）。核心资产：硬规则 H1-H8（裸 except/f-string SQL/eval-exec/硬编码密钥等 CRITICAL 级禁止项）+ 必须项 M1-M5 + 按严重度分组的优先级速查 + OWASP 安全深度清单（SQL/命令/路径/模板注入、反序列化、密钥、依赖 P0-P3、TOCTOU）+ 框架特化检查（FastAPI/Django/Flask/Agentic-LLM）+ Python 版本兼容性核查 + 严重度评级（CRITICAL-LOW/NIT）与反馈标签（blocking/suggestion/nit/question/praise）双轨制 + 裁决标准（Approve/Request Changes/Comment）+ 审查反模式自查（橡皮图章/nit 轰炸/只审新增行等）。产物为带 file:line 证据与可执行修复的审查报告，可与 06 发布门控衔接。

> **棕地文档整合 `brownfield-doc-integration`**：独立于 00–07 链路，是 00 Phase 1.5/1.7 在"docs/→.csp/ 双轨整合"上的具体化。棕地项目 onboarding 时跑——把 `docs/` 的 `prd/`/`strategy/`/`solutions/`/`analysis/` 蒸馏+索引进 `.csp/`（PRD→PMS、strategy→lifecycle/VERSION-REGISTRY、solutions→specs/review、analysis→audit/review），原文留 `docs/` 不复制全文，`.csp/` 只存工程蒸馏 + manifest 索引 + front-matter 互链。`.csp/AGENTS.md` 不存在先跑 00。可随时增量重跑（delta）。产物 `.csp/product-spec/` + `.csp/manifest.json` + `docs/` 整理归位。

## 阶段并入说明

- **S0 知识中枢** → `00-knowledge-hub.md`（基座阶段）。
- **S1 需求拆解** → `02-decomposition.md`（独立阶段；PRD 已含模块边界为隐式拆解）。
- **S2 技术选型** → 并入 `03-tech-design.md`「技术选型」节。缺选型时由 03 自行产出 `.csp/tech-decisions/` + ADR；已选型则复用。
- **S2.5/S2.6/S3 技术方案+评审+全栈 Spec** → `03-tech-design.md`。
- **S3.5 任务拆解 + S4 实施规划** → 独立成 `04-task-breakdown.md`（Spec → Task + DAG + Wave），与 `05-implementation.md`（并行开发）分离。同一 Lead 上下文连续（lifecycle-state + 共享 `.csp/tasks/`）。
- **S5 实施** → `05-implementation.md`。
- **S6/S7/S8/S9 质量门控/审查/发布/运维** → `06-verify-ship.md`（本阶段内部子步骤，非管线 stage）。

> 旧 S0-S9 是 CSP `lifecycle-contract.json` 的机器 id 别名，映射见 `csp-workflow/references/lifecycle-contract.json` 的 `stage_id_aliases`；00-07 为正典。

## 三说明书（living baseline）

| 说明书 | 治理对象 | 建立阶段 | 更新节奏 |
|---|---|---|---|
| **PMS** 产品说明书 | PRD 质量、模块边界 | 01 PRD 阶段 | PRD/需求变更时增量 |
| **CMS** 代码说明书 | 代码入口点/调用链/约定 | 棕地设计前 / 05 开发期 | 开发期增量、06 verify 通过后全量 re-align（不等上线） |
| **TMS** 测试说明书 | 存量+增量用例、需求→方法矩阵 | 03 技术方案阶段 | 变更只产 delta 用例 |

## 核心一致性约定

- **知识中枢前置**：每阶段探测第 0 步查 `.csp/AGENTS.md` + `.csp/manifest.json`；不存在 → 提示先执行 00。
- **manifest 回写**：各阶段产出实质页后回写 `.csp/manifest.json` 对应 item `source_type` + `build_status=built` + `content_hash`，保持索引实时。约定见 00「manifest 回写约定」节。
- **追溯锚点（单向）**：`.csp/` 产物 front-matter 单向锚定 `docs/` 原文（`prd_ref`/`original_ref`/`sources`）+ `.csp/` 内部互链（`pms_module`/`spec_ref`/`related_tasks`/`feature_id`/`task_id`）；**`docs/` 原文不内嵌 `.csp/` 引用**（`.csp/` 易变/临时，`docs/` 沉淀精确）；`docs/`↔`.csp/` 双向映射由 `manifest` 承载（`raw_path`↔`output_path`），不靠 `docs/` front-matter 反向链接。
- **数量关系**（详见 03「元数据与一致性」节）：PRD `feature_count`（模块/域级）≈ decomposition 域数 ≤ decomposition 原子 Feature 数 == Spec 数（1:1）；每份 P0/P1 Spec ≥1 Task。
- **归档规范**（详见 06「里程碑归档规范」节）：一次性发布产物用 `mv` 移入 `.csp/milestones/{milestone}/`；living baseline 与增量文档用 `cp -r` 快照归档（原件留在 `.csp/` 继续演进）。
- **变更同步**：各阶段重新执行时先读既有产物 diff delta，只改 delta，沿追溯链传播 stale 标记并回写 manifest `degraded`。
- **跨文档引用**：用**节标题**引用（稳定），不用节号数字（避免增删节后错位）。
- **默认优先**：可逆/非破坏/非外向的决策一律取默认自动执行，不打断用户；仅在破坏性/不可逆/外向操作（删除来源、Git 发布、删业务文档）时人工拍板。各阶段"引导模式"的问询仅针对**输入真缺失**，不针对可默认的偏好。
- **文档管理边界**：`.csp/` = 编程管理统一库（PMS/CMS/TMS + 全部流水线产物，agent/工程消费、git 跟踪）；`docs/` = 非编程人类文档（README/USER-GUIDE/通用概览/analysis/CHANGELOG + PRD 人类原文，其工程形态 PMS 在 `.csp/`）。编程产物不散落 `docs/`，非编程文档不进 `.csp/`。
- **版本号默认 SemVer**：X.Y.Z 语义化（MAJOR 不兼容/MINOR 功能/PATCH 修复），**不自动用日期形式 tag**；tag 取 roadmap 规划的版本号（提前交付仍用规划版本号，非今日日期）。CalVer 仅用户显式 opt-in。
- **战略主题号 ≠ SemVer 发布号**：roadmap 的 v2.0/v3.0 是远期战略愿景叙事，**不是版本发布 tag**。实际发布号按 SemVer 从上一 tag 增量续编：additive（新模块/新端点/无 breaking）→ MINOR+1；breaking API → MAJOR+1；fix → PATCH+1。MAJOR 只在 06 发布时验证到**实际 breaking API 变更**才 bump——战略愿景宏大 ≠ MAJOR bump。
- **攒批发布，feat/fix 分轨**：多个 feat 攒一个 MINOR+1 版本、多个 fix 攒一个 PATCH+1 版本，不为每个小功能单独发版；同迭代既有 feat 又有 fix → 拆两个发布（feat 批 MINOR tag + fix 批 PATCH tag），不混合成一个版本（fix 的 PATCH 性质不被 MINOR 掩盖）。
- **版本全生命周期追踪**：`released ≠ deployed ≠ prod-verified`。`.csp/ship/VERSION-REGISTRY.md` 记录每版本全生命周期（planned→released→deployed→prod-verified→rolled-back）+ 实际交付 + 四方对齐（tag↔package.json↔prod health↔CHANGELOG）。`lifecycle-state.prod_version` ≠ `latest_release`——线上跑的不一定是最新的。05 开始前检查 prod 版本对齐。
- **Finding ID 前缀规则（防冲突）**：audit=`AUDIT-F-NN`，feature-gap=`GAP-F-NN`，07 review=`REV-F-NN`，03 TDD 评审=`TDD-REV-F-NN`，01 PRD 评审=`PRD-REV-F-NN`。不同来源 finding 不混编，追溯按前缀路由。
- **audit 衔接**：audit P0 findings（`快速修复=true`）→ orchestrator 直发 04 拆 fix task（`fix(audit-F-NN)`）→ 05 fix → 06 verify（不等 roadmap/01）；P1/P2 → roadmap 版本-主题表，下一轮走 01→04→05。04 读 `.csp/audit/AUDIT-FINDINGS-{milestone-slug}.json` 拆 fix task。
- **阶段穷尽**：每阶段必须**穷尽完成本阶段全部任务**才可标 `done`、写 lifecycle 进下一阶段，不遗留尾巴到下游。例：03 必须为 decomposition 每个 Feature 产出 Spec（硬门控 Spec 数 == Feature 数）；04 必须为每个 P0/P1 Spec 拆 Task；05 必须按全部 Wave 实施完。下游探测发现上游有缺漏 → 停步路由回上游补全，不臆造、不绕过。
- **评审/批准 gate（默认自动，不等人）**：① **PRD 评审**（01 完成前，reviewer≠author，auto 跑、findings 自动应用、无未解 Critical 自动 `Approved` 进 02，**不要求人工批准**；仅 Rejected fundamental 才人工）；② **Git 发布**（06，S6 质量门控+S7 审查+对账全过后**自动 push+GitHub Release**，gate 即授权，不再二次人工确认；版本号一致性见 06「版本与发布规范」节）；③ **07 复盘**（里程碑后可选触发）。**仅无前置 gate 的纯破坏操作（删 source、删业务文档）才人工拍板。**
- **门控执行完整性（禁止静默降级）**：auto-proceed 只认**真实执行**（`ran: <命令> exit <code>`），不认降级（grep 替代 typecheck/test/build）。工具链不可用→`BLOCKED`→不发布、tag 标 `-draft`。`not-run`=阻断。版本叠加：上版 not-run→本版警告先对齐再加新功能。
- **提交规范（自审通过即 local commit）**：自审 + 本阶段 gate 绿 → 立即本地 commit 到主干（原子、conventional message、禁 WIP 破码），**不留"未提交"收尾态**（不 commit=未完成）；push remote 才 gate（06 release）。格式/哪些说明/哪些忽略见 `version-management.md`「十六、提交规范」。

## 文档与图规范（全链路 Markdown 产物遵守）

- 标题层级 H1→H2→H3 不跳级；代码块标注语言（`` ```typescript ``）。
- 中文排版：中英文之间加空格。
- 仓库内链接用相对路径；图片统一放 `docs/images/`。
- 简单对比用表格，复杂数据用独立文档。
- 架构图用 Mermaid（GitHub 原生渲染），单图 ≤15 节点，每图配 2–3 句文字说明，架构变更时同步更新。
- 公共 API 用 TSDoc/JSDoc 注释（参数、返回、异常、示例），代码即文档。

## 使用方式

每份提示词可直接作为对应阶段 Agent 的 system prompt。Agent 拿到提示词即可独立完成本阶段任务，通过固定目录、front-matter 与 manifest 与上下游阶段互链，不依赖外部技能加载。建议从 00 起，按链路顺序推进；每阶段探测时若发现上游缺失，路由回上游或进引导模式。

## 阶段状态追踪（Agent 如何知道"现在第几步、下一步去哪"）

全链路用**单一状态文件** `.csp/lifecycle-state.json` 记录流水线进度，由 00 初始化、各阶段读/写、06 对账闭环、07 复盘回流。

**粒度原则**：lifecycle-state 只记**阶段级 + 每阶段 progress 摘要（指针/计数）**，不存全量任务/用例。细粒度状态各有归属：Task 在 `.csp/tasks/WBS.md`、AC 覆盖在 `.csp/traceability/COVERAGE-REPORT.md`、产物 build_status 在 `.csp/manifest.json`。lifecycle-state 是导航摘要，避免重复臃肿。

> ⚠️ 以下 JSON 为 **schema 格式示例**，其中的 `milestone`/`prod_version`/`latest_release` 等字段值（`v1.0`/`v1.3.0`/`v1.4.0`/`M1-…`）均为占位演示，**不是本仓库真实版本**。真实版本以 `VERSION` 文件 + `git tag` 为准。

```json
{
  "pipeline_version": 1,
  "milestone": "v1.0",
  "milestone_name": "M1-analytics-ops-dashboard",
  "current_stage": "03-tech-design",
  "last_updated": "...",
  "reconciled": false,
  "prod_version": "v1.3.0",
  "latest_release": "v1.4.0",
  "stages": [
    {"id":"00-knowledge-hub","name":"知识中枢初始化","status":"done","prompt":"00-knowledge-hub.md","outputs":[".csp/AGENTS.md",".csp/manifest.json"],"progress":{"manifest_items":42,"built":40,"pending":2}},
    {"id":"01-prd","name":"PRD 生成","status":"done","prompt":"01-prd.md","prd_slug":"order-refund","feature_count":5,"progress":{"prd_status":"Approved","pms_modules":4}},
    {"id":"02-decomposition","name":"需求拆解","status":"done","prompt":"02-decomposition.md","feature_count":12,"domain_count":4,"progress":{"features":12,"ac_mapped":34,"dag_acyclic":true}},
    {"id":"03-tech-design","name":"技术选型+技术方案+Spec","status":"in_progress","prompt":"03-tech-design.md","progress":{"tech_decisions":"built","tdd_chapters":6,"specs":0,"ac_coverage":"0/34"}},
    {"id":"04-task-breakdown","name":"任务拆解+实施规划","status":"pending","prompt":"04-task-breakdown.md","progress":{"tasks_total":0,"waves":0,"dag_acyclic":null}},
    {"id":"05-implementation","name":"实施开发","status":"pending","prompt":"05-implementation.md","progress":{"tasks_done":0,"commits":0,"waves_done":0}},
    {"id":"06-verify-ship","name":"审查测试发布运维","status":"pending","prompt":"06-verify-ship.md","progress":{"quality_gate":"pending","review":"pending","shipped":false}},
    {"id":"07-reviewer","name":"整体复盘审查","status":"pending","prompt":"07-reviewer.md","progress":{"findings_total":0,"p0":0,"p1":0,"next_iteration":false}}
  ]
}
```

- **status 取值**：`pending`（未开始）/ `in_progress`（进行中）/ `done`（完成）/ `blocked`（阻塞）/ `stale`（上游变更需重跑）。
- **milestone ↔ version 映射（强制，防"代号 vs SemVer"模糊）**：`milestone` 字段**必须**是当前迭代的 SemVer 版本号（格式如 `vX.Y.Z`，取本仓库实际下一版本），**不得**用里程碑代号（`Mxx-codename`）。代号是叙事性愿景，不是机读版本——`milestone` 用代号会让 `milestone`/`prod_version`/`latest_release` 三者不在同一抽象层，映射不可机读。若需保留代号，用独立 `milestone_name` 字段（如 `"milestone": "vX.Y.Z", "milestone_name": "Mxx-codename"`）。06 发布时验证 `milestone`==本次 tag，与 `latest_release` 对齐；代号不参与版本对齐。
- **07 为可选触发阶段**：不在 00→06 的强制线性链路上；里程碑发布（06 done）后由用户触发复盘。07 的 findings 通过 `回流阶段` 字段驱动下一迭代 01-05。
- **每阶段开始（探测 step 0.5）**：读 `lifecycle-state.json`，确认本阶段前置阶段 status==`done`；未完成 → 路由回上游；明确"我是第 N 步、下一步是 Y"。
- **每阶段完成**：写 `lifecycle-state.json`——本阶段 status=`done` + 补 `progress` 摘要（计数/指针，非全量）、`current_stage` 指向下一阶段 id、`last_updated` 更新、`reconciled=false`（待 06 对账）。
- **06 对账闭环（发布归档前必做）**：06 读 lifecycle-state + WBS + COVERAGE-REPORT + manifest + traceability 交叉核对，纠正不一致（如某阶段声称 done 但细粒度未达），写回对账后的 lifecycle-state 并置 `reconciled=true`，再快照归档。详见 06「阶段状态对账与闭环」节。
- **重启/换会话**：Agent 读 `lifecycle-state.json` 即知链路停在何处、已完成哪些阶段、下一步该加载哪份提示词、是否已对账。
- **迭代回路**：上游变更时把受影响下游阶段标 `stale`，回到对应阶段重跑 delta，重置 `reconciled=false`。
- **与 manifest 的分工**：`manifest.json` 索引"有哪些知识产物"（build_status）；`lifecycle-state.json` 记录"流水线走到哪步 + 阶段进度摘要"。两者互补，06 对账时互相校验。

## 进度播报（每阶段开始与完成时向用户输出）

每阶段在 **step 0.5 读 lifecycle-state 后**（开始播报）与**完成写 state 后**（结束播报）各向用户输出一次紧凑进度条，让用户随时知道"现在第几步、已完成哪些、剩哪些"：

```
📊 进度 [00✓][01✓][02✓][03✓][04✓][05✓][06✓][07▶] 当前:07 整体复盘 | 已完成:00-06 | 剩余:下一迭代
```

- 图例：`✓` done / `▶` in_progress / `○` pending / `⛔` blocked / `↻` stale。
- 开始播报：标出本阶段为 `▶`，列已完成与剩余；若前置未完成则改为"⛔ 阻塞：前置 0X 未完成 → 路由回上游"。
- 结束播报：本阶段转 `✓`，`current_stage` 指向下一阶段，列剩余。
- 单行紧凑，不展开；细节在就绪卡/产物块里。
