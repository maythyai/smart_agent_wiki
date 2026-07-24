# Wiki Skills 集成增强方案

> 基于 kbase-llm-wiki (v0.7.0) 与 tribal-wiki (v0.18.0) 两个成熟 Skill 的能力分析，
> 提出 Smart Agent Wiki 的 6 大增强方向及完整实施规格。
>
> 日期：2026-07-24
> 状态：Proposal
> 关联文档：`docs/llm-wiki.md`, `docs/llm_wiki_ecosystem_analysis.md`, `docs/ARCHITECTURE.md`

---

## 一、背景与动机

### 1.1 两个 Skill 的核心能力

**kbase-llm-wiki (v0.7.0)** 是一个文档→知识的编译器。它将不可变的原始文档"编译"为结构化 Wiki 层（`_wiki/` 目录），包含活目录 `index.md`、append-only 编译日志 `log.md`、以及带结构化 metadata 的主题页面。核心流程覆盖初始化、增量编译（Ingest）、查询（Query）、健康检查（Lint）、目录整理（Organize）五大操作。

**tribal-wiki (v0.18.0)** 是一个产品/项目级知识导航与治理协议。它通过 Concept Graph 建立类型化实体关系网络（App-Concept、Tribe-Concept、Concept-Concept），提供两级导航（全局拓扑→概念详情），并通过 Issue/CR 机制实现知识的反馈闭环。同时集成 Code Wiki（仓库级 AI 文档生成）和 Kbase（独立文档知识库）。

### 1.2 SAW 当前短板

| 维度 | 现状 | 差距 |
|------|------|------|
| 知识输出 | Claims 存 SQLite，缺乏人类可读的综合输出层 | 无 index/log/主题页结构 |
| 知识积累 | Query 结果消散在对话中 | 无 Query→Archive 闭环 |
| 质量治理 | Linter 存在但无分级 | 无 auto-fix vs report-only 分离 |
| 图谱语义 | 基于 wiki links 的无类型边 | 无 typed concept relations |
| 协作治理 | 6 Agent 但无结构化修正协议 | 无 Issue/CR 机制 |
| 代码文档 | code_graph + intelligence 但无仓库级文档 | 无 Code Wiki 生成 |

### 1.3 设计原则

- **增量集成**：不重写现有引擎，在现有 hexagonal 架构上扩展
- **编译不可变**：原始文档（Vault）永远不被修改，Wiki 层是派生产物
- **溯源优先**：每个 Wiki 页面的每个断言都可追溯到原始文档的具体位置
- **渐进增强**：每个方向可独立实施，无强耦合依赖

---

## 二、增强方向 1：Wiki 编译层

### 2.1 概述

在 Vault（不可变原始文档）和 Claims（结构化断言）之上，增加第三层输出——**Wiki 编译层**。这是一个面向人类和 Agent 可读的 Markdown 文件集合，由 AI 自动编译和维护，人类只读和提问。

### 2.2 目录结构

```
<vault_root>/
├── _wiki/                      # 编译输出层（AI 维护，人类只读）
│   ├── index.md                # 活目录：按主题分组，表格格式
│   ├── log.md                  # append-only 编译日志
│   ├── concepts/               # 概念类页面
│   │   ├── event-sourcing.md
│   │   └── cqrs.md
│   ├── howto/                  # 操作指南类页面
│   │   └── deploy-pipeline.md
│   ├── faq/                    # 常见问题类页面
│   ├── reference/              # 参考资料类页面
│   ├── comparison/             # 对比分析类页面
│   ├── archive/                # 归档类页面（Query→Archive 产物）
│   └── source-summary/         # 源文档摘要类页面
├── sources/                    # 原始文档（不可变）
│   ├── papers/
│   ├── meeting-notes/
│   └── ...
└── .saw/                       # SAW 内部数据
    ├── claims.db
    └── ...
```

### 2.3 Domain 模型扩展

```python
# src/saw/domain/wiki_layer.py

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


class WikiPageType(str, Enum):
    """Wiki 页面类型（8 种）"""
    CONCEPT = "concept"           # 概念解释
    FAQ = "faq"                   # 常见问题
    HOWTO = "howto"               # 操作指南
    REFERENCE = "reference"       # 参考资料
    COMPARISON = "comparison"     # 对比分析
    ARCHIVE = "archive"           # 查询归档
    SOURCE_SUMMARY = "source-summary"  # 源文档摘要
    ENTITY = "entity"             # 实体页面


class WikiConfidence(str, Enum):
    """Wiki 页面置信度"""
    HIGH = "high"         # 多源交叉验证
    MEDIUM = "medium"     # 单源但逻辑自洽
    LOW = "low"           # 推断或单源未验证


@dataclass(frozen=True)
class WikiSource:
    """Wiki 页面的溯源引用"""
    page_id: str                    # 原始文档在 Vault 中的 ID
    title: str                      # 人类可读标题（禁止用 pageId 代替）
    sections: list[str] = field(default_factory=list)  # 引用的具体章节
    repo_id: Optional[str] = None   # 跨仓库引用时的仓库 ID


@dataclass
class WikiPageMetadata:
    """Wiki 页面结构化元数据"""
    type: WikiPageType
    confidence: WikiConfidence
    sources: list[WikiSource]
    see_also: list[str] = field(default_factory=list)  # 相关页面文件名
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    topic: str = ""                 # 所属主题目录名


@dataclass
class WikiPage:
    """Wiki 编译层页面"""
    filename: str                   # 相对于 _wiki/ 的路径
    title: str
    content: str                    # Markdown 正文
    metadata: WikiPageMetadata
    is_index: bool = False
    is_log: bool = False


@dataclass
class WikiIndex:
    """活目录结构"""
    topics: dict[str, list["WikiIndexEntry"]]  # topic -> entries


@dataclass
class WikiIndexEntry:
    """目录条目"""
    filename: str
    title: str
    summary: str                    # 一行摘要（含源数量）
    updated: datetime
    is_archived: bool = False


@dataclass
class CompileLogEntry:
    """编译日志条目"""
    timestamp: datetime
    action: str                     # ingest | lint | organize | archive | update
    pages_affected: list[str]
    summary: str
    sources_processed: list[str] = field(default_factory=list)
```

### 2.4 Engine 接口

