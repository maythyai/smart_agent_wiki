# 复盘 — v1.12.0 embedding 改用 OpenAI 风格 API（2026-09-05）

> 07 闭环校验。findings 回流下一轮 01。前置：06-ship done（v1.12.0 tagged @50fc8e8，本地未 push）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-embedding-api-v1.12.0 Approved；4 SPEC-F-Q-1..4 1:1 对应 F-Q-1..4（`.csp/specs/SPEC-F-Q-{1..4}.md`，feature_id 字段一一匹配）。PRD 列 4 Feature，Spec 收敛为 4（1:1:1）。|
| Spec → Task | ✅ | TASKS-DELTA-v1.12.0 4 Task（T-F-Q-1..4）1:1 对应 4 Spec；DAG Q-1→{Q-2,Q-3,Q-4} 无环，2 Wave（Wave 1 Q-1 独占；Wave 2 Q-2/Q-3/Q-4 全并行）|
| Task → commit | ✅ | git log：`f4f4869`(feat F-Q-1 provider refactor) / `f4e9f04`(feat F-Q-2 configurable dim) / `4818926`(feat F-Q-3 ST fallback) / `65f036f`(test F-Q-4 API mock + benchmark) + `6c07c89`(docs 05-impl DEV-LOG) + `50fc8e8`(chore reconcile) + `40c8c8a`(release v1.12.0) |
| AC → 测试 | ✅ | 9 AC 全映射（`.csp/traceability/COVERAGE-REPORT.md` v1.12.0 delta，9/9 mapped）；测试文件存在：`tests/unit/test_embedding_index.py`（3 测试 API mock）/ `test_semantic_search.py`（含 ST fallback + API-only 场景）/ `test_related_pages_embedding.py`（2 测试 API mock）/ `test_embedding_degradation.py`（4 测试扩 API 不可用）/ `test_embedding_benchmark.py`（2 测试 新建）/ `test_ci_workflow.py`（扩 no-importorskip 断言） |
| commit → tag | ✅ | `git tag -l v1.12.0` 确认 annotated tag 指向 `50fc8e8`（reconcile commit）。release commit `40c8c8a` 在 tag 之后 1 commit（ship artifacts）。本地未 push 远端。 |
| 测试/lint | ✅ | 2076 passed / 3 skipped / 0 failed；ruff check src/ tests/ 0 errors；saw smoke 6/6 |
| coverage | ✅ | 66%（fail_under=65 ✓，较 v1.11.0 65.36% +0.64pp） |
| 构建 | ✅ | wheel `smart_agent_wiki-1.12.0-py3-none-any.whl`；pyproject.toml version=1.12.0 |
| 无本地 torch 加载 | ✅ | embedding 测试全 mock `litellm.embedding`，无 `importorskip("sentence_transformers")`，无 torch/sentence_transformers 导入 |
| 无 embedding importorskip skip | ✅ | `grep -rn 'importorskip' tests/unit/test_embedding_index.py test_semantic_search.py test_related_pages_embedding.py` → 仅注释行（文档说明已移除），无 `pytest.importorskip` 调用；`test_ci_workflow.py::test_embedding_tests_no_importorskip` 断言 pass |

### 闭环校验诚实标注
- 9 AC 全部经 API mock / 单元测试 pass，无 importorskip skip（v1.10.0 N1 High/P1 **闭合**）。
- **mock 验证了逻辑路径**（向量入库、cosine 排序、维度变更检测、upsert、降级路由、ST fallback 分支），但**真实 API E2E 未跑**——本环境未配真实 embedding API key，mock 向量是构造的固定模式（ML/crypto/web topic-direction 向量），非真实 API 返回。用户设 API key 后跑 `pytest tests/unit/test_embedding_benchmark.py --benchmark-e2e` 可补真实 E2E。
- benchmark 测试用 mock 假向量验证 semantic vs BM25 召回逻辑，**真实召回率对比须真实 API**——mock 延迟为 0，真实 P99 须 E2E。
- 本地 ST fallback 路径（AC-FB-1）通过 mock `_st_available()=True` + API 不可用场景测试，**未真实加载 torch/SentenceTransformer**（测试不调用 ST 路径，避免 runner 打死）。
- `_st_available()` 检测 `sentence_transformers` 可 import——本机实际已装 ST，但测试不依赖此路径（API mock 为主路径，degradation patch `_st_available()=False`）。

## v1.12.0 度量

