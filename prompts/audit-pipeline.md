对当前项目跑一次全链路审计 pipeline，串联六个审查提示词，按"体检 → 实机验证 → UI/UX 专项审查 → 产品批评 → 缺口补强 → 演进交棒"顺序推进，互不重复劳动。

## 运行时模式检测（强制前置——Step 0）

**在 Step 1 开始前必须完成以下检测，决定运行模式：**

```bash
# 检测 1: Agent 工具是否可用（检查 subagent_type 是否可被调起）
AGENT_AVAILABLE=true
SUBAGENT_FILES=$(ls ~/.claude/agents/*.md 2>/dev/null | wc -l)
if [ "$SUBAGENT_FILES" -eq 0 ]; then AGENT_AVAILABLE=false; fi

# 检测 2: 尝试轻量 Agent 调用验证（如果工具存在但配置失效，会在这里暴露）
# 用最小的 subagent_type 做一次 ping——失败即 fallback
```

**两种模式：**

| 模式 | 条件 | 执行方式 | 门控强度 |
|------|------|---------|---------|
| **标准模式** | `Agent` 工具可用 + subagent 定义存在 + 模型配置有效 | 每个 Step 的深度分析由对应 subagent 独立窗口承载，主 agent 只做路由和聚合 | 常规门控 |
| **Fallback 模式** | 上述任一不满足 | 主 agent 串行执行全部 Step，**必须遵守 Fallback 模式完整性门控**（见下文），禁止用批量文件读取替代深度分析 | **硬门控**（每步自检，不通过即 BLOCKED） |

**模式声明（进入 Step 1 前必须输出）：**

```
🔍 运行时检测: Agent 工具={可用/不可用} | Subagent 定义={N 个/缺失} | 模式={标准/Fallback}
```

> ⚠️ **Fallback 模式下，"gate 即授权"语义不变——但 gate 增加了产物完整性校验**（不是"信任串行执行就能覆盖"）。详见「Fallback 模式完整性门控」。

### Step 0.5 — 环境自检 + 会话重建（防止 E2E 依赖断裂）

> **本轮实证**: 实机验证因 docker + 后端 + storageState 三重依赖未启动而 BLOCKED（会话过期 + 依赖栈未起）。审计 pipeline 缺"环境自检 + 会话自动重建"前置步骤。

```bash
# === 环境自检 ===
# 1. 基础设施探活（DB/缓存等）
pg_isready -h localhost -p 5432 2>/dev/null && echo "DB: OK" || echo "DB: DOWN"
redis-cli ping 2>/dev/null && echo "Redis: OK" || echo "Redis: DOWN"

# 2. 后端健康检查（不要凭端口号认——同机可能有无关服务占用相近端口）
BACKEND_URL=$(grep -r 'NEXT_PUBLIC_API_URL\|VITE_API_URL\|API_BASE' .env* 2>/dev/null | head -1 | cut -d= -f2)
curl -sf "${BACKEND_URL}/health" 2>/dev/null && echo "Backend: OK" || echo "Backend: DOWN"

# 3. 前端 dev server
curl -sf "http://localhost:3000" 2>/dev/null && echo "Frontend: OK" || echo "Frontend: DOWN"
```

**一键起栈**（如果上述任一 DOWN）：
```bash
# 用 auth.setup 序列自动重建会话——不是手动登 UI 登录
docker compose up -d 2>/dev/null || echo "No docker-compose.yml"
npx playwright test tests/e2e/auth.setup.ts --project=setup 2>/dev/null
```

**会话有效性检查**：
```bash
# storageState 是否过期（Playwright 的 auth.json）
if [ -f "tests/e2e/.auth/auth.json" ]; then
  EXPIRY=$(node -e "const s=require('./tests/e2e/.auth/auth.json'); console.log(s.cookies?.[0]?.expires||'unknown')" 2>/dev/null)
  echo "Auth expiry: $EXPIRY"
else
  echo "No auth state found — run auth.setup.ts first"
fi
```

**环境自检结论（强制输出）**：
```
🔧 环境自检: DB={OK/DOWN} | Backend={OK/DOWN} | Frontend={OK/DOWN} | Auth={VALID/EXPIRED/MISSING}
   → 全绿 → 继续 Step 1
   → 有 DOWN → 尝试一键起栈（docker compose up + auth.setup）
   → 起栈失败 → 登记 BLOCKED 原因 + 解除条件，不静默跳过 E2E 相关步骤
```

