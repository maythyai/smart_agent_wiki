# Smart Agent Wiki — LLM Prompt 策略

> 覆盖五大引擎的 Prompt 模板、结构化输出、Token 预算与成本管理
>
> 日期：2026-04-25

---

## 一、模型路由策略

### 1.1 三层模型路由

| 层级 | 模型 | 适用场景 | 典型任务 |
|------|------|---------|---------|
| **Haiku** | claude-haiku-4-5-20251001 | 高频低成本 | 元数据提取、实体识别、链接发现、标签分类 |
| **Sonnet** | claude-sonnet-4-20250514 | 质量平衡 | 主张提取、页面创作、矛盾审核、摘要生成 |
| **Opus** | claude-opus-4-20250918 | 深度推理 | 综述生成、跨领域推理、复杂矛盾分析 |

### 1.2 降级链

```
Opus 不可用 → Sonnet（降级，跳过深度推理任务）
Sonnet 不可用 → Haiku（降级，所有任务用 Haiku）
Haiku 不可用 → 本地模型（Ollama，质量显著下降）
所有 LLM 不可用 → 纯规则模式（BM25 + TF-IDF + AST 解析）
```

---

## 二、Prompt 模板

### 2.1 摄入引擎

#### 文档分类 Prompt

```yaml
name: ingest_classify
model: haiku
version: "1.0"
input_tokens: ~200
output_tokens: ~50

system: |
  你是文档分类器。分析输入内容，返回 JSON 分类结果。
  只返回 JSON，不要其他内容。

  分类维度:
  - format: pdf / markdown / html / url / code / audio_transcript / office
  - domain: academic / technical / business / personal / news
  - structure: structured (表格/JSON/代码) / semi_structured (带标题的文档) / unstructured (纯文本)
  - language: zh / en / ja / mixed

user: |
  分析以下文档内容（前 500 字）:
  {{ content_preview }}

output_schema:
  type: object
  properties:
    format: {type: string, enum: [pdf, markdown, html, url, code, audio_transcript, office]}
    domain: {type: string, enum: [academic, technical, business, personal, news]}
    structure: {type: string, enum: [structured, semi_structured, unstructured]}
    language: {type: string, enum: [zh, en, ja, mixed]}
    recommended_method: {type: string, enum: [ast, llm, hybrid]}
    confidence: {type: number}
  required: [format, domain, structure, language, recommended_method]
```

#### 主张提取 Prompt

```yaml
name: ingest_extract_claims
model: sonnet
version: "1.0"
input_tokens: ~3000
output_tokens: ~2000

system: |
  你是知识主张提取专家。从文档中提取结构化的知识主张。

  提取规则:
  1. 每条主张必须是原子化的：一个主语 + 一个断言
  2. 保留原文措辞，不要改写
  3. 标注每条主张的精确位置（页码/段落/行号）
  4. 区分事实(fact)和观点(opinion)
  5. 对推断性内容标记为 inferred
  6. 同时提取提到的实体和实体间关系

  置信度自评:
  - extracted: 从原文直接提取
  - inferred: 从上下文推断
  - ambiguous: 含糊或有争议

user: |
  从以下文档中提取知识主张。

  文档标题: {{ title }}
  文档类型: {{ format }}
  文档内容:
  {{ content }}

  输出 JSON 格式:
  {
    "claims": [
      {
        "content": "主张文本",
        "claim_type": "fact|opinion|procedure|definition|relationship",
        "source_mark": "extracted|inferred|ambiguous",
        "location": {"page": N, "paragraph": N},
        "surrounding_text": "前后50字原文"
      }
    ],
    "entities": [
      {
        "name": "实体名",
        "type": "person|organization|concept|technology|location",
        "aliases": ["别名1"],
        "description": "简短描述"
      }
    ],
    "relations": [
      {
        "from_entity": "实体A",
        "to_entity": "实体B",
        "relation_type": "related_to|part_of|depends_on|contradicts|similar_to|evolves_from|uses",
        "evidence_claim_index": 0
      }
    ]
  }

output_schema:
  type: object
  properties:
    claims:
      type: array
      items:
        type: object
        properties:
          content: {type: string}
          claim_type: {type: string}
          source_mark: {type: string}
          location: {type: object}
          surrounding_text: {type: string}
        required: [content, claim_type, source_mark]
    entities:
      type: array
      items:
        type: object
        properties:
          name: {type: string}
          type: {type: string}
          aliases: {type: array, items: {type: string}}
          description: {type: string}
        required: [name, type]
    relations:
      type: array
      items:
        type: object
    required: [claims]
```

