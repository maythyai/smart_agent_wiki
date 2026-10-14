# 系统提示词集（端到端交付链路）

一套自包含的系统提示词 + 一个外环战略规划，覆盖从长期规划到上线运维与整体复盘的完整链路。外环 `roadmap.md` 先于 00 跑一次（每个项目通常跑一次用很久）；内环 00-07 每版本迭代执行。八份内环 + 一份外环同源同构：统一目录约定（`docs/` + `.csp/`）、统一 slug/feature-id 命名、统一 front-matter 单向锚定（`.csp/`→`docs/`）+ manifest 双向映射、PMS/CMS/TMS 三说明书全程 living 治理、归档就绪、变更 delta 同步。

## 链路与文件

| 顺序 | 阶段 | 文件 | 产出目录 |
|---|---|---|---|
| 外环 | 产品长期规划（战略锚点+版本号规则+版本序列路径+**版本功能集成必要性审视 gate**） | [roadmap.md](./roadmap.md) | `docs/strategy/`（STRATEGY+ROADMAP）+ `docs/analysis/`（INTEGRATION-NECESSITY） |
| 0 | 知识中枢初始化 | [00-knowledge-hub.md](./00-knowledge-hub.md) | `.csp/AGENTS.md` + `.csp/manifest.json` |
| 1 | PRD 生成（产品需求） | [01-prd.md](./01-prd.md) | `docs/prd/` + `.csp/product-spec/`（PMS） |
| 2 | 需求拆解（工程级 Feature） | [02-decomposition.md](./02-decomposition.md) | `.csp/decomposition/` |
| 3 | 技术选型 + 技术方案 + 全栈 Spec | [03-tech-design.md](./03-tech-design.md) | `.csp/tech-decisions/` + `.csp/tech-design/` + `.csp/specs/` + `.csp/test-spec/`（TMS） |
| 4 | 任务拆解 + 实施规划 | [04-task-breakdown.md](./04-task-breakdown.md) | `.csp/tasks/`（WBS/DAG/WAVE-PLAN） |
| 5 | 实施开发（多 Agent 团队） | [05-implementation.md](./05-implementation.md) | 代码（git worktree）+ `.csp/code-spec/`（CMS 增量）+ `.csp/artifacts/` |
| 6 | 审查·测试·发布交付·运维 | [06-verify-ship.md](./06-verify-ship.md) | `.csp/artifacts/{verify,review}/` + `.csp/ship/` + `.csp/ops/` + `.csp/milestones/` |
| 7 | 整体复盘审查（产品+技术，迭代探索） | [07-reviewer.md](./07-reviewer.md) | `.csp/review/` + `docs/solutions/`（摘要） |
| 独立 | 模块化审计+可用性审查+联动测试+roadmap bump | [audit.md](./audit.md) | `.csp/audit/` + `docs/analysis/`（摘要） |
| 独立 | 单页面/单功能模块缺口与增强深潜（通用面+领域目录+联动） | [feature-gap-analysis.md](./feature-gap-analysis.md) | `.csp/gap-analysis/` + `docs/analysis/`（摘要） |
| 独立 | E2E 深度验证（M1 交互验证+修复 / M2 建套件 / M3 取证 / M4 全路由 sweep+按钮级点击审计+孤儿路由/隐藏后端功能审计+结构健康核查） | [e2e-deep-audit.md](./e2e-deep-audit.md) | `verify/` + `evidence/` + `gap-analysis/`（零 skill 依赖，可独立粘贴） |
| 独立 | 产品总监批评性审查（重复/冗余/IA/视觉交互一致性/用户习惯/定位/完整性/状态 七镜头，带产品 sense 给 critic judgement） | [product-critic-review.md](./product-critic-review.md) | `.csp/critic/` + `docs/analysis/`（前缀 `CRITIC-F-NN`，交棒 roadmap→Phase 2.5） |
| 独立 | UI/UX 设计总监审查——从审查方法到版本迭代的完整闭环（八镜头→提升点分级→落实到 PRD/Spec/Task→版本迭代路线图→回归验证） | [ui-review-to-iteration.md](./ui-review-to-iteration.md) | `.csp/ui-review/` + `docs/analysis/`（前缀 `UI-F-NN`，交棒 roadmap） |
| 棕地 | docs/→.csp/ 双轨整合（PRD→PMS、strategy→lifecycle、solutions→specs、analysis→audit） | [brownfield-doc-integration.md](./brownfield-doc-integration.md) | `.csp/product-spec/` + `.csp/manifest.json` + `docs/` 整理归位 |

