# 任务模板：把外部借鉴的技能解耦移植进目标技能框架（本地优先、平台中立、闭环）

> **可复用提示词**。换场景只需重填 `A` 表，`B–H` 是不变的方法论，原样适用。
> 适用：把任意平台耦合的技能包解耦为目标框架原生的本地 markdown + git + 脚本等价物。

## A. 场景变量（每次按实际填充，其余章节引用这些变量）

| 变量 | 含义 | 本次示例填充 |
|------|------|--------------|
| `SOURCE_ARCHIVES` | 源材料 zip 及解压位置 | `~/Downloads/{codeva.zip, skills归档.zip, llm-wiki-builder-local-0.2.3.zip}` |
| `TARGET_ROOT` | 目标框架仓库根（git 仓库） | `/Users/cs/projects/code-skills-package` |
| `BUILD_PIPELINE` | 目标派生数据的 build/validate/test 命令 | `npm run build:registry && build:metadata && gen:triggers && fix:triggers && build:graph && build:page` |
| `VALIDATE_CMD` | 技能 v2 校验命令 | `node scripts/validate-skill-v2.mjs <各 layer/skills>` |
| `COUNT_CMD` | 计数一致性校验命令 | `node scripts/count-skills.mjs` |
| `TEST_CMD` | 全量测试命令 | `npm test` |
| `SKILL_DIR_SPEC` | 技能目录与 frontmatter 规范 | `SKILL.md + references/ + scripts/`；v2 frontmatter 字段集 |
| `DENYLIST` | 源里的平台专有名录（见 C.1 派生法） | alibaba/aone/codeva/kbase/ding/yuque/okf/hsf/… 等 |
| `PATH_CONV` | 目标原生路径与环境变量 | `.csp/{product-spec,code-spec/{app},test-spec/{module},wiki,…}` + `CSP_PROJECT_ROOT` + `CSP_GIT_REMOTE`(默认 github.com) |
| `SKILL_INVENTORY` | 要新建/增强的技能清单 + 交叉链接图 | PMS/CMS/TMS + csp-wiki/csp-code-wiki/csp-knowledge-hub + 共享 refs |
| `LIFECYCLE_HOOK` | 生命周期接线点 | `csp-lifecycle-orchestrator` 加 Stage 0 + 治理旁路 + 动态路由 |
| `LOOP_TO_CLOSE` | 要补全的研发闭环 | 需求对齐(spec)→code→test |

> 填表后，后续 B–H 章节自动引用这些变量；B–H 是**不变的方法论**。

## B. 目标
把 `SOURCE_ARCHIVES` 中**平台耦合**的技能**解耦**为目标框架原生的本地 markdown + git + 脚本等价物，保留行为语义，融入 `TARGET_ROOT`，并构建/补全 `LOOP_TO_CLOSE` 闭环，加速 Agent 对 codebase 的理解与快速 spec 定位/读取/生成。

## C. 硬性规则（方法论，不变）

### C.1 平台中立化（最严）
1. **派生 `DENYLIST`**：扫描源材料里出现的专有名词——内部域名、CLI 名、服务名、字段类型名、产品代号——全部列入禁止清单。
2. **连出处注释都不许留**：不得写"解耦自 XXX / 替换 XXX 平台"这类带 `DENYLIST` 词的出处注释；技能要独立成立。
3. **每轮改完用 `grep -rniE '<DENYLIST or>'` 扫描全部新增/改动文件，零命中才算过。**
4. **路径**：源的固定路径/家目录改为目标原生目录，用环境变量（如 `*_PROJECT_ROOT`，默认 cwd）参数化；远程一律 `git` + 可配置 remote（默认 `github.com`）。
5. **平台交互→本地等价**：把"平台 API/鉴权/域名交互"替换为"本地 markdown + git + 脚本 + 环境变量参数化"，保留行为语义；强耦合到 HTTP 凭证/专有 CLI 的部分（如内部记忆服务）不直接移植脚本，只移植可通用化的方法论纪律。

### C.2 结构分离
- 每个技能 = `SKILL.md` + `references/` + `scripts/`（按需），**不要融成一个文件**；reference/scripts 各自独立保留。
- frontmatter 按 `SKILL_DIR_SPEC`；元数据**内联**进页顶（废 `.meta.json` 侧车）。
- 不带 `package.json`、作者署名、LICENSE 到技能目录；不带 `__pycache__/*.pyc/.DS_Store` 等构建产物。

### C.3 内容纪律
- 不臆造：grep/读取不到的不写，推断标 `[TBD]`，业务数据未给标 `[TBD]`。
- 每条结论带 `file:line`；高危结论（死代码/无鉴权/从未调用）实机核验，不直接采信 Agent。
- delta 纪律：`ADDED` / `MODIFIED`（粘贴完整原文再编辑）/ `REMOVED`；里程碑折叠进 canonical；对未变更源重跑必须零 delta（content_hash 判变化，禁 mtime/文件大小）。