```python
# src/saw/engines/compile/compiler.py

from abc import ABC, abstractmethod
from pathlib import Path


class WikiCompiler(ABC):
    """Wiki 编译器接口"""

    @abstractmethod
    async def initialize(self, vault_root: Path) -> None:
        """初始化 _wiki/ 目录结构（index.md + log.md）"""
        ...

    @abstractmethod
    async def compile_full(self, vault_root: Path) -> "CompileResult":
        """全量编译：Phase A（结构）+ Phase B（内容）"""
        ...

    @abstractmethod
    async def compile_incremental(
        self, vault_root: Path, changed_sources: list[str]
    ) -> "CompileResult":
        """增量编译：仅处理变更的源文档"""
        ...

    @abstractmethod
    async def update_page(
        self, vault_root: Path, filename: str, new_content: str,
        metadata: "WikiPageMetadata"
    ) -> None:
        """更新单个 Wiki 页面"""
        ...

    @abstractmethod
    async def get_index(self, vault_root: Path) -> "WikiIndex":
        """读取当前 index.md 结构"""
        ...


class CompileResult:
    """编译结果"""
    pages_created: list[str]
    pages_updated: list[str]
    pages_unchanged: list[str]
    contradictions_found: list[str]
    log_entry: "CompileLogEntry"
```

### 2.5 编译流程（两阶段）

**Phase A — 结构初始化：**

1. 扫描 Vault 获取所有原始文档列表
2. 对文档进行分类（按主题/领域聚类）
3. 确定需要创建的 Wiki 页面集合（基于文档数量和主题覆盖）
4. 创建/更新 `_wiki/` 目录结构（主题子目录）
5. 初始化或更新 `index.md` 骨架

**Phase B — 内容编译：**

6. 逐文档深度提取（Claims → 综合为 Wiki 页面内容）
7. 交叉引用：识别页面间的 `[[wiki-link]]` 关系
8. 矛盾检测：新内容与已有页面的冲突标注（不解决，只标注）
9. 级联更新：新信息影响已有页面时，更新相关页面
10. Sources 填充：每个页面的 metadata.sources 精确到文档+章节
11. Confidence 评估：根据源数量和交叉验证程度评定置信度
12. 更新 `index.md`（新页面加入目录，摘要更新）
13. 追加 `log.md`（记录本次编译操作）

### 2.6 index.md 模板

```markdown
# Knowledge Wiki Index

> Auto-compiled by Smart Agent Wiki. Last updated: 2026-07-24T10:30:00+08:00
> Total pages: 23 | Sources: 47 | Contradictions: 2

## Concepts

| Page | Summary | Updated |
|------|---------|---------|
| [[event-sourcing]] | 事件溯源核心概念与模式（3 sources） | 2026-07-20 |
| [[cqrs]] | 命令查询职责分离架构（2 sources） | 2026-07-18 |

## How-To

| Page | Summary | Updated |
|------|---------|---------|
| [[deploy-pipeline]] | CI/CD 部署流程操作指南（4 sources） | 2026-07-22 |

## Archive

| Page | Summary | Updated |
|------|---------|---------|
| [[Archived: microservices-vs-monolith]] | 微服务 vs 单体架构对比分析（2 sources） | 2026-07-15 |
```

### 2.7 log.md 模板

```markdown
# Compile Log

> Append-only. Do not edit or delete entries.

## 2026-07-24T10:30:00+08:00 — INGEST

- Action: incremental compile
- Sources processed: `meeting-notes/2026-07-23-arch-review.md`
- Pages created: `concepts/blast-radius.md`
- Pages updated: `concepts/event-sourcing.md`, `howto/deploy-pipeline.md`
- Contradictions: 0
- Duration: 12.3s

## 2026-07-23T14:00:00+08:00 — LINT

- Action: health check (auto-fix)
- Fixed: index consistency (2 entries), seeAlso links (3 pages)
- Reported: 1 stale page, 1 orphan page
- Duration: 4.1s
```

### 2.8 核心约束（11 条规则）

1. `index.md` 和 `log.md` 必须位于 `_wiki/` 根目录
2. 创建 Wiki 页面时必须显式指定所属主题目录（`--topic`）
3. 所有 Wiki 页面（index/log 除外）必须携带完整 metadata
4. `sources[]` 只能引用原始文档（Vault 中的文档），不能引用其他 Wiki 页面（`type: archive` 除外）
5. 低信息量源（如目录页、空文件）不能作为 primary source
6. 删除操作仅限 `contentType=wiki` 的页面，需 4 步验证；永远不删除原始文档
7. Wiki 页面默认不参与向量化索引（`vectorize=false`），除非显式开启
8. 永远不修改 Vault 中的原始文档
9. 遇到矛盾不解决，只标注（`> [!contradiction]` 块）
10. `log.md` 是 append-only，不可编辑或删除已有条目
11. `sources[].title` 必须是人类可读的文档标题，禁止用 pageId 代替

### 2.9 MCP Tool 扩展

```python
# 新增 MCP tools
"saw_compile": {
    "description": "触发 Wiki 编译（全量或增量）",
    "params": {
        "mode": "full | incremental",
        "sources": ["optional: 指定源文档路径列表"]
    }
},
"saw_wiki_index": {
    "description": "读取 Wiki 编译层的 index.md 结构",
    "params": {}
},
"saw_wiki_page": {
    "description": "读取指定 Wiki 页面内容",
    "params": {"filename": "concepts/event-sourcing.md"}
},
"saw_wiki_log": {
    "description": "读取编译日志（最近 N 条）",
    "params": {"limit": 10}
}
```

### 2.10 CLI 命令

```bash
saw compile              # 增量编译（默认）
saw compile --full       # 全量编译
saw compile --source path/to/doc.md  # 编译指定文档
saw wiki index           # 查看 Wiki 目录
saw wiki page <name>     # 查看 Wiki 页面
saw wiki log             # 查看编译日志
saw wiki log --tail 5    # 最近 5 条日志
```

---

## 三、增强方向 2：Query → Archive 闭环

### 3.1 概述

当 Agent 基于 Wiki 回答问题后，可选择将答案归档为新的 Wiki 页面（`type: archive`）。这让 Q&A 产生的知识不会丢失在对话历史中，而是沉淀为可检索、可引用的持久知识。

