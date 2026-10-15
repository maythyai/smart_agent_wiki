# 开发期 UI 预防规范（编码约定 + CI 门禁）

> 从历次 UI/UX 审查 findings 中提取的根因，转化为开发期可机器检查的约束。
> 每条规范对应一类已知的"必然性错误"——不是 AI 偶尔写错，而是缺少约束的必然结果。
> 本文件供 `AGENTS.md` 检查清单引用，CI 门禁脚本化。

## 一、编码规范（8 条，写入 AGENTS.md）

### N1: 路由必须注册

**规则**: 新增页面必须出现在导航配置、豁免表（`EXEMPT_ROUTES`）或"故意隐藏清单"（`HIDDEN_ROUTES`）里，否则 CI 报孤儿路由。

**拦截问题**: 页面存在但无导航入口 → 用户不可达、无人维护。

**违反本轮**: UI-F-05（4 个孤儿路由）

```typescript
// ❌ 创建了页面文件但没有在任何地方注册
// src/app/scheduling/page.tsx — 没有导航入口

// ✅ 三种合法注册方式之一
// 方式 1: 在导航配置中注册
navGroups.push({ path: '/scheduling', label: '排期' })

// 方式 2: 在豁免表中声明（如 /login 不需要导航入口）
export const EXEMPT_ROUTES = ['/login', '/scheduling']

// 方式 3: 在"故意隐藏"清单中声明并配理由
export const HIDDEN_ROUTES = [
  { path: '/scheduling', reason: '已合并到 /calendar?tab=best-time，301 转发中' }
]
```

**CI 门禁**: `route_registry.py`（含动态段解析）→ Gate G1

---

### N2: 导航只放目的地

**规则**: 导航条目禁止指向 301 转发路径。导航中每条 path 必须是最终渲染页面（`page.tsx`/等效入口），不能是转发中间件。

**拦截问题**: 用户点击导航 → 触发 301 → URL 变化 → 体验断层。

**违反本轮**: `/settings/analytics`（导航→301→真实页面）、`/settings/profile`（同上）

```typescript
// ❌ 导航指向 301 转发路径
{ path: '/settings/analytics', label: '分析' }  // /settings/analytics → 301 → /settings/analytics/overview

// ✅ 导航指向最终目的地
{ path: '/settings/analytics/overview', label: '分析' }
```

**CI 门禁**: `wording_check.mjs`（导航条目逐一解析中间件链）→ Gate G2

---

### N3: 同域导航单一事实源

**规则**: 每个导航域只允许一个 navGroups/navItems 导出，其余消费方全部从该单一源派生（import 或 computed）。禁止同域两份独立清单。

**拦截问题**: settings 渲染源 28 条 vs AI 适配器影子源 26 条 → 同域两份清单必然漂移。

**违反本轮**: UI-F-02（settings 双事实源导致条目不同步）

```typescript
// ❌ 两份独立清单
// src/config/settings-nav.ts — 28 条（渲染用）
// src/ai/settings-adapter.ts — 26 条（AI 适配器用，手动维护）

// ✅ 单一源 + 派生
// src/config/settings-nav.ts — 唯一定义 (28 条)
// src/ai/settings-adapter.ts — import 并 filter
import { SETTINGS_GROUPS } from '@/config/settings-nav'
const aiGroups = SETTINGS_GROUPS.filter(g => g.aiVisible !== false)
```

**CI 门禁**: CI 脚本检查同域是否存在两份独立 navGroups 导出 → Gate G2

---

### N4: 按钮文案引用动作词典

**规则**: 发布/保存/导出/删除/新建等核心动作的按钮文案集中在一个常量文件（动作词典），所有按钮只能引用词典键，禁止手写字符串。

**拦截问题**: 同一语义（如"发布"）在不同页面出现 4 种措辞（"确认发布"/"立即发布"/"发布内容"/"Publish"），用户认知混乱。

**违反本轮**: UI-F-01（发布动作 4 种措辞）、UI-F-11（导出动作 3 种措辞）

