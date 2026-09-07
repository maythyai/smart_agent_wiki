---
id: SPEC-F-W-2
title: O4 tag 流程修复（release-manager tag 指向 release commit 非 reconcile）
version: 1.0
status: Approved
author: tech-designer
date: "2026-09-07"
prd_ref: docs/prd/PRD-per-request-ws-v1.18.0.md
pms_ref: .csp/product-spec/PMS-per-request-ws.md
cms_ref: "[无 — 流程约定，非代码改动]"
feature_id: F-W-2
complexity: S
tdd_ref: .csp/tech-decisions/ADR/ADR-018-contextvar-per-request-workspace.md
adr_ref: .csp/tech-decisions/ADR/ADR-018-contextvar-per-request-workspace.md
ac_coverage: 2/2
related_tasks: [.csp/tasks/TASKS-DELTA-v1.18.0.md]
---

# SPEC-F-W-2: O4 tag 流程修复

> ADR-018 决策二：约定文档化（release-manager.md 更新 + scripts/RELEASE-FLOW.md）。
> 复杂度 S → 精简版。ground 自 release-manager.md 约定 + v1.17.0 tag 史。

## 实现 delta（ground 自源码 + 流程文档）

> ADR-018 决策二：O4 tag 流程修复——约定文档化（release-manager.md 更新 + scripts/RELEASE-FLOW.md 新增）。
> 本 Feature 为流程约定文档化，不改运行时代码。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `.claude/agents/release-manager.md` S8 节 | tag 流程描述未明确区分 reconcile commit vs release commit | 明确 tag 顺序：reconcile commit → release commit → **`git tag -a vX.Y.Z` on release commit** |
| `scripts/RELEASE-FLOW.md`（新增） | 不存在 | 新建：完整 release 流程文档（reconcile → release → tag → push → GitHub Release） |

### 不改动

- 06 执行脚本结构不变（release-manager agent 消费约定即可）。
- GitHub Release API 调用方式不变（`gh release create vX.Y.Z` 自动关联 tag）。
- 不做 GPG 签名 tag（后续优化项）。
- 不移动已推送 tag（不可变原则）。

## 维度 1：UI/UX 规格

无 UI 变更。

## 维度 2：数据库 Schema

无 schema 变更。

## 维度 3：API 契约

无 API 变更。

## 维度 4：后端架构

### release-manager.md 更新规格

在 S8 发布交付节的 7.4 发布产物中，明确 tag 流程：

```markdown
### 7.4.1 Tag 流程（O4 修复）

**06 ship 流程 tag 顺序**（强制，不可逆）：

1. **reconcile commit**：`chore(csp): v{milestone} reconcile planning artifacts` — 归档 planning artifacts（decomposition/specs/traceability delta snapshot）。
2. **release commit**：`release: v{milestone}` — 包含全部 ship artifacts：
   - RELEASE-NOTES-{milestone}.md
   - ROLLBACK-PLAN-{milestone}.md
   - .csp/milestones/{milestone}/ 归档（B 类 cp 快照）
   - ROADMAP.md 更新（版本号 + released 状态）
   - VERSION-REGISTRY.md 追加行
   - lifecycle-state.json 更新（06 done）
   - manifest.json writeback
3. **tag release commit**：`git tag -a v{milestone} -m "release: v{milestone}"` — tag 指向 release commit（包含全部 ship artifacts）。
4. **push**：`git push origin master --tags` — 推 master + tag。
5. **GitHub Release**：`gh release create v{milestone} --title "v{milestone}" --notes-file .csp/ship/RELEASE-NOTES-{milestone}.md` — 关联 tag。

**验证**：`git log --oneline v{milestone} -1` 输出 `release: v{milestone}`（非 `chore(csp): v{milestone} reconcile`）。
```

### scripts/RELEASE-FLOW.md 规格