### 3.2 流程设计

```
User Query
    │
    ▼
┌─────────────────┐
│  1. 读取 index  │  定位相关 Wiki 页面
└────────┬────────┘
         ▼
┌─────────────────┐
│  2. 读取页面    │  获取详细内容
└────────┬────────┘
         ▼
┌─────────────────┐
│  3. 综合回答    │  带引用的结构化答案
└────────┬────────┘
         ▼
┌─────────────────┐     No
│  4. 是否归档？  │────────→ 结束
└────────┬────────┘
         │ Yes
         ▼
┌─────────────────┐
│  5. 生成 Archive│  type: archive
│     页面        │  sources: 引用的 Wiki 页面
└────────┬────────┘
         ▼
┌─────────────────┐
│  6. 更新 index  │  [Archived] 前缀
│     追加 log    │
└─────────────────┘
```

### 3.3 Archive 页面模板

```markdown
# {查询问题的简短标题}

> Archived from query on {date}. This is a point-in-time snapshot
> and will NOT receive cascade updates.

## Overview

{查询问题} — {关键发现的一句话总结}

## Findings

{经过轻度编辑的答案正文，保留引用标注}

根据 [[event-sourcing]] 中的描述，事件溯源模式要求...
而 [[cqrs]] 则指出命令与查询应当分离...

## See Also

- [[event-sourcing]]
- [[cqrs]]
- [[deploy-pipeline]]

<!-- metadata:
type: archive
confidence: medium
sources:
  - pageId: wiki/concepts/event-sourcing.md
    title: "Event Sourcing 核心概念"
  - pageId: wiki/concepts/cqrs.md
    title: "CQRS 架构模式"
created: 2026-07-24
-->
```

### 3.4 Domain 模型

```python
# src/saw/domain/archive.py

@dataclass
class ArchiveRequest:
    """归档请求"""
    query: str                      # 原始查询问题
    answer: str                     # 生成的答案
    referenced_pages: list[str]     # 引用的 Wiki 页面路径
    confidence: WikiConfidence


@dataclass
class ArchiveResult:
    """归档结果"""
    filename: str                   # 生成的 archive 页面路径
    index_updated: bool
    log_appended: bool
```

### 3.5 Engine 接口

```python
# src/saw/engines/query/archiver.py

class QueryArchiver(ABC):
    """查询归档器"""

    @abstractmethod
    async def archive(
        self, vault_root: Path, request: ArchiveRequest
    ) -> ArchiveResult:
        """将查询结果归档为 Wiki 页面"""
        ...

    @abstractmethod
    async def suggest_archive(
        self, query: str, answer: str, referenced_pages: list[str]
    ) -> bool:
        """判断是否值得归档（信息密度、新颖度、复用价值）"""
        ...
```

### 3.6 归档判断标准

自动建议归档的条件（满足任意 2 条即建议）：

- 答案综合了 3 个以上 Wiki 页面的信息
- 答案包含原始页面中未显式陈述的推断/综合
- 查询问题具有复用价值（非一次性事实查询）
- 答案揭示了页面间的新关联

### 3.7 特殊规则

- Archive 页面的 `sources` 可以引用其他 Wiki 页面（这是唯一允许引用 Wiki 页面的例外）
- Archive 页面是时间点快照，不参与级联更新
- index.md 中 Archive 条目前缀 `[Archived]`
- 文件名格式：`archive/{slug-from-query}.md`

### 3.8 MCP Tool

```python
"saw_archive": {
    "description": "将查询结果归档为 Wiki 页面",
    "params": {
        "query": "原始查询问题",
        "answer": "生成的答案（Markdown）",
        "referenced_pages": ["引用的 Wiki 页面路径"]
    }
}
```

### 3.9 CLI 命令

```bash
saw query "微服务和单体架构怎么选？" --archive  # 查询并归档
saw archive list                                # 列出所有归档
saw archive remove <filename>                   # 删除归档（4 步验证）
```

---

## 四、增强方向 3：Lint 分级治理

### 4.1 概述

将现有 govern engine 的 linter 重构为两级治理模型：**Auto-fix**（无需确认，自动修复）和 **Report-only**（需人工判断，仅生成报告）。

### 4.2 Auto-fix 类（自动修复）

| 检查项 | 修复动作 |
|--------|----------|
| Index 一致性 | index.md 中的条目与 _wiki/ 实际文件对齐（补缺、删幽灵条目） |
| 内部链接修复 | `[[broken-link]]` → 修正为正确文件名或标记为 TODO |
| Sources 有效性 | 验证 sources[].pageId 在 Vault 中存在，title 非空且≠pageId |
| seeAlso 补全 | 基于内容相似度自动补充 seeAlso 链接 |
| 目录/metadata 一致性 | 文件所在目录与 metadata.type 匹配 |
| log.md 格式 | 验证 log 条目格式合规 |

### 4.3 Report-only 类（仅报告）

| 检查项 | 报告内容 |
|--------|----------|
| 事实矛盾 | 两个页面对同一事实的冲突描述，标注双方 sources |
| 过期内容 | 基于 Freshness 模型检测超过衰减阈值的页面 |
| 孤儿页面 | 无任何入链（backlinks）的页面 |
| 缺失概念页 | 被多次 `[[引用]]` 但不存在的页面 |
| 跨主题引用缺失 | 两个主题下的页面高度相关但无 seeAlso 链接 |
| 低置信度页面 | confidence=low 且超过 30 天未更新的页面 |
| Archive 源更新 | Archive 页面引用的 Wiki 页面已发生重大变更 |

### 4.4 Domain 模型

