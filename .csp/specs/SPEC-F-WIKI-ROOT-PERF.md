---
id: SPEC-F-WIKI-ROOT-PERF
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-20
status: approved
prd_ref: PRD-wiki-root-perf-v1.34.0
target_version: v1.34.0
---

# SPEC — v1.34.0 wiki 根性能 + coverage 推进

## F-1: wiki 根改 wiki/
**文件**: `src/saw/drivers/web/app.py:575`
```python
# 改前: wiki_path = Path(".")
# 改后:
wiki_path = Path("wiki")
```
**证据**: `app.py:575` 当前 `Path(".")` → WikiRepository.rglob("*.md") 扫整个 cwd（.csp/specs/.claude/skills/.cursor/docs = 数百非 wiki .md）→ index_all ~80s。改后只扫 wiki/（collections/concepts/entities/sources = 实际 wiki 内容）→ <1s。

**AC**: wiki/ dir 存在 ✓（已验证）。index_all 扫描 wiki/*.md only。saw web 启动 <5s。

## F-2: coverage → 70%
**补测试目标模块**（thin coverage）:
1. `src/saw/drivers/cli/commands/feed_cmd.py` (12%) — RSS feed 命令 CRUD。
2. `src/saw/ingest/pipeline/phases/parse.py` (13%) — 解析阶段。
3. `src/saw/ingest/pipeline/phases/extract.py` (14%) — 提取阶段。
4. `src/saw/ingest/pipeline/phases/validate.py` (15%) — 校验阶段。

**测试计划**: 每模块补 2-3 个 unit test（mock 输入 → 验证输出/副作用）。目标推 ~500 covered lines（68.42% → 70%）。

## 测试
- `tests/unit/drivers/test_feed_cmd_coverage.py`: feed CRUD 命令。
- `tests/unit/engines/ingest/test_pipeline_phases.py`: parse/extract/validate 阶段。
- pytest --cov-fail-under=70（提升 gate 从 67 → 70）。
- 全量回归 + ruff 0。

## deferred → v1.34.1
- AUDIT-F-01 god-files 拆分 + stale-freshness contamination。
