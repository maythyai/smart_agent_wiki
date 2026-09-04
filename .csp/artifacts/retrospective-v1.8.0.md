# 复盘 — v1.8.0 Smart Linking + AI Summarization（2026-09-04）

> 07 闭环校验。findings 回流下一轮 01。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-smart-linking-v1.8.0 Approved；3 SPEC 1:1（无 ADR，复用引擎无架构变更）|
| Spec → Task | ✅ | WBS 2 Task（T-F-L-1 bundle suggest+audit / T-F-L-3 summarize）覆盖 3 Feature |
| Task → commit | ✅ | dc56e0a（impl + tests + DEV-LOG）|
| AC → 测试 | ✅ | AC-LINK-1(suggest 排除已链) / AC-LINK-2(孤儿+断链) / AC-SUM-1(在线摘要+无LLM报错) |
| commit → tag | ✅ | v1.8.0 annotated @ 0ae5149 |
| 测试/lint | ✅ | 1983 passed/3 skipped；ruff src/+tests/ 0 errors；smoke 6/6 |
| 构建 | ✅ | wheel smart_agent_wiki-1.8.0 |

## v1.8.0 度量
- 3 Feature done（新能力：smart linking suggest + audit + AI summarize）
- 新增测试 6（links 3 + summarize 3）
- 全量 1983 passed（+6 vs v1.7.0）；coverage 64.2%（未变——新 CLI 无引擎覆盖增量）；fail_under=64 持
- 转新能力首轮：复用 query/LLM 引擎，无新引擎

## Findings（回流下一轮）

### L1 — suggest 相关度启发式噪声 [低]
compute_related_pages 是 3-signal 启发式（shared tags/links/type），大库可能噪声。top_k 限制 + reason 透明缓解。
- **回流 03/05**：若噪声大，加 embedding 相似度（需 sentence-transformers）或调权重。

### L2 — 链接自动应用未做 [低]
suggest 只输出建议，用户须手改文件加 `[[link]]`。
- **回流 02**：后续可加 `saw links apply <page> --suggestion` 自动插入（须用户确认，破坏性）。

### L3 — coverage 未增 [低]
本轮新 CLI 覆盖增量小（CLI 薄 wiring，引擎已覆盖），全量 64.2% 未动。compile/compiler.py 17% 仍是 K1 gap。
- **回流 04/05**：K1 续留；compile/compiler 深覆盖仍是 north-star 杠杆。

## 下游衔接 → v1.9.0（新一轮 01）
- 新能力可续：embedding 语义搜索（v4.2 留尾）/ agent 可视化（v4.3）/ desktop 完成（v4.4）。
- K1（coverage 65）/ K2（per-request ws）续留 finding，可择机清。
- smart-linking 本轮首版，suggest/audit/summarize 三 CLI 可作后续 embedding 增强的基线。