### Step 0.6 — 既有 findings 基线强制回读（防止重复侦查）

> **本轮实证**: cookie-health/sre 其实早已在之前登记（GAP-001/002），但花了几轮侦查才交叉到。Pipeline 必须在当前审查 session 开始前，把所有既有 findings 汇聚成一份基线。

```bash
# 汇聚既有 findings（跨前缀、跨路径）
echo "# PRIOR-FINDINGS-BASELINE $(date +%Y-%m-%d)" > .csp/audit/PRIOR-FINDINGS-BASELINE.md
echo "" >> .csp/audit/PRIOR-FINDINGS-BASELINE.md

# 按前缀汇聚
for dir in .csp/audit .csp/ui-review .csp/critic .csp/gap-analysis .csp/review; do
  if [ -d "$dir" ]; then
    echo "## ${dir}" >> .csp/audit/PRIOR-FINDINGS-BASELINE.md
    for f in "$dir"/*FINDINGS*.json; do
      [ -f "$f" ] && echo "- $(basename $f): $(jq '.findings | length' "$f" 2>/dev/null || echo '?') findings" >> .csp/audit/PRIOR-FINDINGS-BASELINE.md
    done
  fi
done
```

**基线回读后必须输出摘要**：
```
📋 既有 findings 基线: AUDIT-F N 条 | UI-F N 条 | CRITIC-F N 条 | GAP-F N 条 | REV-F N 条
   → Step 1-5 审查时：已有登记的不重复报，只报状态变化（resolved→reopened / open→worsened）
   → 引用既有 finding 时附 ID 指针 + 来源文件路径
```

### Step 0.7 — 注册预防规范（开发期引用）

本轮 findings 的根因分类与预防规范已写入 `prompts/prevention-norms.md`（8 条编码规范 + 5 个 CI 门禁 + 7 项审查链路增强）。在进入具体 Step 前，确保理解每条 finding 都有一个对应的**机器可查的预防手段**——审查不是终点，预防才是。

### Step 0.8 — 自动化门禁快照（机器证据前置）

> 详见 `automation-validation.md`。在人工审查前，先跑确定性门禁拿机器证据，避免 agent 用 grep 凑数。

```bash
python scripts/validate_gates.py --json > .csp/audit/GATE-SNAPSHOT-{date}.json 2>&1
python scripts/validate_gates.py   # 人类可读摘要
```

**消费规则**：
- 9 个门禁（G-POS/G-NAV/G-DOC/G-FLAG/G-PLACEHOLDER/G-DUAL-NAV/G-CONTRACT/G-BUTTON/G-LAYER）映射五类根因 Pattern A-E
- `verdict == "BLOCKED"` → 这些阻断项成为 Step 1-5 的**优先审查目标**（机器已定位，人工深挖 product sense）
- 各 Step 引用门禁 metrics 作为证据（如 Step 3 ui-review 镜头 3 引用 G-NAV 的"11 sections > 7"），不重复计数
- 脚本不存在 → 标 SKIPPED + 解除条件，降级为人工检查但须声明"无机器证据"
- 门禁报告与 Step 1-5 的 findings 交叉验证：机器报 ERROR 但人工判误报 → 记入"门禁校准"反馈，调阈值或白名单

---

## 调用顺序与去重归属

### Step 1 — 工程结构体检（主跑：Nielsen 可用性 + 四层测试 + 模块化）
调用 `prompts/audit.md`，跑全量审计 Phase 0–7。
产出：`.csp/audit/MODULE-LIST` / `USABILITY-REPORT` / `AUDIT-VERDICT` / `AUDIT-FINDINGS.json`（前缀 `AUDIT-F-NN`）。
主跑项（后续步骤引用、不重跑）：
- Nielsen 10 可用性 Mode A/B + 状态覆盖（Step 4 critic 镜头 F/G、Step 3 ui-review 镜头 7/8 均引用，不重跑）
- 模块化 + 联动四层测试（裁决报告）
- 结构审计只标"疑似"孤儿路由/隐藏后端/死按钮，交 Step 2 实机确认（不据静态扫描直接报数）

