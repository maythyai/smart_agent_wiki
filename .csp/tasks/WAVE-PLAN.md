# Wave Plan — 并行波次计划

> 3 Wave，镜像 decomposition 波次。共享资源（ci.yml）跨 Wave 串行追加，不并行写。

> **进度（2026-09-03）**：Wave 1 ✅ done（10/10 Task，M1 基础硬化就绪，1853 tests green）。Wave 2/3 留下一周期。

## Wave 1 — 基础层（10 Task，全并行）
| task_id | 描述 | 类型 | 里程碑 |
|---|---|---|---|
| T-F-A-1-1 | 冒烟骨架 | backend-cli | 冒烟可用 |
| T-F-B-1-1 | 宣称 diff | infra-script | 一致性可测 |
| T-F-C-1-1 | 权限矩阵 | test-security | 0 裸路由 |
| T-F-C-2-1 | receipt 闭环 | backend-security | receipt 链 |
| T-F-C-3-1 | 限流双轨 | test-security | 429 生效 |
| T-F-C-4-1 | URL 守卫 | test-security | 守卫覆盖 |
| T-F-C-5-1 | token 同源 [TBD] | backend-security | 后端统一核验 |
| T-F-D-1-1 | logger 收敛 | backend | 统一 logger |
| T-F-D-3-1 | health+JSON | backend | 健康真实 |
| T-F-E-1-1 | coverage 基线 [TBD] | infra-ci | 基线数值 |

## Wave 2 — 核心业务（7 Task）
| task_id | 描述 | 依赖 | 可并行性 |
|---|---|---|---|
| T-F-A-2-1 | ingest+compile 冒烟 | A1 | A2/A3/A4 并行 |
| T-F-A-3-1 | query 冒烟 | A1 | 同上 |
| T-F-A-4-1 | govern+learn 冒烟 | A1 | 同上 |
| T-F-B-2-1 | 能力清单 | B1 | 独立 |
| T-F-B-3-1 | 文档修正 | B1 | 独立 |
| T-F-D-2-1 | trace 贯穿 | D1 | 独立 |
| T-F-E-2-1 | coverage 门禁 | E1 | 独立 |

## Wave 3 — 集成/增强（3 Task）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-A-5-1 | 离线 fallback 冒烟 | A2,A3,A4 | 离线可用 |
| T-F-A-6-1 | CI smoke job | A5 | CI 守卫 |
| T-F-E-3-1 | CI 集成 | A6,E2 | 全 CI 闭环 |

## 共享资源串行
- `.github/workflows/ci.yml`：T-F-A-6-1（smoke job）→ T-F-E-2-1（coverage gate）→ T-F-E-3-1（集成）串行追加，禁并行写同文件。

## 里程碑
- M1（Wave 1 完成）：基础硬化就绪（安全/可观测/冒烟骨架/基线）。
- M2（Wave 2 完成）：核心链路冒烟全绿 + 宣称一致。
- M3（Wave 3 完成）：CI 全闭环 + 离线可用 → 05 可交付。

---

# v1.3.0 波次（硬化尾巴 + 技术债，2026-09-03）

> 源自 PRD-hardening-tail-v1.3.0 + 02 delta。Wave 2/3 Task 沿用既有（spec 已就绪），加 F-debt 3 Task。

## v1.3.0 Wave 2 — 核心业务 + docs（并行）
| task_id | 描述 | 类型 | 并行性 |
|---|---|---|---|
| T-F-A-2-1 | ingest+compile 冒烟 | test | A2/A3/A4 并行 |
| T-F-A-3-1 | query 冒烟 | test | 同上 |
| T-F-A-4-1 | govern+learn 冒烟 | test | 同上 |
| T-F-B-2-1 | 能力清单 CAPABILITIES.md | infra-script | 独立 |
| T-F-B-3-1 | 文档修正 | doc | 独立 |
| T-F-D-2-1 | trace_id 贯穿 | backend | 独立 |
| T-F-E-2-1 | coverage 门禁≥80% | infra-ci | 独立 |
| T-F-Z-2-1 | roadmap narrative 重写 | doc | 独立（docs，与 src 不冲突）|
| T-F-Z-3-1 | v1.2.0 行为变更迁移文档 | doc | 独立（docs）|