| 指标 | v1.11.0 基线 | v1.12.0 | 变化 |
|---|---|---|---|
| pytest passed | 2064 | 2076 | +12（embedding mock 测试从 skip 变 pass + benchmark 新增） |
| skipped | 6 | 3 | -3（3 个 embedding importorskip 文件去 skip 改 mock，全 pass） |
| coverage | 65.36% | 66% | +0.64pp（fail_under=65 持，余量从 0.36pp 升至 1pp） |
| fail_under | 65 | 65 | 持平（66% > 65，余量 1pp） |
| ruff | 0 | 0 | 持平 |
| smoke | 6/6 | 6/6 | 持平 |
| 新增依赖 | — | 无 | 无新引擎、无新外部 DB；litellm 已在核心依赖（pyproject.toml:13 `litellm>=1.83.13`） |
| 新增测试文件 | — | 1 | `test_embedding_benchmark.py`（新建，semantic vs BM25 召回 + P99） |
| importorskip ST skip | 3 文件（7 测试） | 0 | **全去除**（N1 闭合） |
| torch 加载 | N/A | 0 | 测试全 mock，无 torch/sentence_transformers 导入 |

### 4 Feature done

1. **F-Q-1 provider 重构**（commit f4f4869）：`embed_texts()` 三级路由 API→ST→None；新增 `EmbeddingSettings`（model/api_key/api_base/timeout，从 env `SAW_EMBEDDING_MODEL`/`EMBEDDING_API_KEY`/`OPENAI_API_KEY` 读取）；`_api_embedding_available()` 检测 API 配置；`_embed_via_api()` 调 `litellm.embedding()`；`_normalize()` L2 范数化；`embeddings_available()` 改为 API OR ST；`detect_tier()._embeddings_available()` 改为 API OR ST；`embed_texts` 签名不变（下游零改动）。
2. **F-Q-2 维度可配 + 重建检测**（commit f4e9f04）：`EmbeddingSink.write()` model 列动态化（`_current_model_name()` 从 `EmbeddingSettings.model` 取，fallback `all-MiniLM-L6-v2`）；`_upsert_embedding` model 列动态传参；`rebuild_embeddings` 维度检测适配（provider 换了 `embed_texts(["dimension probe"])` 自动走 API/ST）。
3. **F-Q-3 本地 ST 可选 fallback**（commit 4818926）：provider 三级路由确认（API → ST → None）；`_st_available()`/`_embed_via_st()` 保留既有 ST 逻辑（向后兼容 v1.10.0）；`embeddings_available()` OR 逻辑对称；`detect_tier()._embeddings_available()` OR 逻辑对称。
4. **F-Q-4 测试改 API mock + benchmark**（commit 65f036f）：3 文件去 `importorskip("sentence_transformers")` 改 mock `litellm.embedding` 返回固定 1536 维向量（7 测试从 skip 变 pass）；`test_embedding_degradation.py` 扩 mock 到 API 不可用场景（4 测试）；`test_ci_workflow.py` 更新——embedding 测试无 `importorskip`；新建 `test_embedding_benchmark.py`（semantic vs BM25 召回 + P99，2 测试）。

### 清债完成情况

| 07 finding | 维度 | 本轮处理 | 状态 |
|---|---|---|---|
| N1（embedding E2E 未验证, High/P1） | 测试 | F-Q-4 去 importorskip 改 API mock，7 测试从 skip 变 pass | ✅ done（N1 闭合——mock 路径全验证，真实 API E2E 见 Q1 findings） |
| N4（向量检索 P99 benchmark, Medium/P2） | 性能 | F-Q-4 新建 `test_embedding_benchmark.py`，benchmark 可执行（mock baseline） | ✅ done（mock baseline；真实 API E2E 见 Q1 findings） |

## Findings（回流下一轮）

### Q1 — 真实 API E2E 仍未跑（mock 验证了路径，真 API 未跑）[High / P1]
v1.12.0 的核心交付是 embedding 改用 API + E2E 验证。mock `litellm.embedding` 验证了全部逻辑路径（向量入库、cosine 排序、维度变更、upsert、降级路由、ST fallback），7 个原 importorskip 测试从 skip 变 pass。但**本环境未配真实 embedding API key**——mock 向量是构造的固定模式（ML/crypto/web topic-direction 向量），非真实 API 返回的语义向量。真实 API 调用路径（网络请求、限流、超时、维度差异、返回格式解析）未经实跑验证。
- **证据**：`tests/unit/test_embedding_benchmark.py:10-12`（"Real E2E benchmark requires the user to configure a real API key and run: `pytest tests/unit/test_embedding_benchmark.py --benchmark-e2e`"）；`.csp/artifacts/implement.md` v1.12.0 节（"mock `litellm.embedding` via `monkeypatch.setattr`"，"向量基于文本关键词生成 topic-direction 向量"）；`.csp/artifacts/verify/test-results.md` v1.12.0 节（"Zero embedding importorskip skips — all embedding tests now run via mock litellm.embedding"）。
- **影响**：真实 API 调用可能遇 mock 未覆盖的问题——API 返回格式差异、限流/超时降级行为、真实语义向量的召回质量、API dim 与配置不匹配的边界。mock 验证的是代码路径正确性，非 API 互操作性。
- **严重度**：High（N1 的"真 E2E"维度仍未闭环——从"测试 skip"到"mock pass"是进步，但"mock pass"到"真 API pass"还差一步）。
- **优先级**：P1。
- **建议**：用户设 `EMBEDDING_API_KEY`/`OPENAI_API_KEY` + `SAW_EMBEDDING_MODEL` env 后跑 `pytest tests/unit/test_embedding_benchmark.py --benchmark-e2e`（若实现）或手动 `saw search "machine learning" --mode semantic` 验证真实召回。可合并 O1 cache 命中率 benchmark。
- **回流**：下一轮 01（用户设 API key 后验证，或作为下一版本候选）。