### Step 2 — 实机验证（主跑：结构审计实机 + E2E 全页面）
调用 `prompts/e2e-deep-audit.md`，走 M4 深度产品审计。
入口：消费 Step 1 audit 标的"疑似孤儿/隐藏后端/死按钮"线索 → 在此实机确认后才成 finding。
主跑项（后续步骤引用、不重跑）：
- 全路由 sweep + 按钮级点击审计 + 孤儿路由 + 隐藏后端功能（Step 3 ui-review 镜头 3 IA、Step 4 critic 镜头 B、Step 5 gap Phase 4 均引用此结构 findings，不自行做按钮级/路由级实机审计）
- 结构健康核查（schema drift / tsc / mock 债务）
产出：`verify/ui-test-report.md` + `gap-analysis/GAP-REPORT` + 证据。

### Step 3 — UI/UX 设计总监审查（主跑：八镜头系统化 UI/UX 审查 → 提升点分级 → 落实到文档 → 版本迭代）
调用 `prompts/ui-review-to-iteration.md`，逐模块过八镜头 1–8 + 跨模块聚合 + 提升点到文档映射 + 版本迭代路线图。
主跑项（后续步骤引用、不重跑）：
- 镜头 1 视觉层级与布局（M1 设计原则判定）→ **本流程主跑**，Step 4 critic 镜头 C 引用
- 镜头 2 交互模式与反馈（M2 UI 模式清单）→ **本流程主跑**，Step 4 critic 镜头 D 引用
- 镜头 3 信息架构与导航（M7 限界上下文判散乱）→ 引用 Step 2 e2e 结构 findings，不自行做实机审计；跨模块散乱在 Phase 3 聚合阶段裁决
- 镜头 4 视觉与交互一致性（M5 视觉基线对比）→ **本流程主跑**：设计 Token 漂移对照表 + 跨模块一致性批次。Step 4 critic 镜头 C、Step 5 gap U3/U4 均引用此一致性 findings
- 镜头 5 用户习惯与认知（Nielsen ①⑥）→ **本流程主跑**
- 镜头 6 响应式与多端适配（M3 响应式清单）→ **本流程主跑**，Step 5 gap U7 引用
- 镜头 7 可访问性（M6 a11y 清单 + WCAG 2.1）→ **本流程主跑**，Step 5 gap F5 引用
- 镜头 8 状态覆盖与边界 → 引用 Step 1 audit Nielsen/状态覆盖结论，不重跑 Mode A/B；本流程专注 UI 层面的 loading/empty/error/success 态表现
- **落实文档**：产出版本迭代路线图 + PRD/Spec/Task UI 映射格式
去重契约（不重跑）：
- Step 1 audit 的 Nielsen/状态覆盖 → 本流程镜头 7/8 引用 `AUDIT-F`，不重跑
- Step 2 e2e 的结构 findings → 本流程镜头 3 IA 引用，不自行做实机审计
产出：`.csp/ui-review/UI-REVIEW-REPORT` + `UI-FINDINGS.json`（前缀 `UI-F-NN`）+ `CROSS-MODULE-UI` + `docs/analysis/UI-VERSION-PLAN` 版本迭代路线图。

### Step 4 — 产品总监批评性审查（主跑：重复/散乱/定位挑刺 + 跨模块聚合）
调用 `prompts/product-critic-review.md`，逐模块过七镜头 A–G + 跨模块聚合。
去重契约（不重跑）：
- 镜头 F/G 可用性违例 → 引用 Step 1 audit 的 `AUDIT-F`，不重跑 Nielsen；本流程专注重复/散乱/定位（audit 不做）
- 镜头 C/D 视觉交互一致性 → 引用 Step 3 ui-review 的 `UI-F` 一致性 findings、不重跑逐模块视觉/交互审查；只做跨模块一致性批次聚合（若 Step 3 未跑则自行跑 M）
- 镜头 B IA → 引用 Step 2 e2e 结构 findings，不自行做实机审计
产出：`.csp/critic/PRODUCT-CRITIC-REPORT` + `CRITIC-FINDINGS.json`（前缀 `CRITIC-F-NN`）+ `CROSS-MODULE`。