## v1.3.0 Wave 3 — 集成 + ruff 收口（串行末位）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-A-5-1 | 离线 fallback 冒烟 | A2,A3,A4 | 离线可用 |
| T-F-A-6-1 | CI smoke job | A5 | CI 守卫 |
| T-F-E-3-1 | CI 集成 | A6,E2 | 全 CI 闭环 |
| **T-F-Z-1-1** | **ruff baseline 收口** | **A2/A3/A4/D2 后串行** | **lint 门禁就绪** |

## v1.3.0 共享资源串行
- `.github/workflows/ci.yml`：A6→E2→E3 串行追加（沿用既有约束）。
- **F-Z-1 ruff 是共享资源**（pyproject + 全 src）：必须在所有 src 改动（A2/A3/A4/D2）合并后串行执行，禁并行。

## v1.3.0 里程碑
- M2（Wave 2）：核心链路冒烟全绿 + 宣称一致 + trace 贯穿 + coverage 门禁 + debt docs。
- M3（Wave 3）：CI 全闭环 + 离线可用 + ruff lint 门禁 → v1.3.0 可交付。

---

# v1.4.0 波次（平台化与团队协作，2026-09-03）

> 源自 PRD-platform-team-v1.4.0 + 02 delta + ADR-005。platform-team 新域。

## v1.4.0 Wave 1 — platform + debt（并行）
| task_id | 描述 | 类型 | 并行性 |
|---|---|---|---|
| T-F-P-1-1 | RBAC 深化（Cedar 热加载 + e2e） | backend | 独立（auth/）|
| T-F-P-2-1 | 团队部署（docker-compose.prod） | infra | 独立（docker/）|
| T-F-P-3-1 | 可观测闭环（saw health + audit） | backend-cli | 独立（cli/commands/）|
| T-F-Z-5-1 | heavy-SDK importorskip | test | 独立（tests/）|

## v1.4.0 Wave 2 — workspace 隔离（migration v8 串行）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-P-4-1 | 多 workspace 隔离（schema 前缀 + v8 + 授权绑定） | P-1 | 多团队共存 |

## v1.4.0 Wave 3 — ruff 收口续（串行末位）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-Z-4-1 | ruff F401/F841 收口 | P-1/P-3/P-4 后串行 | lint 门禁加严 |

## v1.4.0 共享资源串行
- migration v8（F-P-4 workspace_id 列）：Wave 2 串行。
- ruff F401/F841 全库修（F-Z-4）：Wave 3 串行末位，所有 src 改动后。

## v1.4.0 里程碑
- M4（Wave 1）：platform 基座（RBAC/deploy/observability CLI）+ heavy-SDK 优雅跳过。
- M5（Wave 2）：多 workspace 隔离可用 → 多团队共存。
- M6（Wave 3）：ruff F401/F841 启用 → lint 门禁加严 → v1.4.0 可交付。

---

# v1.10.0 波次（embedding 语义搜索，2026-09-04）

> 源自 PRD-embedding-v1.10.0 + 02 delta + ADR-010。4 Task，2 Wave。DAG N-1→{N-2,N-3,N-4} 无环。

## v1.10.0 Wave 1 — embedding 索引基座（串行先行）
| task_id | 描述 | 类型 | 里程碑 |
|---|---|---|---|
| T-F-N-1 | embedding_store migration v10 + EmbeddingSink + rebuild-embeddings 命令 | db-migration | embedding_store 表 + sink 就绪 |

## v1.10.0 Wave 2 — 语义检索 + smart-linking + 测试（全并行）
| task_id | 描述 | 依赖 | 可并行性 |
|---|---|---|---|
| T-F-N-2 | QueryEngine semantic mode + CLI --mode semantic + REST + 降级 | T-F-N-1 | 独立（engine.py + search_cmd.py + REST） |
| T-F-N-3 | compute_related_pages embedding 第 4 信号 | T-F-N-1 | 独立（related_pages.py + links_cmd.py） |
| T-F-N-4 | importorskip 测试策略 + 降级测试分离 | T-F-N-1 | 独立（tests/unit/ 独占） |

## v1.10.0 共享资源串行
- `db/migrations.py`（migration v10）：Wave 1 串行先行，T-F-N-1 独占。Wave 2 Task 均依赖 embedding_store 表存在。
- `search_cmd.py`：T-F-N-1（Wave 1，rebuild-embeddings 子命令）→ T-F-N-2（Wave 2，--mode semantic）。Wave 1→2 串行，无并行写冲突。

