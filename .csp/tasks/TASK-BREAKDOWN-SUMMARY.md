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

---

# v1.14.0 delta（semantic 性能优化，2026-09-06）

## 项目概览（v1.14.0）
- 上游：3 Spec（1:1 decomposition 3 Feature F-S-1..3），1 PMS 模块（semantic-perf）
- Task：3（1:1 Spec，M×2 / L×1），2 Wave，DAG 无环
- 关键路径：T-F-S-2 → T-F-S-3（2 步，最长链）
- 估时：M/L 粒度，人日 [TBD]（无团队速率）

## Task 类型分派矩阵（v1.14.0）
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-logic | T-F-S-1 | 后端（engine.py cache 条件分支 + settings.py env + CHANGELOG） |
| backend-logic | T-F-S-2 | 后端（engine.py ANN 切换 + embeddings.py batch cosine + related_pages.py 复用 + pyproject.toml hnswlib） |
| infra | T-F-S-3 | DevOps（benchmark 脚本更新 + test marker） |

## 拆解门控（v1.14.0）
- [x] Spec 完整性：3 Task == 3 Spec（03 穷尽门控通过，3 Spec == 3 原子 Feature F-S-1..3）
- [x] 每个 Feature 有 ≥1 Task（3/3）
- [x] Task 粒度 ≤4h（M×2 / L×1，L=接近 4h 上限但不超）
- [x] DAG 无环（S-2→S-3 单向边，S-1 独立，拓扑序无回边）
- [x] Task 依赖与 decomposition Feature 依赖一致（F-S-2→F-S-3，F-S-1 独立）
- [x] Wave 划分合理（Wave 1 S-1/S-2 并行；Wave 2 S-3 依赖 S-2；`benchmark_semantic.py` 跨 Wave 串行）
- [x] 每 Task acceptance 非空（指向 AC，共 15 AC 全映射）
- [x] 不越 PMS 边界（semantic-perf 模块）
- [x] 并行检测通过（Wave 1 两 Task 文件集无重叠，engine.py 同文件不同 section 需合并协调）

## 05 实施指引（v1.14.0）
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 两路并行（worktree 隔离）。
- Wave 1 T-F-S-1 / T-F-S-2 并行，但均写 `engine.py` 不同 section（cache 条件分支 vs cosine→ANN），须合并协调。
- Wave 2 T-F-S-3 独占（依赖 S-2 ANN 路径完成）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 共享文件 `engine.py`：T-F-S-1 + T-F-S-2 同时 Wave 1 写不同 section，worktree 隔离 + 合并。
- 共享文件 `scripts/benchmark_semantic.py`：T-F-S-1（Wave 1 阈值读 env）→ T-F-S-3（Wave 2 大规模更新），Wave 1→2 串行。
- 详见 `.csp/tasks/TASKS-DELTA-v1.14.0.md`。

## assumptions / [TBD]（v1.14.0）
- `SAW_ANN_THRESHOLD` 默认值 500 [TBD]（须 05 实施后 benchmark 实测确认拐点）
- ANN 召回率 ≥95% [TBD]（须 benchmark 验证）
- ANN 索引增量更新策略 [TBD]（05 实施时决定增量 vs 全量重建）
- ANN P99 / cosine P99 实际值 [TBD]（benchmark 跑完填）
- 规模延迟曲线实际值 [TBD]（benchmark 跑完填）
- `SAW_SEMANTIC_CACHE_THRESHOLD_MS` 实际效果 [TBD]（须 benchmark 验证）

---

# v1.15.0 delta（agent/link 能力，2026-09-06）

## 项目概览（v1.15.0）
- 上游：3 Spec（1:1 decomposition 3 Feature F-T-1..3），1 PMS 模块（agent-link）
- Task：3（1:1 Spec，M×3），1 Wave 全并行，DAG 无环
- 关键路径：无（3 Task 无依赖，全并行 1 步）
- 估时：M 粒度，人日 [TBD]（无团队速率）

## Task 类型分派矩阵（v1.15.0）
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-logic | T-F-T-1 | 后端（YAML 加载 + additive 合并 + CLI/REST 可见 + workflow validate） |
| backend-logic | T-F-T-2 | 后端（links apply CLI 逻辑 + WikiRepository.write 复用 + 去重） |
| backend-logic | T-F-T-3 | 后端（event_bus subscriber + 内存计数器 + REST activity 端点 + CLI） |