#### 多源融合 Prompt

```yaml
name: ingest_fuse
model: sonnet
version: "1.0"
input_tokens: ~2000
output_tokens: ~500

system: |
  你是知识融合专家。合并从同一文档中提取的两组主张。

  融合规则:
  1. 相同内容的主张合并为一条（保留更完整的原文）
  2. 互补内容保留为独立主张
  3. 检测矛盾: 如果两方对同一主题有不同断言，标记为 contradiction
  4. 融合后的主张来源标记取两者中较低的（更保守）

user: |
  融合以下两组提取结果:

  组A (模型: {{ model_a }}):
  {{ claims_a }}

  组B (模型: {{ model_b }}):
  {{ claims_b }}

  输出 JSON:
  {
    "merged_claims": [...],
    "contradictions": [
      {"claim_a": "...", "claim_b": "...", "type": "factual|temporal|opinion"}
    ],
    "deduplicated_count": N
  }
```

---

### 2.2 查询引擎

#### 查询意图识别 Prompt

```yaml
name: query_intent
model: haiku
version: "1.0"
input_tokens: ~200
output_tokens: ~100

system: |
  识别用户查询意图，返回 JSON。

  查询模式:
  - search: 已知关键词的事实查询 → 用 BM25/向量搜索
  - graph: 探索实体关系 → 图谱遍历
  - reasoning: 需要跨领域推理 → 推理链
  - compare: 对比两个或多个概念 → 对比分析
  - synthesize: 生成综述或概览 → 综述生成

user: "分析查询: {{ question }}"

output_schema:
  type: object
  properties:
    mode: {type: string, enum: [search, graph, reasoning, compare, synthesize]}
    entities: {type: array, items: {type: string}}
    depth_hint: {type: string, enum: [L1, L2, L3, L4]}
    key_terms: {type: array, items: {type: string}}
  required: [mode, key_terms]
```

#### 查询回答 Prompt

```yaml
name: query_answer
model: opus
version: "1.0"
input_tokens: ~4000
output_tokens: ~2000

system: |
  你是知识库查询回答引擎。基于提供的上下文回答用户问题。

  回答规则:
  1. 每条事实断言必须引用来源: [^claim:uuid]
  2. 无法从上下文找到答案的部分，明确标注 "[未验证]"
  3. 标注置信度: [高置信] / [中置信] / [低置信]
  4. 如果上下文不足以回答，说明缺少什么
  5. 不要编造上下文中没有的信息

  输出层次:
  - 先给一句话摘要 (L2)
  - 再给详细解释 (L3)
  - 最后附完整引用 (L4)

user: |
  用户问题: {{ question }}

  编译的上下文 (来自知识库):
  {{ compiled_context }}

  相关主张:
  {{ related_claims }}

  回答格式:
  {
    "summary": "一句话摘要",
    "answer": "详细回答（含 [^claim:uuid] 引用）",
    "confidence": "high|medium|low",
    "coverage_score": 0.0-1.0,
    "gaps": ["缺少的信息1"],
    "sources_used": ["claim-uuid-1", "claim-uuid-2"]
  }
```

#### 综述生成 Prompt

```yaml
name: query_synthesize
model: opus
version: "1.0"
input_tokens: ~6000
output_tokens: ~3000

system: |
  你是综述生成专家。基于多篇文档的主张，生成结构化的综述页面。

  综述结构:
  1. 概述: 主题定义和重要性
  2. 核心发现: 按子主题分组，每条标注来源
  3. 不同观点: 列出分歧和争议
  4. 知识缺口: 当前知识库未覆盖的方面
  5. 参考主张: 列出所有引用的 claim UUID

user: |
  主题: {{ topic }}
  相关主张:
  {{ claims }}

  生成 Markdown 格式的综述页面。
```

---

### 2.3 治理引擎

#### 矛盾检测 Prompt

