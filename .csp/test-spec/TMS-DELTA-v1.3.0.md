# TMS Delta — v1.3.0（2026-09-03）

> 新一轮 03 测试规约 delta。Wave 2/3 AC 已在既有 TMS-{module}.md 映射（增量用例，不重写）。
> 本 delta 仅记录 F-debt 新 AC + Wave 2/3 实施时新增的增量用例落点。

## F-debt 新 AC（无既有 TMS，本次新增）

| AC | 来源 | 用例落点 | 状态 |
|---|---|---|---|
| AC-LINT-1 | F-Z-1 | `tests/unit/test_lint_baseline.py`（新建）：`ruff check src/ tests/` 0 errors | [TBD-impl] |
| AC-DOC-1 | F-Z-2 | `tests/unit/test_roadmap_consistency.py`（新建）：ROADMAP 版本主题与 git tag 对齐 | [TBD-impl] |
| AC-DOC-2 | F-Z-3 | 手动校验（文档无单测必要）；MIGRATION 含 JSON 日志/health 行为变更段 | manual |

## Wave 2/3 增量用例落点（沿用既有 TMS，仅标 delta）

| Feature | AC | 既有 TMS | 增量用例 |
|---|---|---|---|
| F-A-2 | AC-E2E-1 | TMS-e2e-usability | `saw smoke --node ingest` PASS + compile 增量 |
| F-A-3 | AC-E2E-1 | TMS-e2e-usability | `saw smoke --node query`（关键词+NL） |
| F-A-4 | AC-E2E-1 | TMS-e2e-usability | `saw smoke --node govern/learn` |
| F-A-5 | AC-E2E-2 | TMS-e2e-usability | 离线模式降级标记 |
| F-A-6 | AC-E2E-1 | TMS-e2e-usability | CI smoke job exit-code gate |
| F-B-2 | AC-ALIGN-2 | TMS-claim-alignment | CAPABILITIES.md 与代码一致 |
| F-D-2 | AC-OBS-1 | TMS-observability | trace_id 贯穿 engines→sinks |
| F-E-2 | AC-TEST-1 | TMS-test-gate | 核心 coverage <80% 阻断 |
| F-E-3 | AC-TEST-2 | TMS-test-gate | CI 全绿才合并 |

## 约定
- 只产增量用例，不重写存量（per 03 TMS 纪律）。
- 未映射 AC 标 [TBD-impl]，实施时补。
