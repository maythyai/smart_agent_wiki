---
id: SPEC-F-I-2
title: Learn CLI（distill 在线 + gaps）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-intelligence-adaptation-v1.5.0.md
pms_ref: .csp/product-spec/PMS-intelligence-adaptation.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-I-2
complexity: S
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-I-2]
---

# SPEC-F-I-2: Learn CLI surface

## 实现 delta（ground 自源码）
- 新增 `drivers/cli/commands/learn_cmd.py`（Typer sub-app：distill/gaps），`main.py` 注册 `app.add_typer(learn_app, name="learn")`。
- 引擎层复用：`engines/learn/distiller.py:Distiller.extract_sop`（LLMRouter.extract_claims 在线路径）+ `run_distillation(approved_file)`；`engines/learn/trends.py:TrendSenser.detect_gaps`。**不改引擎**。
- distill 需 LLMRouter 装配（在线）；CI 无 LLM → 测试 mock LLMRouter.extract_claims 返回固定 SOP dict。
- gaps 需 claims_repo + wiki_repo 装配（复用 query_cmd 既有 repo 装配）。

## 接口契约
- `saw learn distill [--approved approved.yaml]` → 在线产 SOP（非空），存 `.saw/sops/*.yaml`，打印 name/trigger/steps。
- `saw learn gaps` → 输出 KnowledgeGap 列表（topic/coverage）。
- 无 LLM 时 distill 报错退出 1（"LLM unavailable"），不静默 fallback（PRD：在线路径，离线 fallback 留 engine 内部）。

## UI/DB
- 无新 DB（SOP 落 `.saw/sops/` 文件；gaps 从 claim/wiki repo 读）。

## 后端逻辑
- distill：load approved.yaml → group by action → extract_sop（LLM）→ save。
- gaps：wiki.list_pages → per page stem → claims.search → 无结果=gap。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-LR-1（distill 在线产 SOP 非空） | `tests/unit/engines/learn/test_distiller_cli.py`：mock LLMRouter → assert SOP.steps 非空 + `.saw/sops/` 落盘 |
| AC-LR-2（gaps 输出列表） | `test_trends_cli.py`：fresh repo + 空 wiki → gaps 列表 |

## 实现就绪度
- [x] 引擎全就绪（distiller/trends）
- [x] AC 覆盖 2/2
- [TBD] LLMRouter 装配复用路径（mcp_cmd/web_cmd 既有）
