# Coverage Report — AC 覆盖与缺口

> 每条 PRD §6 AC 映射 ≥1 用例。未映射 AC 显式标缺口，不掩盖。

## AC 覆盖
| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-E2E-1 | 端到端冒烟 fresh 全 PASS 退出 0 | F-A-1, F-A-6 | test_smoke_skeleton_pass, test_ci_smoke_gate | covered |
| AC-E2E-2 | 离线降级 fallback PASS | F-A-5 | test_smoke_offline_fallback, test_smoke_offline_nl_degraded | covered |
| AC-ALIGN-1 | 宣称与代码 0 diff | F-B-1 | test_claim_diff_mcp, test_claim_diff_clean | covered |
| AC-ALIGN-2 | 未验证项标 [unverified] | F-B-2, F-B-3 | test_capabilities_unverified_marked, test_doc_aligned_or_marked | covered |
| AC-SEC-1 | 0 裸 write 路由 | F-C-1 | test_no_unprotected_write_routes | covered |
| AC-SEC-2 | receipt 链不断裂 | F-C-2 | test_receipt_chain_intact, test_receipt_coverage | covered |
| AC-SEC-3 | 超 100/h→429+Retry-After | F-C-3 | test_rate_limit_429 | covered |
| AC-OBS-1 | trace_id 贯穿 | F-D-1, F-D-2 | test_trace_id_propagated, test_logger_via_init | covered |
| AC-OBS-2 | /health/ready engine 异常非200 | F-D-3 | test_health_ready_reflects_engine | covered |
| AC-TEST-1 | 核心 ≥80% 否则红 | F-E-2 | test_coverage_gate_core | covered |
| AC-TEST-2 | CI 冒烟全过 | F-A-6, F-E-3 | test_ci_smoke_gate, test_ci_integrated_runs | covered |

## 汇总
- PRD AC 总数：11
- 已覆盖：11（100%）
- 缺口：0

## [TBD] 留尾（非 AC 缺口，实现期待验）
- F-C-2 receipt 覆盖率（核验后补用例）
- F-C-5 前端 token 互通（实机核验后补）
- F-E-1 覆盖率基线数值（实测后定）
- F-A-1 冒烟命令名

## v1.10.0 delta（embedding 语义搜索，12 AC）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-EMB-1 | embedding 索引随 ingest 写入 | F-N-1 | test_embedding_index.py（importorskip） | [TBD-impl] |
| AC-EMB-2 | 无 [learn] 时不报错 | F-N-1 | test_embedding_degradation.py（mock） | [TBD-impl] |
| AC-EMB-3 | 存量重建索引 | F-N-1 | test_embedding_index.py（importorskip） | [TBD-impl] |
| AC-SEM-1 | 语义检索返回同义结果 | F-N-2 | test_semantic_search.py（importorskip） | [TBD-impl] |
| AC-SEM-2 | 无 [learn] 降级 BM25 | F-N-2 | test_embedding_degradation.py（mock） | [TBD-impl] |
| AC-SEM-3 | 空索引优雅处理 | F-N-2 | test_semantic_search.py（importorskip） | [TBD-impl] |
| AC-LINK-1 | suggest 含语义相似页面 | F-N-3 | test_related_pages_embedding.py（importorskip） | [TBD-impl] |
| AC-LINK-2 | 无 [learn] 保持 3-signal | F-N-3 | test_embedding_degradation.py（mock） | [TBD-impl] |
| AC-LINK-3 | 语义不相似排名下降 | F-N-3 | test_related_pages_embedding.py（importorskip） | [TBD-impl] |
| AC-TEST-1 | CI skip embedding 测试 | F-N-4 | test_embedding_index.py（importorskip skip） | [TBD-impl] |
| AC-TEST-2 | 本地 embedding 测试 pass | F-N-4 | test_embedding_index.py（importorskip pass） | [TBD-impl] |
| AC-TEST-3 | coverage 不回归 | F-N-4 | test_ci_workflow.py（扩） | [TBD-impl] |

### v1.10.0 汇总
- PRD AC 总数（本轮）：12
- 已映射：12（100%）
- 缺口：0
- 全部 [TBD-impl]：05 实施后落定

