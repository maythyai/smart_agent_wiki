---
id: SPEC-F-I-3
title: Token bench CLI（实测节省 %）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-intelligence-adaptation-v1.5.0.md
pms_ref: .csp/product-spec/PMS-intelligence-adaptation.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-I-3
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-I-3]
---

# SPEC-F-I-3: Token bench

## 实现 delta（ground 自源码）
- 新增 `drivers/cli/commands/token_cmd.py`（Typer sub-app：bench），`main.py` 注册 `app.add_typer(token_app, name="token")`。
- 复用 `token_optimizer/anatomy.py:estimate_tokens`（char-based, ~15% 精度）+ `session_tracker.py:SessionTracker` + `anatomy.py:AnatomyIndex`。
- bench 场景（确定性，非随机）：固定语料（`examples/` 下既有 markdown/code 样本 N 个）。
  - **baseline**：逐文件全量读取累计 token（每个文件 `estimate_tokens(content)`）。
  - **optimized**：anatomy 命中后只读摘要（`anatomy_hits` 替代全量）+ 重复读取走 cache（SessionTracker.track_read 的 warning）。
  - 输出：baseline_tokens / optimized_tokens / saved_pct / repeat_rate / anatomy_hit_rate。

## 接口契约
- `saw token bench [--corpus examples/]` → 打印对比表 + saved %。退出 0。
- 无 HTTP/MCP。

## UI/DB
- N/A（无 DB；只读语料目录）。

## 后端逻辑
- 跑两遍同一语料：一遍全量（baseline），一遍 anatomy-aware（optimized）→ 对比。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-TK-1（实测节省 % 对比基线） | `tests/unit/test_token_bench.py`：固定语料 → assert saved_pct > 0 + baseline > optimized + 确定性（同输入两次同输出） |

## 实现就绪度
- [x] AnatomyIndex/SessionTracker/estimate_tokens 全就绪
- [x] AC 覆盖 1/1
- 确定性语料须选既有 examples/（不造新 fixture 增维护）