```markdown
# Release Flow（06 Ship 流程）

> 完整 release 流程文档。release-manager agent 消费此文档执行 06 ship。

## 前置条件

- 05 实施完成（WBS 全 Task done）
- 06 S6 质量门控通过（pytest/ruff/build/typecheck/AC 逐条/文档）
- 06 S7 审查通过（代码评审 6 维度 + Spec 对齐 + 安全/性能）
- 回滚计划就绪
- 监控就绪

## 流程

### Step 1: Reconcile Commit

```bash
git add .csp/
git commit -m "chore(csp): v{milestone} reconcile planning artifacts"
```

内容：decomposition/specs/traceability delta snapshot。

### Step 2: Release Commit

```bash
# 生成 ship artifacts
# - RELEASE-NOTES-{milestone}.md
# - ROLLBACK-PLAN-{milestone}.md
# - 归档 .csp/milestones/{milestone}/
# - 更新 ROADMAP.md
# - 更新 VERSION-REGISTRY.md
# - 更新 lifecycle-state.json
# - writeback manifest.json

git add -A
git commit -m "release: v{milestone}"
```

### Step 3: Tag Release Commit

```bash
git tag -a v{milestone} -m "release: v{milestone}

$(cat .csp/ship/RELEASE-NOTES-{milestone}.md | head -20)"
```

**关键：tag 指向 release commit（Step 2 的 commit），非 reconcile commit（Step 1 的 commit）。**

### Step 4: Push

```bash
git push origin master --tags
```

### Step 5: GitHub Release

```bash
gh release create v{milestone} \
  --title "v{milestone}" \
  --notes-file .csp/ship/RELEASE-NOTES-{milestone}.md
```

上传构建产物（如有）：
```bash
gh release upload v{milestone} dist/*
```

### 验证

```bash
# tag 指向 release commit
git log --oneline v{milestone} -1
# 期望输出：{sha} release: v{milestone}
# 不应输出：{sha} chore(csp): v{milestone} reconcile planning artifacts

# GitHub Release 关联正确
gh release view v{milestone}
```

## 异常处理

- release commit 失败：修复后重 commit，tag 在新 commit 上。
- tag 已存在（重跑 06）：不移动已推送 tag（不可变原则），仅本地未推送时可重建。
- GitHub Release 创建失败：重试 `gh release create`，确保 tag 已推送。
```

## 维度 5：前端架构

无前端变更。

## 维度 6：基础设施需求

无新基础设施需求。

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 |
|---|---|---|---|
| AC-O4-1 | `test_o4_tag_flow.py::test_tag_points_to_release_commit`（06 执行时验证）：`git log --oneline v1.18.0 -1` → 断言输出含 `release: v1.18.0`（非 `reconcile`） | integration（06 ship 时执行） | tag 指向 release commit |
| AC-O4-2 | `test_o4_tag_flow.py::test_github_release_association`（06 执行时验证）：`gh release view v1.18.0` → 断言 tag_name = `v1.18.0`，target_commitish = release commit SHA | integration（06 ship 时执行） | GitHub Release 关联正确 |

### 文档验证测试

| 场景 | 用例 | 类型 | 断言 |
|---|---|---|---|
| release-manager.md 含 tag 顺序 | `test_release_flow_docs.py::test_release_manager_mentions_tag_order` | unit（grep/text） | release-manager.md 含 "tag release commit" 或 "tag 指向 release commit" |
| scripts/RELEASE-FLOW.md 存在 | `test_release_flow_docs.py::test_release_flow_exists` | unit（文件检查） | scripts/RELEASE-FLOW.md 存在且非空 |
| RELEASE-FLOW.md 含 5 step | `test_release_flow_docs.py::test_release_flow_steps` | unit（text parse） | 含 Step 1-5（reconcile/release/tag/push/GitHub Release） |

### CI 兼容

文档验证测试 pytest 运行，CI 始终跑。06 执行时验证测试仅在 release 时跑（06 ship 流程内）。

## 维度 8：安全考量

- 已推送 tag 不可移动（不可变原则）——防止 tag 篡改。
- 不做 GPG 签名 tag（后续优化项）——当前 threat model 不要求 tag 签名。
- GitHub Release 使用 `gh release create`（GitHub 官方 CLI），不手写 API 调用——减少出错。

## 实现就绪度

- [x] release-manager.md 更新规格明确（S8 7.4.1 Tag 流程节）
- [x] scripts/RELEASE-FLOW.md 规格完整（5 step + 验证 + 异常处理）
- [x] AC 覆盖 2/2
- [ ] 05 实施后文档写入 + 06 执行时验证 tag 指向