```typescript
// ✅ 动作词典
// src/i18n/actions.ts
export const ACTION_LABELS = {
  publish: '发布',
  save: '保存',
  export: '导出',
  delete: '删除',
  create: '新建',
  cancel: '取消',
} as const

// 所有按钮只能引用
<Button>{ACTION_LABELS.publish}</Button>

// ❌ 手写字符串
<Button>确认发布</Button>
<Button>立即发布</Button>
```

**CI 门禁**: `wording_check.mjs`（diff 级：新增字符串与词典对照，超出词典报 WARNING）→ Gate G2

---

### N5: 占位规范

**规则**: 未上线功能一律用 `disabled 按钮 + title/说明文案` 占位，禁止 toast 型占位（点击后弹出"即将上线"）。项目中"即将上线"类占位出现次数设 CI 上限（不增长门禁），新增需审批。

**拦截问题**: 15 处占位用了 3 种不同模式（toast/disabled/文案），用户点击后反馈不一致；credits 同一页出现两种占位模式。

**违反本轮**: UI-F-06（占位模式漂移）、UI-F-18（toast 型占位，用户点击无反馈可预期）

```typescript
// ✅ 统一占位模式
<Button disabled title="该功能正在开发中，预计 v2.1 上线">
  即将上线
</Button>

// ❌ toast 型占位（点击后才告知不可用）
<Button onClick={() => toast('即将上线，敬请期待')}>
  智能推荐
</Button>

// ❌ 仅文案占位（无可供性，看起来像已上线但不可交互）
<div className="feature-card">
  <h3>智能推荐</h3>
  <span>即将上线</span>  {/* 无 disabled 态 */}
</div>
```

**CI 门禁**: `placeholder_gate.mjs`（计数占位出现次数，diff 新增占位 ≥ 既有时报 WARNING）→ Gate G3

---

### N6: hex/token 纪律

**规则**: 品牌色/主题色走设计系统 token（`PLATFORM_COLORS` 或等效常量），禁止页面/组件内硬编码 hex 字面量。

**拦截问题**: 同一平台色在 27 处出现了略微不同的 hex 值（`#1a8cff` vs `#1890ff` vs `#1b9cfc`），设计系统 token 形同虚设。

**违反本轮**: UI-F-07（27 处 hex 硬编码漂移）

```typescript
// ❌ 硬编码 hex
<div style={{ color: '#1a8cff' }}>  {/* 应该是 #1890ff */}
<Button style={{ background: '#1b9cfc' }}>  {/* 同上 */}

// ✅ 引用 token
import { COLORS } from '@/design-tokens'
<div style={{ color: COLORS.primary }}>
<Button style={{ background: COLORS.platform.linkedin }}>
```

**CI 门禁**: `hex_lint.mjs`（diff 级：新增 hex 色值与 token 表对照，不在表中的报 ERROR）→ Gate G5

---

### N7: deprecation 带 TTL

**规则**: 旧路径的 301 转发表中，每条带 `remove_by_version` 字段（载体删除截止版本）。到期后 CI 报"转发存在但载体未删"，强制回收。

**拦截问题**: `/scheduling` 和 `/calendar?tab=best-time` 两入口并存、`/editor` 和 `/studio/editor` 并存；301 解决了用户转发，但没有解决旧入口/旧组件的清理。

**违反本轮**: UI-F-08（新旧入口并存）、UI-F-14（GAP-005 同模式：4 个孤儿路由 = 入口删了但载体还在）

```typescript
// ✅ deprecation 带 TTL
// src/config/redirects.ts
export const REDIRECTS = [
  {
    source: '/scheduling',
    destination: '/calendar?tab=best-time',
    deprecated_since: 'v1.8.0',
    remove_by_version: 'v1.10.0',  // ← TTL
    reason: '排期功能合并到日历最佳时间视图',
  },
  {
    source: '/editor',
    destination: '/studio/editor',
    deprecated_since: 'v1.6.0',
    remove_by_version: 'v1.8.0',    // ← 已过期，CI 报错
    reason: '编辑器统一迁移到 Studio',
  }
]
```

