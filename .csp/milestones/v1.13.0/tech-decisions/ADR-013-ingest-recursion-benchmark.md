# ADR-013: Ingest 目录递归 + Benchmark 方法论

## 状态：Accepted

## 上下文

v1.13.0 E2E 收尾轮暴露两类工程问题，须 ADR 留档决策依据：

### 问题一：`saw ingest <dir>` 把目录当单文件（Bug A）

`saw ingest <dir>` 传目录时报 "Is a directory"，根因在 classifier + pipeline 两层：

1. **classifier.py**（`src/saw/engines/ingest/classifier.py:149` `if source_path.is_dir():`）：检测到目录后，遍历首层子文件，从首个可识别子文件推断 `format`，但返回 `ClassifiedSource(format=child_class.format, path=source_path, ...)`——**`path` 字段填的是目录路径本身**，而非子文件路径。下游 extractor 拿到的是目录路径。
2. **pipeline.py**（`src/saw/engines/ingest/pipeline.py:100` `def ingest(...)`）：`ingest()` 只处理单个 source——`classify(source)` → 按 `classified.format` 路由到单个 extractor（`:120-130` markdown 分支 `self._markdown_extractor.extract(classified.path, ...)`），**无 `is_dir` 分支、无 `walk`/`rglob` 递归枚举子文件**。extractor 尝试 `open(目录)` → `OSError: Is a directory` → 被 `:210-211` `except Exception as e: errors.append(f"Extraction failed for {source}: {e}...")` 捕获记入 errors。

结果是：目录参数永远失败，用户 `saw ingest ./docs` 批量入库不可用。

### 问题二：既有 benchmark 是 mock 假向量（Q2/O1）

v1.12.0 建立的 benchmark（`tests/unit/test_embedding_benchmark.py`）用 `_topic_vec`（`:26`）手工构造 topic-direction 向量（ML/crypto/web 三方向），`_mock_embedding_response`（`:44`）返回构造向量——非真实 API 语义向量。retrospective-v1.12.0.md findings Q1（真实 API E2E 未跑，High/P1）+ Q2（benchmark mock 假向量，Medium/P2）+ O1（cache 命中率未 benchmark，Medium/P2）均指向同一缺口：**须用真实 vLLM `qwen_embedding@8001` 跑 semantic vs BM25 召回率 + P99 + cache 命中率，产出真实 baseline**。

vLLM `qwen_embedding@8001` 已由用户启动（commit `84e1776` 已验证 httpx 直连 vLLM 通），benchmark 可真测。

### CMS 出处（ground 自源码）

| 事实 | file:line | 现状 |
|---|---|---|
| classifier is_dir 检测后返回目录路径 | `src/saw/engines/ingest/classifier.py:149` | `if source_path.is_dir():` 遍历 `source_path.iterdir()` 找首个子文件，`return ClassifiedSource(format=child_class.format, path=source_path, language=child_class.language)`——`path` 是目录本身，非子文件 |
| pipeline ingest() 无目录递归分支 | `src/saw/engines/ingest/pipeline.py:100` | `def ingest(self, source, ...)`：`classify(source)` → 按 `classified.format` 路由单 extractor；无 `is_dir` 分支、无 walk |
| extractor 收目录路径报错被捕获 | `src/saw/engines/ingest/pipeline.py:120-130,210-211` | markdown 分支 `self._markdown_extractor.extract(classified.path, ...)` 收目录 → `open(dir)` → OSError；`:210` `except Exception as e:` → `:211` `errors.append(f"Extraction failed for {source}: {e}...")` |
| _keyword_search 是 BM25 baseline + cache | `src/saw/engines/query/engine.py:212,224-226,296,300` | `_keyword_search` 调 `get_cache()`（`:226`）+ `mode="search"`（`:296`）+ `_cache.set`（`:300`）；走 `self._search.search(question, ...)`（FTS5 BM25） |
| _semantic_search cosine + cache | `src/saw/engines/query/engine.py:458,484-486,528,578,589` | `_semantic_search` 调 `get_cache()`（`:486`）+ `mode="semantic"`（`:528`/`:578`）+ `_cache.set`（`:589`）；cosine 排序；fallback BM25（`embeddings_available()` False → `_keyword_search`） |
| benchmark 用 mock 假向量 | `tests/unit/test_embedding_benchmark.py:26,44` | `_topic_vec` 手工构造 topic-direction 向量；`_mock_embedding_response` 返回构造向量——非真实 API |
| REST list_workflows 响应无别名 | `src/saw/api/routes/collaborate.py:328,358,373,401` | `list_workflows` 读 `workflow_executions` 表 + merge `_workflows` in-memory；响应 item `definition_name`（`:373`/`:401`），无 `name`/`workflow` 别名 |
| coverage fail_under=65 | `pyproject.toml:127` | `fail_under = 65`；当前 66%，余量 1pp；目标 67 |