```python
# src/saw/domain/lint.py

from enum import Enum


class LintSeverity(str, Enum):
    AUTO_FIX = "auto_fix"       # 自动修复
    WARNING = "warning"         # 需关注
    ERROR = "error"             # 需人工处理


class LintCategory(str, Enum):
    INDEX_CONSISTENCY = "index_consistency"
    BROKEN_LINK = "broken_link"
    SOURCE_VALIDITY = "source_validity"
    SEE_ALSO = "see_also"
    DIR_METADATA = "dir_metadata"
    LOG_FORMAT = "log_format"
    CONTRADICTION = "contradiction"
    STALE_CONTENT = "stale_content"
    ORPHAN_PAGE = "orphan_page"
    MISSING_CONCEPT = "missing_concept"
    CROSS_TOPIC = "cross_topic"
    LOW_CONFIDENCE = "low_confidence"
    ARCHIVE_STALE = "archive_stale"


@dataclass
class LintFinding:
    """单条 lint 发现"""
    category: LintCategory
    severity: LintSeverity
    page: str                       # 受影响的页面
    description: str                # 问题描述
    suggestion: str                 # 修复建议
    auto_fixed: bool = False        # 是否已自动修复
    fix_detail: str = ""            # 自动修复的具体操作


@dataclass
class LintReport:
    """Lint 报告"""
    timestamp: datetime
    total_findings: int
    auto_fixed: list[LintFinding]
    warnings: list[LintFinding]
    errors: list[LintFinding]
    exploration_suggestions: list[str]  # 主动建议（如"建议补充 X 概念页"）
    duration_seconds: float
```

### 4.5 Engine 接口

```python
# src/saw/engines/govern/linter.py

class WikiLinter(ABC):
    """Wiki 健康检查器"""

    @abstractmethod
    async def lint(
        self, vault_root: Path, auto_fix: bool = True
    ) -> LintReport:
        """执行完整 lint 检查"""
        ...

    @abstractmethod
    async def lint_category(
        self, vault_root: Path, category: LintCategory
    ) -> list[LintFinding]:
        """执行单项检查"""
        ...

    @abstractmethod
    async def fix(self, vault_root: Path, findings: list[LintFinding]) -> list[LintFinding]:
        """执行自动修复（仅处理 severity=AUTO_FIX 的 findings）"""
        ...
```

### 4.6 执行流程

1. 读取 `_wiki/index.md` 和所有 Wiki 页面
2. 执行 Auto-fix 检查，直接修复（通过 write_queue）
3. 执行 Report-only 检查，生成 findings 列表
4. 生成 exploration_suggestions（主动建议）
5. 输出结构化 LintReport
6. 追加 `log.md`（记录本次 lint 操作）

### 4.7 Exploration Suggestions（主动建议）

Lint 不只找问题，还主动建议改进：

- "检测到 3 个页面都提到了 'event storming' 但没有专门的概念页，建议创建 `concepts/event-storming.md`"
- "concepts/ 目录下有 12 个页面但无导航页，建议创建 `concepts/README.md` 作为主题入口"
- "最近 7 天有 5 个新源文档未编译，建议运行 `saw compile`"

### 4.8 MCP Tool

```python
"saw_lint": {
    "description": "Wiki 健康检查（分级治理）",
    "params": {
        "auto_fix": true,           # 是否执行自动修复
        "category": "optional: 仅检查指定类别"
    }
}
```

### 4.9 CLI 命令

```bash
saw lint                    # 完整检查 + 自动修复
saw lint --no-fix           # 仅报告，不修复
saw lint --category links   # 仅检查链接
saw lint --json             # JSON 格式输出（供 CI 消费）
```

---

## 五、增强方向 4：Concept Graph 与类型化关系

### 5.1 概述

在现有知识图谱（基于 wiki links 的无类型边）基础上，引入**类型化概念关系**和**产品级导航**能力。借鉴 tribal-wiki 的 Concept Graph 设计，支持三种关系类型和 Stable/Fresh 知识分类。

### 5.2 关系类型

```python
# src/saw/domain/concept.py

from enum import Enum


class ConceptRelationType(str, Enum):
    """概念关系类型"""
    # 结构关系
    IS_PART_OF = "is_part_of"         # A 是 B 的组成部分
    DEPENDS_ON = "depends_on"         # A 依赖 B
    IMPLEMENTS = "implements"         # A 实现了 B（代码→概念）

    # 语义关系
    RELATED_TO = "related_to"         # 一般性关联
    CONTRADICTS = "contradicts"       # 与...矛盾
    SUPERSEDES = "supersedes"         # 取代/更新
    SPECIALIZES = "specializes"       # 是...的特化

    # 导航关系
    BELONGS_TO_TOPIC = "belongs_to"   # 属于某主题
    REFERENCES_CODE = "references_code"  # 关联代码实体


@dataclass(frozen=True)
class ConceptRelation:
    """类型化概念关系"""
    source: str                       # 源节点（页面/概念/代码实体）
    target: str                       # 目标节点
    relation_type: ConceptRelationType
    confidence: WikiConfidence
    evidence: list[WikiSource] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)


class KnowledgeStability(str, Enum):
    """知识稳定性分类"""
    STABLE = "stable"     # 高层稳定知识：需严格证据才能更新
    FRESH = "fresh"       # 新鲜知识：AI 可自由更新，滚动衰减
```

### 5.3 Stable vs Fresh 治理规则

| 维度 | Stable | Fresh |
|------|--------|-------|
| 更新权限 | 需 Human Verified 或 CR 审批 | AI Agent 可自主更新 |
| 衰减速度 | 慢（半衰期 90 天） | 快（半衰期 14 天） |
| 矛盾处理 | 保留两者，开 Issue 讨论 | 新覆盖旧，记录 log |
| 典型内容 | 架构决策、核心概念、术语定义 | 会议纪要、近期变更、临时方案 |
| 标记方式 | metadata.stability: stable | metadata.stability: fresh（默认） |

### 5.4 与现有 Freshness 模型的融合

SAW 现有 9 级 Freshness 模型增加 stability 维度：

```python
# 修改 src/saw/domain/freshness.py

@dataclass
class FreshnessConfig:
    """新鲜度配置（融合 stability）"""
    base_half_life_days: int          # 基础半衰期
    stability_multiplier: float       # Stable=3.0, Fresh=1.0
    auto_update_allowed: bool         # Fresh=True, Stable=False
    decay_acceleration_on_conflict: float  # 矛盾时加速衰减
```

### 5.5 产品级导航（两级）

借鉴 tribal-wiki 的导航模式：

**Level 1 — 全局拓扑：**
```bash
saw graph --overview
# 输出：主题聚类、核心概念节点、关系密度热力图
```

