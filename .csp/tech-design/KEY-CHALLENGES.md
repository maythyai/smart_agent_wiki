# Key Challenges — 关键技术难点 + 多方案对比

## 难点 1：离线 fallback 路径完整性（F-A-5）
- **问题**：LLM 不可达时核心链路须可跑通（agent NL query / NL query 编译）。
- **方案对比**：
| 方案 | 原理 | 优势 | 劣势 | 复杂度 |
|---|---|---|---|---|
| 规则 fallback（复用） | agent `_classify_fallback`（`librarian.py:78`）+ query 关键词路径 | 已实现，零成本 | NL 答案降级 | S |
| mock LLM | 注入假 LLM 返回 | 测试可复现 | 不反映真实降级 | M |
| 强制在线 | 拒绝离线 | 简单 | 破可用性 | — |
- **推荐**：规则 fallback（复用）+ 冒烟暴露缺口逐项补。阶段策略：MVP 先跑通 agent fallback，NL query 降级标记。
- **指标**：离线冒烟核心路径 100% PASS。

## 难点 2：trace_id 贯穿各层（F-D-2）
- **问题**：request_id 须从 drivers 贯穿 engines→write_queue→sinks。
- **方案对比**：
| 方案 | 原理 | 优势 | 劣势 | 复杂度 |
|---|---|---|---|---|
| contextvar 传递 | Python contextvar 跨 async 传 trace_id | 标准，零依赖 | 需各层取 context | M |
| 显式参数透传 | 每函数加 trace_id 参数 | 显式 | 侵入大 | L |
| 日志中间件只挂 drivers | 只 drivers 层有 trace | 简单 | engines 无 trace，定位弱 | S |
- **推荐**：contextvar 传递（复用 `_RequestIdFilter` context）。阶段策略：MVP 先 HTTP 入口，CLI/MCP 归 V1.1。

## 难点 3：路由双轨统一（Drift D4）
- **问题**：`api/`（自带 prefix）与 `drivers/web/routes/`（include 挂 prefix）两套，prefix 体系不一。
- **方案对比**：
| 方案 | 原理 | 优势 | 劣势 | 复杂度 |
|---|---|---|---|---|
| 现状保留 + 自检覆盖 | 不重构，安全自检覆盖两套 | 零迁移 | 双轨长期在 | S |
| 统一到 `api/` | 全部自带 prefix | 一致 | 大量 rename | L |
| 统一到 `drivers/web/routes/` | include 挂 prefix | 集中 | 同上 | L |
- **推荐**：现状保留（硬化不重构双轨，归后续）；F-C-1 自检覆盖两套路由。阶段策略：MVP 不动双轨。

## 难点 4：覆盖率门禁基线（F-E-1/E-2）
- **问题**：既有 128 测试，覆盖率基线 [TBD]，阈值过高则门禁不可达。
- **方案对比**：
| 方案 | 原理 | 优势 | 劣势 |
|---|---|---|---|
| 实测后定阈值 | 先跑 coverage 再设 | 现实可达 | 延迟门禁 | 
| 固定 80% 硬阈值 | 直接设 | 明确 | 可能红 |
| 分阶段提 | 基线→逐步提 | 平滑 | 需跟踪 |
- **推荐**：实测后定（F-E-1）+ 分阶段提至 80%（核心引擎）。指标：核心引擎 ≥80%、非核心 ≥60%。
