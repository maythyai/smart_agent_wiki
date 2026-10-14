# E2E 深度验证提示词（Deep Audit）

> 用途：给 Agent 下达「全页面 E2E 验证 / 深度产品审计」类任务时直接粘贴。零外部依赖，所有命令、代码模式、判定纪律均内联。
> 模式：M1 交互验证+修复 / M2 建套件 / M3 只取证 / M4 深度审计（四层+结构健康核查）。
> 默认模式：判不清走 M1；"全页面验证/发布前体检"走 M4。

---

## 一、模式路由（先判属于哪种，判不清默认 M1）

- **M1 交互验证+修复**：改完想确认并修到 complete → 证据→失败签名→最小修复→回归（同用例→相邻→全量）。允许最小修复代码。
- **M2 建套件/补 flaky/接 CI**：POM+fixture+mock+sharding 工程化。只产测试代码，不改被测功能。
- **M3 只截图取证**：输出 FIX_SUGGESTION，不改项目代码。
- **M4 深度产品审计**：M1 基础上加四层——① 全路由 sweep ② 按钮级点击审计 ③ 孤儿路由审计 ④ 隐藏后端功能审计 + IA 合理性评审 + 结构健康核查（L5）。用于版本发布前/大重构后全量体检，**不进日常 PR 反馈**（太重）。

## 二、环境前置（先探实测值再开工）

1. **基础设施健康**：DB/缓存等用 `pg_isready` / `redis-cli ping` 等探活，**Docker 容器不必特意起**，原生服务在跑即可。
2. **后端**：起后端到约定端口，用 `GET <健康检查路径>` 确认。⚠️ 同机可能有**无关服务占用相近端口**——按健康检查路径+响应体确认是本项目后端，不要凭端口号认。
3. **限流/风控开关**：全量套件必跑前，`.env` 关闭限流（如 `RATE_LIMIT_ENABLED=false`），否则全量跑必现 429、断言精确数据的用例会挂。
4. **前端**：`<dev 命令>` 起 dev server，等就绪日志取端口。Turbopack/冷编译首访可达 15s+，断言 poll 超时给 30s。
5. **长任务脱离执行 shell**：起 dev server/后端等长进程必须**脱离**当前 shell——runner 断连会连带杀 background shell 进程。macOS 无 `setsid`，用
   `python3 -c "import subprocess,sys; subprocess.Popen(sys.argv[1:], start_new_session=True)" <cmd...>` 派生；
   产物写 /tmp 文件，用短轮询（≤60s/次）读进度，**禁止长 sleep 同步等待**。
6. **登录态**：套件用 `tests/e2e/auth.setup.ts`（API 登录→`storageState`，绕过 UI 登录，每测免登）；手工排查用 `playwright-cli state-load <auth.json>`。前端 login 报凭证错时，**先查后端起没起、健康检查通不通**，再怀疑凭证。

## 三、四类证据（每次判定必须附，缺一不判）

1. **DOM 快照**：`snapshot`（大页 `snapshot "#panel"` 或 `--depth=4` 限流）。
2. **过滤后网络**：`--raw network | grep "<接口关键词>"` 或 `grep -E " 5[0-9]{2} "` 看 5xx，**不全量导出**。
3. **控制台**：`console error` 默认判失败证据（除非证明与用例无关）；`warning` 记录不阻断。
4. **截图**：落 `evidence/<用例ID>-<步骤>-<状态>.png`，通过/失败成对保留。
判定结论必须引用至少一类证据——读代码不能替代跑页面。

## 四、操作范式（snapshot-ref 驱动）

先 `snapshot` 拿元素 ref（如 e15）→ 用 ref 操作 → 操作后回显新快照验证：
```
playwright-cli snapshot
playwright-cli fill e5 "user@example.com" --submit
playwright-cli click e3
playwright-cli snapshot
```
ref 失效降级链：`getByRole('button',{name:'提交'})` → `getByTestId('submit-btn')` → CSS（最后手段）。
被测项目已有 `playwright.config.ts`/`tests/` 时：先跑存量套件 `PLAYWRIGHT_HTML_OPEN=never npx playwright test`；失败用 `--debug=cli` 挂会话调试，手工稳定后把操作序列沉淀为正式 spec（playwright-cli 操作会回显对应 TS 代码，可直接拷进测试）。

## 五、风险评估 + Fast Path（M1）