### Step 5 — 单模块缺口与增强深潜（主跑：逐模块功能缺口 + 领域增强目录）
调用 `prompts/feature-gap-analysis.md`，全界面自动巡检，逐模块深潜。
去重契约（不重跑）：
- U1–U7 + M1–M8 逐模块命中 → 引用 Step 3 ui-review 的 `UI-F` 按维度引用已有结论、不重跑逐模块 UI 审查；本流程专注"还缺什么功能/能加什么功能"（Step 3 不做的功能缺口部分）
- F2/F5 状态覆盖/a11y → 引用 Step 1 audit + Step 3 ui-review 结论、不重跑；本流程专注功能缺口
- Phase 4 联动检查 → 引用 Step 2 e2e 结构 findings，不自行做实机审计
产出：`.csp/gap-analysis/GAP-REPORT-{slug}` + `GAP-FINDINGS-{slug}.json`（前缀 `GAP-F-NN`）+ `CROSS-MODULE-UI`。

### Step 6 — 产品演进交棒（聚合全部 findings → roadmap）
调用 `prompts/product-audit-to-roadmap.md`，多角度审查 + 主题候选提炼 + 交棒 roadmap。
输入：聚合 Step 1–5 全部 findings（`AUDIT-F` / `UI-F` / `CRITIC-F` / `GAP-F` 前缀不同，可并存去重，按前缀路由来源）。
特别处理：Step 3 ui-review 产出的 `docs/analysis/UI-VERSION-PLAN-{date}.md` 版本迭代路线图直接作为本步骤的 UI 主题候选输入，其中的 P0/P1/P2 分级与版本批次建议供 roadmap 消费。
产出：`docs/audit/PRODUCT-AUDIT` + `docs/analysis/AUDIT-TO-ROADMAP` 交棒清单 → `csp-roadmap-update` / `roadmap-planner`（过 Phase 2.5 集成必要性审视）。

## 全局纪律
- **证据先于断言**：每条 finding 带 `file:line` / 截图 / 路由 / 命令输出 / Token 漂移对比；"应该/大概/看着"即停。
- **去重即契约**：上述每处主跑归属不可越界重跑；引用上游结论时附 finding ID 指针（`AUDIT-F-NN` / `UI-F-NN` / `CRITIC-F-NN` / `GAP-F-NN`）。
- **禁止降级审计**：工具/浏览器不可用 → 报 BLOCKED + 停手 + 重试，不产出降级报告；预算耗尽标"未验证-预算不足"出部分报告，剩余显式列出未审。
- **不改代码不发版**：六步均只产审计 + 建议；P0 findings 标 `快速修复=true` 直发 04 拆 fix task → 05 → 06（quick-fix 通道只跳 roadmap/01，不跳 04/05/06）。
- **留尾纪律**：findings 只能 `open` / `BLOCKED`（附阻塞+谁解除）/ `deferred`（附解除条件）；禁止"下轮再补/性价比延后/目录式凑数/纯审美占高优"。
- **gate 即授权**：顺序、范围、去重归属、严重度校准、P0–P3 分级、deferred 取舍自己拍板，记 DEV-LOG，不逐步问我；仅在审查清单真模糊且问询后仍不明 / 基线全缺且无法限定降级 / 真破坏操作（改代码删文档）/ 无法 auto-resolve 的报错 这几类才打断我。
- **Fallback 模式必须遵守完整性门控**（见下文），不因"主 agent 串行执行"而降低产物质量标准。

---

## Fallback 模式完整性门控（当 Agent 工具不可用时激活）

> 子代理不可用时，主 agent 串行执行全部 Step。**最大风险不是"没跑"，而是"跑了一半、用批量文件读取替代了深度分析、产物结构不符合预期"**。以下门控是 **硬约束**——每步完成后必须自检，任一不通过即标 `BLOCKED`、不进入下一步。

### F-0: Fallback 模式总纲

```
🚨 FALLBACK 模式激活。以下规则覆盖"全局纪律"中的对应条目：
   1. 每步必须产独立的文件（不允许合并到"总报告"）
   2. 每步必须产出独立的 findings JSON（不允许共用）
   3. finding 前缀必须与标准模式一致（不允许混编）
   4. 批量文件读取只能用于 Phase 1 现状重建，不能替代 Phase 2+ 的逐镜头/逐面深度分析
   5. 每步完成后必须先自检（下文 F-GATE 清单），自检通过才播报进度条、进入下一步
   6. 自检不通过 → 标 BLOCKED（附缺失项清单），不强行进入下一步
```

### F-GATE: 逐步完整性自检清单

每步完成后，**必须输出以下自检表**（不是可选的，是强制输出）。任一 `❌` 即 BLOCKED。

#### Step 1 自检（audit）

