---
id: SPEC-F-N-4
title: heavy-SDK 测试 importorskip 沿用（embedding 测试 skip 策略 + CI coverage 不回归）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-embedding-v1.10.0.md
pms_ref: .csp/product-spec/PMS-embedding.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-N-4
complexity: S
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
ac_coverage: 3/3
related_tasks: [T-F-N-4]
---

# SPEC-F-N-4: heavy-SDK 测试 importorskip 沿用

## 实现 delta（ground 自源码）

- **importorskip 先例**：`tests/unit/engines/learn/test_fsrs.py:15` 用 `pytest.importorskip("fsrs")`，CI 无 fsrs 时自动 skip。
- **CI workflow 检测逻辑**：`tests/unit/test_ci_workflow.py:62-70` 检测 CI workflow 文件中 importorskip 策略覆盖。
- **embedding 测试文件**：F-N-1/F-N-2/F-N-3 实现时产出的 `test_embedding_index.py` / `test_semantic_search.py` / `test_related_pages_embedding.py` 统一加 `pytest.importorskip("sentence_transformers")`。
- **coverage 兼容**：importorskip 跳过的测试不计入 fail，coverage 不因 skip 下降（沿用既有 `--ignore learn` → `importorskip` 策略）。

## 测试策略

### importorskip 模式

每个 embedding 相关测试文件首行（参照 `test_fsrs.py:15`）：

```python
import pytest
pytest.importorskip("sentence_transformers")
```

**行为**：
- CI 环境（无 `[learn]` extra）：`sentence_transformers` 不可导入 → 测试被 skip（status=skipped），不 fail，不需 `--ignore`。
- 本地环境（有 `[learn]` extra）：正常导入 → 测试正常运行并 pass。

### 测试文件清单

| 测试文件 | Feature | importorskip | AC 覆盖 |
|---|---|---|---|
| `tests/unit/test_embedding_index.py` | F-N-1 | `sentence_transformers` | AC-EMB-1/2/3 |
| `tests/unit/test_semantic_search.py` | F-N-2 | `sentence_transformers` | AC-SEM-1/2/3 |
| `tests/unit/test_related_pages_embedding.py` | F-N-3 | `sentence_transformers` | AC-LINK-1/2/3 |

> AC-SEM-2 和 AC-LINK-2（降级测试）需要 mock `embeddings_available()=False`，但 importorskip 会跳过整个文件。因此降级测试须放在**独立测试文件**中（不加 importorskip），用 mock 模拟 `embeddings_available()=False` 的行为，不依赖真实 `sentence_transformers` 导入。

### 降级测试分离策略

| 测试文件 | 加 importorskip? | 测试内容 |
|---|---|---|
| `tests/unit/test_embedding_index.py` | 是 | AC-EMB-1（正常索引）、AC-EMB-3（重建） |
| `tests/unit/test_semantic_search.py` | 是 | AC-SEM-1（正常语义检索）、AC-SEM-3（空索引） |
| `tests/unit/test_related_pages_embedding.py` | 是 | AC-LINK-1（语义 suggest）、AC-LINK-3（排序下降） |
| `tests/unit/test_embedding_degradation.py` | **否** | AC-EMB-2（无 [learn] 不报错）、AC-SEM-2（降级 BM25）、AC-LINK-2（保持 3-signal） |

**降级测试文件**（`test_embedding_degradation.py`）不加 importorskip，用 `unittest.mock.patch` 模拟 `embeddings_available()=False`：

```python
from unittest.mock import patch

def test_emb_ac2_no_learn_no_error():
    """AC-EMB-2: tier=LIGHTWEIGHT → ingest 不报错, embedding_store 空."""
    with patch("saw.adapters.embeddings.embeddings_available", return_value=False):
        # ingest a claim → no exception, embedding_store empty
        ...
```

### CI workflow 兼容

`tests/unit/test_ci_workflow.py:62-70` 中的 importorskip 检测逻辑须验证 embedding 测试文件也被覆盖：

```python
def test_ci_workflow_importorskip_coverage():
    """AC-TEST-3: CI workflow coverage 不因 embedding skip 下降."""
    # Assert embedding test files have importorskip
    embedding_test_files = [
        "tests/unit/test_embedding_index.py",
        "tests/unit/test_semantic_search.py",
        "tests/unit/test_related_pages_embedding.py",
    ]
    for f in embedding_test_files:
        content = Path(f).read_text()
        assert "importorskip" in content
    # Assert degradation test file does NOT have importorskip (uses mock instead)
    deg_content = Path("tests/unit/test_embedding_degradation.py").read_text()
    # degradation file uses mock, not importorskip
```

## 测试映射（AC→用例）

| AC | 用例落点 | 类型 | 断言 |
|---|---|---|---|
| AC-TEST-1（CI skip embedding 测试） | `tests/unit/test_embedding_index.py`（含 importorskip）：CI 无 sentence_transformers → skip 不 fail | importorskip | pytest tests/ 无 fail + skip status |
| AC-TEST-2（本地 embedding 测试 pass） | `tests/unit/test_embedding_index.py`：本地有 [learn] → 测试正常运行 pass | functional | 测试 pass |
| AC-TEST-3（coverage 不回归） | `tests/unit/test_ci_workflow.py`（扩）：验证 embedding 测试文件 importorskip 覆盖 + coverage 不下降 | CI workflow | coverage ≥ 既有基线 |

## 实现就绪度

- [x] importorskip 先例已有（`test_fsrs.py:15`）
- [x] CI workflow 检测逻辑已有（`test_ci_workflow.py:62-70`）
- [x] 降级测试分离策略设计完整（importorskip 文件 vs mock 文件）
- [x] AC 覆盖 3/3
- [x] coverage 不回归策略（importorskip skip 不计入 fail）
- [ ] 降级测试 mock 策略需 05 实施时验证 mock 边界
