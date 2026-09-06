# PMS: e2e-tail — E2E 收尾轮

> 产品说明书（living baseline）。模块边界 = PRD 模块边界，下游 02/03 不得越界。

## 模块边界

**slug**: `e2e-tail`

**边界一句话**：E2E 收尾轮——ingest 目录递归 + 真实 vLLM embedding benchmark + REST `/workflows` 兼容别名+CHANGELOG + coverage 棘轮 67 + 闭合 Q1/Q3 复盘补记。

**做什么**：
1. 修复 `saw ingest <dir>` 递归遍历目录下文件（Bug A）
2. 用 vLLM `qwen_embedding@8001` 真测 semantic vs BM25 召回 + P99 + cache 命中率（Q2/O1）
3. REST `GET /workflows` 加 `name`/`workflow` 别名 + 建 `CHANGELOG.md` 标注行为变更（O3）
4. `pyproject.toml` `fail_under` 65→67，补测达 67%（O2）
5. retrospective Q1/Q3 标闭合（commit `84e1776` 证据）

**不做什么**：
- 不引入新能力（纯 bug fix + benchmark + doc + coverage）
- 不改 embedding provider（v1.12.0 已 pivot 到 API，本轮 baseline 内含 `84e1776`）
- 不做 per-request workspace 注入（N3/K2，v2.0 架构候选）
- 不做 agent 活动聚合（M2，续留）
- 不做链接自动 apply（L2，续留）
- 不规范 tag 指向（O4，续留）
- benchmark 不用 mock 假向量（须真实 vLLM）

## 验收形态

| AC ID | 验收点 | 来源 |
|---|---|---|
| AC-A-1..5 | ingest 目录递归、空目录、部分失败、子目录、排除内部目录 | PRD §3.1 |
| AC-B-1..4 | 真实 API 召回、P99、cache 命中率、vLLM 不可达报错 | PRD §3.2 |
| AC-C-1..3 | REST 别名兼容、CHANGELOG 存在、CHANGELOG 回溯 | PRD §3.3 |
| AC-D-1..2 | fail_under=67、实际覆盖率 ≥67% | PRD §3.4 |
| AC-E-1..2 | Q1/Q3 闭合标注 | PRD §3.5 |

**NFR**：2076+ passed 不回归；ruff 0；smoke 6/6；benchmark 单次 < 5 min；100 文件目录 ingest < 60s（无 LLM）。

## 对外接口契约摘要

- `saw ingest <dir>`：目录参数递归遍历，返回聚合 IngestResult（claim_count/entity_count/relation_count 汇总，parser="directory-batch"）
- `GET /api/v1/workflows`：响应 item 新增 `name`/`workflow` 别名字段（= `definition_name`，镜像值），既有字段不变
- benchmark 脚本/命令 `[TBD]`：输出结构化结果（recall_semantic/recall_bm25/p99_ms/cache_hit_rate）

## 关联 PRD

- `docs/prd/PRD-e2e-tail-v1.13.0.md`（status: Approved, target_version: v1.13.0）

## 关联 Spec

- `.csp/specs/SPEC-F-R-1.md`（F-R-1 ingest 目录递归遍历）
- `.csp/specs/SPEC-F-R-2.md`（F-R-2 真实 embedding benchmark 脚本）
- `.csp/specs/SPEC-F-R-3.md`（F-R-3 REST /workflows 别名 + CHANGELOG）
- `.csp/specs/SPEC-F-R-4.md`（F-R-4 coverage 棘轮 67）
- `.csp/specs/SPEC-F-R-5.md`（F-R-5 Q1/Q3 闭合补记）

## 状态

- ready（边界已定，待 02 拆解 + 03 技术方案）

## 上游来源

- `.csp/artifacts/retrospective-v1.12.0.md`#Q2-O1-O3-O2 + E2E Bug A
- `docs/strategy/ROADMAP.md`#v1.13.0