```markdown
### F-GATE Step 1: audit 完整性自检

| 检查项 | 判定 | 实际值 |
|--------|------|--------|
| `.csp/audit/AUDIT-FINDINGS.json` 存在 | ✅/❌ | |
| JSON 中 `finding_id` 前缀为 `AUDIT-F-` | ✅/❌ | |
| finding 总数 > 0（若为 0 须有"经审查无问题"的逐模块声明） | ✅/❌ | N = __ |
| Nielsen 10 每项有 Mode A/B 判定记录（命中/未命中/不适用） | ✅/❌ | |
| MODULE-LIST 覆盖预先枚举的全部模块 | ✅/❌ | N 个模块 |
| 每条 finding 含 ≥1 条 `evidence`（`file:line`/截图/命令输出） | ✅/❌ | |
| 无"应该/大概/看着"类无依据断言 | ✅/❌ | |

**自检结论**: PASS / BLOCKED（原因: ___）
```

#### Step 2 自检（e2e-deep-audit）

```markdown
### F-GATE Step 2: e2e 完整性自检

| 检查项 | 判定 | 实际值 |
|--------|------|--------|
| `verify/ui-test-report.md` 存在 | ✅/❌ | |
| L2 全路由 sweep 覆盖 ___ 个路由（从路由表枚举） | ✅/❌ | ___ 个 |
| L3 按钮级审计 JSONL 非空（若浏览器不可用 → BLOCKED 而非跳过） | ✅/❌ | ___ 条 |
| L4 孤儿路由/隐藏后端载入 finding 列表（引用 Step 1 "疑似" + 本步确认结论） | ✅/❌ | ___ 个 |
| 死按钮候选列表（有 handler 核验结论，非仅 `NONE` 猜测） | ✅/❌ | ___ 个 |
| L5 schema drift / tsc / mock 债务有执行记录（ran: 命令 exit 码） | ✅/❌ | |
| 每条 finding 含执行证据（snapshot/network/console/screenshot ≥1 类） | ✅/❌ | |

**自检结论**: PASS / BLOCKED（原因: ___）
```

#### Step 3 自检（ui-review）

```markdown
### F-GATE Step 3: ui-review 完整性自检

| 检查项 | 判定 | 实际值 |
|--------|------|--------|
| `.csp/ui-review/UI-FINDINGS.json` 存在 | ✅/❌ | |
| JSON 中 `finding_id` 前缀为 `UI-F-` | ✅/❌ | |
| finding 总数 > 0（若某镜头无发现须有"本镜头经逐项对照无 issue"声明） | ✅/❌ | N = __ |
| 8 个镜头每镜头有独立成节的审查记录（不是合并描述） | ✅/❌ | ___/8 |
| 镜头 4 含 Token 漂移对照表（设计值 vs 实际值 vs file:line） | ✅/❌ | ___ 条漂移 |
| `.csp/ui-review/CROSS-MODULE-UI-{date}.md` 存在且含： | ✅/❌ | |
|   - 跨模块一致性批次列表（≥1 批） | ✅/❌ | ___ 批 |
|   - 信息架构重组建议（按 M7 限界上下文法） | ✅/❌ | |
| `docs/analysis/UI-VERSION-PLAN-{date}.md` 存在且含： | ✅/❌ | |
|   - P0/P1/P2/P3 四级分组 | ✅/❌ | |
|   - 版本批次对应表 | ✅/❌ | |
| 每条 finding 含 `user_impact` 字段（对用户的具体伤害论证） | ✅/❌ | |
| UI 改动建议附原型/截图对照（M4），无悬空提建议 | ✅/❌ | |
| 引用 Step 1 `AUDIT-F` + Step 2 e2e findings 处有明确指针（ID+文件路径） | ✅/❌ | |

**自检结论**: PASS / BLOCKED（原因: ___）
```

#### Step 4 自检（critic）