**CI 门禁**: `deprecation_ttl.py`（检查 `remove_by_version <= current_version` → 报 ERROR）→ Gate G4

---

### N8: 立项查重

**规则**: 新功能/新路由开工前，用域词典（同义动词 + 名词组合）在既有 features 清单和路由表中做语义查重。命中重叠 → 先讨论合并/区分，再开工。

**拦截问题**: "一鱼多吃" vs "一稿多发"、选题+爆款 vs 选题发现谱系重叠——功能命名和概念在立项时不做交叉查重，导致模块职责重叠、用户认知混乱。

**违反本轮**: CRITIC-F 中发现的功能谱系重叠（镜头 A1 功能重复 + 镜头 E 定位错位）

```bash
# 查重命令（立项时跑）
grep -riE 'repurpose|multi.?post|cross.?platform|one.?fish|一鱼|多发|多吃|一稿' \
  docs/FEATURES.md .csp/product-spec/ --include='*.md'
```

**工具**: 维护一份 `DOMAIN-THESAURUS.md`（域词典）：动词（发布/分发/复用/同步）→ 名词（内容/素材/帖子/文章）→ 既有 feature 列表对照表。

---

## 二、CI 门禁（5 个，脚本化）

| Gate | 脚本 | 拦截问题 | 对应规范 | 触发时机 | 阻断级别 |
|------|------|---------|---------|---------|---------|
| **G1** | `route_registry.py` | 孤儿路由、未注册页面、动态段未解析 | N1 | PR + pre-push | ERROR |
| **G2** | `wording_check.mjs` | 同动作多措辞、导航指向 301、同域两份导航源 | N2/N3/N4 | PR | WARNING（累计 >3 升 ERROR） |
| **G3** | `placeholder_gate.mjs` | 占位数量增长、toast 型占位 | N5 | PR | WARNING（新增 toast 占位 = ERROR） |
| **G4** | `deprecation_ttl.py` | 301 转发到期但载体未清理 | N7 | 每次 CI + 版本发布前 | ERROR |
| **G5** | `hex_lint.mjs` | 新代码引入不在 token 表中的 hex 色值 | N6 | PR（diff 级） | ERROR |

### 门禁执行策略

```
PR 阶段: G2, G3, G5（检查 diff，轻量快速，≤30s 完成）
├─ ERROR 阻断合并
└─ WARNING 可合并但累计计数（同类型 WARNING ≥3 自动升 ERROR）

Push 阶段: G1, G4（全量检查，可较重，≤2min 完成）
└─ ERROR 阻断 push

发布前: G1-G5 全量复跑
└─ 任一 ERROR 阻断发布
```

### 门禁脚本接口约定

所有门禁脚本统一接口：

```bash
# 入口
<gate_script> --mode <pr|push|release> [--diff <git-diff-range>]

# 退出码
# 0: PASS
# 1: ERROR（阻断）
# 2: WARNING（记录但不阻断，累计 ≥3 升 ERROR）
# 3: SKIPPED（门禁条件不适用，如无 hex 变更时 G5 返回 SKIPPED）

# 输出（stdout JSON）
{
  "gate": "G1",
  "mode": "push",
  "result": "PASS|ERROR|WARNING|SKIPPED",
  "findings": [
    {"severity": "ERROR", "file": "src/app/secret/page.tsx", "line": 1, "message": "孤儿路由：未在导航/豁免/隐藏清单中注册"}
  ],
  "stats": {"total": 42, "errors": 1, "warnings": 0}
}
```

---

## 三、审查链路增强（基于本轮实证）

> 以下不是编码规范，而是审查 pipeline 本身的增强要求。见各 prompt 文件对应节的更新。

