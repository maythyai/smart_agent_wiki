# 自动化验证层（Automation Validation）——提示词 ↔ 脚本契约

> 本文档定义**机器可执行的治理门禁**与提示词流程的绑定关系。每个门禁对应一个脚本命令、一个退出码语义、一个 JSON 输出 schema、以及消费它的提示词 Phase。
>
> **核心原则**：提示词负责"判断与裁决"（需要 product sense 的部分），脚本负责"确定性检测"（可机器判定的部分）。两者通过 `GATE-REPORT-{date}.json` 交接——脚本产出结构化证据，提示词消费证据做裁决。
>
> **通用实现**：`prompts/scripts/validate_gates.py`（配置驱动，项目无关）+ `prompts/scripts/gates.config.example.json`（配置示例）。各项目只维护自己的 `.csp/gates.config.json`，脚本随 prompts 同步。另有 `findings_closure_check.py`（findings 闭合真实性闸门）+ `version_integrity_check.py`（版本完整性闸门）两个通用脚本，见 `develop_pipeline.md` 的发布门禁。

## 一、为什么需要自动化验证层

纯提示词审查的三个固有缺陷：

| 缺陷 | 后果 | 自动化层如何解决 |
|------|------|----------------|
| **判断不可复现** | 同一项目两次审查结论不同 | 脚本对同一输入永远产出同一结果 |
| **证据靠人工搜集** | agent 用 grep 凑数，遗漏系统性问题 | 脚本全量扫描，输出精确计数 |
| **门禁无强制力** | "建议收敛导航"被忽略 | 脚本 exit 1 → CI/流水线硬阻断 |

**分工边界**：
- **脚本做**：计数、存在性、关键词匹配、阈值比较、调用既有 lint/audit 工具
- **提示词做**：定位对齐裁决、支柱归属判断、功能取舍、IA 方向、product sense rationale

## 二、门禁清单（9 个，映射五类根因 Pattern）

| 门禁 | 检测内容 | 根因 Pattern | 脚本/命令 | 阻断级别 | 消费方 |
|------|---------|------------|----------|---------|--------|
| **G-POS** | 定位漂移（to-B 关键词 vs AGENTS.md single-operator） | A | `validate_gates.py --gate G-POS` | 🔴 阻断 | convergence D5 |
| **G-NAV** | 导航预算（顶级 section 数 vs budget=7） | B | `validate_gates.py --gate G-NAV` | 🔴 阻断 | convergence D3 |
| **G-DOC** | DOC-STATUS 新鲜度（last_audit vs today） | E | `validate_gates.py --gate G-DOC` | 🔴 阻断(>60d) | convergence D6.3 |
| **G-FLAG** | Feature Flag 卫生（default-off 死代码 + 定位冲突） | D/A | `validate_gates.py --gate G-FLAG` | 🔴 阻断 | convergence D6.2 |
| **G-PLACEHOLDER** | 占位增长（代码计数 vs registry baseline，只降不增） | C/D | `validate_gates.py --gate G-PLACEHOLDER` | 🔴 阻断 | convergence D6 / 06 release |
| **G-DUAL-NAV** | 多导航源（单一事实源违反） | B | `validate_gates.py --gate G-DUAL-NAV` | 🟡 警告 | convergence D3 |
| **G-CONTRACT** | OpenAPI 契约 + 前端孤儿调用 | C | `scan_contract.py --strict` | 🔴 阻断 | audit Step1 / e2e L4 |
| **G-BUTTON** | 按钮 a11y/onClick 缺失 | C | `button_audit.py` | 🟡 警告 | ui-review 镜头7 / e2e L3 |
| **G-LAYER** | 分层违规（Router/Service 绕过 Repository） | D | `lint_layer.py --strict` | 🔴 阻断 | audit Step1 |

## 三、统一编排命令

> **通用配置驱动版**（推荐）：脚本本体项目无关，全部路径/关键词/阈值/委托脚本来自配置文件。
> 脚本：`prompts/scripts/validate_gates.py`；配置示例：`prompts/scripts/gates.config.example.json`。

