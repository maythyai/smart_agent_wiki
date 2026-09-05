# 复盘 — v1.10.0 embedding 语义搜索（2026-09-04）

> 07 闭环校验。findings 回流下一轮 01。前置：06-ship done（v1.10.0 tagged @3865c75，本地未 push）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-embedding-v1.10.0 Approved；4 SPEC-F-N-1..4 1:1 对应 F-N-1..4（`.csp/specs/SPEC-F-N-{1..4}.md`，feature_id 字段一一匹配）|
| Spec → Task | ✅ | WBS/TASKS-DELTA-v1.10.0 4 Task（T-F-N-1..4）1:1 对应 4 Spec；DAG N-1→{N-2,N-3,N-4} 无环 |
| Task → commit | ✅ | git log：`ecbdb75`(feat F-N-1) / `9660ecc`(feat F-N-2) / `3b2039e`(feat F-N-3) / `e7fb6c6`(test F-N-4) + `15bb5fe`(chore(csp) reconcile) + `3865c75`(release v1.10.0) |
| AC → 测试 | ✅ | 12 AC 全映射（`.csp/traceability/COVERAGE-REPORT.md` v1.10.0 delta，12/12 mapped）；测试文件存在：`tests/unit/test_embedding_index.py` / `test_semantic_search.py` / `test_related_pages_embedding.py` / `test_embedding_degradation.py`（importorskip 3 文件 skip + degradation mock 4 测试 pass） |
| commit → tag | ✅ | `git tag -l v1.10.0` 确认 annotated tag 指向 `3865c75`（release commit，本地未 push 远端） |
| 测试/lint | ✅ | 1993 passed / 6 skipped（3 原有 + 3 新 embedding importorskip）/ 0 failed；ruff check src/ tests/ 0 errors；saw smoke 6/6 |
| 构建 | ✅ | wheel `smart_agent_wiki-1.10.0-py3-none-any.whl`（820KB）+ sdist；pyproject.toml version=1.10.0 |

### 闭环校验诚实标注
- 12 AC 中 7 条（AC-EMB-1/3, AC-SEM-1/3, AC-LINK-1/3, AC-TEST-2）的测试以 `pytest.importorskip("sentence_transformers")` 落地，**本环境 sentence_transformers 未装 → 全部 skip**，未实际执行。
- 仅降级路径（AC-EMB-2 / AC-SEM-2 / AC-LINK-2）+ CI 结构断言（AC-TEST-1 / AC-TEST-3）经 mock 通过。
- **embedding E2E 未经真实运行验证**（见 finding N1）。

## v1.10.0 度量
- 4 Feature done（embedding 索引 / 语义检索 / smart-linking embedding 信号 / importorskip 测试策略）
- 新增测试：6（3 importorskip-skip + 3 degradation-mock pass）；ci_workflow 扩 importorskip 覆盖断言
- 全量 1993 passed（+6 vs v1.9.0 的 1987）；6 skipped（+3 vs v1.9.0 的 3）
- coverage 未实测（DEV-LOG 未跑 coverage step）；fail_under=64 持（v1.7.0 ratchet）。新增为 CLI 薄 wiring + importorskip skip，预估 coverage 未变（~64.2%）
- 新增 CLI：`saw search --mode semantic` + `saw rebuild-embeddings` 顶层命令
- 新增 REST：`GET /api/v1/search?mode=semantic`
- 复用既有 `src/saw/adapters/embeddings.py`（embed_texts/cosine_similarity）+ Write Queue sink 范式 + detect_tier FULL 检测——**无新引擎、无新依赖、无新外部 DB**（embedding_store 表用本地 SQLite BLOB + numpy cosine）
- migration v10（`_create_embedding_store`）追加，表含 doc_id/entity_type/model/vector/dim/workspace_id/created_at，PK (doc_id, workspace_id)

## Findings（回流下一轮）