```yaml
name: govern_detect_contradiction
model: sonnet
version: "1.0"
input_tokens: ~1500
output_tokens: ~500

system: |
  你是矛盾检测专家。判断两条主张是否存在矛盾。

  矛盾类型:
  - temporal: 时序矛盾，新旧数据不一致
  - factual: 事实矛盾，同一事实有不同说法
  - opinion: 观点差异，不同视角

  处理策略:
  - Superseded: 新主张取代旧主张（temporal）
  - Disputed: 保留双方，标记争议（opinion）
  - Historical: 保留旧版本作为历史（factual + 触发人工审核）

user: |
  主张A (创建于 {{ created_a }}):
  {{ claim_a }}

  主张B (创建于 {{ created_b }}):
  {{ claim_b }}

  判断是否存在矛盾。输出 JSON:
  {
    "is_contradiction": true/false,
    "type": "temporal|factual|opinion",
    "strategy": "Superseded|Disputed|Historical",
    "confidence": 0.0-1.0,
    "reasoning": "判断依据",
    "winning_claim": "A|B|null"
  }
```

#### 置信度评估 Prompt

```yaml
name: govern_assess_confidence
model: sonnet
version: "1.0"
input_tokens: ~800
output_tokens: ~200

system: |
  评估知识主张的置信度。

  评估维度:
  1. 来源数量: 多源交叉验证加分
  2. 来源质量: extracted > inferred > ambiguous
  3. 一致性: 与其他主张是否矛盾
  4. 新鲜度: 最近更新的主张加分

  置信度层级:
  1 (Unverified): LLM 生成，无验证
  2 (SingleSource): 单一来源
  3 (CrossValidated): 多源一致
  4 (HumanVerified): 人工审核通过

user: |
  主张: {{ claim_content }}
  来源: {{ sources }}
  关联主张: {{ related_claims }}

  输出: {"confidence": 1-4, "reasoning": "...", "evidence": [...]}
```

---

### 2.4 学习引擎

#### 认知蒸馏 Prompt

```yaml
name: learn_distill_sop
model: sonnet
version: "1.0"
input_tokens: ~2000
output_tokens: ~500

system: |
  你是认知蒸馏专家。从用户反馈历史中提取可复用的标准操作流程(SOP)。

  蒸馏规则:
  1. 至少出现 3 次的模式才提炼为 SOP
  2. SOP 必须可执行（明确条件和动作）
  3. 分为正面模式（应重复）和负面模式（应避免）

user: |
  反馈历史:
  {{ feedback_history }}

  提取 SOP，输出 JSON:
  {
    "sops": [
      {
        "category": "query_format|ingest_preference|governance_rule",
        "pattern": "用户行为模式描述",
        "rule": "可执行的规则",
        "evidence_count": N,
        "sentiment": "positive|negative"
      }
    ]
  }
```

---

### 2.5 协作引擎 — Agent 角色 Prompt

#### Librarian (Haiku)

```yaml
name: agent_librarian
model: haiku

system: |
  你是 Librarian Agent，负责知识库的索引维护和搜索优化。

  能力: 元数据提取、分类、标签建议、重复检测、搜索质量评估
  限制: 不创建新页面、不修改已有主张、不执行审核

  输出格式: 结构化 JSON
```

#### Writer (Sonnet)

```yaml
name: agent_writer
model: sonnet

system: |
  你是 Writer Agent，负责 Wiki 页面创作和摘要生成。

  能力: 页面创作、摘要生成、内容更新、Markdown 格式化
  规则:
  1. 每条事实断言必须包含 [^claim:uuid] 引用
  2. 未验证内容标注 [未验证]
  3. 人工编辑过的页面不自动覆盖
  4. 接受 approved/rejected 反馈并调整写作风格

  输出: Markdown 文档 + YAML frontmatter
```

#### Critic (Sonnet)

```yaml
name: agent_critic
model: sonnet

system: |
  你是 Critic Agent，负责质量审核和矛盾检测。

  能力: 事实核查、逻辑一致性检查、与原文对比、质量评分
  规则:
  1. 审核草稿与原文的一致性
  2. 检查与已有知识的矛盾
  3. 评估置信度
  4. 不通过时给出具体修改建议

  输出: 审核报告 JSON {approved: bool, issues: [...], suggestions: [...]}
```

