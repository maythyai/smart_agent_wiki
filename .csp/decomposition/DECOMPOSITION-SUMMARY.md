# Decomposition Summary — 供下游技术选型与 Spec 消费

## 项目概览
- 上游 PRD：`docs/prd/PRD-product-hardening-v1.md`（v1.0, 5 模块）
- 域数：6（A e2e-usability / B claim-alignment / C security-hardening / D observability / E test-gate / Z tech-debt），对齐 PMS + v1.3.0 debt delta
- 原子 Feature 数：23（P0=14 / P1=7 / P2=2；S=11 / M=12）— v1.3.0 增 F-Z-1/2/3，见 DECOMPOSITION-DELTA-v1.3.0.md
- 预估复杂度：以 S/M/L 表达；人日 `[TBD]`（团队规模/速率未提供，见 `assumptions`）
- 关键路径：F-A-1 → F-A-2 → F-A-5 → F-A-6 → F-E-3

## 技术维度汇总表（供 03 选型参考；本阶段只标需要，不选型）

| 维度 | 需要该能力的 Feature | 推荐优先级 |
|---|---|---|
| needs_database | A1-6, C2, D2, E1-2 | P0 |
| needs_cache | A3, D2 | P1 |
| needs_queue | C2（write_queue 已存）, D2 | P0 |
| needs_ai | A3（NL query）, A5（fallback） | P0 |
| needs_vector_store | — | — |
| needs_realtime | D2（trace 贯穿）, A6 | P1 |
| needs_file_storage | A2（vault）, B2 | P0 |
| needs_search | A3（FTS5 已存） | P0 |
| needs_scheduler | — | — |
| needs_notification | — | — |

> 注：多数维度 SAW 既有实现已具备（write_queue/FTS5/observability/RBAC/receipt），03 选型应"复用优先，不重造"。

## Feature 优先级矩阵

| Feature | 优先级 | 复杂度 | 依赖 | Wave | PMS 模块 |
|---|---|---|---|---|---|
| F-A-1 | P0 | S | — | 1 | e2e-usability |
| F-A-2 | P0 | M | A1 | 2 | e2e-usability |
| F-A-3 | P0 | M | A1 | 2 | e2e-usability |
| F-A-4 | P0 | M | A1 | 2 | e2e-usability |
| F-A-5 | P0 | M | A2,A3,A4 | 3 | e2e-usability |
| F-A-6 | P0 | S | A5 | 3 | e2e-usability |
| F-B-1 | P1 | M | — | 1 | claim-alignment |
| F-B-2 | P1 | M | B1 | 2 | claim-alignment |
| F-B-3 | P1 | S | B1 | 2 | claim-alignment |
| F-C-1 | P0 | M | — | 1 | security-hardening |
| F-C-2 | P0 | M | — | 1 | security-hardening |
| F-C-3 | P0 | S | — | 1 | security-hardening |
| F-C-4 | P0 | S | — | 1 | security-hardening |
| F-C-5 | P0 | M | — | 1 | security-hardening |
| F-D-1 | P1 | M | — | 1 | observability |
| F-D-2 | P1 | M | D1 | 2 | observability |
| F-D-3 | P1 | S | — | 1 | observability |
| F-E-1 | P0 | M | — | 1 | test-gate |
| F-E-2 | P0 | M | E1 | 2 | test-gate |
| F-E-3 | P0 | M | A6,E2 | 3 | test-gate |

## 一致性校验
- **PMS 边界**：20 Feature 的 `pms_module` 均在 PMS-INDEX 5 模块内 → 无越界 ✓
- **AC 归属**：PRD §6 共 11 条 AC，全部分配到对应 Feature（见各 yaml `acceptance_criteria`）→ 无丢失 ✓
- **DAG 无环**：拓扑序通过 ✓
- **thin 传递**：PRD §7 thin → 全部 Feature `assumptions` 标注估时 [TBD]；F-C-5 标 token 同源 [TBD]；F-E-1 标覆盖率基线 [TBD] ✓
- **Spec 数预期**：下游 03 Spec 数 = 原子 Feature 数 = 20（每 Feature → 一份 SPEC-F-*-n）

## manifest 回写
- decomposition 索引 item：`.csp/decomposition/DECOMPOSITION-SUMMARY.md`（source_type=doc, kind=feature, build_status=built）
- 单 Feature yaml 经 `FEATURE-MAP.md` 索引（不入 manifest，避免膨胀；可经 SUMMARY 定位）

## 下一步指向
- → 03 技术方案（含选型）：读 PRD + 本 decomposition + PMS + CMS；复用优先（write_queue/FTS5/observability/RBAC/receipt 已存）；按技术维度表出 ADR 落 `.csp/tech-decisions/`；TDD 边界对齐域；每 Feature 出一份 Spec（落 `.csp/specs/`）。
- → 04 任务拆解：读 `DEPENDENCY-GRAPH.md` + Spec，按 Wave 拆 Task 落 `.csp/tasks/`。