**Level 2 — 概念详情：**
```bash
saw concept view "event-sourcing"
# 输出：
# - 概念定义（来自 Wiki 页面）
# - 关联概念（typed relations）
# - 关联代码实体（implements 关系的反向）
# - 相关页面（seeAlso + backlinks）
# - 知识状态（confidence, freshness, stability）
```

### 5.6 Engine 接口

```python
# src/saw/engines/query/concept_graph.py

class ConceptGraphEngine(ABC):
    """类型化概念图谱引擎"""

    @abstractmethod
    async def add_relation(self, relation: ConceptRelation) -> None:
        """添加类型化关系"""
        ...

    @abstractmethod
    async def remove_relation(
        self, source: str, target: str, relation_type: ConceptRelationType
    ) -> None:
        """移除关系（不删除节点本身）"""
        ...

    @abstractmethod
    async def get_concept(self, name: str) -> "ConceptDetail":
        """获取概念详情（定义+关系+关联代码+状态）"""
        ...

    @abstractmethod
    async def get_overview(self) -> "GraphOverview":
        """获取全局拓扑概览"""
        ...

    @abstractmethod
    async def infer_relations(self, page: WikiPage) -> list[ConceptRelation]:
        """从页面内容自动推断关系（AI 辅助）"""
        ...

    @abstractmethod
    async def navigate(
        self, start: str, relation_types: list[ConceptRelationType], depth: int = 2
    ) -> list["ConceptNode"]:
        """从起点沿指定关系类型导航"""
        ...
```

### 5.7 自动关系推断

编译阶段（Phase B）自动推断关系：

- 页面中的 `[[wiki-link]]` → `RELATED_TO`
- 页面 metadata.type=concept 且被 code 页面引用 → `IMPLEMENTS`（反向）
- 页面 metadata.topic 相同 → `BELONGS_TO_TOPIC`
- 页面中出现 "depends on"、"requires"、"based on" 等模式 → `DEPENDS_ON`
- 矛盾标注 → `CONTRADICTS`

### 5.8 MCP Tool 扩展

```python
"saw_concept_view": {
    "description": "查看概念详情（定义+关系+代码关联+状态）",
    "params": {"name": "概念名称"}
},
"saw_concept_relate": {
    "description": "添加/移除概念间关系",
    "params": {
        "source": "源节点",
        "target": "目标节点",
        "relation": "关系类型",
        "action": "add | remove"
    }
},
"saw_graph_overview": {
    "description": "获取知识图谱全局拓扑",
    "params": {"include_code_entities": false}
},
"saw_navigate": {
    "description": "从起点沿关系类型导航",
    "params": {
        "start": "起始节点",
        "relations": ["depends_on", "implements"],
        "depth": 2
    }
}
```

### 5.9 CLI 命令

```bash
saw concept list                    # 列出所有概念
saw concept view "event-sourcing"   # 概念详情
saw concept relate A B depends_on   # 添加关系
saw concept relate A B depends_on --remove  # 移除关系
saw graph --overview                # 全局拓扑
saw graph --topic "architecture"    # 按主题过滤
saw navigate "event-sourcing" --via depends_on --depth 3
```

### 5.10 前端可视化增强

在现有 Cytoscape.js 图谱基础上：

- 边着色：不同 relation_type 用不同颜色/线型
- 节点形状：concept（圆）、code entity（方）、wiki page（菱形）
- Stability 标记：Stable 节点实线边框，Fresh 节点虚线边框
- 交互：点击边显示关系详情和 evidence
- 过滤面板：按 relation_type、stability、confidence 过滤

---

## 六、增强方向 5：知识反馈闭环（Issue/CR 机制）

### 6.1 概述

引入结构化的知识质疑与修正协议。当 Agent 或人类发现知识问题时，通过 Issue（轻量反馈）或 CR（重量级修改）进行结构化处理，防止 AI 自我审批，确保知识质量。

### 6.2 Issue 类型

| 类型 | 触发场景 | 处理方式 |
|------|----------|----------|
| challenge | 内容与已知事实矛盾 | 讨论→修正或标注 |
| request | 知识缺口（需要但缺失的知识） | 研究→补充 |
| suggestion | 改进建议（结构、表述、关联） | 评估→采纳或拒绝 |

### 6.3 CR（Change Request）流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Create  │────→│  Review  │────→│  Apply   │
│  (任何人) │     │  (审批人) │     │  (系统)  │
└──────────┘     └──────────┘     └──────────┘
                      │
                      ▼ Reject
                 ┌──────────┐
                 │ Rejected │
                 └──────────┘
```

**关键规则：**
- AI Agent 不能自我审批（创建者≠审批人）
- Stable 知识的 CR 必须经 Human Verified 角色审批
- Fresh 知识的 CR 可由另一个 Agent（非创建者）审批
- CR 只用于 UPDATE 操作；DELETE 直接执行（4 步验证）；ADD 直接执行

### 6.4 Domain 模型

```python
# src/saw/domain/feedback.py

from enum import Enum


class IssueType(str, Enum):
    CHALLENGE = "challenge"     # 内容与事实矛盾
    REQUEST = "request"         # 知识缺口
    SUGGESTION = "suggestion"   # 改进建议


class IssueStatus(str, Enum):
    OPEN = "open"
    DISCUSSING = "discussing"
    RESOLVED = "resolved"
    WONTFIX = "wontfix"


class CRStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass
class KnowledgeIssue:
    """知识问题反馈"""
    id: str
    type: IssueType
    title: str
    description: str
    affected_pages: list[str]       # 受影响的 Wiki 页面
    reporter: str                   # 报告者（human/agent name）
    status: IssueStatus = IssueStatus.OPEN
    comments: list["IssueComment"] = field(default_factory=list)
    linked_cr: Optional[str] = None  # 关联的 CR ID
    created: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


@dataclass
class IssueComment:
    """Issue 评论"""
    author: str
    content: str
    created: datetime = field(default_factory=datetime.now)


@dataclass
class ChangeRequest:
    """知识变更请求"""
    id: str
    title: str
    description: str
    target_page: str                # 目标 Wiki 页面
    proposed_content: str           # 提议的新内容（diff 或全文）
    creator: str                    # 创建者
    reviewer: Optional[str] = None  # 审批人（≠creator）
    status: CRStatus = CRStatus.PENDING
    review_comment: str = ""
    linked_issue: Optional[str] = None  # 关联的 Issue ID
    created: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None


