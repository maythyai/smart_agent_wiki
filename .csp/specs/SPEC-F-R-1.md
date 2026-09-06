---
id: SPEC-F-R-1
title: ingest 目录递归遍历（Bug A）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-e2e-tail-v1.13.0.md
pms_ref: .csp/product-spec/PMS-e2e-tail.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-R-1
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-013-ingest-recursion-benchmark.md
adr_ref: .csp/tech-decisions/ADR/ADR-013-ingest-recursion-benchmark.md
ac_coverage: 5/5
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.13.0.md#T-F-R-1
---

# SPEC-F-R-1: ingest 目录递归遍历

## 实现 delta（ground 自源码）

> ADR-013 决策一：pipeline.py `ingest()` 入口加目录递归分支；classifier.py `is_dir` 块改为返回 `UNKNOWN`。

### 改动点

| 文件 | 行 | 现状 | 改为 |
|---|---|---|---|
| `src/saw/engines/ingest/classifier.py:149` | `if source_path.is_dir():` 遍历 `source_path.iterdir()` 找首个子文件，`return ClassifiedSource(format=child_class.format, path=source_path, language=child_class.language)`——`path` 是目录本身 | `if source_path.is_dir(): return ClassifiedSource(format=DocumentFormat.UNKNOWN, path=source_path)`——目录不再从子文件猜格式，统一返回 UNKNOWN 由 pipeline 入口处理 |
| `src/saw/engines/ingest/pipeline.py:100` | `def ingest(self, source, ...)`：`classify(source)` → 按 `classified.format` 路由单 extractor；无 `is_dir` 分支、无 walk | `ingest()` 入口先检测 `Path(source).is_dir()` → 若目录，`os.walk` 递归枚举子文件（排除噪声目录）→ 逐文件调 `_ingest_single_file()` → 聚合 IngestResult（`parser="directory-batch"`） |
| `src/saw/engines/ingest/pipeline.py:120-130,210-211` | extractor 收目录路径 → `open(dir)` → OSError "Is a directory" → `:210 except Exception` → `:211 errors.append(...)` | 目录由入口递归处理，extractor 不再收目录路径（单文件路径 `_ingest_single_file` 收到的 `classified.path` 是文件） |

### 不改动

- 既有 classify→extract→fuse→validate→enqueue 单文件链路完全复用（`_ingest_single_file` = 原有 `ingest()` 逻辑提取为内部方法）。
- `IngestResult` 结构不变（`session_id`/`claim_count`/`entity_count`/`relation_count`/`errors`/`warnings`/`parser`）。
- 单文件路径行为不变（`Path(source).is_dir()` False → 走既有 `_ingest_single_file`，不触发递归）。
- extractor 内部逻辑不变（markdown/pdf/code/json/table/audio/video 各自不变）。
- `DocumentFormat` 枚举不变。

## 后端架构

### 排除目录清单（HOW，本 Spec 定）

递归枚举时跳过以下目录（PRD 只要求排除 SAW 内部 + VCS，本 Spec 补全合理噪声目录）：

| 目录 | 排除理由 |
|---|---|
| `.git/` | VCS 内部（PRD 要求） |
| `.saw/` | SAW 内部（PRD 要求） |
| `node_modules/` | 依赖目录（PRD 提及，建议项） |
| `.venv/` / `venv*/` | 虚拟环境（噪声） |
| `__pycache__/` | Python 编译缓存（噪声） |
| `.mypy_cache/` / `.ruff_cache/` / `.pytest_cache/` | 工具缓存（噪声） |

排除实现：`os.walk` 时 prune `dirnames`（`walk(topdown=True)` 修改 `dirs[:]` in-place 移除噪声目录），不进入。

### ingest() 递归分支（`src/saw/engines/ingest/pipeline.py`）

```python
import os
from pathlib import Path

_NOISE_DIRS = {
    ".git", ".saw", "node_modules", ".venv", "venv",
    "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache",
}

def ingest(
    self,
    source: str,
    options: dict | None = None,
    progress_callback=None,
    workspace_id: str = "default",
) -> IngestResult:
    """Ingest a source (file path, URL, or directory)."""
    # Directory → recursive ingest
    source_path = Path(source)
    if source_path.is_dir():
        return self._ingest_directory(
            source, source_path, options, progress_callback, workspace_id
        )
    # Single file / URL → existing path
    return self._ingest_single_file(
        source, options, progress_callback, workspace_id
    )

def _ingest_single_file(self, source, options, progress_callback, workspace_id):
    """Existing ingest() logic, extracted verbatim (classify→extract→fuse→validate→enqueue)."""
    # ... (current ingest() body, unchanged)

def _ingest_directory(
    self, source, source_path, options, progress_callback, workspace_id
) -> IngestResult:
    """Recursively ingest all supported files in a directory."""
    session_id = str(uuid.uuid4())
    errors: list[str] = []
    warnings: list[str] = []

    # Enumerate files, pruning noise dirs
    files: list[Path] = []
    for root, dirnames, filenames in os.walk(source_path, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in _NOISE_DIRS]
        for fn in filenames:
            files.append(Path(root) / fn)

    if not files:
        return IngestResult(
            session_id=session_id,
            claim_count=0, entity_count=0, relation_count=0,
            errors=[f"No ingestible files found in directory: {source}"],
            parser="directory-batch",
        )

    # Per-file ingest (best-effort), aggregate
    total_claims = total_entities = total_relations = 0
    for fp in files:
        single = self._ingest_single_file(
            str(fp), options, progress_callback, workspace_id
        )
        total_claims += single.claim_count
        total_entities += single.entity_count
        total_relations += single.relation_count
        errors.extend(single.errors)
        warnings.extend(single.warnings)

    return IngestResult(
        session_id=session_id,
        claim_count=total_claims,
        entity_count=total_entities,
        relation_count=total_relations,
        errors=errors,
        warnings=warnings,
        parser="directory-batch",
    )
```