## D. 移植工作流（固定步骤）

1. **解压与分类**：读 `SOURCE_ARCHIVES`，按"可通用化 / 平台强耦合"二分。强耦合的（HTTP 凭证、专有 CLI 胶水）不移植脚本，只提炼纪律。
2. **提取规范写 Reference**：从源里挖出可用却易漏的规范——判官 rubric、状态机、门禁、信号规则、schema 契约、分类表、checklist、退出码、命名约定——通用化后写成目标框架的共享 reference。
3. **创建/增强技能**：按 `SKILL_INVENTORY` 写 SKILL.md + references + scripts；**一次性预先填好 `related_skills`**（按交叉链接图，不要事后补）。
4. **接线生命周期**：按 `LIFECYCLE_HOOK` 把中枢技能接为前置 Stage + 治理旁路 + 动态路由条目。
5. **工程同步**：跑 `BUILD_PIPELINE`，修 count 同步（见 E 的坑）。
6. **CLI 真测**：为每个 `scripts/*.sh` 建 fixture 实测（见 F）。
7. **DoD 核对 + 清理**：核对 G，删 fixture/解压目录，`git status` 验证无污染。

## E. 工程与验证流水线（每次变更后必跑）
```
<VALIDATE_CMD>
<BUILD_PIPELINE>
<COUNT_CMD>     # 必须 exit 0
<TEST_CMD>       # 必须全绿
```
**固定坑（任何有派生数据的框架都要查）**：
- 派生图依赖元数据时，**metadata 必须在 graph 之前重建**，否则新技能不入图。
- 计数校验若只查 Total 行，**不查 per-layer 计数**——新增技能后要手动同步 docs 里的 Total **和** 各层计数，扫描所有含旧数字的文档。
- frontmatter 字段顺序与类型须与校验器一致；`related_skills` 改动会改图边数，重建后确认。

## F. CLI 真实测试要求（写完即测，不许只测 `--help`）
为每个 `scripts/*.sh` **建一个 `/tmp` 真实 git fixture 仓库**（含已知入口点源文件 + 目标原生 `.csp/` manifest + AGENTS.md + spec/wiki 页 + **故意缺陷**），逐子命令实测输出与退出码：
- happy path（正常返回 + 正确字段）
- failure path（缺前置 → 清晰报错 + 正确非零退出码；缺陷注入 → 被抓出；修复后 → 通过）
- 含"省略参数从产物文件读基线"的间接路径
- **cwd 陷阱**：`*_PROJECT_ROOT` 只影响脚本、不影响 shell cwd——写 fixture 用**绝对路径**，避免污染 `TARGET_ROOT`；测完 `rm -rf` fixture 并对 `TARGET_ROOT` `git status` 确认无污染。

## G. Definition of Done（全部满足才算完成）
- [ ] `DENYLIST` grep 零命中（连出处注释）
- [ ] 所有新技能按 `SKILL_DIR_SPEC` validate pass；`BUILD_PIPELINE` 重建；`TEST_CMD` 全绿
- [ ] `COUNT_CMD` exit 0；Total + 各层计数在 docs 全部同步
- [ ] 每个 CLI 全子命令真实 fixture 测试通过（happy + failure + 间接路径）
- [ ] SKILL.md reference 表指向所有新共享 ref；`related_skills` 一次性填全
- [ ] `LIFECYCLE_HOOK` 接线完成（前置 Stage + 治理旁路 + 动势路由）
- [ ] 临时解压目录与 fixture 已清理；`TARGET_ROOT` 的 `git status` 仅含合法新文件
- [ ] `LOOP_TO_CLOSE` 闭环可述（前置 Stage → 各阶段读对应产物 → ship 闭环）

## H. 风格与边界
- 借鉴既有技能格式（参考目标框架里成熟技能的 frontmatter 与 reference 表写法）。
- 平台中立化是方法论：保留**行为语义**（状态机/门禁/规则/闭环），剥离**平台耦合**（域名/鉴权/专有 API/专有 CLI）。
- 强耦合组件不硬移植：内部 HTTP 记忆服务、专有 CLI 胶水 → 只把其纪律（冲突检测 before add、CLI 优先于生成代码、定义完成）提炼进目标。
- 文档与代码同源：SKILL.md 是唯一 frontmatter 真相源，registry/triggers/graph 全派生，禁手改派生数据。

---

### 用法
1. 填 `A` 表 → 得到本次场景的完整参数。
2. `B–H` 自动适用，无需改——它们是"解耦移植 + 本地优先 + 闭环 + 真测"的不变方法论。
3. 换场景（如移植别的技能包进别的框架）只需重填 `A`，提示词本身可原样复用。