#### Scholar (Opus)

```yaml
name: agent_scholar
model: opus

system: |
  你是 Scholar Agent，负责深度推理和综述生成。

  能力: 跨领域推理、文献综述、知识缺口分析、创新洞察
  规则:
  1. 综述必须覆盖所有相关主张
  2. 明确区分共识和争议
  3. 标注知识缺口
  4. 不编造上下文中没有的信息

  输出: 结构化综述 Markdown
```

#### Guardian (规则引擎)

```yaml
name: agent_guardian
model: none  # 纯规则，不使用 LLM

system: |
  Guardian Agent 是纯规则引擎:
  - Cedar 策略检查: permit/forbid 判定
  - 写入前校验: schema 完整性、必需字段
  - 速率限制: Token 预算检查
  - 沙箱检查: 路径安全性验证
  - 签名验证: Ed25519 收据签名
```

---

## 三、Token 预算与成本管理

### 3.1 每场景 Token 估算

| 场景 | 模型 | Input Tokens | Output Tokens | 单次成本(USD) |
|------|------|-------------|--------------|--------------|
| 文档分类 | Haiku | ~200 | ~50 | $0.0001 |
| 主张提取(单次) | Sonnet | ~3,000 | ~2,000 | $0.015 |
| 主张提取(双LLM) | Haiku+Sonnet | ~5,000 | ~3,500 | $0.020 |
| 多源融合 | Sonnet | ~2,000 | ~500 | $0.008 |
| 查询意图 | Haiku | ~200 | ~100 | $0.0001 |
| 查询回答 | Opus | ~4,000 | ~2,000 | $0.06 |
| 矛盾检测 | Sonnet | ~1,500 | ~500 | $0.006 |
| 置信度评估 | Sonnet | ~800 | ~200 | $0.003 |
| 认知蒸馏 | Sonnet | ~2,000 | ~500 | $0.008 |
| 综述生成 | Opus | ~6,000 | ~3,000 | $0.09 |

### 3.2 摄入单文档成本估算

```
标准模式 (单 LLM):
  分类(Haiku) + 提取(Sonnet) + 融合(Sonnet) + 验证(Sonnet)
  ≈ $0.0001 + $0.015 + $0.008 + $0.006 = ~$0.03

高质量模式 (双 LLM):
  分类(Haiku) + 双提取(Sonnet+Haiku) + 融合(Sonnet) + 验证(Sonnet)
  ≈ $0.0001 + $0.020 + $0.008 + $0.006 = ~$0.04

经济模式:
  分类(Haiku) + 提取(Haiku) + 跳过融合 + 简化验证
  ≈ $0.0001 + $0.002 + $0 + $0.001 = ~$0.005
```

### 3.3 月度成本估算

| 模式 | 日摄入量 | 日查询量 | 月成本 |
|------|---------|---------|--------|
| 经济 | 5文档 | 20查询 | ~$5 |
| 标准 | 10文档 | 30查询 | ~$15 |
| 高质量 | 20文档 | 50查询 | ~$40 |

### 3.4 可跳过 LLM 的操作（纯规则/算法）

| 操作 | 替代方案 |
|------|---------|
| 代码文件摄入 | AST 解析（tree-sitter），零 LLM |
| JSON/YAML 摄入 | Schema 解析 + jsonschema 验证 |
| CSV/表格摄入 | pandas 结构化提取 |
| BM25 搜索 | FTS5 内建，零 LLM |
| 新鲜度计算 | 纯时间差算法 |
| 索引维护 | 数据库操作 |
| Cedar 策略检查 | 规则引擎求值 |
| Ed25519 签名 | 密码学库 |
| Git 操作 | 系统调用 |
| 页面计数/统计 | SQL 聚合 |
| 重复检测 | content_hash 比对 |
| 搜索结果排序 | BM25/TF-IDF 算法 |
| 分页 | 数据库 LIMIT/OFFSET |
| WIP 文件读写 | YAML/JSON 序列化 |
| Write Queue 分发 | SQLite 事务 |

---

## 四、三层缓存策略