@dataclass
class FeedbackDecision:
    """反馈决策（基于确定性程度）"""
    certainty: float                # 0.0-1.0
    action: str                     # "direct_update" | "create_cr" | "create_issue" | "annotate_only"
    reason: str
```

### 6.5 决策矩阵

| 确定性 | 知识类型 | 动作 |
|--------|----------|------|
| > 0.9 | Fresh | 直接更新 + log 记录 |
| > 0.9 | Stable | 创建 CR（需审批） |
| 0.6 - 0.9 | 任何 | 创建 Issue (challenge) + 标注 |
| < 0.6 | 任何 | 仅标注 `> [!uncertain]`，不修改 |

### 6.6 Engine 接口

```python
# src/saw/engines/govern/feedback.py

class FeedbackEngine(ABC):
    """知识反馈引擎"""

    # Issue 操作
    @abstractmethod
    async def create_issue(
        self, issue_type: IssueType, title: str, description: str,
        affected_pages: list[str], reporter: str
    ) -> KnowledgeIssue:
        ...

    @abstractmethod
    async def comment_issue(self, issue_id: str, author: str, content: str) -> None:
        ...

    @abstractmethod
    async def resolve_issue(self, issue_id: str, resolution: str) -> None:
        ...

    @abstractmethod
    async def list_issues(
        self, status: Optional[IssueStatus] = None,
        issue_type: Optional[IssueType] = None
    ) -> list[KnowledgeIssue]:
        ...

    # CR 操作
    @abstractmethod
    async def create_cr(
        self, title: str, target_page: str, proposed_content: str,
        creator: str, linked_issue: Optional[str] = None
    ) -> ChangeRequest:
        ...

    @abstractmethod
    async def review_cr(
        self, cr_id: str, reviewer: str, approved: bool, comment: str = ""
    ) -> ChangeRequest:
        """审批 CR（reviewer ≠ creator 强制校验）"""
        ...

    @abstractmethod
    async def apply_cr(self, cr_id: str) -> None:
        """应用已审批的 CR（更新页面 + index + log）"""
        ...

    # 决策辅助
    @abstractmethod
    async def decide_action(
        self, certainty: float, stability: KnowledgeStability
    ) -> FeedbackDecision:
        """根据确定性和知识稳定性决定反馈动作"""
        ...
```

### 6.7 与 6-Agent 系统的集成

| Agent | 反馈角色 |
|-------|----------|
| Critic | 发现矛盾时创建 Issue (challenge) |
| Scholar | 研究完成后提交 CR（更新知识） |
| Guardian | 校验 CR 流程合规（creator≠reviewer） |
| Writer | 执行 CR apply 后的页面重写 |
| Librarian | 更新 index/log |
| Linker | CR apply 后修复受影响的链接 |

### 6.8 MCP Tool 扩展

```python
"saw_issue_create": {
    "description": "创建知识问题反馈",
    "params": {
        "type": "challenge | request | suggestion",
        "title": "问题标题",
        "description": "详细描述",
        "affected_pages": ["受影响的页面"]
    }
},
"saw_issue_list": {
    "description": "列出知识问题",
    "params": {"status": "open", "type": "optional"}
},
"saw_cr_create": {
    "description": "创建知识变更请求",
    "params": {
        "title": "变更标题",
        "target_page": "目标页面",
        "proposed_content": "提议内容",
        "linked_issue": "optional: 关联 Issue ID"
    }
},
"saw_cr_review": {
    "description": "审批变更请求",
    "params": {
        "cr_id": "CR ID",
        "approved": true,
        "comment": "审批意见"
    }
}
```

### 6.9 CLI 命令

```bash
saw issue list                      # 列出所有 Issue
saw issue list --status open        # 仅 open 状态
saw issue create --type challenge --title "..." --pages "a.md,b.md"
saw issue comment <id> --message "..."
saw issue resolve <id>