## 拆解门控（v1.15.0）
- [x] Spec 完整性：3 Task == 3 Spec（03 穷尽门控通过，3 Spec == 3 原子 Feature F-T-1..3）
- [x] 每个 Feature 有 ≥1 Task（3/3）
- [x] Task 粒度 ≤4h（M×3）
- [x] DAG 无环（T-1/T-2/T-3 互相独立，无依赖边，实机校验 cycle=none）
- [x] Task 依赖与 decomposition Feature 依赖一致（F-T-1/F-T-2/F-T-3 全独立无边）
- [x] Wave 划分合理（全 Wave 1 并行，无共享资源串行约束）
- [x] 每 Task acceptance 非空（指向 AC，共 12 AC 全映射）
- [x] 不越 PMS 边界（agent-link 模块）
- [x] 并行检测通过（`collaborate.py`/`agents_cmd.py`/`test_agents_rest.py` 同文件不同 section，需合并协调）

## 05 实施指引（v1.15.0）
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 三路并行（worktree 隔离）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 共享文件 `collaborate.py`：T-F-T-1 + T-F-T-3 同时写不同端点（list_agents custom 标记 vs activity 端点），worktree 隔离 + 合并。
- 共享文件 `agents_cmd.py`：T-F-T-1 + T-F-T-3 同时写不同子命令（custom 标注 vs activity 子命令），worktree 隔离 + 合并。
- 共享文件 `test_agents_rest.py`：T-F-T-1 + T-F-T-3 同时写不同用例（AC-A-4 vs AC-C-3/4），worktree 隔离 + 合并。
- 详见 `.csp/tasks/TASKS-DELTA-v1.15.0.md`。

## assumptions / [TBD]（v1.15.0）
- 自定义角色 YAML schema 实际用户使用场景 [TBD]（05 实施后 CI 验证）
- links apply 实际建议质量 [TBD]（取决于 compute_related_pages 既有算法质量）
- activity 聚合实际事件频率 [TBD]（取决于 workflow 执行频率，内存态不持久化）
- `collaborate.py` / `agents_cmd.py` / `test_agents_rest.py` 合并冲突解决方案 [TBD]（05 实施时 worktree 隔离 + 合并协调）

---

# v1.16.0 delta（realtime 仪表盘 v4.3，2026-09-07）

## 项目概览（v1.16.0）
- 上游：3 Spec（1:1 decomposition 3 Feature F-U-1..3），1 PMS 模块（dashboard）
- Task：3（1:1 Spec，M×3），2 Wave，DAG 无环
- 关键路径：T-F-U-1 → T-F-U-3（2 步，最长链，与 U-2→U-3 等长）
- 估时：M 粒度，人日 [TBD]（无团队速率）

## Task 类型分派矩阵（v1.16.0）
| 类型 | Task | 推荐分派 |
|---|---|---|
| frontend | T-F-U-1 | 前端（react-query hooks + AgentList/AgentCard 扩展 + types + vitest） |
| frontend | T-F-U-2 | 前端（WorkflowList/WorkflowRow 新建 + react-query hooks + types + vitest） |
| frontend | T-F-U-3 | 前端（useWebSocket 扩展 + polling 降级编排 + 降级横幅 + vitest） |

## 拆解门控（v1.16.0）
- [x] Spec 完整性：3 Task == 3 Spec（03 穷尽门控通过，3 Spec == 3 原子 Feature F-U-1..3）
- [x] 每个 Feature 有 ≥1 Task（3/3）
- [x] Task 粒度 ≤4h（M×3）
- [x] DAG 无环（U-1/U-2 独立，U-1→U-3 + U-2→U-3，拓扑序无回边）
- [x] Task 依赖与 decomposition Feature 依赖一致（F-U-1→F-U-3 + F-U-2→F-U-3，F-U-1/F-U-2 独立）
- [x] Wave 划分合理（Wave 1 U-1/U-2 并行；Wave 2 U-3 依赖 U-1+U-2；`Dashboard.tsx`/`types/api.ts` 同文件不同 section 需合并协调）
- [x] 每 Task acceptance 非空（指向 AC，共 8 AC 全映射 + AC-D-9 系统级 NFR）
- [x] 不越 PMS 边界（dashboard 模块）
- [x] 并行检测通过（Wave 1 两 Task `Dashboard.tsx`/`types/api.ts` 同文件不同 section/类型，需合并协调）