## 决策

### 决策一：Ingest 目录递归 → 候选 ①（classifier walk 子文件 + pipeline 入口递归）

选择候选 ①：**pipeline.py `ingest()` 入口处加目录递归分支**——在 `classify(source)` 之前/之后检测 `Path(source).is_dir()`，若目录则 `os.walk`/`Path.rglob` 递归枚举子文件（排除 `.git/`/`.saw/`/`node_modules/`），逐文件调既有 `ingest()` 单文件路径（classify→extract→fuse→validate→enqueue），聚合 IngestResult（`parser="directory-batch"`，汇总 claim/entity/relation_count，errors 汇总）。classifier.py 的 `is_dir` 块改为返回 `format=UNKNOWN`（不再从子文件推断目录格式），让 pipeline 入口统一处理目录。

### 决策二：Benchmark 方法论 → 候选 ②（独立 scripts/benchmark_semantic.py）

选择候选 ②：**独立可执行脚本 `scripts/benchmark_semantic.py`**——用真实 vLLM API（httpx 直连 `qwen_embedding@8001`，复用 `embed_texts()` API 路径），建测试数据集（≥3 主题 × ≥5 文档），跑 semantic vs BM25 召回率对比 + P99 延迟（N≥100 次）+ cache 命中率（同查询 2 次），输出结构化结果。vLLM 不可达报错退出不 mock。

## 备选方案

### 决策一备选

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① pipeline 入口递归 + classifier is_dir→UNKNOWN（选） | 改动集中在 pipeline.ingest() 入口（单函数），不侵入 extractor；复用既有单文件路径（classify→extract→fuse→validate→enqueue 链路逐文件调用，零重复逻辑）；聚合结果自然（汇总 IngestResult）；classifier 简化（is_dir 不再猜格式）；单文件路径完全不变（不触发递归） | 递归逻辑在 pipeline 层（非 classifier），但 pipeline 本就是编排者，目录编排属其职责 | 目录批量入库 ✓ |
| ② classifier walk 返回多 ClassifiedSource | classify 职责清晰（返回所有子文件分类结果） | `classify()` 签名从 `-> ClassifiedSource` 变 `-> list[ClassifiedSource]`，是 breaking 签名变更，所有调用方须改；extractor 逻辑仍须在 pipeline 聚合；改动面大、收益小 | 不如候选 ① 集中 |

### 决策二备选

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① pytest-benchmark 插件 | 集成 pytest 生态；统计开箱即用 | pytest-benchmark 面向微基准（函数级），benchmark 须建数据集+ingest+多查询编排，非单函数微基准；统计 P99 需自定义；CI 无 vLLM 时须 skip，插件价值打折 | 函数级微基准，非本场景 |
| ② 独立 scripts/benchmark_semantic.py（选） | 可执行脚本入口清晰（`python scripts/benchmark_semantic.py`）；完整编排数据集构建+查询+统计+输出；vLLM 不可达报错退出不 mock（PRD 硬要求）；CI 无 vLLM 时标 `importorskip`/marker skip；量小（≤9 文档）不 OOM；输出结构化 JSON/表格便于 baseline 留档 | 不集成 pytest 生态（须手动跑或 CI step） | 真实 vLLM benchmark ✓ |

## 理由

### 决策一理由

