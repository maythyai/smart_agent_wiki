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
| v1.10.0 | v1.10.0 | released | 2026-09-04 | null | null | embedding 索引+语义检索+smart-linking embedding signal+importorskip 测试 | No | Yes (rollback plan ready) | embedding 语义搜索 |
| v1.11.0 | v1.11.0 | released | 2026-09-05 | null | null | semantic cache+compiler 深覆盖+workflow REST unify DB+Spec 命名回更+hash 复核 | No | Yes (rollback plan ready) | 债务收口 IV / bug fix |
| v1.12.0 | v1.12.0 | released | 2026-09-05 | null | null | embedding provider 重构 litellm API+维度可配 dim 驱动+本地 ST 可选 fallback+测试改 API mock+benchmark | No | Yes (rollback plan ready) | embedding 改用 OpenAI 风格 API |
| v1.13.0 | v1.13.0 | released | 2026-09-06 | null | null | ingest dir recursion+benchmark script (semantic vs BM25)+REST alias/CHANGELOG+coverage 67+Q1/Q3 closure | No | Yes (rollback plan ready) | E2E 收尾轮 |
| v1.14.0 | v1.14.0 | released | 2026-09-06 | null | null | cache threshold configurable (SAW_SEMANTIC_CACHE_ENABLED/THRESHOLD_MS)+ANN index hnswlib scale-driven+numpy batch cosine fallback+benchmark cache.stats ANN vs cosine P99+scale curves | No | Yes (rollback plan ready) | semantic 性能优化 |
| v1.15.0 | v1.15.0 | released | 2026-09-06 | null | null | custom agent role registry YAML+CLI+REST+links auto-apply confirm/dry-run+agent activity aggregation event_bus subscriber+REST/CLI | No | Yes (additive MINOR, no breaking) | agent/link 能力 |
| v1.16.0 | v1.16.0 | released | 2026-09-07 | null | null | agent roster+activity dashboard (react-query)+workflow runtime view+realtime polling 15s+WS invalidate+disconnect degraded | No | Yes (additive MINOR, frontend-only) | realtime 仪表盘 v4.3 |
| v1.17.0 | v1.17.0 | released | 2026-09-07 | null | null | desktop 1.0 bump 0.1.0→1.0.0+config convergence 15项+web dashboard integration frontendDist→web/dist+tauri build .app/.dmg (unsigned ADR-017 defer)+port convergence 8080→8000+CORS localhost:5173 | No | Yes (additive MINOR, desktop 0.x→1.0) | desktop 完成 v4.4 |
| v1.18.0 | v1.18.0 | released | 2026-09-07 | null | null | per-request workspace contextvar injection (N3/K2 closure)+O4 tag flow convention docs (§7.3.5)+middleware per-request workspace_id+QueryEngine contextvar read fallback | No | Yes (additive MINOR, no breaking) | per-request workspace 注入 + O4 tag 流程 |

**Notes**:
- v1.10.0–v1.18.0 all status=released (tag pushed + GitHub Release created).
- v1.18.0 tag @TAG_HASH_PENDING, GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.18.0
- v1.17.0 tag @e391611, GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.17.0 (assets: wheel+sdist+.dmg)
- v1.16.0 tag @57b9550, GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.16.0
- v1.15.0 tag @d5b644f, GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.15.0
- v1.14.0 tag @136befe, GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.14.0
- `Deployed`/`Prod-Verified` remain null — no prod deployment in scope (local-first desktop app, no server deployment).
- Breaking=No for all versions (additive MINOR bumps, no breaking API changes).