### 全局汇总（v1.0 + v1.10.0）
- PRD AC 总数：11（v1.0）+ 12（v1.10.0）= 23
- 已覆盖：11（v1.0 covered）+ 12（v1.10.0 mapped [TBD-impl]）= 23
- 缺口：0

## v1.11.0 delta（债务收口 IV / bug fix，12 AC）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-CACHE-1 | semantic cache 命中 | F-O-1 | test_semantic_cache.py（mock） | [TBD-impl] |
| AC-CACHE-2 | semantic cache workspace 隔离 | F-O-1 | test_semantic_cache.py（mock） | [TBD-impl] |
| AC-CACHE-3 | semantic cache 索引变更失效 | F-O-1 | test_semantic_cache.py（mock） | [TBD-impl] |
| AC-CACHE-4 | semantic fallback 不缓存 | F-O-1 | test_semantic_cache.py（mock） | [TBD-impl] |
| AC-COV-1 | compile/compiler 深覆盖 | F-O-2 | tests/unit/engines/compile/（新建 7 文件） | [TBD-impl] |
| AC-COV-2 | fail_under 棘轮 65 | F-O-2 | test_coverage_config.py | [TBD-impl] |
| AC-WF-1 | REST 读 DB | F-O-3 | test_workflow_rest_db.py | [TBD-impl] |
| AC-WF-2 | REST merge live | F-O-3 | test_workflow_rest_db.py | [TBD-impl] |
| AC-WF-3 | CLI/REST 语义一致 | F-O-3 | test_workflow_rest_db.py | [TBD-impl] |
| AC-SPEC-1 | Spec 命名回更 | F-O-4 | test_spec_naming.py | [TBD-impl] |
| AC-SPEC-2 | 实现不变 | F-O-4 | test_spec_naming.py | [TBD-impl] |
| AC-HASH-1 | hash 三处一致 | F-O-4 | test_hash_consistency.py | [TBD-impl] |

### v1.11.0 汇总
- PRD AC 总数（本轮）：12
- 已映射：12（100%）
- 缺口：0
- 全部 [TBD-impl]：05 实施后落定

### 全局汇总（v1.0 + v1.10.0 + v1.11.0）
- PRD AC 总数：11（v1.0）+ 12（v1.10.0）+ 12（v1.11.0）= 35
- 已覆盖：11（v1.0 covered）+ 12（v1.10.0 [TBD-impl]）+ 12（v1.11.0 [TBD-impl]）= 35
- 缺口：0

## v1.12.0 delta（embedding API 重构，9 AC）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-EA-1 | API 配置可用时语义检索 | F-Q-1 | test_embedding_index.py（改 API mock） | [TBD-impl] |
| AC-EA-2 | API 未配置时降级 | F-Q-1 | test_embedding_degradation.py（扩 API 不可用） | [TBD-impl] |
| AC-DIM-1 | 维度变更触发重建 | F-Q-2 | test_embedding_index.py（改 API mock + dim 变更） | [TBD-impl] |
| AC-DIM-2 | ingest 写入正确 model | F-Q-2 | test_embedding_index.py（改 assert model 列动态） | [TBD-impl] |
| AC-FB-1 | 本地 ST fallback | F-Q-3 | test_semantic_search.py（改 mock API 不可用 + ST 可用） | [TBD-impl] |
| AC-FB-2 | 无 ST 走 API | F-Q-3 | test_semantic_search.py（改 mock API + ST 不可用） | [TBD-impl] |
| AC-TEST-1 | CI embedding 测试全 pass | F-Q-4 | test_embedding_index.py + test_semantic_search.py + test_related_pages_embedding.py（去 importorskip） | [TBD-impl] |
| AC-TEST-2 | CI 无 importorskip | F-Q-4 | test_ci_workflow.py（扩） | [TBD-impl] |
| AC-TEST-3 | benchmark 可执行 | F-Q-4 | test_embedding_benchmark.py（新建） | [TBD-impl] |

### v1.12.0 汇总
- PRD AC 总数（本轮）：9
- 已映射：9（100%）
- 缺口：0
- 全部 [TBD-impl]：05 实施后落定

### 全局汇总（v1.0 + v1.10.0 + v1.11.0 + v1.12.0）
- PRD AC 总数：11（v1.0）+ 12（v1.10.0）+ 12（v1.11.0）+ 9（v1.12.0）= 44
- 已覆盖：11（v1.0 covered）+ 12（v1.10.0 [TBD-impl]）+ 12（v1.11.0 [TBD-impl]）+ 9（v1.12.0 [TBD-impl]）= 44
- 缺口：0

