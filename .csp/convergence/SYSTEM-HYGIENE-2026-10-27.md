---
id: SYSTEM-HYGIENE-2026-10-27
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-27
status: active
---

# 系统级卫生审查 — Smart Agent Wiki（2026-10-27）

## 后端能力膨胀
- API 端点数：114（openapi paths）。审计已标孤儿 API（AUDIT-F-05 v1.30.0）。
- 孤儿后端：部分 API 无前端消费（/api/v1/reparse, /api/connectors/github/rate-limit 等）。
- 裁决：不阻断本版本。列入 backlog（非 v1.34.1 主题）。

## Feature Flag 卫生
- `auth_mode`：`local`（default-on，local-first） / `team`（default-off，self-hosted）。
- `team` mode 代码 active（v1.4 实现，非死代码）。
- 裁决：OK。无 TTL 问题。

## 文档权威
- 版本口径：git tag 唯一真相源（version_integrity 闸门通过 ✓）
- ADR 编号：统一 `.csp/tech-decisions/ADR/` 空间，无冲突 ✓
- FINDINGS 基线：双闸门 exit 0 ✓
- PLACEHOLDER 占位：0 ✓
- DOC-STATUS 新鲜度：⚠️ 部分 docs 上次审计 2026-09-18（~40d > 30d 阈值）

## 裁决
| 项 | 状态 | 裁决 |
|----|------|------|
| 后端膨胀 | 🟡 | 不阻断，列入 backlog |
| Feature Flag | 🟢 | OK |
| ADR/版本口径 | 🟢 | OK |
| DOC-STATUS | ⚠️ WARNING | 不阻断；v1.34.1 同批修订 doc freshness |