### N1 — embedding E2E 未验证 [High / P1]
sentence_transformers 未安装（硬约定 #12"缺依赖须用户确认"），3 个 importorskip 测试文件（7 个测试）在 CI 全 skip。AC-EMB-1/3、AC-SEM-1/3、AC-LINK-1/3 的"真实语义检索/索引"路径**未经真实运行验证**——仅降级路径（mock）pass。
- **证据**：`.csp/artifacts/verify/test-results.md`（"sentence_transformers is NOT installed"）；`.csp/artifacts/implement.md` v1.10.0 节（"实际 embedding E2E 须用户装 [learn] extra"）；`tests/unit/test_embedding_index.py` importorskip 行。
- **影响**：本轮"embedding 语义搜索 done"的 done 定义含 caveat——真实 E2E 须用户 `pip install -e ".[learn]"` 后复跑 `pytest tests/unit/test_embedding*.py` 验证。若模型下载失败/维度异常/语义召回不达预期，本轮功能可能需返工。
- **严重度**：High（核心功能未经真实环境验证）+ 置信度 high。
- **优先级**：P1（首版必修——须用户确认装 SDK 后 E2E 验证）。
- **建议**：用户本地装 `[learn]` extra 后跑 `pytest tests/unit/test_embedding*.py tests/unit/test_semantic_search.py tests/unit/test_related_pages_embedding.py -v`；若 fail 须回流 05 修复。CI 若装 SDK 则取消 importorskip。
- **回流**：下一轮 01（决策是否装 SDK + benchmark）或用户本地验证后关闭。

### N2 — coverage 未增，K1 续留 [Medium / P2]
v1.10.0 新增测试为 CLI 薄 wiring + importorskip skip，coverage 未实测但预估未变（~64.2%）。compile/compiler.py 仍 17%（v1.7.0 K1 finding 续留第三轮）。fail_under=64 持。
- **证据**：`pyproject.toml` `[tool.coverage.report]` fail_under 注释（K1 v1.8.0）；`.csp/artifacts/implement.md` v1.10.0 节无 coverage step。
- **影响**：coverage 北极星 65 仍差 ~1pp；compile/compiler 17% 是最后洼地。
- **严重度**：Medium（技术债，非功能缺陷）。
- **优先级**：P2。
- **建议**：下一轮专项深覆盖 compile/compiler.py（复杂编译器，高成本），或随新能力自然增长。
- **回流**：下一轮 01（债务收口候选）。

### N3 — K2 per-request workspace 注入续留 [Medium / P2]
QueryEngine 仍 startup 单例 default workspace；semantic mode 复用 `self._workspace_id`（引擎级），非请求级。web 路径的 per-request workspace 注入未做（v1.7.0 K2 续留第二轮）。
- **证据**：`src/saw/engines/query/engine.py:58`（`__init__` workspace_id 参数）；`.csp/artifacts/implement.md` v1.7.0 节（"请求级 ws 注入留后续架构演进"）。
- **影响**：local-first 单租户场景无问题；多租户 web 部署时 semantic 检索仍可能跨 workspace（须 web 层重建 engine 实例）。
- **严重度**：Medium（架构债，local-first 不阻塞）。
- **优先级**：P2。
- **建议**：v2.0 平台化周期做 request context → engine 注入（需架构演进）。
- **回流**：下一轮 01（v2.0 候选）。

### N4 — 向量检索性能 P99 [TBD] 未 benchmark [Medium / P2]
PRD NFR 写"向量检索 P99 延迟 [TBD]（须优于或接近 BM25 毫秒级）"，本轮未 benchmark。semantic mode 不走 cache（`_keyword_search` 有 F-QS-07 cache，`_semantic_search` 每次全量计算 cosine）。
- **证据**：`docs/prd/PRD-embedding-v1.10.0.md` §4 NFR（"[TBD]"）；`.csp/artifacts/implement.md` v1.10.0 节（"semantic mode 不走 cache"）；`src/saw/engines/query/engine.py`（`_semantic_search` 无 cache 路径）。
- **影响**：规模 >10K docs 时 semantic 检索可能慢于 BM25（全量 cosine 扫描）；无 benchmark 无法定 baseline。
- **严重度**：Medium（性能债，小规模无问题）。
- **优先级**：P2。
- **建议**：用户装 SDK 后跑 `saw search --mode semantic` benchmark 对比 BM25 P99；若不达标加 ANN 索引（如 sqlite-vss）或相似度缓存。
- **回流**：下一轮 01（benchmark 候选）。