## v1.13.0 delta（E2E 收尾轮，16 AC）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-A-1 | 目录递归 ingest | F-R-1 | test_ingest_directory.py | covered |
| AC-A-2 | 空目录 | F-R-1 | test_ingest_directory.py | covered |
| AC-A-3 | 部分失败 | F-R-1 | test_ingest_directory.py | covered |
| AC-A-4 | 子目录递归 | F-R-1 | test_ingest_directory.py | covered |
| AC-A-5 | 排除 SAW 内部目录 | F-R-1 | test_ingest_directory.py | covered |
| AC-B-1 | 真实 API 召回 | F-R-2 | test_embedding_benchmark.py（@benchmark_e2e） | covered |
| AC-B-2 | P99 延迟 | F-R-2 | test_embedding_benchmark.py（@benchmark_e2e） | covered |
| AC-B-3 | cache 命中率 | F-R-2 | test_embedding_benchmark.py（@benchmark_e2e） | covered |
| AC-B-4 | vLLM 不可达报错 | F-R-2 | test_embedding_benchmark.py | covered |
| AC-C-1 | 别名兼容 | F-R-3 | test_workflow_rest_db.py | covered |
| AC-C-2 | CHANGELOG 存在 | F-R-3 | test_changelog.py | covered |
| AC-C-3 | CHANGELOG 回溯 | F-R-3 | test_changelog.py | covered |
| AC-D-1 | fail_under 提升 | F-R-4 | test_coverage_config.py | covered |
| AC-D-2 | 实际覆盖率达标 | F-R-4 | CI pytest --cov 67% | covered |
| AC-E-1 | Q1 闭合标注 | F-R-5 | test_retrospective_closure.py | covered |
| AC-E-2 | Q3 闭合标注 | F-R-5 | test_retrospective_closure.py | covered |

### v1.13.0 汇总
- PRD AC 总数（本轮）：16
- 已覆盖：16（100%）
- 缺口：0

### 全局汇总（v1.0 + v1.10.0 + v1.11.0 + v1.12.0 + v1.13.0）
- PRD AC 总数：44 + 16 = 60
- 已覆盖：44 + 16 = 60
- 缺口：0

## v1.14.0 delta（semantic 性能优化，15 AC）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-A-1 | cache 禁用（hits 不增加） | F-S-1 | test_semantic_cache_config.py（mock） | [TBD-impl] |
| AC-A-2 | cache 启用默认（hits 增加） | F-S-1 | test_semantic_cache_config.py（mock） | [TBD-impl] |
| AC-A-3 | 阈值跳过写入 | F-S-1 | test_semantic_cache_config.py（mock） | [TBD-impl] |
| AC-A-4 | 向后兼容 | F-S-1 | test_semantic_cache_config.py（mock） | [TBD-impl] |
| AC-A-5 | keyword cache 不受影响 | F-S-1 | test_semantic_cache_config.py（mock） | [TBD-impl] |
| AC-B-1 | ANN 自动切换 | F-S-2 | test_ann_search.py（mock） | [TBD-impl] |
| AC-B-2 | 小规模 cosine | F-S-2 | test_ann_search.py（mock） | [TBD-impl] |
| AC-B-3 | ANN 降级 | F-S-2 | test_ann_search.py（mock） | [TBD-impl] |
| AC-B-4 | 召回一致性 ≥95% [TBD] | F-S-2 | test_ann_search.py（marker） | [TBD-impl] |
| AC-B-5 | related_pages 复用 ANN | F-S-2 | test_related_pages_ann.py（mock） | [TBD-impl] |
| AC-C-1 | cache 命中真实度量 | F-S-3 | test_embedding_benchmark.py（mock） | [TBD-impl] |
| AC-C-2 | ANN vs cosine 对比 | F-S-3 | test_embedding_benchmark.py（@benchmark_e2e） | [TBD-impl] |
| AC-C-3 | 规模延迟曲线 | F-S-3 | test_embedding_benchmark.py（@benchmark_e2e） | [TBD-impl] |
| AC-C-4 | vLLM 不可达报错退出 | F-S-3 | test_embedding_benchmark.py | [TBD-impl] |
| AC-C-5 | cache 单元测试 CI 可跑 | F-S-3 | test_embedding_benchmark.py（mock） | [TBD-impl] |