```markdown
### F-GATE Step 4: critic 完整性自检

| 检查项 | 判定 | 实际值 |
|--------|------|--------|
| `.csp/critic/CRITIC-FINDINGS.json` 存在 | ✅/❌ | |
| JSON 中 `finding_id` 前缀为 `CRITIC-F-` | ✅/❌ | |
| 七镜头 A-G 每镜头有独立 findings（若无发现须声明） | ✅/❌ | ___/7 |
| 镜头 A 重复与冗余分 A1/A2/A3/A4 四类独立审查 | ✅/❌ | |
| finding 含 `产品sense_rationale` 字段（不是"看着不对"） | ✅/❌ | |
| 引用 Step 3 `UI-F` 一致性 findings 处有明确指针 | ✅/❌ | |
| 引用 Step 1 `AUDIT-F` Nielsen findings 处有明确指针 | ✅/❌ | |
| `.csp/critic/CROSS-MODULE-{date}.md` 存在（跨模块聚合裁决） | ✅/❌ | |
| P0 findings 标 `快速修复=true` | ✅/❌ | |

**自检结论**: PASS / BLOCKED（原因: ___）
```

#### Step 5 自检（gap）

```markdown
### F-GATE Step 5: gap 完整性自检

| 检查项 | 判定 | 实际值 |
|--------|------|--------|
| 每个枚举模块有独立 `GAP-REPORT-{slug}.md` | ✅/❌ | ___/___ 模块 |
| 每个模块有对应 `GAP-FINDINGS-{slug}.json`（前缀 `GAP-F-`） | ✅/❌ | |
| F1–F12 通用面每面有判定记录（"命中 N 条"或"本面无缺口"） | ✅/❌ | ___/12 |
| U1–U7 维度：引用 Step 3 `UI-F` 已有结论，专注功能缺口 | ✅/❌ | |
| 功能原型目录对照：按模块原型选命中目录，不无脑全报 | ✅/❌ | |
| `.csp/gap-analysis/CROSS-MODULE-UI-{date}.md` 存在 | ✅/❌ | |
| 每条 finding 带依据（file:line/截图/反馈/指标 ≥1 类） | ✅/❌ | |

**自检结论**: PASS / BLOCKED（原因: ___）
```

#### Step 6 自检（product-audit）

```markdown
### F-GATE Step 6: product-audit 完整性自检

| 检查项 | 判定 | 实际值 |
|--------|------|--------|
| `docs/audit/PRODUCT-AUDIT-{date}.md` 存在 | ✅/❌ | |
| 聚合了 Step 1–5 的全部前缀（AUDIT-F/UI-F/CRITIC-F/GAP-F） | ✅/❌ | 4/4 |
| 角度 A-D 必选四角度有独立审查（增强/功能迭代/模块重组/界面规划） | ✅/❌ | 4/4 |
| `docs/analysis/AUDIT-TO-ROADMAP-{date}.md` 存在 | ✅/❌ | |
| 主题候选以模块为单位聚合（遵循 roadmap 攒批原则） | ✅/❌ | ___ 个主题 |
| 每条主题候选含 SemVer 性质标注（minor/major/patch） | ✅/❌ | |
| 跨步骤去重声明：列出合并/引用的 finding ID 对应 | ✅/❌ | |

**自检结论**: PASS / BLOCKED（原因: ___）
```

### F-BLOCKED 处理规则

```
自检 BLOCKED 时：
  1. 停止继续下一步
  2. 输出 BLOCKED 原因 + 缺失项的具体清单
  3. 不产出"合并总报告"作为替代——那比不报告更危险（制造"已完成"假象）
  4. BLOCKED 解除条件：补全缺失项后重新自检 PASS
  5. 同一步骤最多 BLOCKED 2 次；第 3 次仍不通过 → 标 PERMANENTLY_BLOCKED
     并列出"当前模式下无法完成的部分 vs 仍需完成的部分"
     用户决定：修复环境后重试 / 接受部分报告（显式 scope down）

PERMANENTLY_BLOCKED 不是降级审计——是诚实声明"在当前约束下，以下维度无法获得可信结论"。
```

### F-PROGRESS: Fallback 模式进度播报

每步完成后必须播报（标准进度条 + 自检结论）：

```
📊 pipeline [Step i/6 {slug}] [模式:FALLBACK] [就绪✓][重建✓][深度分析✓][自检:PASS✓][交棒✓]
```

若自检 BLOCKED：

```
⛔ pipeline [Step i/6 {slug}] [模式:FALLBACK] [自检:BLOCKED] — 缺失: {清单}
   → 不进入 Step i+1。BLOCKED 原因: ___
```

### F-ANTI: Fallback 模式反模式清单

