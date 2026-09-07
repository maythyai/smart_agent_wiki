# RELEASE-FLOW.md — SAW 发布流程（O4 fix）

> 强制约定：**tag 必指向 release commit，非 reconcile commit**。见 `.claude/agents/release-manager.md` §7.3.5。

## 流程图

```
┌─────────────────────┐
│  S6 质量门控全过     │
│  S7 审查通过         │
│  re-align CMS 完成  │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  reconcile commit    │   chore(csp): vX.Y.Z reconcile planning artifacts
│  （不打 tag）         │   仅 .csp/ 规划制品（manifest/SPEC-INDEX/追溯等）
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  发布制品准备         │
│  - release notes     │   .csp/ship/RELEASE-NOTES-vX.Y.Z.md
│  - rollback plan     │   .csp/ship/ROLLBACK-PLAN-vX.Y.Z.md
│  - VERSION-REGISTRY  │   追加 vX.Y.Z 行
│  - pyproject bump    │   version: X.Y.Z
│  - 里程碑归档          │   .csp/milestones/vX.Y.Z/
│  - ROADMAP/lifecycle │   状态最终更新
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  release commit      │   release: vX.Y.Z — ship artifacts + milestone archive
│  （这才是 tag 该指的） │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  git tag -a vX.Y.Z   │   annotated tag + 发布说明（必在 release commit 上）
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  git push origin vX.Y.Z  │   推 tag
│  git push origin master  │   推主分支（含 reconcile + release commits）
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  gh release create vX.Y.Z │  建 GitHub Release（附 release notes + assets）
│  --notes-file .csp/ship/RELEASE-NOTES-vX.Y.Z.md
│  [--files dist/*.whl dist/*.dmg]
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Release 验证         │   Releases 页面可见、tag 关联、发布说明正确、assets 完整
└─────────────────────┘
```

## 关键约定

### 1. reconcile commit vs release commit

| commit 类型 | message 前缀 | 内容 | 是否打 tag |
|---|---|---|---|
| reconcile commit | `chore(csp): vX.Y.Z reconcile ...` | 规划制品（.csp/manifest + SPEC-INDEX + 追溯 + pyproject bump 等） | **❌ 不打** |
| release commit | `release: vX.Y.Z — ship artifacts + ...` | release notes + rollback plan + VERSION-REGISTRY + 里程碑归档 + ROADMAP/lifecycle 最终状态 | **✅ 打 tag** |

### 2. tag 不可变原则

- tag 一旦推送 → 不移动、不删除、不改写（即使发现 bug 也发 v+1 patch）
- 本地打错未推送 → `git tag -d vX.Y.Z` 删本地重打
- 已推送 → 走 patch release 流程（vX.Y.Z+1）

### 3. tag + GitHub Release 必成对

- **禁止只推 tag 不建 Release**（"有 tag 无 Release" = 半发布）
- CI 若自动建 Release → 确认 workflow 已触发且成功；否则手动 `gh release create` 补齐

## 命令清单（可复制）

```bash
# 1. reconcile commit
git add .csp/ CHANGELOG.md
git commit -m "chore(csp): v1.19.0 reconcile planning artifacts"

# 2. 准备发布制品
#    - 写 .csp/ship/RELEASE-NOTES-v1.19.0.md
#    - 写 .csp/ship/ROLLBACK-PLAN-v1.19.0.md
#    - 更新 .csp/ship/VERSION-REGISTRY.md（追加 v1.19.0 行）
#    - bump pyproject.toml version: 1.19.0
#    - cp .csp/ 关键制品到 .csp/milestones/v1.19.0/
#    - 更新 ROADMAP（v1.19.0 行 status → released + @tag hash）
#    - 更新 lifecycle（06-ship done）
#    - 更新 manifest（+ship/milestone items）

# 3. release commit
git add .csp/ship/ .csp/milestones/ .csp/lifecycle-state.json .csp/manifest.json \
        .csp/ship/VERSION-REGISTRY.md docs/strategy/ROADMAP.md pyproject.toml
git commit -m "release: v1.19.0 — ship artifacts + milestone archive + ROADMAP/lifecycle/manifest update"

# 4. tag (on release commit)
git tag -a v1.19.0 -m "v1.19.0: <one-line theme>. <pytest N passed>, ruff 0, smoke <N/N>. additive MINOR."

# 5. push
git push origin master
git push origin v1.19.0

# 6. GitHub Release (with .dmg / .whl assets if applicable)
gh release create v1.19.0 \
  --notes-file .csp/ship/RELEASE-NOTES-v1.19.0.md \
  --latest \
  dist/smart_agent_wiki-1.19.0-py3-none-any.whl \
  [desktop/src-tauri/target/release/bundle/dmg/*.dmg]

# 7. 验证
gh release view v1.19.0  # 确认 Releases 页面、notes、assets
```

## 反模式（必须避免）

| 反模式 | 症状 | 正确做法 |
|---|---|---|
| tag 打在 reconcile commit | `git show vX.Y.Z` 看到 chore commit 而非 release 状态 | tag 必在 release commit 上 |
| 只推 tag 不建 Release | 远端"有 tag 无 Release" = 半发布 | tag + Release 一起做 |
| tag 后移动/删除 | 已推送 tag 不可变 | 发 patch release (vX.Y.Z+1) |
| lightweight tag | `git tag vX.Y.Z`（无 -a） | 必用 `git tag -a`（annotated）|
| 发布前未 re-align CMS | CMS 落后于代码 ground truth | S6+S7 通过即 re-align，不等上线 |

## 历史示例

### v1.17.0（正确示例）
- reconcile commit: `e391611 chore(csp): v1.17.0 reconcile planning artifacts + pyproject bump 1.16.0→1.17.0 + desktop 1.0.0`
- release commit: `1cca7dc release: v1.17.0 — ship artifacts + milestone archive + ROADMAP/lifecycle/manifest update`
- tag: `v1.17.0` @1cca7dc ✅（正确：tag 在 release commit 上）
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.17.0（含 .dmg asset）

### v1.10.0–v1.16.0（部分版本 tag 在 reconcile commit 上，O4 fix 后统一）
- 历史 tag 不移动（不可变原则）
- 从 v1.17.0 起统一按本流程执行

---

*本文件可被 CI workflow / release-manager agent / 人类复用。更新请保持与 `.claude/agents/release-manager.md` §7.3.5 同步。*
