# API Overview — 接口总览（棕地，reference CMS entry-points）

> 棕地既有 117 Web 路由 + 61 MCP 工具 + 37 CLI 命令，详见 `.csp/code-spec/saw/entry-points.jsonl`。本硬化项目**不新增对外 API**，只新增内部冒烟/自检/diff 命令。下表列硬化相关既有端点锚点。

## 既有端点锚点（源自 CMS）
| 端点 | 方法 | 位置 | 鉴权 | 用途 |
|---|---|---|---|---|
| /api/auth/login | POST | drivers/web/routes/auth.py:152 | 公开 | F-C-5 token 同源 |
| /api/auth/refresh | POST | :205 | Bearer | F-C-5 |
| /health/ready | GET | drivers/web/health.py:100 | 公开 | F-D-3 真实健康 |
| /metrics | GET | :188 | 公开 | F-D-3 |
| /api/v1/lint | POST | api/routes/govern.py:236 | auth_dep | F-C-1 覆盖 |
| /api/v1/verify | POST | :211 | auth_dep | F-C-1 |
| /api/v1/ingest | POST | api/routes/query_ingest_learn.py:146 | auth_dep | F-A-2 冒烟 |
| /api/v1/query | POST | :66 | auth_dep | F-A-3 冒烟 |

## 新增内部入口（硬化）
| 入口 | 类型 | 命令名 [TBD] | 用途 |
|---|---|---|---|
| 冒烟命令 | CLI | `saw smoke` [TBD] | F-A-1..6 |
| 宣称 diff | CLI/脚本 | `scripts/claim_diff.sh` [TBD] | F-B-1 |
| 安全自检 | CLI/脚本 | `saw security-check` [TBD] | F-C-1..4 |
| 覆盖率报告 | CI | ci.yml | F-E-3 |

## 鉴权/限流/错误
见 `INTERFACE-ARCHITECTURE.md`。统一错误格式见 `SHARED-SCHEMAS.md`。