### v1.14.0 汇总
- PRD AC 总数（本轮）：15
- 已映射：15（100%）
- 缺口：0
- 全部 [TBD-impl]：05 实施后落定

## v1.15.0 delta（agent/link 能力，12 AC）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-A-1 | 自定义角色注册并出现在 roster | F-T-1 | test_custom_agents.py（mock .saw/agents/） | [TBD-impl] |
| AC-A-2 | 自定义角色被 workflow 引用 | F-T-1 | test_custom_agents.py（workflow YAML validate） | [TBD-impl] |
| AC-A-3 | 重名角色被拒绝 | F-T-1 | test_custom_agents.py（name=Librarian 重名跳过） | [TBD-impl] |
| AC-A-4 | REST 端点返回自定义角色 | F-T-1 | test_agents_rest.py（GET /api/v1/agents custom:true） | [TBD-impl] |
| AC-B-1 | dry-run 预览不写回 | F-T-2 | test_links_apply.py（无 --confirm 文件不变） | [TBD-impl] |
| AC-B-2 | confirm 写回 | F-T-2 | test_links_apply.py（## Related + frontmatter related） | [TBD-impl] |
| AC-B-3 | 已有链接不重复 | F-T-2 | test_links_apply.py（[[page-b]] skipped） | [TBD-impl] |
| AC-B-4 | apply 后 audit 无新断链 | F-T-2 | test_links_apply.py（audit 无 broken） | [TBD-impl] |
| AC-C-1 | activity 端点返回聚合数据 | F-T-3 | test_agent_activity.py（mock event calls≥1） | [TBD-impl] |
| AC-C-2 | 无活动的 agent 返回空活动 | F-T-3 | test_agent_activity.py（calls=0, null） | [TBD-impl] |
| AC-C-3 | 不存在的 agent 返回 404 | F-T-3 | test_agents_rest.py（404 not found） | [TBD-impl] |
| AC-C-4 | agents 端点含 activity_summary | F-T-3 | test_agents_rest.py（activity_summary calls=3） | [TBD-impl] |

### v1.15.0 汇总
- PRD AC 总数（本轮）：12
- 已映射：12（100%）
- 缺口：0
- 全部 [TBD-impl]：05 实施后落定

### 全局汇总（v1.0 + v1.10.0 + v1.11.0 + v1.12.0 + v1.13.0 + v1.14.0 + v1.15.0）
- PRD AC 总数：75 + 12 = 87
- 已覆盖：75 + 12（[TBD-impl]）= 87
- 缺口：0

## v1.16.0 delta（realtime 仪表盘 v4.3，8 AC + 1 NFR）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-D-1 | roster 表渲染 | F-U-1 | test_agent_roster_render.test.tsx（vitest mock） | [TBD-impl] |
| AC-D-2 | activity 详情展开 | F-U-1 | test_agent_activity_detail.test.tsx（vitest mock） | [TBD-impl] |
| AC-D-3 | activity null 降级 | F-U-1 | test_agent_activity_null.test.tsx（vitest mock） | [TBD-impl] |
| AC-D-4 | activity 404 处理 | F-U-1 | test_agent_activity_404.test.tsx（vitest mock） | [TBD-impl] |
| AC-D-5 | workflow 列表渲染 | F-U-2 | test_workflow_list_render.test.tsx（vitest mock） | [TBD-impl] |
| AC-D-6 | workflow running 置顶 | F-U-2 | test_workflow_running_top.test.tsx（vitest mock） | [TBD-impl] |
| AC-D-7 | WS workflow_progress 更新行 | F-U-2 | test_workflow_ws_update.test.tsx（vitest mock） | [TBD-impl] |
| AC-D-8 | WS 断连降级 | F-U-3 | test_ws_disconnect_polling_degraded.test.tsx（vitest mock） | [TBD-impl] |
| AC-D-9 | 后端不回归 | 系统级 NFR | pytest ≥ 2220 + ruff 0 + coverage ≥ 67% + smoke 6/6 | [TBD-impl] |