> **06 vs 07**：06 是**发布前符合性验证**（实现是否满足 PRD/Spec/AC、能否上线），是门控；07 是**里程碑后整体复盘**（产品对不对、架构稳不稳、下一步做什么），探索性/战略性，不卡发布。07 从用户视角+技术视角发现 Spec 之外的新问题，findings 回流下一迭代 01-05 + 外环 roadmap。

> **外环 roadmap**：`roadmap.md` 先于 00 跑一次——产出战略锚点（STRATEGY.md）+ 版本号规则 + 1/3 年+迭代路径（ROADMAP.md）。01 PRD 读 ROADMAP 定位本版本主题（`roadmap_ref`/`target_version`）；06 release 用版本号规则；07 复盘 findings 回流更新 ROADMAP 下一版本主题。每个项目通常只跑一次，07 回流或战略调整时增量更新。

> **独立审计 `audit`**：`audit.md` 独立于 00–07 链路，可随时运行——模块化拆解（含 DB 模块）→ 并行 fan-out 事实 → 需求可追溯缺口 → 跨层联动测试 → 逐模块可用性审查（Mode A/B + Nielsen 10）→ 评级 → 裁决报告 → findings 带 SemVer bump 建议回流 roadmap。产出 `.csp/audit/`（MODULE-LIST/USABILITY-REPORT/AUDIT-VERDICT/FINDINGS）。兼容 CSP 全部约定；不写 lifecycle、不改代码，只产审计+建议（修复归 05/06）。

> **独立深潜 `feature-gap-analysis`**：`feature-gap-analysis.md` 独立于 00–07 链路，可随时运行——锁定**单个已实现的页面/功能模块**，做现状重建 → 通用能力面扫描（F1–F12 横切关注点）→ **UI 与产品维度深审（U1–U7：宏观定位/信息架构/散乱/视觉与交互一致性/色调/用户习惯/响应式与 a11y，结合 `csp-frontend-design`/`csp-html-prototype`/`dataviz` 等设计技能）** → 领域增强目录对照（认证/CRUD/列表/搜索/上传/支付/Dashboard/消息/设置/审批等功能原型）→ 边界联动检查 → 优先级评级 → 交棒。粒度细到单页面/单模块（如 login 缺密码大小写校验、缺验证码、缺找回流程），findings 前缀 `GAP-F-NN`，落 `.csp/gap-analysis/`。P0 直发 04 拆 fix task → 05 → 06；P1/P2 攒批进 roadmap 版本主题。与 `audit.md`（全项目体检）、`product-audit-to-roadmap.md`（产品级演进方向）互补：audit 出结构问题 → 本流程深潜增强点；多模块 GAP findings 可由 product-audit 聚合。不写 lifecycle、不改代码，只产缺口+建议（实现归 01/03/05）。文末附「全界面自动巡检」驱动提示词——不指定页面时自动发现全部界面逐个深潜 + 跨模块 UI 一致性/重组聚合。

