# 版本号管理规范（独立参考文件）

> 本文件是版本号管理规则的**权威定义**，供 roadmap/06/05/README 引用。各提示词内仍保留各自相关内容；与本文件冲突时以本文件为准。
>
> ⚠️ **本文件出现的所有具体版本号（如 `v1.3.0`、`v1.105.269`、`vX.Y.Z`）与代号（`Mxx-codename`）均为 SemVer 规则的格式示例，不是本仓库的真实版本。** 本仓库真实版本以 `VERSION` 文件与 `git tag` 为准（当前 `0.11.1`）。切勿把示例版本号当作项目当前版本或历史 tag 来引用/对齐。

## 一、默认 SemVer（X.Y.Z）

- `MAJOR.MINOR.PATCH[-pre.N]`
- **MAJOR**（X）：不兼容的 API/架构变更、移除已弃用能力、范式跃迁。**仅在 06 发布时验证到实际 breaking API 变更才 bump MAJOR**——新增模块/新端点/新功能是 additive（MINOR），不是 MAJOR，无论战略愿景多宏大。
- **MINOR**（Y）：向后兼容的功能新增/主题交付（roadmap 每个版本主题通常对应一次 MINOR 递增）。
- **PATCH**（Z）：向后兼容的 bug 修复/小补丁（不改主题、不加功能）。
- **pre**：`alpha.N`（功能未完内部测）/`beta.N`（功能完公开测）/`rc.N`（发布候选）。

## 二、顺序递增不跳跃

- **版本号是顺序计数器，不是"宏大程度"指示器**：v1.105.269 完全正常——做了 105 次 MINOR 递增、269 次 PATCH 修复是正常的迭代节奏；大数字≠大版本，只代表迭代次数多。
- **MINOR/MAJOR 不跳跃**：MINOR 从上一已发 tag +1 顺序递增，**不因"这版很重要/很大"跳 MINOR 或跳 MAJOR**。
- **不轻易跳 MAJOR**：MAJOR 只在**实际 breaking API 变更**时 +1。additive 永远 MINOR+1，哪怕 MINOR 已经是 105。
- **只有 PATCH 可以跳号**（如 v1.2.0 → v1.2.2，跳过 v1.2.1）。
- **攒批发布，不逐功能 bump**：版本号按**发布批次**递增，不按单个功能递增——一个版本可包含多个**同类**变更，攒一批发一次、只 bump 一次。不要"一个小功能就发一版、bump 一次"。
- **以模块为单位聚合（版本作用域规则）**：一个版本**不限于一个功能**——把**同一模块**相关的几个功能打包成一个版本是常态（模块内聚 → 同一版本主题 → 一次 MINOR+1）。跨模块的功能拆到各自版本；同模块但不相关的功能也不硬凑。判定：功能共享同一模块边界/数据/职责链 → 同版本；否则拆分。"一个版本一个功能"不是默认形态，是模块内恰好只剩一个功能时的特例。
- **feat/fix 分轨，不混合**：additive（新功能）与 fix（bug 修复）走不同版本线——多个 feat 攒一个 **MINOR+1** 版本；多个 fix 攒一个 **PATCH+1** 版本。同迭代若既有 feat 又有 fix，**拆成两个发布**（feat 批打 MINOR tag、fix 批打 PATCH tag，commit 也按类型分开），不混合成一个 MINOR+1 版本（否则 fix 的 PATCH 性质被 MINOR 掩盖）。为某 feat 自身服务的修复属该 feat 一部分（归 MINOR 批）；面向已发布功能的独立 bug fix 走 PATCH 批。

## 三、战略主题号 ≠ SemVer 发布号

- roadmap 的 **战略主题**（如"平台化""生态开放"）是**叙事性愿景**，**不是 SemVer 发布号**——不能用战略主题号打版本的发布 tag。
- **实际发布号**按 SemVer 从上一个已发 tag **增量续编**。
- roadmap 的 v2.0/v3.0 战略号只在**实际 breaking/范式跃迁真正发生时**才作为 SemVer 号使用；在那之前，版本号按 SemVer 增量续编（v1.4/v1.5/...），逐步逼近战略号。

## 四、CalVer（仅显式 opt-in）