## v1.10.0 Wave 2 文件冲突分析
| 文件 | Wave 2 写入方 | 冲突? |
|---|---|---|
| engines/query/engine.py | T-F-N-2 | 否（N-3 写 related_pages.py） |
| engines/query/related_pages.py | T-F-N-3 | 否 |
| tests/unit/test_*.py | T-F-N-4 | 否（测试文件独占） |

## v1.10.0 里程碑
- M-EMB-1（Wave 1）：embedding_store 表 + EmbeddingSink + rebuild 命令就绪 → 向量可持久化。
- M-EMB-2（Wave 2）：语义检索 + smart-linking embedding + 测试就绪 → v1.10.0 可交付。

---

# v1.11.0 波次（债务收口 IV / bug fix，2026-09-05）

> 源自 PRD-debt-closure-v1.11.0 + 02 delta + ADR-011。4 Task，1 Wave 全并行。DAG 无环（4 Task 互相独立，无依赖边）。

## v1.11.0 Wave 1 — 全并行（4 Task，无依赖）
| task_id | 描述 | 类型 | 里程碑 |
|---|---|---|---|
| T-F-O-1 | semantic cache（_semantic_search 入口 cache.get + 出口 cache.set + 失效钩子） | backend-logic | semantic cache 命中/隔离/失效/不缓存 fallback |
| T-F-O-2 | compile/compiler.py 深覆盖（7 测试文件 + 20 用例 + fail_under 64→65） | test | compiler 覆盖 17%→高 + coverage 棘轮 65 |
| T-F-O-3 | workflow REST 统一读 DB（list_workflows 读 workflow_executions + merge live） | backend-api | REST/CLI 同源 DB |
| T-F-O-4 | Spec 命名回更 + tag hash 复核 | docs | SPEC-F-N-1 命名 + hash 三处一致 |

## v1.11.0 共享资源串行
- 无共享资源串行约束。4 Task 触及完全不同的文件集，无重叠。