**v1.13.0 闭合**：commit `84e1776` 用 httpx 直连 vLLM `qwen_embedding@8001`，
真实 API E2E 验证通过（semantic 检索召回正常）。Q1（真实 API E2E 未跑）→ closed。

### Q2 — benchmark 用 mock 假向量，真实召回率对比须真 API [Medium / P2]
`test_embedding_benchmark.py` 用 mock 生成固定模式向量（ML/crypto/web topic-direction），验证了 semantic vs BM25 召回逻辑——semantic 能召回 BM25 漏的同义文档。但 mock 向量是手工构造的固定模式，非真实 API 语义向量，无法代表真实召回率。PRD §1.3 "semantic vs BM25 召回率优于纯 BM25 `[TBD]`" 仍为 [TBD]。
- **证据**：`tests/unit/test_embedding_benchmark.py`（mock 向量基于 `_make_mock_embedding` 函数，手工构造 topic-direction 向量）；`.csp/tasks/TASKS-DELTA-v1.12.0.md` assumptions（"semantic vs BM25 召回率 [TBD]"）；PRD §1.3（"[TBD]"）。
- **影响**：无法量化 embedding 质量是否优于 BM25；真实召回率、P99 延迟均为 [TBD]。
- **严重度**：Medium（benchmark 框架已建好，只缺真实数据）。
- **优先级**：P2。
- **建议**：用户配 API key 后跑真实 benchmark，记录召回率 + P99 baseline。与 Q1 合并执行。
- **回流**：下一轮 01（须真实 API key）。

### Q3 — 本地 ST fallback 路径未测（避免 torch 加载）[Low / P3]
F-Q-3 实现了 provider 三级路由 API→ST→None，保留了本地 ST fallback 分支。但测试用 mock `_st_available()=True` + API 不可用场景验证路由逻辑，**未真实加载 torch/SentenceTransformer 执行 ST encode 路径**——避免 torch 加载打死后 runner（这是 v1.12.0 的核心目标）。ST fallback 代码路径的 `_get_model().encode()` 未经运行验证。
- **证据**：`.csp/specs/SPEC-F-Q-3.md`（`_embed_via_st()` 保留既有逻辑）；`.csp/artifacts/implement.md` v1.12.0 节（"degradation 测试 patch `_st_available`=False"，"测试不调用 ST 路径"）。
- **影响**：ST fallback 路径有逻辑验证但无运行验证——极端情况下 ST 加载或 encode 可能失败（但此路径是向后兼容 v1.10.0 的，v1.10.0 时已有真实 ST 跑过）。
- **严重度**：Low（向后兼容路径，v1.10.0 已验证过；非默认路径）。
- **优先级**：P3。
- **建议**：可选——用户装 `[learn]` extra 后跑一次 ST fallback 路径测试，确认无回归。非紧急。
- **回流**：可选（低优先级）。

**v1.13.0 闭合**：commit `84e1776` 删除了 ST fallback 路径
（`_st_available`/`_embed_via_st` 移除），provider 改为 API-only
（httpx 直连 vLLM），无 ST fallback 分支需测。Q3（ST fallback 路径未测）→ closed。

### 续留 findings（来自前轮，未本轮处理）

| finding | 维度 | 来源 | 状态 | 说明 |
|---|---|---|---|---|
| N3/K2 | per-request workspace 注入 | v1.7.0 K2 | 续留 | QueryEngine 仍 startup 单例 default workspace；web 路径请求级 ws 注入未做。须 v2.0 架构演进。Medium/P2 |
| M2 | agent "最近活动" 聚合 | v1.9.0 M2 | 续留 | roster 是静态，agent 最近活动需 event bus 聚合。Medium/P2 |
| L2 | 链接自动 apply | v1.8.0 L2 | 续留 | suggest 只输出不自动改文件。Low/P3 |
| O1 | semantic cache 命中率未 benchmark | v1.11.0 O1 | 续留 | cache 机制已实现 + mock 测试 pass，无真实 embedding 环境命中率/延迟对比。Low/P2 |
| O2 | coverage 余量薄 | v1.11.0 O2 | **改善** | v1.11.0 65.36%（余量 0.36pp）→ v1.12.0 66%（余量 1pp），改善但仍薄。Low/P3 |
| O3 | workflow REST 行为变更无 CHANGELOG | v1.11.0 O3 | 续留 | 项目无 CHANGELOG 文件，REST `/workflows` 字段名变更未标注。Low/P3 |
| O4 | tag 指向 reconcile 非 release commit | v1.11.0 O4 | **v1.12.0 同模式** | v1.12.0 tag 指向 `50fc8e8`（reconcile），release commit `40c8c8a` 在 tag 之后 1 commit。同 v1.11.0 模式。Low/P3 |

