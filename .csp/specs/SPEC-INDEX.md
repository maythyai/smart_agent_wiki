# Spec Index

> 1:1 对应 decomposition 20 原子 Feature（穷尽门控：Spec 数 == decomposition 原子 Feature 数 == 20）。
> 棕地 hardening feature，S/M 级精简 Spec，reference CMS，不重复 spec 已有 schema/API。

| spec_id | feature_id | title | complexity | pms_module | ac_coverage | file |
|---|---|---|---|---|---|---|
| SPEC-F-A-1 | F-A-1 | 冒烟命令骨架 | S | e2e-usability | 2/2 | SPEC-F-A-1.md |
| SPEC-F-A-2 | F-A-2 | ingest+compile 冒烟 | M | e2e-usability | 2/2 | SPEC-F-A-2.md |
| SPEC-F-A-3 | F-A-3 | query 链路冒烟 | M | e2e-usability | 2/2 | SPEC-F-A-3.md |
| SPEC-F-A-4 | F-A-4 | govern+learn 冒烟 | M | e2e-usability | 2/2 | SPEC-F-A-4.md |
| SPEC-F-A-5 | F-A-5 | 离线 fallback 冒烟 | M | e2e-usability | 2/2 | SPEC-F-A-5.md |
| SPEC-F-A-6 | F-A-6 | 冒烟纳入 CI | S | e2e-usability | 2/2 | SPEC-F-A-6.md |
| SPEC-F-B-1 | F-B-1 | 宣称 diff 脚本 | M | claim-alignment | 2/2 | SPEC-F-B-1.md |
| SPEC-F-B-2 | F-B-2 | 能力清单生成 | M | claim-alignment | 2/2 | SPEC-F-B-2.md |
| SPEC-F-B-3 | F-B-3 | 过时文档修正 | S | claim-alignment | 2/2 | SPEC-F-B-3.md |
| SPEC-F-C-1 | F-C-1 | 权限矩阵全覆盖 | M | security-hardening | 2/2 | SPEC-F-C-1.md |
| SPEC-F-C-2 | F-C-2 | Ed25519 receipt 闭环 | M | security-hardening | 2/2 | SPEC-F-C-2.md |
| SPEC-F-C-3 | F-C-3 | 限流双轨 | S | security-hardening | 2/2 | SPEC-F-C-3.md |
| SPEC-F-C-4 | F-C-4 | URL 守卫全覆盖 | S | security-hardening | 2/2 | SPEC-F-C-4.md |
| SPEC-F-C-5 | F-C-5 | 前后端 token 同源 | M | security-hardening | 2/2 | SPEC-F-C-5.md |
| SPEC-F-D-1 | F-D-1 | 统一 logger 收敛 | M | observability | 2/2 | SPEC-F-D-1.md |
| SPEC-F-D-2 | F-D-2 | trace_id 贯穿 | M | observability | 2/2 | SPEC-F-D-2.md |
| SPEC-F-D-3 | F-D-3 | 健康真实+JSON 日志 | S | observability | 2/2 | SPEC-F-D-3.md |
| SPEC-F-E-1 | F-E-1 | 覆盖率基线 | M | test-gate | 2/2 | SPEC-F-E-1.md |
| SPEC-F-E-2 | F-E-2 | 覆盖率门禁 | M | test-gate | 2/2 | SPEC-F-E-2.md |
| SPEC-F-E-3 | F-E-3 | CI 集成 | M | test-gate | 2/2 | SPEC-F-E-3.md |

