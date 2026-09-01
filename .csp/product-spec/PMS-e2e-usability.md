---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-product-hardening-v1.md]]"
  - "[[.csp/code-spec/saw/CODE-MODULE-SPEC.md]]"
seeAlso:
  - "[[code-spec/saw/knowledge-graph.json]]"
created: "2026-09-01"
updated: "2026-09-01"
---

# PMS: e2e-usability（端到端可用性闭环与冒烟基线）

## 模块边界
- **做什么**：为五引擎主链路（Ingest→Compile→Query→Govern→Learn）建立可复跑端到端冒烟基线；验收主链路在任意 commit 后可用；支持离线（无 LLM）fallback 路径冒烟。
- **不做什么**：不新增对外功能；不定义性能优化的实现方式（HOW）；不覆盖非核心引擎（research/synthesize 的深链路 [TBD] 归 V1.1）。
- **PMS 边界=PRD §3.1**：下游 Feature 拆解不得越出本边界。

## 验收形态
- 一条命令跑通 fresh 库端到端冒烟，退出码反映成败；逐节点 PASS/FAIL+耗时。
- 覆盖 ingest(md+url)/compile/wiki 增量/query(关键词+NL)/govern(lint+verify)/learn(distill)。
- 离线降级路径仍 PASS；每条 claim 可溯源原文。
- CI（ci.yml）自动跑冒烟。

## 接口契约摘要
- 入口：CLI 冒烟命令 `[TBD 命令名]`；退出码 0/1；输出节点级 PASS/FAIL。
- 数据：fresh `saw.db`；不依赖外部 LLM（fallback/mock）。

## 关联
- PRD: `docs/prd/PRD-product-hardening-v1.md` §3.1
- CMS ground: `engines/ingest/pipeline.py:102`、`engines/query/engine.py:82`、`engines/govern/governor.py:39`、`engines/compile/compiler.py`、`engines/learn/engine.py`
- 下游 Spec: [待 03 回填]
