# Feature Map — 完整 Feature 清单（表格视图）

> 域 = PMS 模块（边界不越界）。20 Feature / 5 域。详见 `FEATURE-DETAILS/F-*.yaml`。

| id | name | domain(PMS) | priority | complexity | depends_on | wave | prd_ref |
|---|---|---|---|---|---|---|---|
| F-A-1 | 冒烟命令骨架与 fresh 库初始化 | e2e-usability | P0 | S | — | 1 | §3.1 |
| F-A-2 | ingest+compile 链路冒烟 | e2e-usability | P0 | M | F-A-1 | 2 | §3.1 |
| F-A-3 | query 链路冒烟（关键词+NL） | e2e-usability | P0 | M | F-A-1 | 2 | §3.1 |
| F-A-4 | govern+learn 链路冒烟 | e2e-usability | P0 | M | F-A-1 | 2 | §3.1 |
| F-A-5 | 离线 fallback 冒烟（无 LLM） | e2e-usability | P0 | M | F-A-2,A-3,A-4 | 3 | §3.1 |
| F-A-6 | 冒烟纳入 CI | e2e-usability | P0 | S | F-A-5 | 3 | §3.1 |
| F-B-1 | 宣称 diff 脚本 | claim-alignment | P1 | M | — | 1 | §3.2 |
| F-B-2 | 能力清单生成（CAPABILITIES.md） | claim-alignment | P1 | M | F-B-1 | 2 | §3.2 |
| F-B-3 | 过时文档修正 + unverified 标注 | claim-alignment | P1 | S | F-B-1 | 2 | §3.2 |
| F-C-1 | 权限矩阵全覆盖（裸路由检测） | security-hardening | P0 | M | — | 1 | §3.3 |
| F-C-2 | Ed25519 receipt 全链路闭环 | security-hardening | P0 | M | — | 1 | §3.3 |
| F-C-3 | 限流双轨生效（429+Retry-After） | security-hardening | P0 | S | — | 1 | §3.3 |
| F-C-4 | 输入消毒/URL 守卫全覆盖 | security-hardening | P0 | S | — | 1 | §3.3 |
| F-C-5 | 前后端 token 同源核验与补齐 | security-hardening | P0 | M | — | 1 | §3.3 |
| F-D-1 | 统一 logger 收敛 | observability | P1 | M | — | 1 | §3.4 |
| F-D-2 | trace_id 贯穿各层 | observability | P1 | M | F-D-1 | 2 | §3.4 |
| F-D-3 | 健康端点真实化 + JSON 日志默认 | observability | P1 | S | — | 1 | §3.4 |
| F-E-1 | 覆盖率基线实测 + 阈值设定 | test-gate | P0 | M | — | 1 | §3.5 |
| F-E-2 | 核心引擎覆盖率门禁（≥80%） | test-gate | P0 | M | F-E-1 | 2 | §3.5 |
| F-E-3 | CI 集成（冒烟+coverage+报告） | test-gate | P0 | M | F-A-6,F-E-2 | 3 | §3.5 |

## 汇总
- 域：5（A e2e-usability / B claim-alignment / C security-hardening / D observability / E test-gate）
- Feature：20（P0=14，P1=6）
- 复杂度：S=8，M=12
- Wave：1=10，2=7，3=3
- 关键路径：F-A-1 → F-A-2 → F-A-5 → F-A-6 → F-E-3（5 步）
