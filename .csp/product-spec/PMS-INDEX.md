# PMS Index — 产品说明书 living baseline

> 全部产品模块边界索引。下游 02 拆解/03 技术方案**不得越出**本表模块边界；确需越界 → 先回 PRD 改边界再传播 PMS（变更见 PRD 变更同步节）。
> 变更只写 delta，里程碑归档时折叠进 canonical。

| slug | 边界（一句话） | 优先级 | 关联 PRD | 关联 Spec | 状态 | file |
|---|---|---|---|---|---|---|
| e2e-usability | 五引擎端到端冒烟基线与可用性验收 | P0 | PRD-product-hardening-v1 §3.1 | [待回填] | ready | PMS-e2e-usability.md |
| claim-alignment | 以代码为事实源校准宣称+能力清单 | P1 | PRD-product-hardening-v1 §3.2 | [待回填] | ready | PMS-claim-alignment.md |
| security-hardening | RBAC/限流/receipt 全链路闭环 | P0 | PRD-product-hardening-v1 §3.3 | [待回填] | ready | PMS-security-hardening.md |
| observability | 统一 logger+trace_id 贯穿+健康真实 | P1 | PRD-product-hardening-v1 §3.4 | [待回填] | ready | PMS-observability.md |
| test-gate | 核心引擎覆盖率门禁+CI 阻断 | P0 | PRD-product-hardening-v1 §3.5 | [待回填] | ready | PMS-test-gate.md |
| intelligence-adaptation | workflow 编排/Learn 在线/Token 实测/agent 一致性 + v1.4.0 债 H1/H2/H4/H5 | P0 | PRD-intelligence-adaptation-v1.5.0 §2 | [待回填] | ready | PMS-intelligence-adaptation.md |

## 状态约定
- ready（边界已定）/ built（spec 已产出）/ degraded（source 变更待 re-align）/ blocked
- MVP（P0）：e2e-usability + security-hardening + test-gate