## 05 实施指引（v1.16.0）
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 两路并行（worktree 隔离）。
- Wave 1 T-F-U-1 / T-F-U-2 并行，但均写 `Dashboard.tsx`/`types/api.ts` 不同 section/类型，须合并协调。
- Wave 2 T-F-U-3 独占（依赖 U-1 useAgents + U-2 useWorkflows 已建好 react-query 查询）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 共享文件 `Dashboard.tsx`：T-F-U-1 + T-F-U-2 同时 Wave 1 写不同区域，worktree 隔离 + 合并。
- 共享文件 `types/api.ts`：T-F-U-1 + T-F-U-2 同时 Wave 1 写不同类型，worktree 隔离 + 合并。
- 共享文件 `useWebSocket.ts`：T-F-U-3 Wave 2 扩展（U-1/U-2 不改此文件），Wave 1→2 串行。
- 详见 `.csp/tasks/TASKS-DELTA-v1.16.0.md`。

## assumptions / [TBD]（v1.16.0）
- polling interval 15s 实际体感延迟 [TBD]（05 实施后用户测试）
- WS 断连后 polling 降级横幅实际触发频率 [TBD]（取决于网络稳定性）
- `Dashboard.tsx`/`types/api.ts` 合并冲突解决方案 [TBD]（05 实施时 worktree 隔离 + 合并协调）
- live workflow 标记判定逻辑（`finished_at === null && status === 'running'` vs 后端 live merge 标记）[TBD]（05 实施时确认后端 list_workflows 返回结构）

---

# v1.17.0 delta（desktop 完成 v4.4，2026-09-07）

## 项目概览（v1.17.0）
- 上游：4 Spec（1:1 decomposition 4 Feature F-V-1..4），1 PMS 模块（desktop）
- Task：4（1:1 Spec，S×1 / M×2 / L×1），2 Wave，DAG 无环
- 关键路径：T-F-V-1 → T-F-V-2（2 步，最长链，与 V-1→V-3 / V-1→V-4 等长）
- 估时：S/M/L 粒度，人日 [TBD]（无团队速率）

## Task 类型分派矩阵（v1.17.0）
| 类型 | Task | 推荐分派 |
|---|---|---|
| infra | T-F-V-1 | DevOps（版本 bump 4 文件 + 配置审查 15 项 + 版本一致性/配置测试） |
| frontend | T-F-V-2 | 前端（仪表盘集成验证：frontendDist 路径 + web/dist 产出 + beforeBuildCommand/devUrl 配置验证测试） |
| infra | T-F-V-3 | DevOps（tauri build smoke + bundle.targets 配置验证） |
| backend-logic | T-F-V-4 | 后端（vite proxy 端口收敛 + CORS 扩展 + prod 模式连接验证测试） |

## 拆解门控（v1.17.0）
- [x] Spec 完整性：4 Task == 4 Spec（03 穷尽门控通过，4 Spec == 4 原子 Feature F-V-1..4）
- [x] 每个 Feature 有 ≥1 Task（4/4）
- [x] Task 粒度 ≤4h（S×1 / M×2 / L×1，L=接近 4h 上限但不超）
- [x] DAG 无环（V-1→{V-2,V-3,V-4}，拓扑序无回边）
- [x] Task 依赖与 decomposition Feature 依赖一致（F-V-1→{F-V-2,F-V-3,F-V-4}）
- [x] Wave 划分合理（Wave 1 V-1 先行；Wave 2 V-2/V-3/V-4 全并行，不同文件集无冲突）
- [x] 每 Task acceptance 非空（指向 AC，共 9 AC 全映射）
- [x] 不越 PMS 边界（desktop 模块）
- [x] 并行检测通过（Wave 2 三 Task 文件集完全无重叠）

