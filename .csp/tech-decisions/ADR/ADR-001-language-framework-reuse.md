# ADR-001: 主语言与三入口框架复用（Python + Typer/FastAPI/FastMCP）

## 状态：Accepted
## 上下文
棕地，SAW 已用 Python 3.11+ + Typer CLI + FastAPI Web + FastMCP，61 MCP 工具 / 37 CLI 命令 / 117 Web 路由已在（CMS `entry-points.jsonl`）。硬化项目不涉及语言/框架迁移。
## 决策
复用既有：Python 3.11+ 后端；Typer CLI；FastAPI Web；FastMCP。不引入新框架。
## 备选方案
| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| 复用既有 | 零迁移成本，CMS/既有能力全可复用 | — | 棕地硬化 ✓ |
| 迁移 Node/TS 全栈 | 前后端统一 | 重写全量 engines，丢弃 Python AI 生态 | 绿地或弃 Python |
| Go 微服务化 | 高并发 | 单机 local-first 项目无此需求，破坏 local-first | 大规模 SaaS |
## 理由
需求匹配（local-first + AI/ML 生态 + 单机）40% + 团队能力（既有 Python）20% + 生态成熟 15% + 运维（单二进制/无服务）15% + 成本 10%。硬化 delta 在既有框架内闭环，无触发新维度。
## 后果
- 正：零迁移，CMS 全可 reference。
- 负：无。
- 风险：无。
## 关联 Feature
F-A-1..6（CLI 冒烟）、F-D-1..3（observability 复用 middleware）、F-C-*（FastAPI auth_dep）
