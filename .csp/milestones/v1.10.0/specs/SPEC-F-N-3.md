---
id: SPEC-F-N-3
title: smart-linking suggest 接 embedding 相似度信号
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-embedding-v1.10.0.md
pms_ref: .csp/product-spec/PMS-embedding.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-N-3
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
adr_ref: .csp/tech-decisions/ADR/ADR-010-embedding-storage-retrieval.md
ac_coverage: 3/3
related_tasks: [T-F-N-3]
---

# SPEC-F-N-3: smart-linking suggest 接 embedding 相似度信号

## 实现 delta（ground 自源码）

- **`compute_related_pages()`** 增第 4 信号：页面内容 embedding 相似度（`src/saw/engines/query/related_pages.py:26,35-57`）。
- **tier=FULL 时**：embedding 信号参与排序（加权模式，权重 2.5）；tier<FULL 时：完全保持 3-signal 不变。
- **页面无 embedding 向量时**：跳过 embedding 信号，仅用 3-signal 评分（安全降级）。
- **全部页面均无向量时**：完全降级到 3-signal，行为与 v1.8.0 一致。
- **复用** `embeddings.py::cosine_similarity()` / `embeddings_available()` + `detect_tier()`。
- **新增参数**：`compute_related_pages()` 签名增 `conn` + `workspace_id` 参数（可选，default None → 不查 embedding）。

## 后端架构

### compute_related_pages() 签名扩展

**当前签名**（`related_pages.py:26`）：
```python
def compute_related_pages(slug: str, wiki_repo, top_k: int = 8) -> list[dict]:
```

**扩展后**：
```python
def compute_related_pages(
    slug: str,
    wiki_repo,
    top_k: int = 8,
    conn: sqlite3.Connection | None = None,
    workspace_id: str = "default",
) -> list[dict]:
```

`conn=None` 时跳过 embedding 信号（向后兼容 v1.8.0 行为）。调用方（`links_cmd.py`）在 tier=FULL 时传入 conn。

### embedding 信号逻辑

在 3-signal 评分计算后（`related_pages.py:57` 附近），追加：

```python
# Signal 4: Embedding similarity (weight 2.5, tier=FULL only)
embedding_score = 0.0
if conn is not None:
    from saw.adapters.embeddings import embeddings_available, cosine_similarity
    if embeddings_available():
        import struct
        # Load source page vector
        src_row = conn.execute(
            "SELECT vector, dim FROM embedding_store WHERE doc_id = ? AND workspace_id = ?",
            (slug, workspace_id),
        ).fetchone()
        if src_row:
            src_vec = list(struct.unpack(f"<{src_row[1]}f", src_row[0]))
            # Load target page vector
            tgt_row = conn.execute(
                "SELECT vector, dim FROM embedding_store WHERE doc_id = ? AND workspace_id = ?",
                (page_slug, workspace_id),
            ).fetchone()
            if tgt_row:
                tgt_vec = list(struct.unpack(f"<{tgt_row[1]}f", tgt_row[0]))
                sim = cosine_similarity(src_vec, tgt_vec)
                embedding_score = sim * 2.5  # weight 2.5

total_score = tag_score + link_score + type_score + embedding_score
```

### 评分权重设计

| 信号 | 权重 | 来源 | 说明 |
|---|---|---|---|
| Shared tags (Jaccard) | 2.0 | 既有 | tag 重合度 |
| Shared links (Jaccard) | 3.0 | 既有 | link 重合度（最强信号） |
| Type affinity | 1.0 | 既有 | 同类型加成 |
| **Embedding similarity** | **2.5** | **新增** | 语义相似度（介于 tag 和 link 之间） |

**权重选择理由**：
- embedding 权重 2.5 介于 tag(2.0) 和 link(3.0) 之间：语义相似度是强信号但不应压过显式 link 关系（link 是人工标注的强意图）。
- 权重可调（后续可 benchmark 优化 [TBD]），但本轮固定 2.5。

### reasons 追加

在 `_build_reasons()`（`related_pages.py:71`）中追加：
```python
if r.embedding_sim is not None and r.embedding_sim > 0.3:
    reasons.append(f"semantic similarity: {r.embedding_sim:.2f}")
```