| # | 增强项 | 更新到 | 本轮实证 |
|---|--------|--------|---------|
| R1 | 动态路由必须解析配置表，不能跳过 `[slug]` 段 | `e2e-deep-audit.md` L2 | `[dashboard]/page.tsx:17-26` 枚举了 11 个子模块 |
| R2 | 先判渲染源再判数据源——实际渲染的是 JSX 中的组件引用，不是数据常量 | `e2e-deep-audit.md` L4 | `SETTINGS_GROUPS` ≠ 实际渲染的 `UserCenterNav` |
| R3 | import 级 + 字符串级两级引用扫描标准化 | `e2e-deep-audit.md` L4 | 字符串拼接路径/常量表引用需要额外扫描 |
| R4 | 按钮审查先做动作文案聚类（"发布族/导出族/删除族"），再逐页审查 | `ui-review-to-iteration.md` 镜头 2 | 8 处发布入口分散在不同文件，按页看不出"发布族" |
| R5 | Step 0 强制环境自检 + 会话自动重建 | `audit-pipeline.md` Step 0 | docker + 后端 + storageState 三重依赖导致 BLOCKED |
| R6 | Step 0 强制既有 findings 基线回读 | `audit-pipeline.md` Step 0 | cookie-health/sre 已登记但未被发现 |
| R7 | 每步产物带"检测盲区声明" | 全部 prompt 文件 | UNSCREENED 分层登记未验项 |

## 三.5、自动化门禁映射（G1-G5 编码门禁 ↔ G-* 治理门禁）

> 本文件的 G1-G5 是**编码级门禁**（PR/push 拦截具体代码问题）；`automation-validation.md` 的 G-POS/G-NAV/G-DOC/G-FLAG/G-PLACEHOLDER/G-DUAL-NAV 是**治理级门禁**（收敛闸门拦截架构/定位问题）。两层互补，统一由 `scripts/validate_gates.py` 编排治理级，编码级由各 CI 脚本独立跑。

| 编码门禁（本文件） | 对应治理门禁 | 关系 |
|------------------|------------|------|
| G1 route_registry.py | G-NAV / G-DUAL-NAV | G1 查单条孤儿路由；G-NAV 查导航总量预算 |
| G2 wording_check.mjs | G-POS | G2 查文案一致性；G-POS 查定位漂移（to-B 关键词） |
| G3 placeholder_gate.mjs | G-PLACEHOLDER | 同一门禁，G3 是 CI 脚本名，G-PLACEHOLDER 是 validate_gates 委托封装 |
| G4 deprecation_ttl.py | —（治理级未覆盖） | deprecation TTL 仍由 G4 独立跑 |
| G5 hex_lint.mjs | —（治理级未覆盖） | hex/token 纪律仍由 G5 独立跑（diff 级） |

**统一编排**：`python scripts/validate_gates.py` 跑全部治理级门禁 + 委托 G-CONTRACT/G-BUTTON/G-LAYER 到既有脚本。编码级 G1/G2/G4/G5 在 PR CI 独立跑（见 §二门禁执行策略）。参考实现见 auto_content `scripts/validate_gates.py`，移植指引见 `automation-validation.md` §六。

---

## 四、根因 → 规范映射速查

| 根因类别 | 违反本轮 finding | 预防规范（编码） | 预防规范（CI 门禁） | 审查增强 |
|---------|-----------------|---------------|-------------------|---------|
| A 历史增量叠加 | 8 入口三层叠加 | N1, N2, N7 | G1, G4 | — |
| B 双事实源 | settings 28 vs 26 | N3 | G2 | R2 |
| C 删入口不删实现 | 4 个孤儿 + 新旧入口并存 | N7 | G1, G4 | R2, R3 |
| D 占位/反馈模式漂移 | 15 处 3 种占位模式 | N5 | G3 | R4 |
| E 生成代码硬编码惯性 | 27 处 hex + 4 种措辞 | N4, N6 | G2, G5 | R4 |
| F 开发视角泄漏 | 谱系重叠 | N8 | — | — |