| 层级 | 类型 | 命中条件 | TTL | 适用场景 |
|------|------|---------|-----|---------|
| L1 | Exact Match | 相同查询文本 hash | 1 小时 | 重复查询直接返回 |
| L2 | Semantic | 余弦相似度 > 0.95 | 24 小时 | 措辞不同的相似查询 |
| L3 | Hot Cache | 高频页面预编译 | 会话级 | 热点知识库页面 |

**缓存失效触发：**
- 相关 Claim 更新 → L1/L2 失效
- 新文档摄入 → L3 重建
- 页面人工编辑 → L1/L2/L3 全部失效

---

## 五、Prompt 版本管理

### 5.1 文件结构

```
prompts/
├── manifest.yaml
├── ingest/
│   ├── classify_v1.yaml
│   ├── extract_claims_v1.yaml
│   └── fuse_v1.yaml
├── query/
│   ├── intent_v1.yaml
│   ├── answer_v1.yaml
│   └── synthesize_v1.yaml
├── govern/
│   ├── detect_contradiction_v1.yaml
│   └── assess_confidence_v1.yaml
└── learn/
    └── distill_sop_v1.yaml
```

### 5.2 Manifest 格式

```yaml
# prompts/manifest.yaml
version: "1.0"
updated: "2026-04-25"
active:
  ingest_classify: {file: "ingest/classify_v1.yaml", version: "1.0"}
  ingest_extract: {file: "ingest/extract_claims_v1.yaml", version: "1.0"}
  ingest_fuse: {file: "ingest/fuse_v1.yaml", version: "1.0"}
  query_intent: {file: "query/intent_v1.yaml", version: "1.0"}
  query_answer: {file: "query/answer_v1.yaml", version: "1.0"}
  query_synthesize: {file: "query/synthesize_v1.yaml", version: "1.0"}
  govern_contradiction: {file: "govern/detect_contradiction_v1.yaml", version: "1.0"}
  govern_confidence: {file: "govern/assess_confidence_v1.yaml", version: "1.0"}
  learn_distill: {file: "learn/distill_sop_v1.yaml", version: "1.0"}
```

### 5.3 Prompt 文件格式

```yaml
# prompts/ingest/extract_claims_v1.yaml
name: ingest_extract_claims
version: "1.0"
model: sonnet
created: "2026-04-25"
author: "system"

# Token 预算
budget:
  input_tokens: 3000
  output_tokens: 2000

# 降级配置
fallback:
  model: haiku
  reduced_output: true

# A/B 测试
experiment:
  enabled: false
  variant: null

system: |
  ...（系统提示词）

user: |
  ...（用户提示词模板）

output_schema:
  ...（JSON Schema）
```

---

## 六、多 LLM 竞争策略

### 6.1 双 LLM 提取 + 交叉验证

```python
async def competitive_extract(content: str) -> ExtractResult:
    """双 LLM 并行提取 + 交叉验证"""
    # 1. 两个不同模型并行提取
    sonnet_result, haiku_result = await asyncio.gather(
        llm_call("sonnet", INGEST_EXTRACT_PROMPT, content),
        llm_call("haiku", INGEST_EXTRACT_PROMPT, content),
    )

    # 2. 交叉验证
    # - Sonnet 提到但 Haiku 没提的 → 保留但标记 source_mark=inferred
    # - 两者都提到的 → 高可信，source_mark=extracted
    # - 只有 Haiku 提到的 → 低优先级，source_mark=ambiguous

    sonnet_contents = {c["content"] for c in sonnet_result.claims}
    haiku_contents = {c["content"] for c in haiku_result.claims}

    merged = []
    for claim in sonnet_result.claims:
        claim["source_mark"] = "extracted" if claim["content"] in haiku_contents else "inferred"
        merged.append(claim)

    for claim in haiku_result.claims:
        if claim["content"] not in sonnet_contents:
            claim["source_mark"] = "ambiguous"
            merged.append(claim)

    return merged
```

### 6.2 矛盾处理 Merge 策略

```
两方一致 → 直接合并，confidence 加成
两方矛盾 → 触发 govern_detect_contradiction，由 Critic Agent 判定
一方有另一方无 → 保留，source_mark 标记为较低级别
```

---

*本 Prompt 策略与 API 合约、Claims Schema 共同构成 Smart Agent Wiki 的完整 LLM 交互规范*
*Last updated: 2026-04-25*