低风险（纯样式/文案/纯展示、使用方行为不变）→ Fast Path：冒烟级（页面可开+关键元素可见+主交互一次+前后截图），报告标 `[fast-path]`。任一冒烟失败立即转完整流程。
高风险（交互/状态/数据流/接口契约变）走完整流程（全用例+四类证据）。

## 六、M4 深度审计四层 + 结构健康核查

### L1 存量套件
`PLAYWRIGHT_HTML_OPEN=never npx playwright test`（含路由/按钮审计 spec 则更久，shard 跑）。

### L2 全路由 sweep（文件系统自动发现，不手维护清单）
- 路由来源：遍历文件系统（如 `src/app/**/page.tsx`），跳过 `api/`/`login`/`(auth)`，**新增页面自动纳入**。
- ⚠️ **动态段禁止跳过**：`[slug]`/`[id]`/`[...catchAll]` 动态路由段必须解析内部配置表（如 `[dashboard]/page.tsx:17-26` 枚举了全部子模块），不是直接用 `[slug]` 做单个 URL 请求。**本轮实证**：`phase-k/[dashboard]` 承接 11 个深度模块，扫描脚本因 `if "[" in route: return None` 全跳过——直到手动审查才发现。
- 每路由断言：内容渲染（多 `<main>` 时取 **max-over-mains**，禁 `.last()`/`.first()` 误判嵌套 layout）/ 0 非良性 console error / 0 个 5xx / 可见 heading 或 button。
- **必须 `expect.poll` 带超时**：一次性检查在 shell 导航文本先渲染时竞态误报；冷编译首访可达 15s+，poll 超时给 30s。
- 每路由**独立 page + 独立 error probe**（共享 probe 无法定位到路由）。

路由发现参考实现（按框架适配）：
```typescript
// 以 Next.js app router 为例
import { readdirSync, readFileSync } from "fs"; import { join, relative } from "path";
const SKIP = /\/(api|login|\(auth\))/;  // ← 不再跳过 [dynamic]
function discover(dir: string, out: string[] = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) discover(p, out);
    else if (e.name === "page.tsx") {
      const r = "/" + relative("src/app", dir).replace(/\\/g,"/").replace(/^\(.*?\)\//,"");
      if (!SKIP.test(r)) {
        // 动态段解析：读取 page.tsx 内的子模块配置表
        if (r.includes("[")) {
          const src = readFileSync(p, "utf-8");
          // 模式 1: 枚举配置（const DASHBOARD_MODULES = [...]）
          const configMatch = src.match(/(?:MODULES|TABS|ROUTES|ITEMS)\s*=\s*\[([\s\S]*?)\]/);
          if (configMatch) {
            // 从配置表中提取每个子模块的 path/slug
            const slugs = [...configMatch[1].matchAll(/(?:path|slug|href)\s*:\s*["']([^"']+)["']/g)];
            slugs.forEach(s => out.push(r.replace(/\[.*?\]/, s[1])));
          } else {
            // 模式 2: generateStaticParams（读取返回值中的 params）
            const genMatch = src.match(/generateStaticParams[\s\S]*?return\s+\[([\s\S]*?)\]/);
            if (genMatch) {
              const slugs = [...genMatch[1].matchAll(/(?:slug|id)\s*:\s*["']([^"']+)["']/g)];
              slugs.forEach(s => out.push(r.replace(/\[.*?\]/, s[1])));
            } else {
              out.push(r); // 无法解析配置表 → 保留原始动态路由占位
            }
          }
        } else {
          out.push(r || "/");
        }
      }
    }
  }
  return [...new Set(out)];
}
```

### L3 按钮级点击审计
- 每路由枚举可见 button，逐个真实点击；shell 按钮只在 `/dashboard` 审一次，其余页只审 `main` 内 button。
- 每次点击记录：`NET(method+path+status)` / `DIALOG` / `TOAST` / `NAV` / `NONE(无反应=死按钮候选)`，流式写 JSONL（`/tmp/button_audit*.jsonl`），失败可断点续析。
- **安全 deny-list 强制**（只记 `SKIPPED` 不点击）：删除|移除|退出登录|注销|清空|重置|退订|支付|购买|立即发布|授权|绑定|停用|丢弃|delete|remove|logout|reset|dissolve|pay|purchase|revoke…
- 挂 `page.on("dialog"→dismiss / filechooser→拦截 / popup→close)` 防原生弹窗卡死。
- **归因局限（判读必记）**：`router.push` 的 RSC 提交慢于观测窗，`NONE`/`NET` 会串到下一个按钮——「NONE」只是死按钮**候选**，定性必须回源码看 handler + 与静态扫描交叉。
- 每路由按钮上限（超出记 `SKIPPED(cap)` 不静默截断）；大型审计分片 `--shard=i/N` + `AUDIT_TAG=_s$i` 各写各的 JSONL。