- `vYYYY.M.DD[-alpha.N|-beta.N]`：取**发布日期**。
- **默认不用日期形式**。仅当用户明确要求日期版本（典型：每日构建的终端应用）才用。
- 即便用 CalVer，tag 取 **roadmap 规划的版本号**，不自动用今日日期打 tag——提前/延后交付不改 tag。
- **AI 开发下时间形式版本号无意义**：AI 产出节奏与日历无关（可能几小时完成一个版本），按年/季/月/日定版本或估时毫无依据。默认 SemVer 增量续编，不引入日期维度。

## 五、Tag 规则

- `v` 前缀 + annotated tag（`-a`）+ 不可变（已推送不移动/删除）。
- CI 触发 `tags: ['v*']`。
- tag 取 **roadmap 规划的版本号**，不以今日日期生成 tag。

## 六、预发布与质量分级

- `alpha`（功能未完内部测）/`beta`（功能完公开测）/`rc`（发布候选）。
- NPM dist-tags：`alpha`/`beta`/`latest`。
- 质量分级：`exploration → insider → stable`。

## 七、SemVer bump 验证（06 发布时）

不从 roadmap 战略主题号取版本号；按**实际交付量**从**上一已发 git tag 顺序 +1**：
- additive（新模块/新端点/无 breaking API 变更）→ **MINOR+1**（如 v1.3.0→v1.4.0）。
- breaking（移除 deprecated/改变响应语义/不兼容 API）→ **MAJOR+1**。
- bug fix → **PATCH+1**。
- **战略愿景宏大 ≠ MAJOR bump**。不跳跃 MINOR/MAJOR。大数字正常。
- **攒批发布（同类型内）**：多个 feat 攒一个 MINOR+1 版本、多个 fix 攒一个 PATCH+1 版本，不为每个小功能单独发版递增。
- **feat/fix 分轨**：同迭代既有 feat 又有 fix → 拆两个发布（feat 批 MINOR tag + fix 批 PATCH tag），不混合成一个版本；详见 §二。

## 八、多平台版本同步（全源一致 + 单源派生）

版本号是**一个事实**，但各生态工具各自只认自己的文件。原则：**一处定义、多处派生、禁手填、脚本校验**——不手填就不会漂移。

### 8.1 来源分类（4 类）

| 类 | 角色 | 举例 |
|---|---|---|
| **真相源 (canonical)** | 唯一定义点 | `git tag`（发布锚点，不可变）+ 一个 canonical 文件（`VERSION` 或 `pkg/version.py`） |
| **打包消费** | 各生态打包工具读 | `package.json`、`pyproject.toml`、`tauri.conf.json`、Docker tag、iOS `CURRENT_PROJECT_VERSION` |
| **代码内常量** | 代码 import 的版本常量 | `version.py.__version__`、`src/version.ts`、`bin/*.mjs` 硬编码（如 `CSP_VERSION`） |
| **发布元数据/运行时** | 人读/线上报告 | GitHub Release tag_name+title、CHANGELOG 最新条目、prod health 端点 |

### 8.2 单源派生（禁手填，全部从 canonical 派生）

| 来源 | 派生方式 |
|---|---|
| `package.json` | build 时从 VERSION 注入，或 `scripts/sync-version` 写入 |
| `pyproject.toml` | `dynamic = ["version"]` + `version = {attr = "pkg.version.__version__"}`，从 version.py 派生 |
| `tauri`/Docker/iOS | build 时从 VERSION 注入（Docker `ARG VERSION`、iOS build setting） |
| 代码内常量 | build 注入 / `import` VERSION / 运行时读包 `package.json`，**不手填**（本仓库 `bin/csp-sdk.mjs` 的 `CSP_VERSION` 即此模式） |
| GitHub Release | 发版动作从 tag 创建，tag_name 自动==tag |
| CHANGELOG | 发版时校验最新条目==tag |
| prod health | 从打包注入的版本常量读，不另填 |

### 8.3 强制门控

- **sync 脚本**（`scripts/sync-version`）：从 canonical 读，写入所有派生文件。改版本只改 canonical + 跑 sync，一处。
- **verify 脚本**：发布前校验**全源字符串完全一致**，任一不一致 `exit 1` 阻断发布（详见 §十）。纳入 06 发布前清单为强制 gate。
- **禁手改派生文件**：派生版本字段不人工编辑；CI 校验版本与 canonical 不一致且非 sync 生成 → 失败。

## 九、版本注册表（VERSION-REGISTRY）

`.csp/ship/VERSION-REGISTRY.md`，每版本一行，记录全生命周期：

| SemVer | Tag | Status | Released | Deployed | Prod-Verified | Main Features（实际交付） | Breaking | Rollback | Roadmap 主题 |
|---|---|---|---|---|---|---|---|---|---|