**关键设计**：
- `session_id`：目录批次共享一个 session_id（聚合结果），各文件共用。PRD 留 03 定——本 Spec 选共享（聚合结果，一个批次一个 session，便于追溯）。
- 逐文件 best-effort：单文件失败记 errors 不中断（`_ingest_single_file` 内部已有 `except Exception`，返回 `errors` 非空但 `claim_count` 可能 0）。
- 空目录：`files` 为空 → 返回 `errors=["No ingestible files found in directory: {dir}"]`，`claim_count=0`，`parser="directory-batch"`（AC-A-2）。
- `parser="directory-batch"`：标识目录批次聚合结果。

### classifier.py 适配

```python
# Directory — no longer guess format from children; pipeline handles recursion
if source_path.is_dir():
    return ClassifiedSource(
        format=DocumentFormat.UNKNOWN,
        path=source_path,
    )
```

目录返回 UNKNOWN，pipeline 入口 `Path(source).is_dir()` 先于 classify 拦截（目录分支不调 classify），但即使误入 classify 也返回 UNKNOWN（安全兜底）。

## CLI（既有，行为扩展）

```
saw ingest ./docs --path <wiki>     # 目录 → 递归枚举子文件 → 逐文件 ingest → 聚合
saw ingest ./readme.md --path <wiki>  # 单文件 → 既有路径（不变）
```

**结果打印**（Panel，既有 ingest 命令的 Rich Panel）：目录批次额外显示文件数 + 总 claims。

## 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 目录不存在 | `Path(source).is_dir()` False → 走单文件 → classify UNKNOWN → "Unknown format" | "Error: directory not found or no ingestible files" |
| 空目录（无可识别文件） | `files` 为空 → IngestResult errors=["No ingestible files found..."], claim_count=0, Exit 1 | "No ingestible files found in directory: {dir}" |
| 部分文件提取失败 | `_ingest_single_file` 返回 errors，best-effort 继续其余 | "Warnings: N files failed (see errors)" + 成功部分 Panel |
| 目录含子目录 | `os.walk` 递归进入（prune 噪声） | 正常 Panel（含递归文件数） |
| 排除 SAW 内部目录 | `_NOISE_DIRS` prune `.saw/`/`.git/` 等 | `.saw/` 内文件不被 ingest |

## 安全考量

- 排除 `.git/` 防止 VCS 内部文件泄露（PRD NFR security）。
- 排除 `.saw/` 防止 SAW 内部目录干扰。
- 递归不跟随符号链接（`os.walk` 默认 `followlinks=False`）。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-A-1（目录递归 ingest） | `tests/unit/test_ingest_directory.py`（新建）：建 tmp dir 含 3 .md → `pipeline.ingest(dir)` → 3 文件全部入库，claim_count ≥ 3，0 "Is a directory" 错误 | claim_count ≥ 3 + errors 无 "Is a directory" |
| AC-A-2（空目录） | `test_ingest_directory.py`：建 tmp 空目录 → `pipeline.ingest(dir)` → errors 含 "No ingestible files found" + claim_count=0 | errors[0] 含 "No ingestible files" + claim_count=0 |
| AC-A-3（部分失败） | `test_ingest_directory.py`：建 tmp dir 含 2 .md + 1 损坏 .pdf → `pipeline.ingest(dir)` → 2 .md 成功 + 1 .pdf 记 errors + 不中断 | 2 md claims + errors 含 pdf 失败 |
| AC-A-4（子目录递归） | `test_ingest_directory.py`：建 tmp dir 含子目录，子目录内 1 .md → `pipeline.ingest(dir)` → 子目录文件被 ingest + claim_count 含子目录 | claim_count 含子目录文件 |
| AC-A-5（排除 SAW 内部目录） | `test_ingest_directory.py`：建 tmp dir 含 `.saw/` 子目录 + `.saw/inside.md` → `pipeline.ingest(dir)` → `.saw/inside.md` 不被 ingest | errors 不含 `.saw/inside.md` + claim_count 不含 `.saw/` 文件 |

## 实现就绪度

- [x] 改动点明确（classifier.py:149 + pipeline.py:100 入口 + 提取 `_ingest_single_file`）
- [x] 排除目录清单定（`.git/`/`.saw/`/`node_modules/`/`.venv/`/`__pycache__/`/缓存目录）
- [x] session_id 共享（聚合批次）
- [x] 单文件路径不回归（`is_dir` False → 既有路径）
- [x] AC 覆盖 5/5
- [ ] 100 文件 60s NFR [TBD]（05 实施后实测，无 LLM 模式）