| 反模式 | 症状 | 为什么危险 | 正确做法 |
|--------|------|-----------|---------|
| **批量收集替代深度分析** | 大量 `grep`/`glob` 后输出"经审查发现以下问题"类泛泛总结 | 看起来做了很多工作，实际上跳过了所有 lens 维度的结构化判定 | 每 lens 必须逐条对照检查项列表，每条 finding 带 product rationale |
| **合并产物** | 6 个 Step 产出 1 个合并 report | 下游无法按前缀路由，去重契约崩溃 | 每步必须产独立文件（路径+前缀与标准模式一致） |
| **跳过自检** | 不输出 F-GATE 自检表 | 无法验证产物是否完整，质量退化成"感觉跑完了" | F-GATE 自检表是强制输出，不是建议 |
| **空 findings 伪装完整** | JSON 文件存在但 findings 数组为空，没有"经审查无问题"的逐模块声明 | 无法区分"真的没问题"和"没做审查" | finding 数=0 时必须有逐模块/逐镜头声明 |
| **Token 漂移对照表为空壳** | 写了"Token 漂移对照表"标题但无实际 file:line 对比 | 镜头 4 的主跑项实质未执行 | 必须含 ≥1 条具体漂移记录（设计值 vs 实际值 vs 位置），或声明"经逐页对比，无不一致" |
| **跨模块聚合节为泛泛之谈** | CROSS-MODULE 文件只写"发现了一些不一致"无具体列表 | 聚合裁决阶段的核心产出全部缺失 | 必须含具体批次列表（每批：涉及的模块、具体的 finding IDs、裁决结论） |
| **忽略"自检不通过 → BLOCKED"** | 自检有 ❌ 但结论写了 PASS | 最危险的模式——制造"已完成"假象 | 任一 ❌ 即 BLOCKED，不允许自检结论与检查项矛盾 |

---

## 进度播报（标准模式）
每完成一步按进度条播报：
`📊 pipeline [Step i/6 {slug}] [就绪✓][主跑✓][去重引用✓][findings✓][交棒✓]`
六步全跑完，输出总 findings 清单（按 `AUDIT-F` / `UI-F` / `CRITIC-F` / `GAP-F` + 跨模块重组批次分组，附产物路径），再停。

> Fallback 模式进度播报格式见上文 F-PROGRESS。

## 并行优化
**Wave 1（可并行）**：Step 1 audit（静态扫）+ Step 2 e2e（实机跑）互不阻塞，可并行起跑。

**Wave 2（barrier 后跑）**：Step 1 + Step 2 均完成后，Step 3 ui-review 启动（需消费 Step 1 的 Nielsen/状态覆盖结论 + Step 2 的结构 findings）。

**Wave 3（barrier 后跑）**：Step 3 ui-review 完成后，Step 4 critic 与 Step 5 gap 可并行起跑——二者均消费 Step 1/2/3 的不同维度结论，各自专注不同领域（critic 做产品定位批评、gap 做功能缺口补强），互不阻塞。

**Wave 4（barrier 后跑）**：Step 4 + Step 5 均完成后，Step 6 product-audit 聚合全部 findings 交棒 roadmap。

> ⚠️ **Fallback 模式下不适用并行优化**——主 agent 串行执行，必须严格按 Step 顺序推进并逐步自检。Wave 优化仅供标准模式使用。

## Finding 前缀路由速查

| 来源 (Step) | 前缀 | 焦点 | 产物路径 |
|------------|------|------|---------|
| Step 1 audit | `AUDIT-F-NN` | 工程结构/可用性/Nielsen | `.csp/audit/` |
| Step 2 e2e | — | 实机验证/死按钮/结构健康 | `verify/` |
| Step 3 ui-review | `UI-F-NN` | UI/UX 专项（8 镜头） | `.csp/ui-review/` |
| Step 4 critic | `CRITIC-F-NN` | 产品批评（重复/散乱/定位） | `.csp/critic/` |
| Step 5 gap | `GAP-F-NN` | 功能缺口与增强 | `.csp/gap-analysis/` |
| Step 6 product-audit | `AUDIT-F-NN`（同族） | 产品演进交棒 | `docs/audit/` |

## 自动发现
未指定范围时：从路由表 + `.csp/product-spec/` 模块清单 + `.csp/code-spec/entry-points.jsonl` + `docs/FEATURES.md` 枚举全部页面/功能模块，按"核心路径优先 + P0 高危模块优先 + 高频反馈模块优先"排序，写入各自 `SCAN-LIST` 后即开始，不等我确认。

---

按要求执行任务