`RelatedPage` dataclass 增字段：
```python
@dataclass
class RelatedPage:
    slug: str
    title: str
    score: float
    shared_tags: list[str]
    shared_links: list[str]
    same_type: bool
    embedding_sim: float | None = None  # 新增
```

### 性能考量

- **O(pages²) 担忧**：当前 `compute_related_pages` 已是 O(pages)（遍历所有页面与源页比较），embedding 信号只增加每页一次 cosine_similarity（384 维纯 Python dot），不改变复杂度量级。
- **限 top N**：已有 `top_k=8` 限制，embedding 信号只影响排序不影响计算量。
- **缓存 [TBD]**：若性能不足，可缓存页面间相似度矩阵（后续优化）。

## API 契约

无新端点。`saw links suggest <page>` 行为增强（tier=FULL 时建议列表含语义相似页面）。

### CLI 行为

```
saw links suggest <page> [--path DIR]
```

- tier=FULL：建议列表含 4-signal 评分（含 embedding 信号），reasons 可能含 "semantic similarity: 0.82"。
- tier<FULL：行为与 v1.8.0 完全一致（3-signal），不报错。

### 调用方修改

`links_cmd.py` 中调用 `compute_related_pages()` 时，当 `detect_tier() >= FULL` 时传入 `conn` + `workspace_id`：

```python
from saw.config.settings import detect_tier
from saw.domain.value_objects import CapabilityTier

tier = detect_tier()
conn_to_pass = conn if tier >= CapabilityTier.FULL else None
related = compute_related_pages(slug, wiki_repo, top_k=8, conn=conn_to_pass, workspace_id=workspace_id)
```

## 降级策略

| 条件 | 行为 |
|---|---|
| tier=FULL + 页面有向量 | 4-signal 评分（embedding 权重 2.5） |
| tier=FULL + 页面无向量 | 跳过 embedding 信号，仅 3-signal（embedding_score=0） |
| tier=FULL + 全部无向量 | 完全降级到 3-signal，行为不变 |
| tier<FULL（LIGHTWEIGHT/OFFLINE） | conn=None → 不查 embedding，3-signal 不变 |

## 安全考量

- **workspace 隔离**：embedding 向量查询 `WHERE workspace_id = ?`，跨 workspace 不泄漏。`compute_related_pages` 透传 `workspace_id`（参照 ADR-007 读取隔离范式）。
- **3-signal 不改动**：tier<FULL 时 3-signal 逻辑完全保持，无回归风险。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-LINK-1（suggest 含语义相似页面） | `tests/unit/test_related_pages_embedding.py`（新建）：importorskip + seed 2 pages 无共享 tag/link 但语义相似 → suggest → 相似页面出现在建议列表 + reasons 含 "semantic similarity" | 无共享 tag/link 的语义相似页面出现 + reasons 含语义信号 |
| AC-LINK-2（无 [learn] 保持 3-signal） | `tests/unit/test_related_pages_embedding.py`：mock `embeddings_available()=False` → suggest → 行为与 v1.8.0 一致（3-signal 评分 + 无 embedding reason） | 3-signal 行为不变 + 无 embedding reason + 无异常 |
| AC-LINK-3（语义不相似排名下降） | `tests/unit/test_related_pages_embedding.py`：seed 3 pages（A=爬虫+tag python, B=Web框架+tag python, C=爬虫+tag python）→ suggest A → C 排名高于 B（因 A-C 语义相似 > A-B） | 共享 tag 但语义不同的页面排名下降 |

## 实现就绪度

- [x] `compute_related_pages()` 签名可扩展（增 conn + workspace_id 可选参数）
- [x] 3-signal 逻辑不改动（tier<FULL 时行为不变）
- [x] embedding 信号加权设计（权重 2.5，可调）
- [x] `cosine_similarity()` 既有可复用
- [x] workspace 隔离覆盖（WHERE workspace_id=?）
- [x] AC 覆盖 3/3
- [x] 降级策略完备（4 种条件全覆盖）
- [ ] embedding 信号权重 2.5 需 benchmark 调优 [TBD]
- [ ] 相似度缓存 [TBD]（后续优化）