**Status 流转**：
- `planned`（roadmap 规划）
- `released`（tag + GitHub Release 推送）
- `deployed`（灰度/全量部署到 prod）
- `prod-verified`（健康端点报告版本 == tag + 第一小时指标稳定）
- `rolled-back`（回滚 + 原因）

**released ≠ deployed ≠ prod-verified**——tag 推了不等于线上在跑。

## 十、版本对齐检查（发布前 gate + 部署后核对）

**verify-version 脚本 = 发布前强制 gate**（不通过 = BLOCKED，不发布、tag 标 `-draft`）：全源字符串必须完全一致——
1. `git tag` == canonical 文件（`VERSION` / `version.py`）
2. `package.json` == `pyproject.toml` == `tauri.conf.json` == Docker tag == iOS == canonical
3. **代码内版本常量**（`__version__` / `src/version.ts` / `bin` 硬编码 / `CSP_VERSION`）== canonical
4. CHANGELOG 最新条目 == tag
5. GitHub Release tag_name + title == tag（发版动作创建）

部署后核对：
6. **prod 健康端点报告版本** == tag（线上实际在跑）
7. VERSION-REGISTRY 最新行 status == `prod-verified`

任一不一致 → 标 `misaligned`，不标 prod-verified；发布前 gate 阻断发布。

## 十一、prod_version vs latest_release

- `lifecycle-state.prod_version`：线上实际在跑的版本（从 health endpoint 验证）。
- `lifecycle-state.latest_release`：最新推送的 tag。
- `lifecycle-state.milestone`：**当前迭代 SemVer 版本号**（格式如 `vX.Y.Z`，取本仓库实际下一版本），**非代号**；06 发布时验证 `milestone`==本次 tag。若保留代号用独立 `milestone_name` 字段（如 `Mxx-codename`）。`milestone`/`prod_version`/`latest_release` 三者必须同一抽象层（SemVer），代号不参与版本对齐——否则"milestone 是代号、version 是 SemVer"映射不可机读。
- **两者不一致 = 线上落后于最新发布**——05 开始前检查此差异。
- prod-verified 后更新 `lifecycle-state.prod_version = <verified version>`。

## 十二、版本漂移自动校正

package.json / VERSION 与**已发布 git tag** 不一致 → 以 tag 为 canonical，自动 bump 到 tag 版本，不问；仅多 tag 冲突/canonical 不明才人工。

## 十三、实际交付回填

release 后从 `git log <prev-tag>..<tag> --oneline` + CHANGELOG 回填"Main Features"到 VERSION-REGISTRY + roadmap version-主题表（`实际交付` 字段），与规划对比标 `planned vs delivered` 差异。

## 十四、05 版本叠加检查

开始新版本开发前，检查：
1. 上一版 06 门控执行记录——若任一 gate 是 `not-run`（降级/跳过）→ 警告"代码叠在未验证地基上"。
2. VERSION-REGISTRY 最新行 status——若不是 `prod-verified` → 警告"线上版本与最新 tag 不对齐"。
3. `lifecycle-state.prod_version` vs `latest_release` 不一致 → 警告"线上落后于最新发布"。

## 十五、反模式

| 反模式 | 症状 | 正确做法 |
|---|---|---|
| 战略号当 SemVer 打 tag | 版本做了起步标 v2.0.0（MAJOR）但无 breaking | additive→MINOR+1 递增；MAJOR 只在真实 breaking；大数字正常(v1.105.269) |
| 版本号跳跃 | 从 v1.4 直接 v2.0 无 breaking，或跳 MINOR | 从上一 tag 顺序+1，不跳 MINOR/MAJOR；PATCH 可跳 |
| 逐功能 bump 版本 | 一个小功能就发一版、bump 一次，版本号膨胀快 | 同类型攒批：多个 feat 合并一个 MINOR+1、多个 fix 合并一个 PATCH+1 |
| 强行一功能一版本 | 同模块的几个相关功能被拆成多个版本，主题碎片化、MINOR 号虚涨 | 以模块为单位聚合：同模块相关功能打包一个版本（不限于一个功能）；跨模块才拆 |
| feat/fix 混合 bump | additive+fix 同打一个 MINOR+1，fix 的 PATCH 性质丢失 | 分轨：feat 批 MINOR+1、fix 批 PATCH+1，同迭代有两类拆两个发布 |
| 日期形式 tag | 不问用户就用 v2026.9.3 | 默认 SemVer；CalVer 仅显式 opt-in |
| released 当 deployed | tag 推了就以为线上在跑 | released≠deployed≠prod-verified；五方对齐 + prod health 验证 |
| 版本字符串不一致 | tag ≠ package.json ≠ Release title | 五方完全一致，脚本校验 |
| 不回填实际交付 | release 后"实际做了什么"没记录 | git log + CHANGELOG 回填 VERSION-REGISTRY + roadmap |
| 静默门控降级后 auto-release | 工具链坏→grep 替代→auto-proceed | not-run=BLOCKED=阻断发布，tag 标 -draft |
| 代号当 milestone | `milestone` 写代号（`Mxx-codename`），与 `prod_version`/`latest_release` 不同层，映射不可机读 | `milestone`=SemVer（`vX.Y.Z`）；代号进 `milestone_name`；三者同层对齐 |

