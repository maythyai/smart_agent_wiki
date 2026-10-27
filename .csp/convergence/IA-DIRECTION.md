---
id: IA-DIRECTION
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-27
status: active
---

# IA 优化方向 + 导航预算 — Smart Agent Wiki

> 03 技术方案前置输入。

## 当前导航结构
- pages（页面列表/编辑）
- search（搜索）
- graph（知识图谱可视化）
- dashboard（概览/工作流/agent 活动）
- integrations（平台连接管理）← v1.33.0 补入 nav
- import（导入）
- templates（模板）
- timeline（时间线）

## 导航预算
- 当前：7（满额）
- 预算上限：7
- 本版本新增：0
- 本版本修改：Dashboard 按钮去重（v1.34.1 CRITIC-F-01：移除 duplicate nav 入口，改为状态卡）

## IA 方向
- 导航分类与用户心智模型一致（按任务域）
- 核心任务 ≤3 次点击可达 ✅
- 无功能孤岛（v1.33.0 修复 /integrations nav）
- 无同级功能散落多处

## 本版本不再新增顶级导航
- 已满额 7/7。后续如需新增，须先合并/降级现有节点。