saw cr list                         # 列出所有 CR
saw cr create --page "concepts/x.md" --content-file proposed.md
saw cr approve <id> --comment "LGTM"
saw cr reject <id> --comment "证据不足"
saw cr apply <id>                   # 应用已审批的 CR
```

### 6.10 存储设计

```sql
-- 新增表（通过 migration）
CREATE TABLE knowledge_issues (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('challenge', 'request', 'suggestion')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_pages TEXT NOT NULL,     -- JSON array
    reporter TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    linked_cr TEXT,
    created_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE issue_comments (
    id TEXT PRIMARY KEY,
    issue_id TEXT NOT NULL REFERENCES knowledge_issues(id),
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE change_requests (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    target_page TEXT NOT NULL,
    proposed_content TEXT NOT NULL,
    creator TEXT NOT NULL,
    reviewer TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    review_comment TEXT,
    linked_issue TEXT,
    created_at TEXT NOT NULL,
    reviewed_at TEXT,
    applied_at TEXT,
    CHECK(creator != reviewer)        -- 禁止自我审批
);
```

---

## 七、增强方向 6：Code Wiki 生成

### 7.1 概述

将 SAW 现有的 code_graph（AST 解析、社区检测）和 code intelligence（impact/process/staleness）能力，编译为**仓库级 AI 文档**（Code Wiki），纳入统一的 Wiki 编译层。

### 7.2 与现有能力的关系

```
code_graph (AST)  ──┐
                    ├──→  Code Wiki Compiler  ──→  _wiki/code/
code intelligence ──┘         │
                              ▼
                    type: reference
                    sources: 代码文件路径
```

### 7.3 Code Wiki 页面结构

```
_wiki/
├── code/                           # Code Wiki 目录
│   ├── README.md                   # 仓库概览（架构、模块划分、技术栈）
│   ├── modules/                    # 按模块/目录组织
│   │   ├── auth.md                 # auth 模块文档
│   │   ├── ingest-pipeline.md      # ingest 模块文档
│   │   └── query-engine.md         # query 模块文档
│   ├── apis/                       # API 文档
│   │   ├── rest-endpoints.md
│   │   └── mcp-tools.md
│   └── data-models/                # 数据模型文档
│       ├── domain-entities.md
│       └── database-schema.md
```

### 7.4 页面模板

```markdown
# {模块名}

> Auto-generated from code analysis. Source: `{repo_path}/{module_path}`
> Last analyzed: {date} | Commit: {short_hash}

## Overview

{模块职责的一段话描述}

## Architecture

{模块内部结构：类/函数关系、设计模式}

## Key Components

### {ClassOrFunction}

- **Purpose**: {职责}
- **Inputs**: {参数说明}
- **Outputs**: {返回值说明}
- **Dependencies**: {依赖的其他模块}

## Data Flow

{数据在模块内的流转路径}

## Impact Scope

- WILL_BREAK: {直接依赖此模块的组件}
- LIKELY_AFFECTED: {间接依赖}
- MAY_NEED_TESTING: {可能受影响的测试}

## See Also

- [[code/modules/auth]] — 认证模块（被本模块依赖）
- [[concepts/event-sourcing]] — 相关领域概念

<!-- metadata:
type: reference
confidence: high
stability: fresh
sources:
  - pageId: "src/saw/engines/ingest/"
    title: "Ingest Engine 源码"
    sections: ["pipeline.py", "extractors.py"]
created: 2026-07-24
-->
```

### 7.5 Domain 模型

```python
# src/saw/domain/code_wiki.py

@dataclass
class CodeWikiConfig:
    """Code Wiki 生成配置"""
    repo_path: Path                   # 代码仓库路径
    target_path: str = ""             # monorepo 时的子目录
    branch: str = "main"
    skip_if_exists: bool = False      # 增量模式
    include_patterns: list[str] = field(default_factory=lambda: ["**/*.py", "**/*.ts"])
    exclude_patterns: list[str] = field(default_factory=lambda: ["**/node_modules/**", "**/.git/**"])
    depth: int = 3                    # 分析深度（目录层级）


@dataclass
class CodeWikiPage:
    """Code Wiki 页面"""
    filename: str                     # 相对于 _wiki/code/ 的路径
    title: str
    content: str
    source_files: list[str]           # 分析的源文件列表
    commit_hash: str                  # 分析时的 commit
    metadata: WikiPageMetadata


@dataclass
class CodeWikiResult:
    """Code Wiki 生成结果"""
    pages_generated: list[str]
    pages_updated: list[str]
    pages_skipped: list[str]          # skip_if_exists 跳过的
    total_source_files: int
    duration_seconds: float
```

### 7.6 Engine 接口

```python
# src/saw/engines/compile/code_wiki.py

class CodeWikiCompiler(ABC):
    """Code Wiki 编译器"""

    @abstractmethod
    async def generate(self, config: CodeWikiConfig) -> CodeWikiResult:
        """生成/更新 Code Wiki"""
        ...

    @abstractmethod
    async def generate_module(
        self, config: CodeWikiConfig, module_path: str
    ) -> CodeWikiPage:
        """生成单个模块的文档"""
        ...

    @abstractmethod
    async def status(self, config: CodeWikiConfig) -> "CodeWikiStatus":
        """检查 Code Wiki 状态（是否存在、是否过期）"""
        ...

    @abstractmethod
    async def diff_since_last(
        self, config: CodeWikiConfig
    ) -> list[str]:
        """返回自上次生成以来变更的源文件列表"""
        ...
```

### 7.7 生成流程

1. **扫描**：遍历仓库，按 include/exclude 模式筛选源文件
2. **分组**：按目录/模块聚类（利用 code_graph 的社区检测结果）
3. **分析**：对每个模块执行 AST 解析 + impact analysis
4. **编译**：LLM 将分析结果编译为人类可读的文档页面
5. **关联**：识别模块间依赖，建立 `[[wiki-link]]` 和 `DEPENDS_ON` 关系
6. **概念锚定**：将代码实体与已有概念页面关联（`IMPLEMENTS` 关系）
7. **写入**：输出到 `_wiki/code/` 目录
8. **更新**：刷新 index.md（Code 主题）+ 追加 log.md

### 7.8 增量更新策略

- 基于 `git diff` 检测自上次生成以来变更的文件
- 仅重新生成受影响模块的文档
- `--skip-if-exists` 模式：已有文档的模块跳过（适合首次生成后的小幅更新）
- Staleness 检测：当源文件变更但 Code Wiki 未更新时，标记为 stale

### 7.9 MCP Tool

```python
"saw_code_wiki_generate": {
    "description": "生成/更新 Code Wiki",
    "params": {
        "repo_path": "代码仓库路径",
        "target_path": "optional: monorepo 子目录",
        "skip_if_exists": false,
        "branch": "main"
    }
},
"saw_code_wiki_status": {
    "description": "检查 Code Wiki 状态",
    "params": {"repo_path": "代码仓库路径"}
},
"saw_code_wiki_diff": {
    "description": "查看自上次生成以来的代码变更",
    "params": {"repo_path": "代码仓库路径"}
}
```

### 7.10 CLI 命令

```bash
saw code-wiki generate /path/to/repo              # 全量生成
saw code-wiki generate /path/to/repo --incremental # 增量更新
saw code-wiki generate /path/to/repo --module src/auth  # 单模块
saw code-wiki status /path/to/repo                # 查看状态
saw code-wiki diff /path/to/repo                  # 查看变更
```

---

## 八、实施路线图

### 8.1 依赖关系

```
方向 1（Wiki 编译层）
    │
    ├──→ 方向 2（Query→Archive）    依赖 Wiki 层存在
    │
    ├──→ 方向 3（Lint 分级）        依赖 Wiki 层存在
    │
    ├──→ 方向 6（Code Wiki）        依赖 Wiki 层存在
    │
    └──→ 方向 4（Concept Graph）    可与方向 1 并行，但 typed edges 需要页面存在
    
方向 5（Issue/CR）                  独立，可与任何方向并行
```

### 8.2 分阶段计划

| 阶段 | 内容 | 预估工作量 | 里程碑 |
|------|------|-----------|--------|
| Phase 1 | 方向 1 核心：_wiki/ 结构 + compiler + index/log | 3-4 天 | v4.2-alpha |
| Phase 2 | 方向 3：Lint 分级（auto-fix + report） | 2 天 | v4.2-alpha |
| Phase 3 | 方向 2：Query→Archive 闭环 | 1-2 天 | v4.2-beta |
| Phase 4 | 方向 4：Concept Graph typed edges + 导航 | 3-4 天 | v4.2-beta |
| Phase 5 | 方向 5：Issue/CR 反馈机制 | 2-3 天 | v4.2-rc |
| Phase 6 | 方向 6：Code Wiki 生成 | 3-4 天 | v4.3 |
| Phase 7 | 前端集成：Wiki 浏览器 + 图谱增强 + Issue 面板 | 4-5 天 | v4.3 |

### 8.3 验收标准

**Phase 1 验收：**
- `saw compile` 能从 Vault 中的 3+ 源文档编译出结构化 Wiki 层
- index.md 正确反映所有页面，按主题分组
- log.md 记录每次编译操作
- 每个页面有完整 metadata（type, confidence, sources）
- sources 可追溯到具体文档和章节

**Phase 2 验收：**
- `saw lint` 自动修复 index 不一致和断链
- 报告矛盾、过期、孤儿页等问题
- 输出结构化 LintReport（JSON 可消费）

**Phase 3 验收：**
- `saw query "..." --archive` 生成 archive 页面
- Archive 页面 sources 正确引用 Wiki 页面
- index 中出现 `[Archived]` 条目

**Phase 4 验收：**
- 概念间可建立 typed relations
- `saw concept view` 显示完整概念详情
- 图谱可视化区分不同关系类型
- Stable/Fresh 分类影响衰减速度

**Phase 5 验收：**
- 可创建 Issue 和 CR
- CR 强制 creator≠reviewer
- CR apply 后页面正确更新
- 6-Agent 系统正确集成反馈流程

**Phase 6 验收：**
- `saw code-wiki generate` 从代码仓库生成模块文档
- 文档包含 impact scope 和依赖关系
- 增量更新仅处理变更文件
- Code Wiki 页面纳入统一 index

---

## 九、与现有架构的集成点

### 9.1 Write Queue 集成

所有 Wiki 层写操作通过现有 write_queue（SQLite outbox pattern）：

```python
# 新增 sink
class WikiLayerSink:
    """Wiki 编译层写入 sink"""
    async def handle(self, event: WriteEvent) -> None:
        if event.type == "wiki_page_create":
            # 写入 _wiki/ 文件 + 更新 index + 追加 log
        elif event.type == "wiki_page_update":
            # 更新文件 + 级联检查 + 追加 log
        elif event.type == "wiki_page_delete":
            # 4 步验证 + 删除 + 更新 index + 追加 log
```

### 9.2 MCP Server 集成

在现有 `src/saw/drivers/mcp/` 中新增 tool 模块：

```
src/saw/drivers/mcp/tools/
├── ingest.py          # 现有
├── query.py           # 现有
├── govern.py          # 现有
├── learn.py           # 现有
├── pages.py           # 现有
├── compile.py         # 新增：Wiki 编译层 tools
├── concept.py         # 新增：Concept Graph tools
├── feedback.py        # 新增：Issue/CR tools
└── code_wiki.py       # 新增：Code Wiki tools
```

### 9.3 Web API 集成

新增 FastAPI routes：

```
src/saw/drivers/web/routes/
├── wiki_compile.py    # POST /api/wiki/compile, GET /api/wiki/index, GET /api/wiki/page/{path}
├── concepts.py        # GET /api/concepts, GET /api/concepts/{name}, POST /api/concepts/relate
├── feedback.py        # CRUD /api/issues, CRUD /api/change-requests
└── code_wiki.py       # POST /api/code-wiki/generate, GET /api/code-wiki/status
```

### 9.4 前端页面

```
web/src/pages/
├── WikiBrowser.tsx    # Wiki 编译层浏览器（index 树 + 页面阅读）
├── ConceptGraph.tsx   # 增强版图谱（typed edges + 过滤）
├── Feedback.tsx       # Issue/CR 管理面板
└── CodeWiki.tsx       # Code Wiki 状态与生成控制
```

---

## 十、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 编译层与 Claims 层数据不一致 | 用户困惑 | 编译层是 Claims 的"视图"，单向派生，不允许反向写入 |
| LLM 编译质量不稳定 | Wiki 页面质量波动 | confidence 标注 + lint 自动检查 + 人工 review 机制 |
| Code Wiki 过期 | 文档与代码脱节 | git hook 触发增量更新 + staleness 检测 + Freshness 衰减 |
| CR 流程过重 | 小修改也要审批 | Fresh 知识允许直接更新，仅 Stable 知识需 CR |
| 图谱关系爆炸 | 可视化混乱 | 默认只显示 confidence≥medium 的关系 + 按类型过滤 |
| 与现有 v4.2 semantic features 冲突 | 重复建设 | Concept Graph 是 semantic search 的基础设施，互补不冲突 |

---

## 附录 A：参考资料

- kbase-llm-wiki v0.7.0 SKILL.md（编译流程、11 条约束、metadata 规格）
- tribal-wiki v0.18.0 SKILL.md（Concept Graph、Issue/CR、Code Wiki）
- `docs/llm-wiki.md`（Karpathy LLM Wiki 原始概念）
- `docs/llm_wiki_ecosystem_analysis.md`（181 个开源项目生态分析）
- `docs/ARCHITECTURE.md`（SAW 现有架构）

## 附录 B：术语对照

| kbase-llm-wiki 术语 | tribal-wiki 术语 | SAW 对应 |
|---------------------|-----------------|----------|
| _wiki/ 层 | Wiki Pages | Wiki 编译层（新增） |
| raw documents | Kbase 文档 | Vault（已有） |
| index.md | tw pages | WikiIndex（新增） |
| log.md | — | CompileLog（新增） |
| metadata.type | — | WikiPageType（新增） |
| sources[] | — | WikiSource（新增，关联 Claim.evidence） |
| lint | — | WikiLinter（增强现有 linter） |
| — | Concept Graph | ConceptGraphEngine（新增） |
| — | tw graph | GraphOverview（增强现有 graph） |
| — | Issue | KnowledgeIssue（新增） |
| — | CR (Change Request) | ChangeRequest（新增） |
| — | Code Wiki | CodeWikiCompiler（新增） |
| — | Stable/Fresh | KnowledgeStability（融合 Freshness） |
| compile/ingest | generate | WikiCompiler.compile_*（新增） |
| query + archive | — | QueryArchiver（新增） |
