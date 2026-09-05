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