## 十六、提交规范（commit convention）

> 本节集中提交规则，供 00/05/06/各 agent 引用。**本地 commit 是正常操作（自审通过 + 任务/gate 完成即 commit 到主干）；push 到 remote 才 gate（06 release）**。禁止"任务结束留未提交工作树"作为收尾态——要么 commit，要么标 BLOCKED。

### 16.1 何时 commit
- **自审通过 + 本阶段 gate 绿** → 立即 local commit 到主干（master/main），不积压、不留"未提交"。
- **原子提交**：一个逻辑变更一个 commit；每 commit 独立可编译/可测过；**禁止 WIP 破码提交**（不通过 typecheck/test 的代码不 commit）；文件可数 ≤6、单一职责。
- `.csp/` 知识产物（manifest/lifecycle-state/PMS/CMS/TMS/specs/tasks/traceability/归档）= 共享基础设施 → 提交到主干，不建 side branch。
- **push 才 gate**：push remote + GitHub Release 在 06 release（S6/S7/对账全过）自动执行；非发布场景不 push。

### 16.2 格式（Conventional Commits）
```
<type>(<scope>): <subject>      # 一句话，祈使句，≤72 字，风格统一

<body>                           # 可选：解释 why（动机/取舍/breaking/迁移）；what 不必赘述（diff 自解释）

<footer>                         # 可选：BREAKING CHANGE: / Fixes #NN / Refs AUDIT-F-NN / Implements T-NN
```
**type**：`feat`（新功能）/`fix`（bug）/`docs`（仅文档）/`refactor`（不改行为）/`perf`/`test`/`build`/`ci`/`chore`（构建/脚手架/杂务/派生数据）/`style`（格式）。

### 16.3 哪些要说明（写 body）
- 非显而易见的改动：**为什么**这么做（动机/取舍/约束），而非做了什么。
- breaking 变更 + 迁移说明（footer `BREAKING CHANGE:`）。
- 关联追溯：finding/任务 id（`Fixes AUDIT-F-NN` / `Refs REV-F-NN` / `Implements T-NN`）。
- 约定/架构调整：why + 影响范围。

### 16.4 哪些可忽略（subject 足矣，不写 body）
- 纯机械编辑：路径 rename、格式化、typo、派生数据重生成（`chore: rebuild derived registry/triggers`）。
- 单一明显修复：subject 自解释的 one-liner（`fix(auth): token refresh resets retry counter`）。
- 文档措辞微调。

### 16.5 示例
```
feat(order): 支持订单退款全链路（PRD→PMS→Spec→Task）

采纳 07 finding REV-F-12（高并发退款事务回滚不一致）；扣库存并入退款事务
（见 .csp/specs/SPEC-F-order-3 §事务边界）。AC ORD-003..006 全演示。

Refs REV-F-12, Implements T-14
```
```
chore(csp): 统一产物路径到 .csp/（.planning→.csp/planning, spark-output→.csp/spark）
```
```
fix(auth): token 刷新后未重置 retry 计数
```

### 16.6 反模式
- **"未提交留工作树"收尾** → 自审通过必 commit；不 commit = 任务未完成（与 [[csp-artifact-path-convention]] 同期整改）。
- **WIP 破码提交** → 不通过门控的代码不 commit。
- **巨型 commit** → 一变更一 commit，文件可数 ≤6、单一职责。
- **只写 what 不写 why**（非显然改动） → body 写 why。
- **subject = "update"/"fix bug"** → 须自解释（祈使句 + scope）。
- **commit 半生体 push** → push 只在 06 release gate 通过后。
