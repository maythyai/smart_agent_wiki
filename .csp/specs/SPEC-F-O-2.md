---
id: SPEC-F-O-2
title: compile/compiler.py 深覆盖（30 函数 17%→高，fail_under 64→65）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
prd_ref: docs/prd/PRD-debt-closure-v1.11.0.md
pms_ref: .csp/product-spec/PMS-debt-closure.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-O-2
complexity: L
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
ac_coverage: 2/2
related_tasks: [.csp/tasks/TASKS-DELTA-v1.11.0.md#T-F-O-2]
---

# SPEC-F-O-2: compile/compiler.py 深覆盖

## 实现 delta（ground 自源码）

- **目标文件**：`src/saw/engines/compile/compiler.py`（`WikiCompileEngine` 类，30 个 def，当前 ~17% 覆盖）。
- **测试目录**：`tests/unit/engines/compile/` **当前不存在**（ground 确认），本轮新建。
- **fail_under**：`pyproject.toml` `[tool.coverage.report]` `fail_under` 从 `64` → `65`。
- **不改实现**：仅加测试，不改 `compiler.py`（PRD §3.2 明确）。

## 未测函数清单（ground 自 `compiler.py`）

| 函数 | 行号 | 功能 | 优先级 | 测试策略 |
|---|---|---|---|---|
| `__init__` | L67 | 初始化 vault_root/wiki_root/claims_repo/wiki_repo/llm | P1 | fixture 初始化断言 |
| `attach_concept_graph` | L92 | 挂载 ConceptGraphEngine | P2 | mock graph 断言 |
| `_rebuild_concept_graph` | L106 | rebuild_from_wiki 调用 | P2 | mock graph rebuild + 异常降级 |
| `initialize` | L118 | _wiki/ 目录初始化 + index/log 骨架 | P0 | tmp_path → initialize → 断言目录/文件存在 |
| `compile_full` | L147 | Phase A + Phase B 全量编译 | P0 | tmp vault seed → compile_full → 断言 pages_created |
| `compile_incremental` | L197 | 增量编译 + cascade | P0 | seed + compile_incremental → 断言 pages_updated |
| `get_index` | L239 | 解析 index.md | P1 | compile_full 后 get_index → 断言 entries |
| `get_log` | L248 | 读 recent log | P1 | compile 后 get_log → 断言 entries |
| `read_page` | L258 | 读单页 | P1 | compile 后 read_page → 断言 metadata |
| `list_pages` | L267 | 列所有页 | P1 | compile 后 list_pages → 断言 count |
| `_content_hash` | L282 | SHA-256 内容去重 | P0 | 两个同内容文件 → 去重 |
| `_scan_vault_sources` | L297 | 扫描 Vault 源文档 | P0 | seed 多文件 → 断言排除 _wiki/.saw |
| `_classify_sources_by_topic` | L316 | 按目录分类 | P1 | 多目录 seed → 断言 topic 映射 |
| `_infer_topic` | L324 | 从路径推断 topic | P1 | 多路径 → 断言 topic |
| `_ensure_topic_directories` | L337 | 创建 topic 子目录 | P1 | classify → ensure → 断言目录存在 |
| `_compile_source` | L393 | 编译单文档 | P0 | seed md → compile_source → 断言 page |
| `_detect_page_type` | L407 | 页面类型检测 | P1 | 多内容 → 断言 FAQ/HOWTO/CONCEPT |
| `_assess_confidence` | L419 | 置信度评估 | P1 | 长/短/有引用/无引用 → HIGH/MEDIUM/LOW |
| `_compile_content` | L443 | 内容编译入口（LLM/rule-based 路由） | P0 | mock LLM + 无 LLM → 两路径 |
| `_rule_based_compile` | L461 | 规则编译 | P0 | 无 LLM → 断言 title + degraded banner |
| `_llm_synthesize` | L497 | LLM 合成 | P1 | mock LLM.complete → 断言 output |
| `_extract_title` | L504 | 提取标题 | P1 | H1/no-H1 → 断言 |
| `_slugify` | L511 | slug 生成 | P0 | 多种输入 → 断言 |
| `_write_page` | L518 | 写页面到磁盘 | P0 | write → read → 断言 metadata 注释 |
| `_update_index_entry` | L541 | 更新 index.md 条目 | P0 | compile → parse index → 断言 entry |
| `_update_index_header` | L562 | 更新 index.md header stats | P1 | compile → 断言 "Total pages: N" |
| `_cascade_update` | L587 | 级联更新（引用页面记录） | P0 | seed A/B，B 引用 A → update A → 断言 log 含 B |
| `_append_log` | L612 | 追加 log.md | P1 | compile → log.md → 断言 entry |
| `_parse_index` | L620 | 委托 parser | P1 | delegate → 断言 WikiIndex |
| `_parse_index_row` | L626 | 委托 parser | P2 | delegate → 断言 entry |
| `_parse_page` | L632 | 委托 parser | P1 | delegate → 断言 page |
| `_parse_log` | L638 | 委托 parser | P1 | delegate → 断言 entries |
| `_render_empty_index` | L644 | 委托 parser | P1 | delegate → 断言 template |
| `_render_index` | L650 | 渲染 index → Markdown | P0 | WikiIndex → render → 断言 markdown |
| `_render_log_header` | L658 | 渲染 log header | P2 | 断言 "Compile Log" header |
| `is_initialized` | L88 | property 检查初始化 | P2 | before/after initialize |
| `wiki_root` | L84 | property | P2 | 断言 path |

> 共 30+ def（含 property/attach）。高优先级 P0 函数 12 个，覆盖后预计 compiler.py 覆盖率从 17% → ~70%+。

## 测试用例表

| 用例 ID | 场景 | 类型 | 断言 | AC |
|---|---|---|---|---|
| TC-COMP-01 | `initialize` 创建 _wiki/ + index.md + log.md | unit | 目录存在 + 文件存在 + log 含 "initialize" | AC-COV-1 |
| TC-COMP-02 | `compile_full` 全量编译 3 源文档 → 3 pages_created | unit | pages_created=3 + index.md 含 3 entries | AC-COV-1 |
| TC-COMP-03 | `compile_incremental` 增量编译 → pages_updated | unit | pages_updated 含目标 page | AC-COV-1 |
| TC-COMP-04 | `_content_hash` 同内容去重 → pages_unchanged | unit | 第二个同内容文件进 pages_unchanged | AC-COV-1 |
| TC-COMP-05 | `_scan_vault_sources` 排除 _wiki/.saw/.git | unit | sources 不含 _wiki/ 内文件 | AC-COV-1 |
| TC-COMP-06 | `_detect_page_type` FAQ/HOWTO/CONCEPT 检测 | unit | 各类型正确返回 | AC-COV-1 |
| TC-COMP-07 | `_assess_confidence` HIGH/MEDIUM/LOW | unit | 长内容+引用→HIGH；短→LOW | AC-COV-1 |
| TC-COMP-08 | `_compile_content` LLM 路径（mock）→ 合成输出 | unit | mock LLM.complete → 输出 >100 chars | AC-COV-1 |
| TC-COMP-09 | `_compile_content` rule-based 路径（无 LLM）→ 标题+内容 | unit | 输出含 "# {title}" | AC-COV-1 |
| TC-COMP-10 | `_compile_content` LLM 失败降级 → degraded banner | unit | 输出含 "⚠️ Rule-based compile" | AC-COV-1 |
| TC-COMP-11 | `_slugify` 多种输入 → URL-friendly | unit | "My Page!" → "my-page" | AC-COV-1 |
| TC-COMP-12 | `_write_page` 写 + 读 → metadata 注释正确 | unit | 读回含 `<!-- metadata:` + type/confidence | AC-COV-1 |
| TC-COMP-13 | `_update_index_entry` 条目更新 | unit | index.md 含新 entry | AC-COV-1 |
| TC-COMP-14 | `_update_index_header` total count 更新 | unit | "Total pages: N" 正确 | AC-COV-1 |
| TC-COMP-15 | `_cascade_update` 级联 → log 含引用页 | unit | log.md 含 "Cascade" + 引用页 | AC-COV-1 |
| TC-COMP-16 | `_render_index` WikiIndex → Markdown | unit | 输出含 "## {topic}" + table header | AC-COV-1 |
| TC-COMP-17 | `_extract_title` H1 / fallback | unit | H1 → 提取；无 H1 → fallback | AC-COV-1 |
| TC-COMP-18 | `get_index` / `get_log` / `read_page` / `list_pages` | unit | compile 后各读取方法返回正确 | AC-COV-1 |
| TC-COMP-19 | `is_initialized` / `wiki_root` property | unit | before/after initialize 布尔正确 | AC-COV-1 |
| TC-COMP-20 | `attach_concept_graph` + `_rebuild_concept_graph` | unit | mock graph rebuild 被调用 + 异常降级 | AC-COV-1 |
| TC-COV-01 | `pyproject.toml` fail_under=65 | config | grep `fail_under = 65` | AC-COV-2 |

## 测试文件结构

```
tests/unit/engines/compile/
├── __init__.py
├── conftest.py          # tmp_vault fixture（tmp_path + seed md files）
├── test_compiler_init.py     # TC-COMP-01/19/20（initialize/property/concept_graph）
├── test_compiler_compile.py  # TC-COMP-02/03/04（compile_full/incremental/dedup）
├── test_compiler_helpers.py  # TC-COMP-05/06/07/11/17（scan/detect/assess/slugify/title）
├── test_compiler_content.py  # TC-COMP-08/09/10/12（compile_content LLM/rule/write_page）
├── test_compiler_index.py    # TC-COMP-13/14/16（index entry/header/render）
├── test_compiler_cascade.py  # TC-COMP-15（cascade_update）
└── test_coverage_config.py   # TC-COV-01（fail_under=65）
```

## 测试 fixture 设计

```python
# conftest.py
import pytest
from pathlib import Path
from saw.engines.compile.compiler import WikiCompileEngine

@pytest.fixture
def tmp_vault(tmp_path):
    """临时 vault 目录，seed 3 个 md 文件。"""
    (tmp_path / "concepts" / "ml").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "concepts" / "ml.md").write_text(
        "# Machine Learning\n\nLong content about ML...\n" + "word " * 300
    )
    (tmp_path / "guides" / "how-to-train.md").write_text(
        "# How to Train\n\n```python\nstep 1\n```\n" + "word " * 100
    )
    (tmp_path / "faq" / "what-is-ml.md").write_text(
        "# What is ML?\n\nQ: What is ML?\nA: It is...\n"
    )
    return tmp_path

@pytest.fixture
def engine(tmp_vault):
    """WikiCompileEngine 实例（无 LLM）。"""
    return WikiCompileEngine(vault_root=tmp_vault)
```

## pyproject.toml 变更

```toml
[tool.coverage.report]
# T-F-O-2 (v1.11.0): ratcheted 64→65 (measured 65.x% after compile/compiler
# deep coverage). 65 = north-star target (PRD §1.3).
fail_under = 65
```

## API 契约

无新端点（测试基础设施，无用户交互）。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-COV-1（compile/compiler 深覆盖） | `tests/unit/engines/compile/test_*.py`（新建 7 文件 + conftest） | compiler.py 覆盖率 17%→[TBD]，全量 coverage ≥65% |
| AC-COV-2（fail_under 棘轮） | `tests/unit/engines/compile/test_coverage_config.py` | `pyproject.toml` `fail_under = 65` |

## 安全考量

- 测试使用 `tmp_path` fixture（pytest 内置临时目录），不污染生产数据。
- mock LLM 路径不依赖外部服务。

## 实现就绪度

- [x] 未测函数清单完整（30+ def，ground 自源码行号）
- [x] 测试用例表 20 条（覆盖 P0 + P1 函数）
- [x] 测试文件结构设计完整（7 测试文件 + conftest）
- [x] fixture 设计明确（tmp_vault + engine）
- [x] pyproject.toml 变更明确（fail_under 64→65）
- [x] AC 覆盖 2/2
- [ ] compiler.py 覆盖率目标值 [TBD]（须 05 实施后测量）
- [ ] 全量 coverage 65 是否仅靠 compiler 深覆盖即可达成 [TBD]（须实施后验证）