## 05 实施指引（v1.17.0）
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 T-F-V-1 独占（版本 bump + 配置收敛先行）。
- Wave 2 三路并行（worktree 隔离）：T-F-V-2（仪表盘集成验证）/ T-F-V-3（tauri build）/ T-F-V-4（端口收敛+CORS）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 共享文件 `tauri.conf.json`：T-F-V-1（Wave 1 bump version）→ T-F-V-2/V-3（Wave 2 只读验证），Wave 1→2 串行。
- 共享文件 `Cargo.toml`：T-F-V-1（Wave 1 bump version）→ T-F-V-3（Wave 2 build 依赖），Wave 1→2 串行。
- 详见 `.csp/tasks/TASKS-DELTA-v1.17.0.md`。

## assumptions / [TBD]（v1.17.0）
- `tauri build` 首次编译时间 [TBD]（预计 2-4h，PRD §7）
- 构建产物大小 [TBD] MB（首次基线，无回归阈值）
- macOS `.app`/`.dmg` 为声明性目标（实际产出依赖构建环境）
- 签名/公证 defer 到后续版本（需 Apple Developer ID + notarytool）
- 自动更新（tauri updater）defer 到后续版本
- `app.security.csp = null` 后续可加固（defer）

---

# v1.18.0 delta（per-request workspace 注入 + O4 tag 流程，2026-09-07）

## 项目概览（v1.18.0）
- 上游：2 Spec（1:1 decomposition 2 Feature F-W-1..2），1 PMS 模块（per-request-ws）
- Task：2（1:1 Spec，M×1 / S×1），1 Wave 全并行，DAG 无环
- 关键路径：无（2 Task 无依赖，全并行 1 步）
- 估时：M/S 粒度，人日 [TBD]（无团队速率）

## Task 类型分派矩阵（v1.18.0）
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-logic | T-F-W-1 | 后端（FastAPI middleware contextvar 注入 + QueryEngine/子服务 _effective_workspace_id() + JSON 日志 workspace_id + ThreadPoolExecutor 传播） |
| infra | T-F-W-2 | DevOps（release-manager.md S8 tag 流程约定 + scripts/RELEASE-FLOW.md 新建 + 文档验证测试） |

## 拆解门控（v1.18.0）
- [x] Spec 完整性：2 Task == 2 Spec（03 穷尽门控通过，2 Spec == 2 原子 Feature F-W-1..2）
- [x] 每个 Feature 有 ≥1 Task（2/2）
- [x] Task 粒度 ≤4h（M×1 / S×1）
- [x] DAG 无环（W-1 / W-2 互相独立，无依赖边，实机校验 cycle=none）
- [x] Task 依赖与 decomposition Feature 依赖一致（F-W-1 / F-W-2 全独立无边）
- [x] Wave 划分合理（全 Wave 1 并行，无共享资源串行约束）
- [x] 每 Task acceptance 非空（指向 AC，共 7 AC 全映射）
- [x] 不越 PMS 边界（per-request-ws 模块）
- [x] 并行检测通过（2 Task 文件集完全无重叠，不同关注点）

## 05 实施指引（v1.18.0）
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 两路并行（worktree 隔离）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 无共享文件冲突，2 Task 可同时启动。
- T-F-W-1 后端 Task：FastAPI middleware + QueryEngine 改造 + 子服务改造 + JSON 日志 + ThreadPoolExecutor 传播 + 6 测试。
- T-F-W-2 infra Task：release-manager.md S8 更新 + scripts/RELEASE-FLOW.md 新建 + 2 测试。
- 详见 `.csp/tasks/TASKS-DELTA-v1.18.0.md`。

## assumptions / [TBD]（v1.18.0）
- contextvar 传播至 ThreadPoolExecutor 实测行为 [TBD]（Python 3.9+ asyncio.to_thread 内置 copy_context，05 实施后验证）
- workspace_id 校验正则实际用户场景覆盖度 [TBD]（05 实施后 CI 验证）
- 多租户集成测试 mock DB 策略 [TBD]（05 实施时决定 mock vs sqlite 内存）
- GPG 签名 tag defer 到后续版本（当前 threat model 不要求）
- `collaborate.py` asyncio.to_thread 后并发控制影响 [TBD]（05 实施时评估）
