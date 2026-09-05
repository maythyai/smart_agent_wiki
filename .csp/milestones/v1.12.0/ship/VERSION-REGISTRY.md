# Version Registry — smart-agent-wiki

| SemVer | Tag | Status | Released | Deployed | Prod-Verified | Main Features | Breaking | Rollback | Roadmap 主题 |
|---|---|---|---|---|---|---|---|---|---|
| v1.0.1 | v1.0.1 | released | 2026-08-20 | null | null | MVP 可运行基线（四层存储+治理引擎+多代理） | No | No | MVP 基线 |
| v1.1.0 | v1.1.0 | released | 2026-08-22 | null | null | MCP 思考工具+Breadcrumb+JSON/表格提取器+41批缺陷 | No | No | MCP+前端可用性 |
| v1.2.0 | v1.2.0 | released | 2026-09-03 | null | null | Ed25519 receipt 链/裸路由检测/Token 校验/结构化日志 | No | No | 安全/可观测硬化 |
| v1.3.0 | v1.3.0 | released | 2026-09-03 | null | null | 五引擎冒烟基线/宣称-实现 diff/trace 贯穿/CI 覆盖率门禁 | No | No | 硬化尾巴+技术债 |
| v1.4.0 | v1.4.0 | released | 2026-09-03 | null | null | RBAC 深化/docker-compose.prod/workspace 隔离/F401 启用 | No | No | 平台化与团队协作 |
| v1.5.0 | v1.5.0 | released | 2026-09-03 | null | null | workflow 编排 resume/Learn 引擎/Token 优化/F841 启用 | No | No | 智能与自适应 |
| v1.6.0 | v1.6.0 | released | 2026-09-03 | null | null | workspace 读全路径+写隔离+query 深覆盖+policy web | No | No | 债务收口 II |
| v1.7.0 | v1.7.0 | released | 2026-09-03 | null | null | graph workspace 隔离+scope 清理+synthesize 深覆盖 | No | No | 债务收口 III |
| v1.8.0 | v1.8.0 | released | 2026-09-03 | null | null | saw links suggest+audit+saw summarize | No | No | Smart Linking+AI 摘要 |
| v1.9.0 | v1.9.0 | released | 2026-09-04 | null | null | saw workflow list+saw agents roster+GET /api/v1/agents | No | No | Agent & Workflow 可视化 |
| v1.10.0 | v1.10.0 | tagged-local | 2026-09-04 | null | null | embedding 索引+语义检索+smart-linking embedding signal+importorskip 测试 | No | Yes (rollback plan ready) | embedding 语义搜索 |
| v1.11.0 | v1.11.0 | tagged-local | 2026-09-05 | null | null | semantic cache+compiler 深覆盖+workflow REST unify DB+Spec 命名回更+hash 复核 | No | Yes (rollback plan ready) | 债务收口 IV / bug fix |
| v1.12.0 | v1.12.0 | tagged-local | 2026-09-05 | null | null | embedding provider 重构 litellm API+维度可配 dim 驱动+本地 ST 可选 fallback+测试改 API mock+benchmark | No | Yes (rollback plan ready) | embedding 改用 OpenAI 风格 API |

**Notes**:
- v1.10.0 status=tagged-local (local annotated tag created, pending remote push). Will become `released` after `git push origin v1.10.0` + GitHub Release created.
- v1.11.0 status=tagged-local (local annotated tag created @5fca85b, pending remote push). Will become `released` after `git push origin v1.11.0` + GitHub Release created.
- v1.12.0 status=tagged-local (local annotated tag created @50fc8e8, pending remote push). Will become `released` after `git push origin v1.12.0` + GitHub Release created.
- `Deployed`/`Prod-Verified` remain null — no prod deployment in scope (local-first desktop app, no server deployment).
- Breaking=No for all versions (additive MINOR bumps, no breaking API changes).