### N5 — CLI 子命令路径偏离 Spec [Low / P3]
SPEC-F-N-1 写 `saw search rebuild-embeddings`（子命令），实际改为顶层独立命令 `saw rebuild-embeddings`（因 `search` 是独立函数非 Typer 子命令组）。功能等价，但 Spec→实现有偏离。
- **证据**：`.csp/specs/SPEC-F-N-1.md`（Spec 写 `saw search rebuild-embeddings`）；`src/saw/drivers/cli/commands/search_cmd.py:176`（`def rebuild_embeddings` 独立函数 + `app.command(name="rebuild-embeddings")`）；`.csp/artifacts/implement.md` v1.10.0 节偏离#1。
- **影响**：用户文档/CLI help 与 Spec 不一致（功能无影响）。
- **严重度**：Low（文档一致性）。
- **优先级**：P3。
- **建议**：回更 SPEC-F-N-1 命令名为 `saw rebuild-embeddings`（Spec 是蓝图，实现偏离须回更）。
- **回流**：下一轮 03（Spec 回更）。

### N6 — ROADMAP/lifecycle note tag commit hash 不一致 [Low / P3]
ROADMAP v1.10.0 行写 `@20b95f8`，lifecycle-state note 写 `@15bb5fe`，**实际** `git tag v1.10.0` 指向 `3865c75`（release commit）。三者不一致。
- **证据**：`docs/strategy/ROADMAP.md` v1.10.0 行（`@20b95f8`）；`.csp/lifecycle-state.json` 06-ship progress（`@15bb5fe`）；`git rev-list -n 1 v1.10.0` = `3865c75`。
- **影响**：追溯时 commit hash 混淆（功能无影响，tag 本身正确）。
- **严重度**：Low（记录一致性）。
- **优先级**：P3。
- **建议**：回更 ROADMAP v1.10.0 行为 `@3865c75`；lifecycle note 也更正。
- **回流**：下一轮 06/lifecycle 回更。

### N7 — semantic mode 不走 cache，ADR-010 [TBD] 缓存优化 [Low / P3]
`_semantic_search` 每次全量计算 cosine，不复用 `_keyword_search` 的 F-QS-07 cache 路径。ADR-010 标 [TBD] 缓存优化。
- **证据**：`src/saw/engines/query/engine.py`（`_semantic_search` 无 cache）；`.csp/tech-decisions/ADR/ADR-010-embedding-storage-retrieval.md`（[TBD]）。
- **影响**：重复查询无缓存，规模大时性能下降（见 N4）。
- **严重度**：Low（优化项）。
- **优先级**：P3。
- **建议**：benchmark 后若需缓存，加 query-text→embedding→results 缓存层（TTL + 索引变更失效）。
- **回流**：下一轮 03（缓存优化 ADR）。

### 续留 findings（来自前轮，未本轮处理）
- **M2**（agent "最近活动"未聚合）— 续留，须 event bus 聚合。
- **M3**（CLI workflow list vs REST /workflows 语义双重）— 续留，须文档明确或统一读 DB。
- **L2**（链接自动 apply 未做）— 续留，suggest 只输出不自动改文件。

## 下游衔接 → 下一迭代（候选主题，供下一轮 01 决策）

> 不下定论，列候选。v1.10.0 周期闭环，current_stage 标 `next-cycle-pending`。

| 候选 | 价值 | 依据 | findings 关联 |
|---|---|---|---|
| embedding E2E 验证 + benchmark | 闭环本轮 caveat；装 SDK 后跑真实语义检索 + P99 benchmark | N1/N4 | 解 P1 |
| realtime 仪表盘（v4.3 完整前端） | agent/workflow 运行态实时可视化 | roadmap v4.3 | M2/M3 |
| desktop 完成（v4.4 Tauri） | 桌面端达 v1.0 | roadmap v4.4 | — |
| 清 K1/K2 债 | coverage→65（compile/compiler 深覆盖）+ per-request workspace 注入 | K1/K2 | N2/N3 |
| 自定义 agent 角色注册 | v1.5.0 留 v2.0 候选 | roadmap | — |
| 缓存优化 + ANN 索引 | semantic 检索性能 | N4/N7 | — |

- v2.0.0（MAJOR）推迟到真实 breaking API 变更/范式跃迁时再 bump；当前 v1.x 序列继续 additive 逼近。
- 累计 v1.5.0–v1.10.0 六轮：3 轮债务收口（workspace 三闭环）+ 3 轮新能力（smart linking + agent 可视化 + embedding）。

---

*本复盘所有证据均经 git/manifest 真实状态核验。embedding E2E 未假装已验证（无 SDK）。findings 带证据 file:line/DEV-LOG。*