## v1.11.0 Wave 1 文件冲突分析
| 文件 | Wave 1 写入方 | 冲突? |
|---|---|---|
| engines/query/engine.py | T-F-O-1 | 否 |
| tests/unit/engines/compile/* | T-F-O-2 | 否（新建测试目录） |
| pyproject.toml | T-F-O-2 | 否（仅 O-2） |
| api/routes/collaborate.py | T-F-O-3 | 否 |
| .csp/specs/SPEC-F-N-1.md | T-F-O-4 | 否 |
| docs/strategy/ROADMAP.md | T-F-O-4 | 否（仅复核） |

## v1.11.0 里程碑
- M-DEBT-IV（Wave 1）：semantic cache + compile 深覆盖 + workflow REST 统一 + Spec 回更就绪 → v1.11.0 可交付。

---

# v1.12.0 波次（embedding API 重构，2026-09-05）

> 源自 PRD-embedding-api-v1.12.0 + 02 delta + ADR-012。4 Task，2 Wave。DAG Q-1→{Q-2,Q-3,Q-4} 无环。

## v1.12.0 Wave 1 — provider 重构（串行先行）
| task_id | 描述 | 类型 | 里程碑 |
|---|---|---|---|
| T-F-Q-1 | embed_texts 改 litellm.embedding + EmbeddingSettings + embeddings_available/detect_tier API 检测 | backend-logic | embed_texts 走 litellm API 就绪 |

## v1.12.0 Wave 2 — 维度+fallback+测试（全并行）
| task_id | 描述 | 依赖 | 可并行性 |
|---|---|---|---|
| T-F-Q-2 | EmbeddingSink/_upsert model 列动态 + rebuild 维度检测适配 | T-F-Q-1 | 独立（embedding_sink.py + search_cmd.py） |
| T-F-Q-3 | 本地 ST 可选 fallback 分支 + embeddings_available OR 逻辑 | T-F-Q-1 | 独立（embeddings.py + settings.py，续写 Wave 1） |
| T-F-Q-4 | 测试改 API mock + benchmark semantic vs BM25 | T-F-Q-1 | 独立（tests/unit/ 独占） |

## v1.12.0 共享资源串行
- `src/saw/adapters/embeddings.py`：T-F-Q-1（Wave 1，建 API 路径 + OR 骨架）→ T-F-Q-3（Wave 2，补 ST fallback 分支 + OR 对称）。Wave 1→2 串行。
- `src/saw/config/settings.py`：T-F-Q-1（Wave 1，新增 EmbeddingSettings + API 检测）→ T-F-Q-3（Wave 2，OR 逻辑扩展 ST importable）。Wave 1→2 串行。

## v1.12.0 Wave 2 文件冲突分析
| 文件 | Wave 2 写入方 | 冲突? |
|---|---|---|
| src/saw/write_queue/sinks/embedding_sink.py | T-F-Q-2 | 否 |
| src/saw/drivers/cli/commands/search_cmd.py | T-F-Q-2 | 否 |
| src/saw/adapters/embeddings.py | T-F-Q-3 | 否（Q-1 Wave 1 已完成，Wave 2 仅 Q-3 续写） |
| src/saw/config/settings.py | T-F-Q-3 | 否（同上） |
| tests/unit/test_*.py | T-F-Q-4 | 否（测试文件独占） |

## v1.12.0 里程碑
- M-EMB-API-1（Wave 1）：embed_texts 走 litellm API 就绪（provider 重构前置，解锁 Wave 2）。
- M-EMB-API-2（Wave 2）：维度可配+重建检测 / ST fallback / 测试 mock+benchmark 就绪 → v1.12.0 可交付。

---

# v1.14.0 波次（semantic 性能优化，2026-09-06）

> 源自 PRD-semantic-perf-v1.14.0 + 02 delta + ADR-014。3 Task，2 Wave。DAG S-2→S-3 单向边，S-1 独立，无环。

## v1.14.0 Wave 1 — cache 可配 + ANN 索引（2 路并行）
| task_id | 描述 | 类型 | 并行性 |
|---|---|---|---|
| T-F-S-1 | cache 阈值可配（engine.py cache 条件分支 + settings.py env + benchmark 阈值读 env + CHANGELOG） | backend-logic | 独立（engine.py cache section / settings.py / benchmark / CHANGELOG） |
| T-F-S-2 | ANN 索引（engine.py cosine→ANN 切换 + embeddings.py batch cosine + related_pages.py 复用 + pyproject.toml hnswlib） | backend-logic | 独立（engine.py ANN section / embeddings.py / related_pages.py / pyproject.toml） |

## v1.14.0 Wave 2 — benchmark 更新（依赖 S-2）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-S-3 | benchmark 更新（cache.stats() 真实度量 + ANN vs cosine P99 + 规模延迟曲线） | T-F-S-2 | benchmark 更新就绪 → v1.14.0 可交付 |

## v1.14.0 共享资源串行
- `scripts/benchmark_semantic.py`：T-F-S-1（Wave 1，阈值读 env 小改）→ T-F-S-3（Wave 2，大规模更新 cache/ANN/scale）。Wave 1→2 串行，无并行写冲突。
- `src/saw/engines/query/engine.py`：T-F-S-1（cache 条件分支）+ T-F-S-2（cosine→ANN 切换）均 Wave 1 写同文件不同 section。05 实施须 worktree 隔离 + 合并协调（不同代码段，merge 可行）。

## v1.14.0 Wave 1 文件冲突分析
| 文件 | Wave 1 写入方 | 冲突? |
|---|---|---|
| src/saw/engines/query/engine.py | T-F-S-1 + T-F-S-2 | 同文件不同 section（cache 条件分支 vs cosine→ANN），需合并协调 |
| src/saw/config/settings.py | T-F-S-1 | 否 |
| scripts/benchmark_semantic.py | T-F-S-1 | 否（S-3 在 Wave 2） |
| CHANGELOG.md | T-F-S-1 | 否 |
| tests/unit/test_semantic_cache_config.py | T-F-S-1 | 否（新建） |
| src/saw/adapters/embeddings.py | T-F-S-2 | 否 |
| src/saw/engines/query/related_pages.py | T-F-S-2 | 否 |
| pyproject.toml | T-F-S-2 | 否 |
| tests/unit/test_ann_search.py | T-F-S-2 | 否（新建） |
| tests/unit/test_related_pages_ann.py | T-F-S-2 | 否（新建） |

## v1.14.0 里程碑
- M-SEM-PERF-1（Wave 1）：cache 阈值可配 + ANN 索引就绪（cosine→ANN 规模驱动切换 + numpy fallback）。
- M-SEM-PERF-2（Wave 2）：benchmark 更新就绪（cache 真实度量 + ANN vs cosine + 规模曲线）→ v1.14.0 可交付。

---

# v1.15.0 波次（agent/link 能力，2026-09-06）

> 源自 PRD-agent-link-v1.15.0 + 02 delta + ADR-015。3 Task，1 Wave 全并行。DAG 无环（3 Task 互相独立，无边）。

## v1.15.0 Wave 1 — 全并行（3 Task，无依赖）
| task_id | 描述 | 类型 | 并行性 |
|---|---|---|---|
| T-F-T-1 | 自定义 agent 角色注册（YAML 加载 + additive 合并 + CLI/REST 可见 + workflow validate） | backend-logic | 独立（agents 模块 + workflow_parser + REST list_agents） |
| T-F-T-2 | L2 links auto-apply（saw links apply + dry-run/confirm + ## Related 写回 + 去重） | backend-logic | 独立（links_cmd + WikiRepository 复用） |
| T-F-T-3 | M2 agent 活动聚合（event_bus subscriber + 内存计数器 + REST activity 端点 + CLI） | backend-logic | 独立（activity_tracker 新建 + app lifespan + REST activity 端点） |

## v1.15.0 共享资源串行
- 无共享资源串行约束。3 Task 全独立，Wave 1 全并行。

## v1.15.0 Wave 1 文件冲突分析
| 文件 | Wave 1 写入方 | 冲突? |
|---|---|
| src/saw/api/routes/collaborate.py | T-F-T-1 + T-F-T-3 | 同文件不同端点（T-1: list_agents custom 标记 / T-3: activity 端点 + activity_summary），需合并协调 |
| src/saw/drivers/cli/commands/agents_cmd.py | T-F-T-1 + T-F-T-3 | 同文件不同子命令（T-1: custom 标注 / T-3: activity 子命令），需合并协调 |
| tests/unit/test_agents_rest.py | T-F-T-1 + T-F-T-3 | 同测试文件不同用例（T-1: AC-A-4 / T-3: AC-C-3/4），需合并协调 |
| 其余文件 | 各 Task 独占 | 否 |

## v1.15.0 里程碑
- M-AGENT-LINK（Wave 1）：自定义角色注册 + links auto-apply + 活动聚合就绪 → v1.15.0 可交付。

---

# v1.16.0 波次（realtime 仪表盘 v4.3，2026-09-07）

> 源自 PRD-dashboard-v1.16.0 + 02 delta + ADR-016。3 Task，2 Wave。DAG U-1+U-2→U-3 无环。纯前端消费 v1.15.0 后端 REST 端点。

## v1.16.0 Wave 1 — agent roster + workflow 列表（2 路并行）
| task_id | 描述 | 类型 | 并行性 |
|---|---|---|---|
| T-F-U-1 | agent roster+activity 仪表盘（Dashboard.tsx 接 react-query 拉 GET /api/v1/agents + /agents/{name}/activity + AgentList/AgentCard 扩展） | frontend | 独立（AgentRosterSection + agents hooks） |
| T-F-U-2 | workflow 运行态视图（新建 WorkflowList/WorkflowRow + useWorkflows/useWorkflowStatus 拉 GET /api/v1/workflows + /workflows/{id}/status） | frontend | 独立（WorkflowRuntimeSection + workflow hooks） |

## v1.16.0 Wave 2 — 实时更新编排（依赖 U-1+U-2）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-U-3 | 实时更新（useWebSocket 扩展 invalidateQueries(['workflows']) + polling 15s 降级横幅 + 重连恢复 + 手动刷新） | T-F-U-1, T-F-U-2 | 实时更新 + 降级横幅就绪 → v1.16.0 可交付 |

## v1.16.0 共享资源串行
- `web/src/pages/Dashboard.tsx`：T-F-U-1（AgentRosterSection）+ T-F-U-2（WorkflowRuntimeSection）Wave 1 同文件不同区域 → worktree 隔离 + 合并协调。
- `web/src/types/api.ts`：T-F-U-1（AgentRosterEntry 等）+ T-F-U-2（WorkflowExecution 等）Wave 1 同文件不同类型 → 合并协调。
- `web/src/hooks/useWebSocket.ts`：T-F-U-3（Wave 2）扩展追加 invalidateQueries(['workflows']）。Wave 1→2 串行。

## v1.16.0 Wave 1 文件冲突分析
| 文件 | Wave 1 写入方 | 冲突? |
|---|---|---|
| web/src/pages/Dashboard.tsx | T-F-U-1 + T-F-U-2 | 同文件不同区域（AgentRosterSection vs WorkflowRuntimeSection），需合并协调 |
| web/src/types/api.ts | T-F-U-1 + T-F-U-2 | 同文件不同类型定义，需合并协调 |
| web/src/components/dashboard/AgentList.tsx | T-F-U-1 | 否 |
| web/src/components/dashboard/AgentCard.tsx | T-F-U-1 | 否 |
| web/src/components/dashboard/WorkflowList.tsx | T-F-U-2 | 否（新建） |
| web/src/components/dashboard/WorkflowRow.tsx | T-F-U-2 | 否（新建） |
| web/src/hooks/useAgents.ts | T-F-U-1 | 否（新建） |
| web/src/hooks/useAgentActivity.ts | T-F-U-1 | 否（新建） |
| web/src/hooks/useWorkflows.ts | T-F-U-2 | 否（新建） |
| web/src/hooks/useWorkflowStatus.ts | T-F-U-2 | 否（新建） |
| web/tests/test_agent_*.test.tsx | T-F-U-1 | 否（4 文件独占） |
| web/tests/test_workflow_*.test.tsx | T-F-U-2 | 否（3 文件独占） |

## v1.16.0 里程碑
- M-DASHBOARD-1（Wave 1）：agent roster + activity 仪表盘 + workflow 运行态列表就绪（REST 消费 + react-query polling 15s）。
- M-DASHBOARD-2（Wave 2）：实时更新编排就绪（WS invalidateQueries 扩展 + polling 降级横幅 + 重连恢复）→ v1.16.0 可交付。

---

# v1.17.0 波次（desktop 完成 v4.4，2026-09-07）

> 源自 PRD-desktop-v1.17.0 + 02 delta + ADR-017。4 Task，2 Wave。DAG V-1→{V-2,V-3,V-4} 无环。desktop 0.1.0→1.0.0 版本对齐 + tauri build 验证 + 后端端口收敛。

## v1.17.0 Wave 1 — 版本 bump + 配置收敛（串行先行）
| task_id | 描述 | 类型 | 里程碑 |
|---|---|---|---|
| T-F-V-1 | 4 文件版本号 0.1.0→1.0.0 + tauri.conf.json 15 项配置一致性审查 | infra | 1.0.0 版本基线就绪 |

## v1.17.0 Wave 2 — 验证 + 构建 + 端口（3 路全并行）
| task_id | 描述 | 依赖 | 可并行性 |
|---|---|---|---|
| T-F-V-2 | web 仪表盘集成验证（frontendDist + web/dist 产出 + devUrl + @tauri-apps/api） | T-F-V-1 | 独立（只读 tauri.conf.json + web/dist） |
| T-F-V-3 | tauri build 验证（cargo build --release + bundle 原生包） | T-F-V-1 | 独立（只读 Cargo.toml + 执行 build） |
| T-F-V-4 | 后端协同 + 端口收敛（vite proxy 8080→8000 + CORS +5173 + prod 连接） | T-F-V-1 | 独立（写 vite.config.ts + web_cmd.py + app.py） |

## v1.17.0 共享资源串行
- `desktop/src-tauri/tauri.conf.json`：T-F-V-1（Wave 1，bump version）→ T-F-V-2/V-3（Wave 2，只读验证）。Wave 1→2 串行。
- `desktop/src-tauri/Cargo.toml`：T-F-V-1（Wave 1，bump version）→ T-F-V-3（Wave 2，build 依赖 1.0.0）。Wave 1→2 串行。

## v1.17.0 Wave 2 文件冲突分析
| 文件 | Wave 2 写入方 | 冲突? |
|---|---|---|
| desktop/src-tauri/tauri.conf.json | T-F-V-2（只读）+ T-F-V-3（只读） | 否（V-1 Wave 1 已 bump） |
| web/vite.config.ts | T-F-V-4 | 否（V-2 只读不写） |
| src/saw/drivers/cli/commands/web_cmd.py | T-F-V-4 | 否 |
| src/saw/drivers/web/app.py | T-F-V-4 | 否 |
| tests/unit/test_*.py | 各 Task 独占 | 否（新建文件各独占） |

## v1.17.0 里程碑
- M-DESKTOP-1（Wave 1）：1.0.0 版本基线就绪（4 文件版本一致 + 配置审查通过）。
- M-DESKTOP-2（Wave 2）：仪表盘集成验证 + tauri build 原生包产出 + 端口收敛 CORS 扩展就绪 → v1.17.0 可交付。