### L4 结构审计（三路静态 + 渲染引用链 + 两级引用扫描，可并行子代理）
> **去重契约**：本层是结构审计（孤儿路由/隐藏后端功能/死按钮）的**实机主跑方**；`audit.md` Phase 0 只标"疑似"，须在此实机确认后才成 finding。`product-critic-review` 镜头 B（IA）与 `feature-gap-analysis` Phase 4（联动）均引用本层结构 findings，不自行做按钮级/路由级实机审计。
- **孤儿路由**：全部路由 × 全部导航源（sidebar 配置 / 设置分组 / 用户中心导航 / 命令面板 / 快捷键 / hub 内链 / deprecated 重定向中间件）交叉；区分 真孤儿 / redirect 别名 / 有意隐藏（运维页、骨架页、重复页）。
  - ⚠️ **先判渲染源再判数据源**（本轮实证）：静态扫描看到 `SETTINGS_GROUPS` 就以为它是导航，实际渲染的是 `UserCenterNav` 组件。缺"JSX 渲染引用链"分析这一步。必须追踪：哪个组件 `import` 了哪个数据常量 → 哪个组件实际渲染了导航条目 → 对比两者是否一致。
  - ⚠️ **两级引用扫描**（本轮实证）：第一轮按 `import` 扫描后，又补了字符串级（拼接路径、常量表、`getRoute()` 等动态构造）才最终确证 4 个孤儿。**必须两级扫描后两个结果取并集**，缺一级即漏报。
- **隐藏后端功能**：后端全部路由注册 × 前端调用点交叉（生成函数存在 ≠ 被调用）；分 `WIRED`/`PARTIAL`/`ORPHAN`；`PARTIAL` 列具体缺失端点；识别"后端已有能力但 UI 显示即将上线"的前后端进度脱节。
- **死按钮静态扫描**：无 onClick 的 button / 非 submit 表单外按钮 / `href="#"` / `()=>{}` / 裸 disabled 无启用路径 / 仅 toast"即将上线"占位（诚实占位单列、低 severity）；排除误报（Radix DialogClose 的取消、Link 包裹的 Button、图标 SVG）。

### L4.5 — 渲染引用链分析（新增，本轮实证需求）

**问题**: 静态扫描看到数据常量（如 `SETTINGS_GROUPS`）不等于它就是渲染源。

**分析步骤**:
1. 找到导航入口组件（如 `Layout.tsx` / `Sidebar.tsx` / `AppShell.tsx`）
2. 追踪其 `import` 链：谁 import 谁、谁最后渲染了导航条目
3. 对比"数据常量"和"实际渲染组件引用的数据源"
4. 不一致 → 报 finding（双事实源 / 渲染漂移）

```typescript
// 示例：追踪链
// Step 1: AppShell.tsx → import Sidebar from './Sidebar'
// Step 2: Sidebar.tsx → import { SETTINGS_GROUPS } from '@/config/settings'
//     BUT: 实际渲染的是 <UserCenterNav /> 不是 SETTINGS_GROUPS.map()
// Step 3: UserCenterNav.tsx → 有自己的 navItems 定义
// Step 4: 对比 SETTINGS_GROUPS (28 条) vs UserCenterNav.navItems (26 条)
// Step 5: → 双事实源 finding
```

### L4.6 — 两级引用扫描标准化（新增，本轮实证需求）

**第一级: import 级引用扫描**
```bash
# 对每个路由 path，查 import 引用
grep -r "from.*${path_segment}" src/ --include='*.ts' --include='*.tsx' -l
```

