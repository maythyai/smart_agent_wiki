---
id: PRD-hardening-tail-v1.3.0
title: 硬化尾巴 + 技术债清理
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-03"
product_type: platform
feature_count: 4
mvp_scope: [e2e-usability, claim-alignment, test-gate, tech-debt]
thin_sections: [4]
upstream_source: "docs/strategy/ROADMAP.md + .csp/artifacts/retrospective-v1.2.0.md (findings F1-F6)"
target_version: v1.3.0
roadmap_ref: ROADMAP
related_pms:
  - .csp/product-spec/PMS-e2e-usability.md
  - .csp/product-spec/PMS-claim-alignment.md
  - .csp/product-spec/PMS-test-gate.md
related_specs:
  - .csp/specs/SPEC-F-A-2.md   # ingest+compile 冒烟（Wave 2，spec 已就绪）
  - .csp/specs/SPEC-F-A-3.md   # query 冒烟
  - .csp/specs/SPEC-F-A-4.md   # govern+learn 冒烟
  - .csp/specs/SPEC-F-A-5.md   # 离线 fallback 冒烟（Wave 3）
  - .csp/specs/SPEC-F-A-6.md   # CI smoke job
  - .csp/specs/SPEC-F-B-2.md   # 能力清单
  - .csp/specs/SPEC-F-B-3.md   # 文档修正
  - .csp/specs/SPEC-F-D-2.md   # trace_id 贯穿
  - .csp/specs/SPEC-F-E-2.md   # coverage 门禁
  - .csp/specs/SPEC-F-E-3.md   # CI 集成
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
related_retrospective: .csp/artifacts/retrospective-v1.2.0.md
---

# PRD-hardening-tail-v1.3.0：硬化尾巴 + 技术债清理

> v1.2.0 闭环后的新一轮 01。延续 PRD-product-hardening-v1 的 Wave 2/3（spec 已就绪，无需重拆），并纳入 v1.2.0 复盘 findings F2/F3/F4 的新技术债范围。目标：把产品加固弧线收口，为 v1.4.0 平台化/团队协作扫清基线。

## 1. 背景与动机（源自复盘 findings）

v1.2.0 完成了 Wave 1（10/10，安全/可观测/测试门禁基线，1853 tests green）。复盘（retrospective-v1.2.0.md）回流 6 条 findings：

- **F2（中）**：ruff baseline 未绿——项目无 ruff 配置，`timezone.utc`/`except Exception` 是全库既有 pattern，默认 lint 报 ~7 处 UP017/文件。v1.2.0 决策"新代码匹配 pattern，不顺手重构"——本周期收口。
- **F3（中）**：roadmap 现实漂移——v1.1.0 narrative 主题与实际发布不符；v1.2.0 narrative 未重写。本周期重写 roadmap 使主题链对齐。
- **F4（中）**：v1.2.0 行为变更（JSON 日志默认 ON、/health/ready engine-aware 503）未入迁移文档。
- **F6（计划）**：Wave 2（7 Task）+ Wave 3（3 Task）延后——本周期主实施范围。

## 2. 范围（4 Feature 组）

### F-A-tail：端到端冒烟链收口（Wave 2+3）
延续 SPEC-F-A-2/3/4/5/6。`saw smoke` 骨架已就绪（v1.2.0），本周期填实 ingest/query/govern/learn 节点体 + 离线 fallback + CI smoke job。
- **AC-E2E-1**（续）：`saw smoke --full` 全节点 PASS，失败节点定位到 file:line。
- **AC-E2E-2**：离线（无 LLM/API）模式降级标记可见，不崩溃。

### F-B-tail：宣称一致性（Wave 2）
延续 SPEC-F-B-2/3。claim_diff MVP 已就绪（v1.2.0），本周期产能力清单（CAPABILITIES.md，per-capability file:line）+ 文档修正。
- **AC-ALIGN-2**：`docs/CAPABILITIES.md` 与代码一致，deep_audit 历史标注豁免。

### F-D-tail：可观测 trace 贯穿（Wave 2）
延续 SPEC-F-D-2。trace_id contextvar 已在 request 层（v1.2.0 收敛 logger），本周期贯穿 engines→sinks（dispatcher 线程继承已验，补 engine/sink 落点）。
- **AC-OBS-1**：任一写操作的全链日志携带同一 request_id。

### F-E-tail：CI 测试门禁闭环（Wave 2+3）
延续 SPEC-F-E-2/3。coverage 基线 62%/64% 已测（v1.2.0），本周期加 ≥80% 核心门禁 + CI 集成（单测+冒烟+coverage+报告）。
- **AC-TEST-1**：核心引擎 coverage < 80% 阻断 PR。
- **AC-TEST-2**：CI 全绿才允许合并。

### F-debt（新，源自 F2/F3/F4）
- **F2 ruff 收口**：加 `pyproject [tool.ruff]` 配置（显式 select + noqa 策略），或全库统一 `timezone.utc`→`UTC` + 精确 except。一次清零 baseline。
- **F3 roadmap 重写**：v1.1.0/v1.2.0 narrative 主题对齐实际发布；重定义 v1.3.0/v1.4.0 主题。
- **F4 迁移文档**：QUICKSTART/MIGRATION 补"v1.2.0 行为变更"段（JSON 日志默认、/health/ready 503）。

## 3. 非目标（本周期不做）
- 平台化/团队协作新能力（留 v1.4.0，见 roadmap）。
- F1 subagent 静默写入——工具链问题，本周期以"Lead 核验"流程缓解，不单独立 feature（无代码解）。
- agent execute() 收据钩子（C-2 deferred）——需架构接入，留 v1.4.0+。

## 4. 里程碑
- M2（Wave 2 完成）：核心链路冒烟全绿 + 宣称一致 + trace 贯穿 + coverage 门禁。
- M3（Wave 3 完成）：CI 全闭环 + 离线可用 → 05 可交付 → v1.3.0 发布。
- M-debt：F2/F3/F4 收口（可与 Wave 并行，F2 是共享资源串行）。

## 5. 风险
- **F1 复发**：subagent 静默写入。缓解：Lead 每 worktree `git status` 核验 + 子 agent 写后回读。
- **F2 范围蔓延**：ruff 全库修可能触及大量文件。约束：只修 lint 规则触发点，不顺手重构逻辑；单 commit 收口。
- **Wave 2 依赖 A1**（已就绪），无阻塞；E2 依赖 E1（已就绪）。

## 6. 下游衔接
- → 02 拆解：F-A/B/D/E-tail 已有 1:1 spec（沿用 v1 拆解，不重拆）；F-debt 需拆 3 个新 Task（ruff/roadmap/迁移文档）。
- → 03 技术：spec 多数 status=Draft→Updated（实机核验后）；F-debt 无新 spec（直接 task）。
- → 04 任务：Wave 2/3 沿用既有 WBS Task；F-debt 加 3 Task，重排 Wave（F2 ruff 串行共享）。