1. **改动集中**：候选 ① 把递归逻辑集中在 `pipeline.ingest()` 入口（单一编排函数），不侵入 extractor/classifier 内部。pipeline 本就是编排者，目录批量编排属其职责（编排 classify→extract→fuse→validate→enqueue 链路）。
2. **复用零重复**：逐文件调既有单文件 `ingest()` 路径（`_ingest_single_file`），classify→extract→fuse→validate→enqueue 链路完全复用，不重复 extractor 逻辑。聚合结果自然（汇总 IngestResult，parser 标 `directory-batch`）。
3. **单文件路径不回归**：传入单文件时 `Path(source).is_dir()` False，走既有路径，不触发递归（AC-A-4 子目录 + 单文件测试覆盖不回归）。
4. **classifier 简化**：`is_dir` 块改为返回 `format=UNKNOWN`（不再从子文件猜目录格式），消除"返回目录路径当单文件"的 bug 根。目录由 pipeline 入口统一处理。
5. **候选 ② 淘汰理由**：`classify()` 签名变 `list` 是 breaking 变更，所有调用方须改，改动面大、收益小。

### 决策二理由

1. **PRD 硬要求真测不 mock**：PRD §3.2 业务规则 1 "benchmark 须用真实 vLLM API，不可用 mock 假向量"。候选 ② 是独立脚本，直接走 `embed_texts()` API 路径（httpx 直连 vLLM），不依赖 mock。
2. **量小不 OOM**：PRD §3.2 规则 7 "≥3 主题 × ≥5 文档"，实际 ≤9 条文档（同 test_embedding_benchmark.py 规模），API 批量 embed ≤9 条不会 OOM，单次 < 5 min（NFR）。
3. **vLLM 不可达报错退出**：脚本先 health check `qwen_embedding@8001`，不可达报 "vLLM embedding endpoint at :8001 unreachable" 退出，不静默退化到 mock（AC-B-4）。
4. **CI 兼容**：脚本作为独立测试用例时标 `importorskip`/marker，CI 无 vLLM 时 skip（不影响 CI 绿）。真实 benchmark 由用户在有 vLLM 环境手动跑。
5. **候选 ① 淘汰理由**：pytest-benchmark 面向函数级微基准，benchmark 须建数据集+ingest+多查询编排，非单函数微基准；统计 P99 需自定义；CI 无 vLLM 时插件价值打折。
6. **插入点清晰**：benchmark 复用 `QueryEngine._semantic_search`（cache + cosine，`engine.py:458-589`）+ `QueryEngine._keyword_search`（BM25 baseline，`engine.py:212-300`），对比两者召回率/P99/cache 命中，不新写检索逻辑。

## 后果

### 正面
- ingest 目录递归可用（`saw ingest ./docs` 递归导入，0 "Is a directory" 报错）。
- benchmark 有真实 baseline（semantic vs BM25 召回率 + P99 + cache 命中率，vLLM 真测）。
- 闭合 Q2（benchmark mock 假向量）+ O1（cache 命中率未 benchmark）——真实数据替换 mock。
- classifier 简化（is_dir→UNKNOWN，不再猜格式），消除 bug 根。

### 负面
- 递归逻辑在 pipeline 层（非 classifier），但 pipeline 本是编排者，可接受。
- benchmark 脚本不集成 pytest 生态（须手动跑或 CI step + vLLM 可达时）。
- ingest 递归改动面触及 pipeline.ingest()（核心路径），须单文件回归测试覆盖。

### 风险
- 排除目录清单不完整导致噪声 → 排除清单至少含 `.git/`/`.saw/`/`node_modules/`/`.venv/`/`__pycache__/`（HOW 留 Spec）。
- benchmark vLLM 不稳定/用户关停 → 脚本报错退出，其他 4 项不依赖 vLLM 可先行。
- 递归改动影响单文件路径 → AC-A-4 排除内部目录 + 单文件测试覆盖不回归。

## 关联 Feature

- F-R-1（ingest 目录递归遍历）
- F-R-2（真实 embedding benchmark 脚本）

## 关联 ADR

- ADR-010（embedding_store BLOB + numpy cosine 存储/检索，Accepted，不变）——benchmark 复用既有存储/检索。
- ADR-011（semantic search cache，Accepted，不变）——benchmark 测 cache 命中率复用既有 cache。
- ADR-012（embedding provider litellm API，Accepted，不变）——benchmark 走 `embed_texts()` API 路径（httpx 直连 vLLM），provider 层不变。