```bash
# 0. 首次：生成项目配置（复制示例后按实际修改）
python3 prompts/scripts/validate_gates.py --write-template .csp/gates.config.json
#    → 编辑 .csp/gates.config.json：填 paths/thresholds/drift_keywords/delegated_gates

# 1. 全量门禁（收敛闸门 / 审计 pipeline Step 0 调用）
python3 prompts/scripts/validate_gates.py --config .csp/gates.config.json

# 2. 仅 JSON（供提示词程序化消费）
python3 prompts/scripts/validate_gates.py --config .csp/gates.config.json --json

# 3. 单门禁（调试 / 增量）
python3 prompts/scripts/validate_gates.py --config .csp/gates.config.json --gate G-NAV

# 4. 严格模式（任一 ERROR 即 exit 1，用于 CI）
python3 prompts/scripts/validate_gates.py --config .csp/gates.config.json --strict

# 5. 指定仓库根（脚本可在任意位置调用）
python3 prompts/scripts/validate_gates.py --config .csp/gates.config.json --root /path/to/repo
```

**退出码语义**：
- `0` = 全部 PASS 或仅 WARNING（可继续，但 WARNING 须登记）
- `1` = 至少一个**阻断门禁** ERROR（收敛闸门不通过 / CI 失败）
- `2` = 验证器自身失败（配置缺失/解析错误——不是被审项目的问题）

**报告落点**：`{report_dir}/GATE-REPORT-{date}.json`（report_dir 来自 config，默认 `.csp/convergence`）

