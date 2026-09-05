# Task Breakdown Summary — 供 05 实施消费

## 项目概览
- 上游：20 Spec（1:1 decomposition 20 Feature），5 PMS 模块
- Task：20（1:1 Spec，S×8 / M×12），3 Wave，DAG 无环
- 关键路径：T-F-A-1-1 → T-F-A-2-1 → T-F-A-5-1 → T-F-A-6-1 → T-F-E-3-1
- 估时：S/M 粒度，人日 [TBD]（无团队速率，见 assumptions）

## Task 类型分派矩阵
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-cli | T-F-A-1-1 | 后端 |
| test | T-F-A-2/3/4/5-1 | QA/后端 |
| infra-ci | T-F-A-6-1, T-F-E-1/2/3-1 | DevOps |
| infra-script | T-F-B-1-1, T-F-B-2-1 | 后端 |
| doc | T-F-B-3-1 | Tech Writer |
| test-security | T-F-C-1/3/4-1 | 安全/QA |
| backend-security | T-F-C-2-1, T-F-C-5-1 | 后端安全 |
| backend | T-F-D-1/2/3-1 | 后端 |

## 拆解门控
- [x] Spec 完整性：20 Spec == 20 Feature（03 穷尽门控通过）
- [x] 每个 P0/P1 Feature Spec 有 ≥1 Task（20/20）
- [x] Task 粒度 ≤4h（S/M）
- [x] DAG 无环（实机校验）
- [x] Task 依赖与 decomposition Feature 依赖一致
- [x] Wave 划分合理（共享 ci.yml 串行）
- [x] 每 Task acceptance 非空（指向 AC）
- [x] 不越 PMS 边界（5 模块）

## 05 实施指引
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 可 10 路并行（worktree 隔离）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 复用优先：棕地 hardening，多数 Task 在既有文件加 delta，不重造（CMS 标"复用"）。
- 共享文件 ci.yml 串行（T-F-A-6-1→T-F-E-2-1→T-F-E-3-1），禁并行写。

## assumptions / [TBD]
- 估时无团队速率 → S/M 表达，人日 [TBD]。
- T-F-C-5-1 前端 token 互通实机核验后定补齐范围。
- T-F-E-1-1 coverage 基线数值实测后定阈值。
- T-F-A-1-1 / T-F-C-1-1 命令名 [TBD]。

## manifest 回写
- tasks 索引 item：`.csp/tasks/TASK-BREAKDOWN-SUMMARY.md`（source_type=doc, kind=feature, built）
- 单 Task 经 WBS 索引（不入 manifest，避免膨胀）

---

# v1.10.0 delta（embedding 语义搜索，2026-09-04）

## 项目概览（v1.10.0）
- 上游：4 Spec（1:1 decomposition 4 Feature F-N-1..4），1 PMS 模块（embedding）
- Task：4（1:1 Spec，S×1 / M×3），2 Wave，DAG 无环
- 关键路径：T-F-N-1 → T-F-N-2（2 步，最长链）
- 估时：S/M 粒度，人日 [TBD]（无团队速率）

## Task 类型分派矩阵（v1.10.0）
| 类型 | Task | 推荐分派 |
|---|---|---|
| db-migration | T-F-N-1 | 后端（DB + sink + CLI） |
| backend-api | T-F-N-2 | 后端（engine + CLI + REST） |
| backend-logic | T-F-N-3 | 后端（related_pages 逻辑） |
| test | T-F-N-4 | QA（测试策略 + 用例） |

## 拆解门控（v1.10.0）
- [x] Spec 完整性：4 Task == 4 Spec（03 穷尽门控通过）
- [x] 每个 Feature 有 ≥1 Task（4/4）
- [x] Task 粒度 ≤4h（S×1 / M×3）
- [x] DAG 无环（N1→{N2,N3,N4}，实机校验 cycle=none）
- [x] Task 依赖与 decomposition Feature 依赖一致（N-1→{N-2,N-3,N-4}）
- [x] Wave 划分合理（db migration Wave 1 串行先行；Wave 2 全并行无文件冲突）
- [x] 每 Task acceptance 非空（指向 AC，共 12 AC 全映射）
- [x] 不越 PMS 边界（embedding 模块）

## 05 实施指引（v1.10.0）
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 T-F-N-1 独占（migration 共享资源）。
- Wave 2 三路并行（worktree 隔离）：T-F-N-2（engine+CLI+REST）/ T-F-N-3（related_pages）/ T-F-N-4（tests）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 共享文件 `search_cmd.py`：T-F-N-1（Wave 1）→ T-F-N-2（Wave 2），Wave 1→2 串行，禁并行写。
- 共享文件 `db/migrations.py`：T-F-N-1 独占 Wave 1。

## assumptions / [TBD]（v1.10.0）
- 向量检索 P99 延迟 [TBD]（05 实施后 benchmark）
- 规模上限 [TBD]（预估 ~10K docs 可接受）
- embedding 信号权重 2.5 需 benchmark 调优 [TBD]
- 相似度缓存 [TBD]（后续优化）
- 降级测试 mock 策略需 05 实施时验证 mock 边界

---

# v1.11.0 delta（债务收口 IV / bug fix，2026-09-05）

