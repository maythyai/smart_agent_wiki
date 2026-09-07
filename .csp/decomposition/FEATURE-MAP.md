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
| F-Z-1 | ruff baseline 收口（配置+全库修） | tech-debt | P1 | S | — | 3 | §F-debt |
| F-Z-2 | roadmap narrative 重写 | tech-debt | P2 | S | — | 2 | §F-debt |
| F-Z-3 | v1.2.0 行为变更迁移文档 | tech-debt | P1 | S | — | 2 | §F-debt |
| F-P-1 | RBAC 深化（Cedar 热加载 + 权限矩阵 e2e） | platform-team | P0 | M | — | 1 | §F-P-1 |
| F-P-2 | 团队部署（docker-compose.prod） | platform-team | P1 | S | — | 1 | §F-P-2 |
| F-P-3 | 可观测生产闭环（saw health + receipt audit） | platform-team | P1 | M | — | 1 | §F-P-3 |
| F-P-4 | 多工作空间隔离（schema 前缀 + 授权绑定） | platform-team | P0 | M | F-P-1 | 2 | §F-P-4 |
| F-Z-4 | ruff 收口续（F401 import 审计 + F841 修） | tech-debt | P1 | M | — | 3 | §F-debt |
| F-Z-5 | heavy-SDK learn 测试 importorskip | tech-debt | P2 | S | — | 1 | §F-debt |
| F-N-1 | embedding 索引（向量入库 Write Queue sink + 重建命令） | embedding | P0 | M | — | 1 | §3.1 |
| F-N-2 | 语义检索端点+CLI（QueryEngine semantic + CLI + REST） | embedding | P0 | M | F-N-1 | 2 | §3.2 |
| F-N-3 | smart-linking suggest 接 embedding 相似度 | embedding | P1 | M | F-N-1 | 2 | §3.3 |
| F-N-4 | heavy-SDK 测试 importorskip 沿用 | embedding | P0 | S | F-N-1 | 2 | §3.4 |
| F-O-1 | semantic search 走 query cache（复用 F-QS-07，TTL + 索引变更失效） | debt-closure | P0 | M | — | 1 | §3.1 |
| F-O-2 | compile/compiler.py 深覆盖（30 函数 17%→高，fail_under 64→65） | debt-closure | P0 | L | — | 1 | §3.2 |
| F-O-3 | workflow REST 统一读 DB（collaborate.py list_workflows 读 workflow_executions + merge live） | debt-closure | P0 | M | — | 1 | §3.3 |
| F-O-4 | Spec 命名回更 + tag hash 复核（N5+N6，文档修复） | debt-closure | P1 | S | — | 1 | §3.4+§3.5 |
| F-Q-1 | embed_texts provider 重构为 litellm API（替代本地 ST，config 驱动） | embedding-api | P0 | M | — | 1 | §3.1 |
| F-Q-2 | 维度可配 + embedding_store dim 列驱动 + 索引重建检测维度变更 | embedding-api | P0 | M | F-Q-1 | 2 | §3.2 |
| F-Q-3 | 本地 ST 可选 fallback（[learn] 装了可用，API 为主 ST 为辅） | embedding-api | P1 | M | F-Q-1 | 2 | §3.3 |
| F-Q-4 | 测试改 API mock（去 importorskip，CI 可跑）+ benchmark | embedding-api | P0 | M | F-Q-1 | 2 | §3.4 |
| F-S-1 | semantic cache 阈值可配（env 驱动启用/禁用 + 触发阈值）+ 文档标注 | semantic-perf | P0 | M | — | 1 | §3.1 |
| F-S-2 | ANN 索引替代全量 cosine 扫描（规模驱动自动切换 + cosine 降级兜底） | semantic-perf | P0 | L | — | 1 | §3.2 |
| F-S-3 | benchmark 更新（cache 真实度量 + ANN vs cosine 对比 + 规模延迟曲线） | semantic-perf | P1 | M | F-S-2 | 2 | §3.3 |
| F-T-1 | 自定义 agent 角色注册（.saw/agents/*.yaml 加载 + build_default_agents 合并 + CLI/REST 可见） | agent-link | P0 | M | — | 1 | §3.1 |
| F-T-2 | L2 links auto-apply（saw links apply --suggestion 写回 WikiRepository + dry-run/confirm + 去重） | agent-link | P0 | M | — | 1 | §3.2 |
| F-T-3 | M2 agent 活动聚合（event bus 订阅 WorkflowStep + GET /api/v1/agents/{name}/activity 端点） | agent-link | P0 | M | — | 1 | §3.3 |
| F-U-1 | Agent roster + activity 仪表盘（Dashboard.tsx 接 react-query 拉 GET /api/v1/agents + /agents/{name}/activity） | dashboard | P0 | M | — | 1 | §3.1 |
| F-U-2 | Workflow 运行态视图（新组件拉 GET /api/v1/workflows durable+live + /workflows/{id}/status 步骤进度） | dashboard | P0 | M | — | 1 | §3.2 |
| F-U-3 | 实时更新（复用 useWebSocket/dashboardStore + react-query invalidateQueries polling 刷新） | dashboard | P0 | M | F-U-1,F-U-2 | 2 | §3.3 |

## 汇总
- 域：10（A e2e-usability / B claim-alignment / C security-hardening / D observability / E test-gate / Z tech-debt / P platform-team / N embedding / O debt-closure / Q embedding-api）+ S semantic-perf + T agent-link + U dashboard
- Feature：50（P0=33，P1=15，P2=3）— v1.4.0 新增 F-P-1..4 + F-Z-4/5；v1.5.0 +F-I-1..4+F-Z-6..9；v1.6.0 +F-J-1..4；v1.7.0 +F-K-1..3；v1.8.0 +F-L-1..3；v1.9.0 +F-M-1..3；v1.10.0 +F-N-1..4（源自 PRD-embedding-v1.10.0 + retro M1/L1）；v1.11.0 +F-O-1..4（源自 PRD-debt-closure-v1.11.0 + retro N7/N2·K1/M3/N5/N6）；v1.12.0 +F-Q-1..4（源自 PRD-embedding-api-v1.12.0 + retro N1/N4 + 用户决策 pivot to API）；v1.14.0 +F-S-1..3（源自 PRD-semantic-perf-v1.14.0 + retro R1/R2）；v1.15.0 +F-T-1..3（源自 PRD-agent-link-v1.15.0 + retro M2/L2 + v1.5.0 自定义 agent 角色候选）；**v1.16.0 +F-U-1..3（源自 PRD-dashboard-v1.16.0 + retro 下一候选 realtime 仪表盘 v4.3 前端）**
- 复杂度：S=10，M=25，L=2（v1.16.0 增量：M=3）
- Wave：v1.16.0 新增 Wave 1=2（F-U-1, F-U-2 并行）+ Wave 2=1（F-U-3 依赖 U-1/U-2）
- 关键路径：F-A-1 → F-A-2 → F-A-5 → F-A-6 → F-E-3（5 步）；v1.10.0 次路径：F-N-1 → F-N-2（2 步）；v1.11.0：无依赖链（4 Feature 全并行 Wave 1）；v1.12.0 次路径：F-Q-1 → {F-Q-2, F-Q-3, F-Q-4}（2 步）；v1.14.0 次路径：F-S-2 → F-S-3（2 步），F-S-1 独立 Wave 1；v1.15.0：无依赖链（3 Feature 全并行 Wave 1，无依赖边）；**v1.16.0 次路径：F-U-1 → F-U-3 + F-U-2 → F-U-3（2 步，U-1/U-2 并行后 U-3）**