**第二级: 字符串级引用扫描**（这一级经常被漏）
```bash
# 拼接路径（`/settings/${tab}`）
grep -rE "['\"]/${path_segment}" src/ --include='*.ts' --include='*.tsx'

# 常量表中的路径（const ROUTES = { settings: '/settings' }）
grep -rE "(path|href|to|route)\s*:\s*['\"].*${path_segment}" src/ --include='*.ts' --include='*.tsx'

# 动态构造（getRoute('settings', { tab })）
grep -rE "getRoute\(.*['\"]${path_segment}" src/ --include='*.ts' --include='*.tsx'
```

**裁决**: 两级结果取**并集**。only-in-import-level 或 only-in-string-level 都要标记——缺一级即漏报。

### L5 结构健康核查（实证有效）
- **schema drift（后端 500 头号根因）**：迁移工具说 head ≠ 物理 schema 到位（可能被 stamp）。用 ORM `Base.metadata` × `information_schema.columns` 全量 diff；修复**只允许 additive**（`ADD COLUMN IF NOT EXISTS`，按模型定义编译 DDL），修完复跑 diff=0。
- **类型检查全量**（`tsc --noEmit` / 各语言等价）：按钮点击出的 ReferenceError 往往**成簇**（一个文件缺多个 import），全量一次抓完。区分"本轮触碰文件的错误（必须 0）"与"存量债（记录不扩大范围）"。
- **mock 债务**：新增导入会让陈旧部分 mock 全文件红——用 **Proxy fallback**（未知导出→中性 div）永久免疫；`it.fails` 债务标记还清后按其契约移除。
- **审计工具自身防悬挂**：每路由按钮上限 + 所有 locator 读取包 race 超时 + dialog/filechooser/popup 三 handler 必挂。

## 七、判定与修复纪律

- **失败签名** `<类型>@<位置>:<关键消息>`，类型 ∈ `locator`/`timing`/`data`/`assert`/`env`。同一签名一轮只修一次，修完回归 同用例→相邻→全量。
- **assert 失败先判"预期是否过期"**：`git log` 找相关 commit（代号去化、懒加载重构会令旧 spec/`waitForResponse` 陈旧）——对齐既定产品决策 ≠ 放宽断言。
- **修测试 vs 修页面先分辨**：测试自身缺陷（选择器/竞态/共享状态）修测试，禁止改页面代码迁就错误断言；页面缺陷修页面。
- **诚实化处置阶梯（死 UI 优先级）**：后端契约已在→直接接线 ＞ 接不了线的 `disabled`+诚实 title（写清缺什么）＞ 演示数据界面标注「演示数据」＞ **禁止留说谎的死 CTA**。
- **前后端契约错位**：以后端实际响应为准修前端（如 `{items:[]}` 包装、字段名漂移）；后端路由自身 bug 修后端。
- **测量竞态要先排除**：批量"失败"先查是否 hasKey/共享状态竞态（实战曾 16 页"失败"实为 hasKey 竞态），再判真缺陷。**禁止盲目重跑掩盖时序问题。**
- **终止条件**：全过=complete；同签名 3 轮无进展换策略（换定位/加等待/补 mock）；外部依赖不可恢复=blocked 写明已试手段+缺什么才能继续。

## 八、反模式（硬禁止）

- `waitForTimeout` 硬等（flaky 头号原因）→ `waitForResponse` / `expect().toBeVisible()`。
- 共用测试数据/共用全局 seed → 每测隔离自建自清理。
- 每测前跑 UI 登录 → API 登录 + `storageState`。
- 靠 retry 掩盖 flaky → 隔离、查根因、必要时 `test.fixme()` 隔离并建票。
- E2E 测业务逻辑 → 下沉单测；E2E 只留关键用户路径（≤20 个核心 journey）。
- 全量 E2E 跑每个 PR → 分层预算：PR CI ≤10min（lint+typecheck+单元+契约）/ main ≤30min（+集成+E2E 冒烟）/ nightly ≤2h（全量 E2E+审计+性能基线）。

