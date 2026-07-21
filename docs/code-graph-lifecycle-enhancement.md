# Code Graph 生命周期增强方案

> 参考项目: [code-review-graph](https://github.com/tirth8205/code-review-graph)
> 目标: 将 SAW 的代码智能图从 placeholder 升级为完整的代码图生命周期系统，与现有 Wiki 知识图谱形成双图融合架构，增强系统健壮性。

---

## 1. 现状诊断

### 1.1 已有能力（可复用）

| 模块 | 路径 | 状态 | 说明 |
|------|------|------|------|
| Wiki 知识图谱引擎 | `src/saw/graph/` | ✅ 生产可用 | 4-Signal 相关性 + Louvain 社区检测 + 洞察生成 |
| 影响分析算法 | `src/saw/analysis/impact.py` | ✅ 算法完整 | GitNexus-style BFS，按深度分级风险 |
| 执行流检测 | `src/saw/analysis/process.py` | ✅ 算法完整 | DFS 调用树构建 |
| 新鲜度检测 | `src/saw/analysis/staleness.py` | ✅ 算法完整 | Git commit 比对 |
| MCP 工具定义 | `src/saw/mcp/tools/impact.py` | ⚠️ 接口就绪 | 依赖 placeholder graph，实际返回空 |
| Ingest DAG Pipeline | `src/saw/ingest/pipeline/` | ✅ 6 阶段 | Classify→Parse→Extract→Merge→Validate→Store |

### 1.2 关键断裂点

```
[代码文件] ──✗──> [AST 解析] ──✗──> [图构建] ──✗──> [图存储]
                                          │
                                          ▼
                              KnowledgeGraph (placeholder)
                              ├── nodes: {} (永远为空)
                              └── edges: [] (永远为空)
                                          │
                                          ▼
                              impact/process/staleness (空转)
```

**根因**: `src/saw/graph.py` 是一个 55 行的 placeholder，无 AST 解析、无持久化、无增量更新、无数据填充机制。两套图系统（wiki 图 vs 代码图）完全割裂。

### 1.3 健壮性缺陷

- 全局可变状态 `_graph` 非线程安全（Web/MCP 多线程场景下竞态）
- 无持久化——进程重启后图数据丢失
- 无增量更新——无法响应代码变更
- 无一致性校验——无法检测图与源码的偏差
- 无降级策略——图不可用时 MCP 工具直接报错

---

## 2. 目标架构：双图融合 + 六阶段生命周期

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAW Unified Graph Layer                        │
├─────────────────────────┬───────────────────────────────────────┤
│   Code Graph (新增)      │   Wiki Knowledge Graph (已有)          │
│   代码结构 · 符号关系     │   页面关联 · 概念社区                  │
├─────────────────────────┴───────────────────────────────────────┤
│                    Bridge Layer (新增)                            │
│   doc↔code 双向锚定 · 跨图查询 · 统一影响分析                    │
├─────────────────────────────────────────────────────────────────┤
│                    Storage Layer (升级)                           │
│   SQLite WAL · FTS5 · 向量索引 · 快照版本                        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 代码图六阶段生命周期

参考 code-review-graph 的完整生命周期，为 SAW 设计六阶段：

```
┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│ 1.Parse  │───>│ 2.Build  │───>│ 3.PostProcess│───>│ 4.Query │───>│ 5.Review │───>│ 6.Update │
│ AST解析   │    │ 图构建    │    │ 派生结构      │    │ 上下文   │    │ 风险评估  │    │ 增量同步  │
└──────────┘    └──────────┘    └──────────────┘    └─────────┘    └──────────┘    └──────────┘
     ▲                                                                        │
     └────────────────────────────────────────────────────────────────────────┘
                              增量反馈环路
```

---

## 3. 各阶段详细设计

### Phase 1: Parse（AST 解析）

**目标**: 将源码文件解析为结构化符号节点和关系边。

**技术选型**: Tree-sitter（零 LLM 依赖，30+ 语言，增量解析）

**新增模块**: `src/saw/code_graph/parser.py`

```python
# 核心数据模型
@dataclass
class CodeNode:
    uid: str                    # 确定性 ID: "{file_path}::{qualified_name}"
    name: str                   # 符号名 (e.g., "AuthService.login")
    kind: NodeKind              # File | Class | Function | Method | Type | Test | Config
    file_path: str
    language: str
    start_line: int
    end_line: int
    signature: str              # 人类可读签名
    parameters: list[str]
    docstring: Optional[str]
    content_hash: str           # SHA-256 of symbol body (增量检测用)
    metadata: dict              # 框架注解、装饰器等

@dataclass
class CodeEdge:
    source: str                 # source node uid
    target: str                 # target node uid
    edge_type: EdgeType         # CALLS | IMPORTS | INHERITS | IMPLEMENTS | CONTAINS | TESTED_BY | REFERENCES
    confidence: float           # 1.0 = AST 精确提取, <1.0 = 推断
    confidence_tier: str        # "EXTRACTED" | "INFERRED" | "RESOLVED"
    metadata: dict
```

**边类型权重**（影响分析用）:

| EdgeType | Weight | 语义 |
|----------|--------|------|
| CALLS | 1.0 | 函数调用 |
| INHERITS | 0.9 | 类继承 |
| IMPLEMENTS | 0.85 | 接口实现 |
| IMPORTS | 0.7 | 模块导入 |
| TESTED_BY | 0.6 | 测试覆盖 |
| CONTAINS | 0.3 | 包含关系 |
| REFERENCES | 0.4 | 类型引用 |

**多语言支持策略**:
- 通用层: Tree-sitter 语法树 → 统一 CodeNode/CodeEdge schema
- 语言特化 Resolver（参考 code-review-graph 模式）:
  - `python_resolver.py`: 装饰器语义（@app.route → endpoint）、动态导入
  - `typescript_resolver.py`: tsconfig paths、re-exports
  - `java_resolver.py`: Spring DI、注解驱动
- 自定义语言: `languages.toml` 声明式配置，无需改代码

**并行解析**: `ProcessPoolExecutor` 并行处理文件批次，MCP stdio 模式降级为 `ThreadPoolExecutor`。

---

### Phase 2: Build（图构建与存储）

**目标**: 将解析结果持久化为可查询的图数据库。

**技术选型**: SQLite WAL 模式（与 SAW 现有 SQLModel 栈一致，无需引入外部图数据库）

**新增模块**: `src/saw/code_graph/store.py`

**Schema 设计**:

```sql
-- 节点表
CREATE TABLE code_nodes (
    uid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    file_path TEXT NOT NULL,
    language TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    signature TEXT,
    content_hash TEXT NOT NULL,
    metadata JSON,
    created_at TEXT,
    updated_at TEXT
);

-- 边表
CREATE TABLE code_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL REFERENCES code_nodes(uid),
    target TEXT NOT NULL REFERENCES code_nodes(uid),
    edge_type TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    confidence_tier TEXT DEFAULT 'EXTRACTED',
    metadata JSON,
    UNIQUE(source, target, edge_type)
);

-- 文件追踪表（增量更新用）
CREATE TABLE file_tracking (
    file_path TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    last_parsed_at TEXT,
    node_count INTEGER,
    edge_count INTEGER
);

-- 图快照元数据
CREATE TABLE graph_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    created_at TEXT,
    trigger TEXT,          -- 'full_build' | 'incremental' | 'manual'
    node_count INTEGER,
    edge_count INTEGER,
    files_changed INTEGER
);

-- FTS5 全文索引
CREATE VIRTUAL TABLE code_nodes_fts USING fts5(
    name, signature, file_path,
    content='code_nodes',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

-- 索引
CREATE INDEX idx_edges_source ON code_edges(source, edge_type);
CREATE INDEX idx_edges_target ON code_edges(target, edge_type);
CREATE INDEX idx_nodes_file ON code_nodes(file_path);
CREATE INDEX idx_nodes_kind ON code_nodes(kind);
CREATE INDEX idx_nodes_name ON code_nodes(name);
```

**原子性保证**:
- 每个文件的节点/边在单个事务内替换（`store_file_batch`）
- WAL 模式确保读写并发安全
- 解决现有 `_graph` 全局变量的线程安全问题

**确定性 UID 策略**（参考 SCIP moniker）:
```
uid = f"{relative_file_path}::{qualified_name}"
# e.g., "src/saw/engines/ingest/pipeline/runner.py::PipelineRunner.execute"
```
- 重命名/移动文件时通过 git 追踪保持 UID 稳定
- 重新索引时 upsert 语义，不产生重复

---

### Phase 3: PostProcess（派生结构计算）

**目标**: 从原始图数据派生高阶结构，提升查询能力。

**新增模块**: `src/saw/code_graph/postprocess.py`

**五步派生管线**（每次 build/update 后自动执行）:

```
Step 1: 裸名解析 (Bare Name Resolution)
  └── 将未限定的跨文件 CALLS 目标解析为完整 UID
  └── 证据门控: 仅当有同文件/导入证据时才解析，防止误连

Step 2: 签名计算 (Signature Computation)
  └── 为每个节点生成人类可读签名
  └── e.g., "def analyze_impact(graph, target, direction='upstream') -> ImpactResult"

Step 3: FTS5 索引重建
  └── 填充全文搜索索引（porter stemmer + unicode61）
  └── 支持 BM25 关键词搜索

Step 4: 执行流追踪 (Flow Tracing)
  └── 检测入口点（框架装饰器、命名约定、无入边节点）
  └── 前向 BFS 沿 CALLS 边追踪执行路径
  └── 关键度评分（安全关键词、测试覆盖、路径长度）

Step 5: 社区检测 (Community Detection)
  └── Leiden 算法（igraph）或 Louvain 降级
  └── 边权重: CALLS=1.0, INHERITS=0.8, IMPLEMENTS=0.7, IMPORTS=0.5
  └── 生成社区名称（成员词汇频率）
  └── 与现有 Wiki 图的 Louvain 社区对齐
```

**可选 Step 6: 向量嵌入刷新**
- 对节点签名+docstring 生成 embedding
- 支持语义搜索（与 FTS5 形成混合检索）
- 本地 sentence-transformers 或 OpenAI-compatible API

---

### Phase 4: Query（上下文查询）

**目标**: 为 AI agent 和用户提供 token 高效的代码结构上下文。

**升级现有 MCP 工具 + 新增工具**:

| 工具 | 功能 | 对应 code-review-graph |
|------|------|----------------------|
| `saw_impact` (升级) | 加权 BFS 影响半径 | `get_impact_radius` |
| `saw_process` (升级) | 执行流追踪 | `get_affected_flows` |
| `saw_code_query` (新增) | 图模式查询 (callers/callees/imports/tests) | `query_graph` |
| `saw_code_search` (新增) | 混合搜索 (FTS5 + vector RRF) | `semantic_search_nodes` |
| `saw_architecture` (新增) | 架构概览 (社区/hub/bridge) | `get_architecture_overview` |
| `saw_code_context` (新增) | token 预算感知的上下文组装 | `get_review_context` |

**影响分析升级**（替换现有简单 BFS）:

```python
# 加权 BFS + 深度衰减 + 分数地板
score = parent_score × edge_weight × depth_decay_factor
# depth_decay: 0.85^depth
# score_floor: 0.05 (低于此分数剪枝)
# 最佳分数松弛: 每个节点只保留最高分路径，防止环形图指数爆炸
```

**多分辨率上下文** (detail_level):
- `minimal`: 仅名称+类型（token 最省）
- `standard`: 签名+关系+风险等级
- `verbose`: 完整源码片段+docstring

**Token 预算感知**:
- 每次查询返回 `context_savings` 元数据
- `get_minimal_context` 入口点：先给摘要，按需展开

---

### Phase 5: Review（风险评估与变更检测）

**目标**: 将代码图与 Git 变更结合，输出风险评分的审查指导。

**新增模块**: `src/saw/code_graph/changes.py`

**核心能力**:

```python
@dataclass
class ChangeAnalysis:
    changed_files: list[str]
    affected_functions: list[AffectedFunction]  # 直接受影响的符号
    risk_score: float                          # 0-1 综合风险
    test_gaps: list[str]                       # 缺少测试覆盖的变更
    security_flags: list[str]                  # 安全敏感变更标记
    affected_flows: list[FlowImpact]           # 受影响的执行流
    review_priority: list[PrioritizedItem]     # 优先级排序的审查建议
```

**风险评分模型**:
- 基础分: 变更符号的入度（被依赖程度）
- 加权: 边类型权重 × 深度衰减
- 加分项: 安全关键词命中、无测试覆盖、跨社区影响
- 输出: 按风险降序排列的审查清单

**与 SAW Govern 引擎集成**:
- 变更检测触发 Govern 引擎的 blast_radius 评估
- 高风险变更自动创建 Wiki 页面的 freshness 告警
- 与 `saw_staleness` 工具联动：代码变了但文档没更新 → 标记过期

---

### Phase 6: Update（增量同步）

**目标**: 代码变更后 < 2 秒完成图更新，无需全量重建。

**新增模块**: `src/saw/code_graph/incremental.py`

**增量策略**:

```
触发源:
  ├── Git hook (post-commit / post-checkout)
  ├── File watcher (watchdog)
  ├── CLI: saw code-graph update
  └── MCP: saw_code_graph_update tool

检测变更:
  ├── git diff --name-only HEAD~1 (Git 模式)
  ├── SHA-256 content hash 比对 (file_tracking 表)
  └── 跳过未变更文件 (hash 命中 → skip)

增量重建:
  ├── 仅重新解析变更文件
  ├── 原子替换该文件的 nodes/edges (单事务)
  ├── 重新解析受影响的跨文件边 (裸名重解析)
  └── 触发 PostProcess 管线 (增量模式)

一致性保证:
  ├── 图 = 源码的派生缓存，源码是 source of truth
  ├── 任何时候可 full rebuild 恢复
  ├── 快照版本化 (graph_snapshots 表)
  └── 完整性自检: saw code-graph verify
```

**性能目标**:
- 2,900 文件项目增量更新 < 2s（参考 code-review-graph 实测）
- 全量构建 < 30s（并行解析）
- 查询响应 < 100ms（SQLite 索引 + 内存缓存）

---

## 4. 双图融合：Bridge Layer

### 4.1 设计目标

将 Code Graph（代码结构）与 Wiki Knowledge Graph（知识文档）打通，实现：
- 文档锚定到代码符号（doc → code）
- 代码符号关联相关文档（code → doc）
- 跨图影响传播（代码变更 → 文档过期检测）
- 统一社区视图（代码模块 ↔ 文档主题对齐）

### 4.2 锚定机制

```python
# Wiki 页面 frontmatter 扩展
---
title: "认证服务设计"
type: concept
code_anchors:                    # 新增字段
  - "src/saw/auth/service.py::AuthService"
  - "src/saw/auth/jwt.py::generate_token"
  - "src/saw/auth/rbac.py::PermissionChecker"
---

# 代码节点 metadata 扩展
metadata: {
    "wiki_pages": ["authentication-design", "jwt-implementation"],
    "last_doc_sync": "2026-07-20T10:00:00Z"
}
```

### 4.3 跨图查询

```python
class BridgeQuery:
    def code_to_docs(self, symbol_uid: str) -> list[WikiPage]:
        """给定代码符号，找到所有关联的 Wiki 文档"""

    def docs_to_code(self, page_id: str) -> list[CodeNode]:
        """给定 Wiki 页面，找到所有锚定的代码符号"""

    def cross_impact(self, changed_files: list[str]) -> CrossImpactResult:
        """代码变更 → 受影响的代码符号 → 关联的 Wiki 文档 → 过期风险"""

    def unified_communities(self) -> list[UnifiedCommunity]:
        """合并代码社区和文档社区，识别对齐/偏差"""
```

### 4.4 与现有引擎集成点

| SAW 引擎 | 集成方式 |
|----------|---------|
| Ingest | 代码文件 ingest 时同步更新 Code Graph |
| Query | 搜索时融合代码图上下文（"这个概念对应哪些代码？"） |
| Govern | 代码变更触发文档 freshness 检查 |
| Learn | 代码图社区 → 自动生成/更新架构文档 |
| Collaborate | Agent 可调用代码图工具获取结构上下文 |

---

## 5. 系统健壮性增强清单

### 5.1 数据完整性

| 措施 | 说明 |
|------|------|
| 确定性 UID | SCIP-style moniker，重索引不产生重复 |
| 幂等 Upsert | 按 content_hash 判断是否需要重解析 |
| 原子文件替换 | 单事务替换一个文件的所有 nodes/edges |
| WAL 模式 | 读写并发安全，crash recovery |
| 快照版本化 | 可回滚到任意历史图状态 |
| 完整性自检 | `saw code-graph verify` 检测图与源码偏差 |

### 5.2 运行时健壮性

| 措施 | 说明 |
|------|------|
| 消除全局可变状态 | 替换 `_graph` 全局变量为连接池/上下文管理器 |
| 线程安全 | SQLite WAL + 连接池，支持 FastAPI 多线程 |
| 优雅降级 | 图不可用时 MCP 工具返回结构化错误 + 建议 |
| 超时保护 | 大图遍历设 max_depth + timeout |
| 内存控制 | 大仓库使用流式解析，不一次性加载全部 AST |
| 错误隔离 | 单文件解析失败不影响整体构建 |

### 5.3 增量与性能

| 措施 | 说明 |
|------|------|
| Content-hash 跳过 | 未变更文件零开销 |
| Git-diff 驱动 | 仅处理变更文件集 |
| 并行解析 | ProcessPoolExecutor 文件批次并行 |
| 派生缓存 | FTS/社区/流 仅在图变更时重算 |
| 查询缓存 | 热点查询结果 LRU 缓存 |
| 懒加载 | 社区/流等派生结构按需计算 |

### 5.4 可观测性

| 措施 | 说明 |
|------|------|
| 构建指标 | 节点数/边数/解析时间/跳过文件数 |
| 查询指标 | 响应时间/命中率/token 节省量 |
| 健康检查 | `saw code-graph health` 输出图状态报告 |
| 变更日志 | 每次增量更新记录 diff 摘要 |
| 告警 | 图过期 > N 天 / 解析错误率 > 阈值 |

---

## 6. 实施路线图

### Sprint 1 (W1-2): 基础设施

- [ ] 创建 `src/saw/code_graph/` 包结构
- [ ] 实现 `store.py`: SQLite schema + CRUD + WAL
- [ ] 实现 `parser.py`: Tree-sitter Python/TypeScript 解析
- [ ] 实现 `incremental.py`: content-hash 增量检测
- [ ] 替换 `src/saw/graph.py` placeholder → 代理到新 store
- [ ] 单元测试: 解析 SAW 自身代码库验证

### Sprint 2 (W3-4): 查询与工具

- [ ] 实现 `postprocess.py`: 裸名解析 + 签名 + FTS5
- [ ] 升级 `saw_impact` MCP 工具 → 加权 BFS
- [ ] 新增 `saw_code_query` / `saw_code_search` MCP 工具
- [ ] 实现 `changes.py`: git diff → 风险评分
- [ ] 集成测试: MCP 工具端到端验证

### Sprint 3 (W5-6): 融合与高级功能

- [ ] 实现 Bridge Layer: doc↔code 锚定
- [ ] 实现社区检测 + 执行流追踪
- [ ] 实现 `saw_architecture` / `saw_code_context` 工具
- [ ] Govern 引擎集成: 代码变更 → 文档过期检测
- [ ] 前端可视化: 代码图 + Wiki 图统一视图

### Sprint 4 (W7-8): 健壮性与打磨

- [ ] 完整性自检 + 快照回滚
- [ ] 多语言 Resolver 扩展 (Java/Go/Rust)
- [ ] 性能基准测试 (目标: 增量 < 2s, 查询 < 100ms)
- [ ] 可观测性: 健康检查 + 指标 + 告警
- [ ] 文档: 用户指南 + API 文档 + 架构决策记录

---

## 7. 新增文件结构

```
src/saw/code_graph/
├── __init__.py              # 包入口，导出 CodeGraphEngine
├── models.py                # CodeNode, CodeEdge, EdgeType, NodeKind 数据模型
├── parser.py                # Tree-sitter 多语言解析器
├── resolvers/               # 语言特化解析器
│   ├── __init__.py
│   ├── base.py              # Resolver 基类
│   ├── python_resolver.py   # Python 装饰器/动态导入
│   ├── typescript_resolver.py  # TS paths/re-exports
│   └── registry.py          # Resolver 注册表
├── store.py                 # SQLite 图存储 (WAL, FTS5)
├── incremental.py           # 增量构建编排
├── postprocess.py           # 派生结构管线
├── flows.py                 # 执行流追踪
├── communities.py           # 社区检测 (Leiden/Louvain)
├── search.py                # 混合搜索 (FTS5 + vector RRF)
├── changes.py               # 变更检测 + 风险评分
├── bridge.py                # 双图融合桥接层
├── snapshot.py              # 图快照与回滚
└── health.py                # 健康检查与可观测性
```

---

## 8. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 图存储 | SQLite (非 Neo4j/KuzuDB) | 与 SAW 现有栈一致，零外部依赖，WAL 够用 |
| 解析器 | Tree-sitter (非 LSP) | 零 LLM 依赖，30+ 语言，增量解析，离线可用 |
| 社区算法 | Leiden (igraph) + Louvain 降级 | 比纯 Louvain 更稳定，igraph 可选依赖 |
| 搜索 | FTS5 + 可选 vector (RRF 融合) | 关键词精确 + 语义召回，渐进增强 |
| 增量策略 | content-hash + git-diff 双模式 | 有 git 用 git，无 git 用 hash |
| UID 方案 | file_path::qualified_name | 确定性、人类可读、重索引稳定 |
| 与 Wiki 图关系 | Bridge 松耦合 (非合并) | 两图更新频率不同，强合并增加复杂度 |

---

## 9. 参考来源

- [code-review-graph](https://github.com/tirth8205/code-review-graph) — 代码图生命周期完整实现
- [Aider repo-map](https://aider.chat/2023/10/22/repomap.html) — Tree-sitter + PageRank 代码图
- [SCIP Protocol](https://github.com/sourcegraph/scip) — 语言无关代码索引协议
- [Cursor codebase indexing](https://cursor.com/blog/secure-codebase-indexing) — Merkle tree 增量同步
- [Codebase-Memory (arXiv 2603.27277)](https://arxiv.org/html/2603.27277v1) — Tree-sitter KG + MCP
- [KG-Based Repo-Level Code Gen (arXiv 2505.14394)](https://arxiv.org/pdf/2505.14394) — 知识图谱提升代码生成质量