### v1.16.0 汇总
- PRD AC 总数（本轮）：8 + 1（NFR）= 9
- 已映射：8 + 1 = 9（100%）
- 缺口：0
- 全部 [TBD-impl]：05 实施后落定

### 全局汇总（v1.0 + v1.10.0 + v1.11.0 + v1.12.0 + v1.13.0 + v1.14.0 + v1.15.0 + v1.16.0）
- PRD AC 总数：87 + 9 = 96
- 已覆盖：87 + 9（[TBD-impl]）= 96
- 缺口：0

## v1.17.0 delta（desktop 完成 v4.4，9 AC）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-V-1 | 4 文件 version=1.0.0 一致 | F-V-1 | test_version_consistency.py（json + re） | [TBD-impl] |
| AC-V-2 | tauri.conf.json 配置一致性 | F-V-1 | test_tauri_config_consistency.py（json.load） | [TBD-impl] |
| AC-W-1 | web/dist prod 集成 | F-V-2 | test_web_dist_integration.py（文件检查 + json） | [TBD-impl] |
| AC-W-2 | dev 模式 localhost:5173 | F-V-2 | test_web_dev_integration.py（json.load） | [TBD-impl] |
| AC-B-1 | tauri build 退出码 0 + 产出原生包 | F-V-3 | test_tauri_build_smoke.py（subprocess，skipif no cargo） | [TBD-impl] |
| AC-B-2 | bundle.targets 含 app/dmg | F-V-3 | test_bundle_targets_config.py（json.load） | [TBD-impl] |
| AC-C-1 | vite proxy 端口收敛 8080→8000 | F-V-4 | test_port_convergence.py（re 文本匹配） | [TBD-impl] |
| AC-C-2 | prod 后端连接配置 | F-V-4 | test_prod_backend_connection.py（文件检查） | [TBD-impl] |
| AC-C-3 | CORS 含 localhost:5173 | F-V-4 | test_cors_expansion.py（re 文本匹配） | [TBD-impl] |

### v1.17.0 汇总
- PRD AC 总数（本轮）：9
- 已映射：9（100%）
- 缺口：0
- 全部 [TBD-impl]：05 实施后落定

### 全局汇总（v1.0 + v1.10.0 + v1.11.0 + v1.12.0 + v1.13.0 + v1.14.0 + v1.15.0 + v1.16.0 + v1.17.0）
- PRD AC 总数：96 + 9 = 105
- 已覆盖：96 + 9（[TBD-impl]）= 105
- 缺口：0

## v1.18.0 delta（per-request workspace 注入 + O4 tag 流程修复，7 AC）

| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-WS-1 | contextvar 注入生效（X-Workspace-Id: team-a → team-a 数据） | F-W-1 | test_workspace_contextvar.py | [TBD-impl] |
| AC-WS-2 | fallback 默认值（无 header → default） | F-W-1 | test_workspace_contextvar.py | [TBD-impl] |
| AC-WS-3 | 跨 workspace 不泄漏（workspace A 搜索不含 B claim） | F-W-1 | test_workspace_isolation.py | [TBD-impl] |
| AC-WS-4 | CLI 不受影响（saw query 用 default workspace） | F-W-1 | test_workspace_cli_compat.py | [TBD-impl] |
| AC-WS-5 | 构造签名不变（QueryEngine.__init__ 参数列表一致） | F-W-1 | test_workspace_signature.py | [TBD-impl] |
| AC-O4-1 | tag 指向 release commit（git log v1.18.0 → release commit） | F-W-2 | test_o4_tag_flow.py（06 时执行） | [TBD-impl] |
| AC-O4-2 | GitHub Release 关联（Release tag → release commit） | F-W-2 | test_o4_tag_flow.py（06 时执行） | [TBD-impl] |

### v1.18.0 汇总
- PRD AC 总数（本轮）：7
- 已映射：7（100%）
- 缺口：0
- 全部 [TBD-impl]：05 实施后落定

### 全局汇总（v1.0 + v1.10.0 + v1.11.0 + v1.12.0 + v1.13.0 + v1.14.0 + v1.15.0 + v1.16.0 + v1.17.0 + v1.18.0）
- PRD AC 总数：105 + 7 = 112
- 已覆盖：105 + 7（[TBD-impl]）= 112
- 缺口：0
