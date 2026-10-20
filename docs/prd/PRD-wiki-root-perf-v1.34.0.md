---
id: PRD-wiki-root-perf-v1.34.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-20
status: approved
roadmap_ref: ROADMAP
target_version: v1.34.0
type: feature
see_also: .csp/artifacts/retrospective-v1.33.0.md (lesson) | .csp/audit/AUDIT-FINDINGS-v1.30.0.json (AUDIT-F-04)
---

# PRD — v1.34.0 wiki 根性能 + coverage 推进 (feat MINOR)

## 四读前置
1. **① 规范**: prompts/prevention-norms.md + version-management.md（G-01~G-08 遵守）。
2. **② findings**: AUDIT-F-04（coverage 68.42% < 70 宣称）→ 入口作验收项。v1.33.0 retro lesson（wiki 根=cwd 扫数百 .md 致 80s 启动）→ 入口。
3. **③ 对账**: lifecycle `released-v1.33.0 / v1.34.0` = ROADMAP。无漂移。
4. **④ BLOCKED**: 无续留 BLOCKED（E2E-BLOCKED-01 已 closed v1.33.0）。

## 范围（2 feat）
1. **wiki 根性能**（v1.33.0 retro lesson）: `app.py:575` `Path(".")` → `Path("wiki")`——WikiRepository 只扫 wiki/（4 namespace 子目录）而非整个 cwd（含 .csp/.claude/.cursor/docs 数百 .md）。saw web 启动从 ~80s → <1s。
2. **coverage 推进**（AUDIT-F-04）: 补 thin 模块测试（feed_cmd 12%, parse 13%, extract 14%, validate 15%, learn 16%）推 coverage 68.42% → ≥70%。

## 非目标（deferred → v1.34.1）
- **AUDIT-F-01 god-files 拆分**（app.py 755/engine.py 631/compiler.py 663 >600 行）: 大重构，拆 v1.34.1。解除条件 v1.34.0 released ✓。
- **stale-freshness contamination**（v1.31.1 deferred）: 需 FreshnessTracker 集成 → v1.34.1。

## GWT 验收
- **GWT-1**: Given saw web 启动；When wiki 根=wiki/；Then index_all 只扫 wiki/*.md（不扫 .csp/.claude），启动 <5s（之前 ~80s）。
- **GWT-2**: Given 补 thin 模块测试；When pytest --cov；Then coverage ≥70%（fail_under 70）。

## 成功指标
- saw web 启动 <5s（实测）。
- coverage ≥70%。
- pytest 0 fail / ruff 0 / tsc clean。
- 双闸门 exit 0。

## 风险
- R1: wiki 根改 wiki/ 后既有测试依赖 cwd wiki → 验证 wiki/ dir 存在（已确认 ✓）。
- R2: coverage 补测试可能不够到 70% → 尽力推 + 诚实标残余 gap。