## v1.5.0 delta（+8）
| spec_id | feature_id | title | complexity | pms_module | ac_coverage | file |
|---|---|---|---|---|---|---|
| SPEC-F-I-1 | F-I-1 | workflow CLI + resume | M | intelligence-adaptation | 2/2 | SPEC-F-I-1.md |
| SPEC-F-I-2 | F-I-2 | Learn CLI（distill+gaps） | S | intelligence-adaptation | 2/2 | SPEC-F-I-2.md |
| SPEC-F-I-3 | F-I-3 | Token bench CLI | S | intelligence-adaptation | 1/1 | SPEC-F-I-3.md |
| SPEC-F-I-4 | F-I-4 | agent 角色一致性 lint | S | intelligence-adaptation | 1/1 | SPEC-F-I-4.md |
| SPEC-F-Z-6 | F-Z-6 | ruff F841 收口 | M | intelligence-adaptation | 1/1 | SPEC-F-Z-6.md |
| SPEC-F-Z-7 | F-Z-7 | workspace 全路径路由 | L | intelligence-adaptation | 1/1 | SPEC-F-Z-7.md |
| SPEC-F-Z-8 | F-Z-8 | Cedar policy reload CLI | S | intelligence-adaptation | 1/1 | SPEC-F-Z-8.md |
| SPEC-F-Z-9 | F-Z-9 | query 测试 + coverage 棘轮 65 | M | test-gate | 1/1 | SPEC-F-Z-9.md |

## v1.6.0 delta（+4）
| spec_id | feature_id | title | complexity | pms_module | ac_coverage | file |
|---|---|---|---|---|---|---|
| SPEC-F-J-1 | F-J-1 | tree_mode+compiler workspace 注入 | M | debt-closure | 1/1 | SPEC-F-J-1.md |
| SPEC-F-J-2 | F-J-2 | insert workspace_id 持久化+ingest 透传 | M | debt-closure | 1/1 | SPEC-F-J-2.md |
| SPEC-F-J-3 | F-J-3 | query 深覆盖→65 | M | test-gate | 1/1 | SPEC-F-J-3.md |
| SPEC-F-J-4 | F-J-4 | policy reload Web admin 端点 | S | debt-closure | 1/1 | SPEC-F-J-4.md |

## v1.7.0 delta（+3）
| spec_id | feature_id | title | complexity | pms_module | ac_coverage | file |
|---|---|---|---|---|---|---|
| SPEC-F-K-1 | F-K-1 | graph workspace 隔离（migration v9 + 读写） | M | graph-workspace | 1/1 | SPEC-F-K-1.md |
| SPEC-F-K-2 | F-K-2 | scope 传播清理（显式 workspace_id） | S | graph-workspace | 1/1 | SPEC-F-K-2.md |
| SPEC-F-K-3 | F-K-3 | synthesize 覆盖 + 棘轮 64 | M | test-gate | 1/1 | SPEC-F-K-3.md |

## v1.8.0 delta（+3）
| spec_id | feature_id | title | complexity | pms_module | ac_coverage | file |
|---|---|---|---|---|---|---|
| SPEC-F-L-1 | F-L-1 | 智能链接建议（saw links suggest） | M | smart-linking | 1/1 | SPEC-F-L-1.md |
| SPEC-F-L-2 | F-L-2 | 链接审计（孤儿页+断链） | M | smart-linking | 1/1 | SPEC-F-L-2.md |
| SPEC-F-L-3 | F-L-3 | AI 摘要（saw summarize） | S | smart-linking | 1/1 | SPEC-F-L-3.md |

## v1.9.0 delta（+3）
| spec_id | feature_id | title | complexity | pms_module | ac_coverage | file |
|---|---|---|---|---|---|---|
| SPEC-F-M-1 | F-M-1 | workflow list durable（saw workflow list） | S | agent-viz | 1/1 | SPEC-F-M-1.md |
| SPEC-F-M-2 | F-M-2 | agent roster CLI（saw agents） | S | agent-viz | 1/1 | SPEC-F-M-2.md |
| SPEC-F-M-3 | F-M-3 | agent roster REST（GET /api/v1/agents） | S | agent-viz | 1/1 | SPEC-F-M-3.md |

## 校验
- Spec 数 == 20 + 8(v1.5.0) + 4(v1.6.0) + 3(v1.7.0) + 3(v1.8.0) + 3(v1.9.0) == decomposition 原子 Feature 数 ✓（1:1）
- 每个 feature_id 在 decomposition FEATURE-DETAILS 存在 ✓
- 每份 Spec ac_coverage 自检无未覆盖 AC ✓