## 项目概览（v1.11.0）
- 上游：4 Spec（1:1 decomposition 4 Feature F-O-1..4），1 PMS 模块（debt-closure）
- Task：4（1:1 Spec，S×1 / M×2 / L×1），1 Wave 全并行，DAG 无环
- 关键路径：无（4 Task 无依赖，全并行 1 步）
- 估时：S/M/L 粒度，人日 [TBD]（无团队速率）

## Task 类型分派矩阵（v1.11.0）
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-logic | T-F-O-1 | 后端（engine.py cache 插入 + 失效钩子） |
| test | T-F-O-2 | QA（compiler 深覆盖测试 + fail_under 棘轮） |
| backend-api | T-F-O-3 | 后端（collaborate.py REST 读 DB + merge live） |
| docs | T-F-O-4 | Tech Writer（Spec 命名回更 + hash 复核） |

## 拆解门控（v1.11.0）
- [x] Spec 完整性：4 Task == 4 Spec（03 穷尽门控通过）
- [x] 每个 Feature 有 ≥1 Task（4/4）
- [x] Task 粒度 ≤4h（S×1 / M×2 / L×1）
- [x] DAG 无环（O1/O2/O3/O4 互相独立，无依赖边，实机校验 cycle=none）
- [x] Task 依赖与 decomposition Feature 依赖一致（4 Feature 全并行无依赖边）
- [x] Wave 划分合理（全 Wave 1 并行，无共享资源串行约束）
- [x] 每 Task acceptance 非空（指向 AC，共 12 AC 全映射）
- [x] 不越 PMS 边界（debt-closure 模块）
- [x] 并行检测通过（4 Task 文件集无重叠）

## 05 实施指引（v1.11.0）
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 四路并行（worktree 隔离）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 无共享文件冲突，4 Task 可同时启动。
- 详见 `.csp/tasks/TASKS-DELTA-v1.11.0.md`。

## assumptions / [TBD]（v1.11.0）
- cache 命中率基线 [TBD]（须 05 实施后 benchmark）
- compiler.py 覆盖率目标值 [TBD]（须 05 实施后测量，预计 17%→~70%+）
- 全量 coverage 65 是否仅靠 compiler 深覆盖即可达成 [TBD]（须实施后验证）
- REST 查询延迟 [TBD]（须 05 实施后与 CLI 同量级验证）

---

# v1.12.0 delta（embedding API 重构，2026-09-05）

## 项目概览（v1.12.0）
- 上游：4 Spec（1:1 decomposition 4 Feature F-Q-1..4），1 PMS 模块（embedding-api）
- Task：4（1:1 Spec，M×4），2 Wave，DAG 无环
- 关键路径：T-F-Q-1 → T-F-Q-2（2 步，最长链，与 Q-1→Q-3/Q-1→Q-4 等长）
- 估时：M 粒度，人日 [TBD]（无团队速率）

## Task 类型分派矩阵（v1.12.0）
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-logic | T-F-Q-1 | 后端（embeddings.py provider 重构 + settings.py EmbeddingSettings） |
| backend-logic | T-F-Q-2 | 后端（embedding_sink.py model 列动态 + search_cmd.py 维度检测） |
| backend-logic | T-F-Q-3 | 后端（embeddings.py ST fallback 分支 + settings.py OR 逻辑） |
| test | T-F-Q-4 | QA（测试改 mock + benchmark 新建） |

## 拆解门控（v1.12.0）
- [x] Spec 完整性：4 Task == 4 Spec（03 穷尽门控通过，4 Spec == 4 原子 Feature F-Q-1..4）
- [x] 每个 Feature 有 ≥1 Task（4/4）
- [x] Task 粒度 ≤4h（M×4）
- [x] DAG 无环（Q-1→{Q-2,Q-3,Q-4}，拓扑序无回边，实机校验 cycle=none）
- [x] Task 依赖与 decomposition Feature 依赖一致（F-Q-1→{F-Q-2,F-Q-3,F-Q-4}）
- [x] Wave 划分合理（Q-1 Wave 1 独占前置；Q-2/Q-3/Q-4 Wave 2 全并行，共享 `embeddings.py`/`settings.py` 串行 Wave 1→2）
- [x] 每 Task acceptance 非空（指向 AC，共 9 AC 全映射）
- [x] 不越 PMS 边界（embedding-api 模块）
- [x] 并行检测通过（Wave 2 三 Task 文件集无重叠）

## 05 实施指引（v1.12.0）
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 T-F-Q-1 独占（provider 重构前置）。
- Wave 2 三路并行（worktree 隔离）：T-F-Q-2（embedding_sink+search_cmd）/ T-F-Q-3（embeddings+settings 续写）/ T-F-Q-4（tests）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 共享文件 `embeddings.py`/`settings.py`：T-F-Q-1（Wave 1）→ T-F-Q-3（Wave 2），Wave 1→2 串行，禁并行写。
- 详见 `.csp/tasks/TASKS-DELTA-v1.12.0.md`。

## assumptions / [TBD]（v1.12.0）
- API embedding P99 延迟 [TBD]（须 05 实施后 benchmark，真实 API key 可选 E2E）
- semantic vs BM25 召回率 [TBD]（须同义查询集 benchmark 后定 baseline）
- 具体模型名 [TBD]（默认 `text-embedding-3-small` 或 config 驱动，dim=1536）
- 向量索引存储开销 [TBD]（API dim 如 1536 > 本地 384，须磁盘测量）
- 全量重建延迟 [TBD]（取决于 claim/wiki 总量 × API embedding 单次延迟）