## 九、CI 与 flaky 治理

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [["html"], ["json", { outputFile: "test-results/results.json" }]],
  use: { screenshot: "only-on-failure", trace: "retain-on-failure", video: "retain-on-failure" },
});
```
并行 sharding：`--shard=i/N` 矩阵，failure 时 `upload-artifact` 保留 `test-results/` + `playwright-report/`。
flaky 根因 checklist（按序）：竞态（换 `waitForResponse`）→ 数据冲突（隔离）→ 动画时序（禁动画或等动画）→ 网络波动（mock）→ 环境差异（CI 资源/并发/时序）。
flaky 隔离：`test("... @flaky", async () => { test.fixme(); /* 建票 */ ... });`

## 十、产物落点（幂等）

- 报告：`verify/ui-test-report.md`（结论 complete/blocked + 模式 + 用例结果表 + 失败签名 + 修复记录 + blocked 说明）。
- 证据：`verify/evidence/`（关键页截图成对保留）；按钮审计 JSONL：`/tmp`（结论摘入报告）。
- Gap 登记：`gap-analysis/GAP-REPORT-*.md`（孤儿路由、隐藏后端功能、IA 不合理等结构性 gap）。
- 沉淀测试：`tests/e2e/page_sweep.spec.ts`（全路由）、`tests/e2e/button_audit.spec.ts`（按钮级，**默认不进** CI 冒烟，nightly 或按需跑）。
> 无 `.csp/` 体系的项目用 `./verify/` + `./gap-analysis/` 即可。

## 十一、已知陷阱速查

| 陷阱 | 症状 | 解法 |
|---|---|---|
| 后端未起/起错端口 | globalSetup `session.user` null、login 凭证错 | 按健康检查路径+响应体确认本项目后端，勿凭端口号认 |
| 限流未关 | 全量跑 429、单跑通过 | 关限流开关（如 `RATE_LIMIT_ENABLED=false`） |
| 执行 shell 断连 | background 进程被连带杀掉 | `start_new_session=True` 派生 + /tmp 文件轮询，禁长 sleep |
| 一个页面编译错误 | Turbopack 毒化，其后所有路由 blank | 先修 Module not found，再重跑 |
| `useSearchParams` 无 Suspense | shell 渲染但主体空 | 拆 inner 组件包 `<Suspense>` |
| redirect stub 互相指 | 重定向环/空渲染 | canonical 路径渲染真 UI，deprecated 路径单向 redirect 且透传 query |
| 导航配置死文件 | 页面存在但 UI 无入口 | 审计 nav 配置 import 关系；配置里禁止留不存在的路由 |
| 迁移 stamp ≠ 已执行 | 多页面按钮一点就 500（UndefinedColumn） | ORM × information_schema diff，additive-only 修复 |
| 共享组件包按钮 | 所有弹窗 hydration error（DialogClose 包 Button） | clone-element（asChild 语义），一处修全局生效 |
| 组件文件从未过类型检查 | 点击特定面板才 ReferenceError（成簇缺 import） | `tsc --noEmit` 全量一次抓完 |
| `.first()`/`.last()` 命中隐藏元素 | 移动端菜单 button 被误选 | max-over-mains + 独立 probe |

## 十二、执行约束

- **真实执行**：用例必须真跑（`ran: <cmd> exit 0`），禁止 not-run/grep 替代、禁止 skip 掩盖、禁止靠放宽断言"修复"。
- **自决策**：模式判定、定位降级、mock 补全、最小修复范围、诚实化处置阶梯选择——自己拍板，记 DEV-LOG，不逐步问人；仅在被测 URL 缺失、预期断言有歧义需用户确认、环境确不可恢复需 blocked 时才问。
- **禁止遗留菜单与性价比延后（审计最易犯）**：收尾禁止输出"下一个性价比最高的遗留项是 X，需要时说一声"——这是非法留尾。被测范围/审计深度/未做项（如破坏性按钮专项、Firefox/WebKit/移动端/axe、平台/支付沙箱）要么本轮做完（done），要么标 `BLOCKED`（附真实外部阻塞+谁解除，如"支付沙箱未开通，需运维"），要么 `deferred`（附真实解除条件，如"沙箱下周开通后补"）。"性价比低/优先级低/按指示搁置"不是 `deferred` 理由——优先级只用于本轮排序，不跨轮延后；自决策授权下下一个该做的项自己拍板做，不抛菜单给用户。审计范围可在开跑前由用户圈定，圈定后范围内必须穷尽，范围外显式标"本次范围外"并列出，不混入"遗留"菜单。
- **幂等**：重跑读既有报告/证据/JSONL 续跑，不重做已通过用例。
- **收尾**：清理浏览器（`close`/`close-all`/`kill-all`）；输出 ui-test-report.md + GAP-REPORT；全量清空后输出总测试摘要（用例数/通过率/flaky 数/死按钮候选数/证据路径）再停。