### 配置文件 schema（`.csp/gates.config.json`）

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_name` | str | 项目名（报告标识） |
| `trust_model` | str | `single-operator`/`team`/`enterprise`/`multi-tenant`——G-POS/G-FLAG 据此判漂移 |
| `paths.*` | str | 各权威文件相对路径；**留空 = 该门禁 SKIPPED**（登记解除条件，不报错） |
| `thresholds.nav_budget` | int | 顶级导航预算（默认 7） |
| `thresholds.doc_stale_warn_days` | int | 文档 WARNING 阈值（默认 30） |
| `thresholds.doc_stale_error_days` | int | 文档 ERROR 阈值（默认 60） |
| `thresholds.placeholder_baseline` | int\|null | 占位 baseline；null = 从 registry 解析"N 处占位" |
| `drift_keywords` | list | 与 trust_model 冲突的关键词（single-operator 填 to-B 词） |
| `severe_drift_keywords` | list | 命中 nav 即 ERROR 的子集 |
| `flag_conflict_pattern` | str | flag 名冲突正则（仅 single-operator 生效） |
| `delegated_gates.*` | obj | `{script, args}`——委托项目既有脚本；script 留空 = SKIPPED |
| `enabled_gates` | list | 启用的门禁（可按项目裁剪，如无前端去掉 G-NAV/G-BUTTON） |
| `blocking_gates` | list | ERROR 即 exit 1 的门禁 |
| `report_dir` | str | 报告输出目录（默认 `.csp/convergence`） |

> **反转检测**：to-B 产品（trust_model=enterprise）应把 `drift_keywords` 改为 to-C 关键词（如"个人/单人/self-hosted"），或禁用 G-POS（从 enabled_gates 移除）。门禁框架对称，关键词方向由 config 决定。

## 四、JSON 输出 Schema（提示词消费契约）

```json
{
  "validator": "validate_gates.py",
  "date": "2026-10-15",
  "summary": {"PASS": 0, "WARNING": 3, "ERROR": 6, "SKIPPED": 0},
  "blocking_errors": ["G-POS", "G-NAV", "G-FLAG", "G-PLACEHOLDER", "G-CONTRACT", "G-LAYER"],
  "verdict": "BLOCKED",
  "gates": [
    {
      "gate": "G-POS",
      "status": "ERROR",
      "pattern": "A",
      "findings": [
        {
          "gate": "G-POS",
          "severity": "ERROR",
          "pattern": "A",
          "message": "Positioning drift: nav exposes to-B features [...] but AGENTS.md declares single-operator",
          "evidence": "sidebar-config.ts keywords: [...]",
          "rule": "AGENTS.md trust model is hard constraint"
        }
      ],
      "metrics": {
        "single_operator_declared": true,
        "drift_hits": {"sidebar": [...], "roadmap": [...], "flags": [...]},
        "total_drift_keywords": 21
      }
    }
  ],
  "report_path": ".csp/convergence/GATE-REPORT-2026-10-15.json"
}
```

**提示词消费规则**：
- `verdict == "BLOCKED"` → 收敛闸门**不通过**，回 roadmap 重排（不是逐个砍功能）
- 每个 `gates[].findings[]` → 转成一条 convergence finding，附 `evidence` + `rule`
- `metrics` → 写入裁决记录的量化依据（如"导航 11 > 预算 7"）
- `blocking_errors` 非空 → 这些门禁对应的功能**禁止进入 01 PRD**

## 五、提示词 ↔ 门禁绑定矩阵

| 提示词 Phase | 调用的门禁 | 用途 |
|-------------|-----------|------|
| **convergence Phase 0**（定位基线） | G-POS | 定位漂移预警，drift>30% → roadmap 回炉 |
| **convergence D3**（IA+导航准入） | G-NAV, G-DUAL-NAV | 导航预算检查，超预算冻结新增顶级导航 |
| **convergence D5**（定位对齐与前提挑战） | G-POS, G-FLAG | 前提挑战的机器证据（冲突 flag/关键词） |
| **convergence D6.2**（Flag 卫生） | G-FLAG | default-off 死代码 + 定位冲突 flag |
| **convergence D6.3**（文档权威） | G-DOC | DOC-STATUS 过期 → 禁止新增功能 |
| **convergence Phase 3**（五类 Pattern） | 全部 | A→G-POS, B→G-NAV/G-DUAL-NAV, C→G-PLACEHOLDER/G-CONTRACT/G-BUTTON, D→G-FLAG/G-LAYER, E→G-DOC |
| **audit-pipeline Step 0.5**（环境自检后） | 全部 | 既有 findings 基线 + 门禁快照 |
| **audit Step 1** | G-CONTRACT, G-LAYER | 工程结构体检的机器证据 |
| **e2e L3/L4** | G-BUTTON, G-CONTRACT | 按钮审计 + 孤儿路由 |
| **ui-review 镜头 7** | G-BUTTON | a11y 机器证据 |
| **06 release** | G-PLACEHOLDER, G-DOC | 发布前占位/文档新鲜度门禁 |

## 六、移植到新项目（配置驱动，零脚本修改）

`prompts/scripts/validate_gates.py` 是**通用配置驱动版**——脚本本体项目无关，移植只需写配置文件，**不改脚本代码**：

1. **复制脚本**（随 prompts 同步自动到位）：`prompts/scripts/validate_gates.py` + `findings_closure_check.py` + `version_integrity_check.py`
2. **生成配置**：`python3 prompts/scripts/validate_gates.py --write-template .csp/gates.config.json`
3. **填配置**（唯一需要项目特定的部分）：
   - `paths.*` → 指向目标项目实际文件（nav_config/feature_flags/doc_status/...）；**没有的留空 = 该门禁 SKIPPED**
   - `trust_model` + `drift_keywords` → 按目标项目定位填（single-operator 填 to-B 词；to-B 产品反转为 to-C 词或禁用 G-POS）
   - `thresholds.*` → nav_budget/doc_stale/placeholder_baseline 按项目调
   - `delegated_gates.*` → 指向目标项目既有 lint/audit 脚本；没有的留空
   - `enabled_gates` → 裁剪不适用门禁（如纯后端项目去掉 G-NAV/G-BUTTON）
4. **运行**：`python3 prompts/scripts/validate_gates.py --config .csp/gates.config.json`

> **对比旧模式**：早期 auto_content 用硬编码路径的项目特定脚本（`auto_content/scripts/validate_gates.py`）。通用版改为配置驱动后，**脚本随 prompts 同步到所有项目，各项目只维护自己的 `.csp/gates.config.json`**——脚本升级一次，全项目受益。

> 提示词层（convergence/audit-pipeline/prevention-norms）**保持项目无关**——引用门禁 ID（G-POS 等）+ JSON schema + config 字段名，不引用具体脚本路径或硬编码常量。

## 七、CI 集成（可选，强化强制力）

```yaml
# .github/workflows/gates.yml（示例）
name: governance-gates
on: [pull_request, push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python scripts/validate_gates.py --strict --json > gate-report.json
      - name: Block on ERROR
        if: failure()
        run: |
          echo "::error::Governance gates BLOCKED — see gate-report.json"
          cat gate-report.json
      - uses: actions/upload-artifact@v4
        with: {name: gate-report, path: gate-report.json}
```

**分层执行**（对齐 prevention-norms.md G1-G5）：
- PR 级（快，≤30s）：G-NAV, G-DOC, G-FLAG, G-PLACEHOLDER, G-DUAL-NAV（纯文本解析）
- Push 级（中，≤2min）：+ G-POS, G-CONTRACT, G-LAYER（需 import 后端）
- Release 级（全量）：+ G-BUTTON + 既有 G1-G5

## 八、与既有脚本的关系（不重复造轮子）

通用 `validate_gates.py` 通过 `delegated_gates` 配置**委托**项目既有脚本，而非重写。以 auto_content 为例：

| 既有脚本 | 配置为 | 说明 |
|---------|--------|------|
| `scripts/scan_contract.py --strict` | `delegated_gates.G-CONTRACT` | OpenAPI 契约 + 前端孤儿 |
| `scripts/button_audit.py` | `delegated_gates.G-BUTTON` | 按钮 a11y/onClick |
| `scripts/lint_layer.py --strict` | `delegated_gates.G-LAYER` | 分层违规 |
| `scripts/orphan_ast_classify.py` | （未委托，e2e L4 直接用） | AST 孤儿分类 |

**新增治理门禁**（既有脚本未覆盖，由 validate_gates.py 本体实现）：G-POS, G-NAV, G-DOC, G-FLAG, G-PLACEHOLDER, G-DUAL-NAV —— 填补"功能准入/定位漂移/导航预算/文档权威"的自动化空白。

**同目录的另外两个通用闸门脚本**（独立于 validate_gates.py，发布期用）：
| 脚本 | 用途 | 调用方 |
|------|------|--------|
| `prompts/scripts/findings_closure_check.py` | findings 闭合真实性（C1-C5：fixed_in 真实/verification 证据/主题交叉/时间序/空 tag），baseline 只降不增 | 06 release 收尾双闸门之一 |
| `prompts/scripts/version_integrity_check.py` | 版本完整性（多 tag 同 commit/空 tag/六处同步/CHANGELOG） | 06 release 收尾双闸门之二 |

> 三者分工：`validate_gates.py` = 收敛/审计期治理门禁；`findings_closure_check.py` + `version_integrity_check.py` = 发布期真实性门禁。均参数化可移植（`--root`/`--config`/`--baseline`）。

## 九、约束与边界

- **脚本不裁决，只检测**：G-POS 报"nav 有变现关键词"是事实；"该不该砍变现功能"是 convergence D5 的 product sense 裁决。脚本输出是证据，不是结论。
- **阈值可调但有默认**：NAV_BUDGET=7、DOC_STALE 30/60d、PLACEHOLDER baseline 从 registry 读。改阈值须在 convergence 报告声明理由。
- **SKIPPED ≠ PASS**：文件缺失/脚本不存在 → SKIPPED，须登记解除条件，不当作通过。
- **委托脚本失败不静默**：G-CONTRACT/G-LAYER 的 exit≠0 → ERROR，不因为"是委托的"就降级。
- **报告幂等**：同日重跑覆盖 `GATE-REPORT-{date}.json`；跨日保留历史。