> **E2E 深度验证 `e2e-deep-audit`**：独立于 00–07 链路，发布前/大重构后全量体检用。四种模式：M1 交互验证+修复（四类证据→失败签名→最小修复→回归循环到 complete）、M2 建套件（POM+fixture+mock+storageState+CI sharding）、M3 只取证（截图/深浅色对比，不改码）、M4 深度审计（L1 存量套件→L2 全路由文件系统自动发现 sweep→L3 按钮级点击审计带安全 deny-list+JSONL 流式续析→L4 孤儿路由/隐藏后端功能/死按钮静态交叉审计→L5 schema drift/类型检查/mock 债务结构健康核查）。诚实化处置阶梯（接线>disabled+诚实 title>演示标注>禁死 CTA）、assert 过期先判、归因局限（NONE≠死按钮）、长任务脱离执行 shell、测量竞态先排除。**零 skill 依赖**，所有命令/代码/纪律内联，可直接粘贴独立执行；产物落 `verify/`+`evidence/`+`gap-analysis/`。与 `audit.md`（结构/可用性体检）互补：audit 出结构问题，本流程做页面级行为验证+死按钮审计。

> **产品总监批评性审查 `product-critic-review`**：独立于 00–07 链路，版本间隙/发布前任意时点触发。以产品总监/资深 PM 视角带 product sense 对**已实现功能与界面挑刺**（不是找缺口增强，而是批评已有问题）。七组镜头全覆盖：A 重复与冗余（功能重复跨模块 / 配置重复多处 / 实现重复 / 入口重复——按限界上下文判归属、单一真相源）、B 信息架构与模块组织、C 视觉与交互一致性、D 用户习惯与认知（Nielsen ①⑥）、E 宏观定位与产品阶段对齐、F 功能完整性与可用性违例（F1-F12 + Nielsen 10 + 领域目录）、G 状态覆盖与边界。内置设计判定清单 M1-M8（视觉层级/交互模式/响应式/原型验证/视觉基线对比/可访问性/限界上下文判散乱/图表规范），UI 改动建议先出原型不悬空提。每条 finding 必带产品 sense rationale（论证对用户认知/效率/信任/定位的具体伤害），区分真问题 vs 审美偏好。落 `.csp/critic/`（`CRITIC-F-NN`）+ `docs/analysis/`，经 `回流阶段` 字段三路径汇入主线：P0 直发 04 fix / P1·P2 经 Phase 2.5 集成必要性审视交棒 roadmap→01 / deferred 自动承继下一版本。与 `audit`（工程结构体检）、`feature-gap`（增强深潜）互补可串联，前缀不同可并存去重。

> **UI/UX 设计总监审查 `ui-review-to-iteration`**：独立于 00–07 链路，版本间隙/发布前任意时点触发。以 UI/UX 设计总监视角对**全部界面做系统性审查**，产出从审查方法到版本迭代的完整闭环。六大 Phase 贯穿：Phase 1 审查前基线建立（产品定位+设计系统+Token 漂移对照表+界面全景）；Phase 2 八镜头逐模块审查（①视觉层级与布局 ②交互模式与反馈 ③信息架构与导航 ④视觉与交互一致性 ⑤用户习惯与认知 ⑥响应式与多端适配 ⑦可访问性 ⑧状态覆盖与边界——8 个镜头共 50+ 细粒度检查项，均内联判定标准+反模式，不依赖外部 skill）；Phase 3 跨模块聚合裁决（一致性聚合/IA 重组/Token 漂移全局治理/宏观定位复检）；Phase 4 提升点优先级矩阵（4 级严重度 + P0-P3 四级优先级 + 版本迭代路线图模板 + 按产品阶段的迭代节奏建议）；Phase 5 落实到产品文档（Finding→PRD/UI 要求、Finding→Spec/验收标准、Finding→Task/实现的具体映射格式）；Phase 6 版本迭代执行与回归验证（执行流+回归清单+闭环度量）。内置附录：审查执行快速参考卡、Nielsen 10 速查表、M1-M8 设计方法速查。落 `.csp/ui-review/`（`UI-F-NN`）+ `docs/analysis/`，交棒 roadmap。与其他提示词互补：`audit` 出结构问题 → 本流程做 UI 级分析 → `feature-gap` 出增强点 → `product-audit-to-roadmap` 聚合成产品演进方向。区别于 `product-critic-review`（产品总监挑刺已有功能，侧重定位/重复/散乱/反习惯）——本流程专注 UI/UX 层面的视觉/交互/一致性/可访问性/状态覆盖，侧重"界面怎么改、怎么排期"。

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