### O1-O4 状态更新

| finding | v1.11.0 状态 | v1.12.0 状态 |
|---|---|---|
| O1（cache 命中率） | open | open（续留，须真实 API key + 重复查询 benchmark） |
| O2（coverage 余量薄） | open | **改善**（65.36%→66%，余量 0.36→1pp；仍 P3 但改善） |
| O3（REST CHANGELOG） | open | open（续留） |
| O4（tag → reconcile） | open | open（v1.12.0 同模式，tag→reconcile `50fc8e8`） |

### 本轮新发现（DEV-LOG 偏离记录）

| 偏离 | 说明 | 影响 |
|---|---|---|
| litellm import 慢（7s remote fetch） | DEV-LOG：`tests/conftest.py` 设 `LITELLM_LOCAL_MODEL_COST_MAP=True`（1.4s） | 无（CI 加速，测试环境优化） |
| `sentence_transformers` 实际已装于本机 | DEV-LOG：`_st_available()` 返回 True，但测试 mock API 为主路径，不走 ST | 无（测试不依赖此，degradation patch `_st_available`=False） |
| `_ML_KW` 去掉 "python" | DEV-LOG：web-framework 内容含 "Python" 导致误匹配 ML 向量 | 无（mock 向量精度修正） |
| degradation patch 目标 | DEV-LOG：必须 patch `saw.write_queue.sinks.embedding_sink.embeddings_available`（模块级 import 不受 embeddings 模块 patch 影响） | 无（测试 patch 精度修正，不影响生产行为） |

## 下游衔接 → 下一迭代候选（供下一轮 01 决策）

> 不下定论，列候选。v1.12.0 周期闭环，current_stage 标 `next-cycle-pending`。

| 候选 | 价值 | 依据 | findings 关联 |
|---|---|---|---|
| 真实 API E2E 验证 + benchmark | 用户设 API key 后跑真实语义检索 + P99 + 召回率 + cache hit/miss 对比 | Q1/Q2/O1 | 解 P1 + P2 |
| realtime 仪表盘（v4.3 完整前端） | agent/workflow 运行态实时可视化 | roadmap v4.3 | M2 |
| desktop 完成（v4.4 Tauri） | 桌面端达 v1.0 | roadmap v4.4 | — |
| K2 per-request workspace 注入 | web 路径请求级 workspace 隔离 | N3/K2 | 架构演进（v2.0 候选） |
| 自定义 agent 角色注册 | v1.5.0 留 v2.0 候选 | roadmap | — |
| 清剩余 coverage 边角 | fail_under 65→67 给余量，非核心模块深测 | O2 | — |
| REST `/workflows` 兼容 alias + CHANGELOG | 字段名兼容 + 文档标注行为变更 | O3 | — |
| tag 指向 release commit 规范 | 下次 tag 指向 release commit 或 ROADMAP 注明 release commit hash | O4 | — |

- v2.0.0（MAJOR）推迟到真实 breaking API 变更/范式跃迁时再 bump；当前 v1.x 序列继续 additive 逼近。
- 累计 v1.5.0–v1.12.0 八轮：4 轮债务收口（workspace 三闭环 + coverage 65 达成 + bug fix）+ 4 轮新能力（smart linking + agent 可视化 + embedding + embedding API pivot）。
- 本轮核心成就：**N1（High/P1）闭合**——embedding 从"本地重 SDK、7 测试 skip"到"API mock、7 测试全 pass、无 torch 加载"；N4 benchmark 框架建立（mock baseline）；coverage 65.36→66%（余量改善）；importorskip ST skip 全去除；复用 litellm + LLM router 同套 config 范式（零新依赖）。2 项 findings 清掉（N1/N4），3 项新 findings 回流（Q1/Q2/Q3），7 项续留（N3/M2/L2/O1-O4，其中 O2 改善）。

---

*本复盘所有证据均经 git/manifest 真实状态核验。不假装真实 API E2E 已跑（仅 mock 验证路径）。findings 带证据 file:line/DEV-LOG。*
