# Decomposition Delta — v1.3.0（2026-09-03）

> 新一轮 02 拆解 delta。源自 PRD-hardening-tail-v1.3.0 + retrospective-v1.2.0.md findings F2/F3/F4。
> Wave 2/3（F-A-2..6 / F-B-2,3 / F-D-2 / F-E-2,3）已有 1:1 spec 与 FEATURE-DETAILS（v1 拆解，不重拆），本 delta 仅追加 F-debt 3 feature。

## 新增 Feature（domain Z tech-debt）

| id | name | priority | complexity | depends_on | wave | blocked_by | source finding |
|---|---|---|---|---|---|---|---|
| F-Z-1 | ruff baseline 收口（配置+全库修） | P1 | S | — | 3 | F-A-2,A-3,A-4,F-D-2（src 改动后串行） | F2 |
| F-Z-2 | roadmap narrative 重写 | P2 | S | — | 2 | — | F3 |
| F-Z-3 | v1.2.0 行为变更迁移文档 | P1 | S | — | 2 | — | F4 |

## DAG delta
- 新增 subgraph WZ（Z1/Z2/Z3）。
- Z1（ruff）是共享资源（pyproject + 全 src），**串行末位**（所有 src 改动完成后），虚线依赖 E3。
- Z2/Z3 独立（docs），可与 Wave 2 src 并行。
- 无新环；Z1 串行不进并行组。

## Wave 重排（v1.3.0）
- **Wave 2（并行）**：F-A-2, F-A-3, F-A-4, F-B-2, F-B-3, F-D-2, F-E-2 + F-Z-2, F-Z-3（docs 并行）
- **Wave 3**：F-A-5, F-A-6, F-E-3（依赖链）→ 末位 F-Z-1（ruff 串行收口）

## 下游消费
- → 03：Wave 2/3 spec status Draft→Updated（实机核验后）；F-Z-1/2/3 无新 spec（直接 task，pms 已存）。
- → 04：Wave 2/3 沿用既有 WBS Task（T-F-A-2-1 等）；F-Z 加 3 Task（T-F-Z-1/2/3），重排 Wave。
