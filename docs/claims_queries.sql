-- =============================================================================
-- Smart Agent Wiki — Claims Database 关键查询示例
-- =============================================================================
-- 覆盖: FTS5 全文搜索、置信度分布、新鲜度衰减、矛盾检测、图谱邻居查询
-- =============================================================================


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q1. FTS5 全文搜索 (BM25 排序)                                          ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 基础全文搜索
SELECT
    c.uuid,
    c.content,
    c.confidence,
    c.claim_type,
    c.source_mark,
    rank
FROM claim_fts f
JOIN claim c ON c.rowid = f.rowid
WHERE claim_fts MATCH 'transformer attention'
ORDER BY rank
LIMIT 20;

-- 按类型过滤的全文搜索
SELECT
    c.uuid,
    c.content,
    c.confidence,
    c.freshness,
    rank
FROM claim_fts f
JOIN claim c ON c.rowid = f.rowid
WHERE claim_fts MATCH 'transformer'
  AND f.claim_type = 'fact'
ORDER BY rank
LIMIT 20;

-- 带置信度阈值的高质量搜索
SELECT
    c.uuid,
    c.content,
    c.confidence,
    c.source_mark,
    rank
FROM claim_fts f
JOIN claim c ON c.rowid = f.rowid
WHERE claim_fts MATCH 'neural network'
  AND c.confidence >= 3                -- CrossValidated 或更高
  AND c.deleted_at IS NULL
ORDER BY rank
LIMIT 20;

-- 多词 OR 搜索（查找包含任一关键词的主张）
SELECT
    c.uuid,
    c.content,
    c.confidence,
    rank
FROM claim_fts f
JOIN claim c ON c.rowid = f.rowid
WHERE claim_fts MATCH 'RNN OR LSTM OR GRU'
  AND c.deleted_at IS NULL
ORDER BY rank
LIMIT 20;

-- 前缀搜索（模糊匹配）
SELECT
    c.uuid,
    c.content,
    rank
FROM claim_fts f
JOIN claim c ON c.rowid = f.rowid
WHERE claim_fts MATCH 'transform*'
  AND c.deleted_at IS NULL
ORDER BY rank
LIMIT 20;

-- 在标签中搜索
SELECT
    c.uuid,
    c.content,
    c.tags,
    rank
FROM claim_fts f
JOIN claim c ON c.rowid = f.rowid
WHERE f.tags_text MATCH 'architecture'
  AND c.deleted_at IS NULL
ORDER BY rank
LIMIT 20;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q2. 置信度分布统计                                                       ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 置信度层级分布
SELECT
    CASE confidence
        WHEN 1 THEN 'L1-Unverified'
        WHEN 2 THEN 'L2-SingleSource'
        WHEN 3 THEN 'L3-CrossValidated'
        WHEN 4 THEN 'L4-HumanVerified'
    END AS confidence_tier,
    COUNT(*) AS claim_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM claim
WHERE deleted_at IS NULL
GROUP BY confidence
ORDER BY confidence;

-- 置信度 x 来源标记 交叉分布（用于识别需要提升的主张）
SELECT
    confidence,
    source_mark,
    COUNT(*) AS cnt
FROM claim
WHERE deleted_at IS NULL
GROUP BY confidence, source_mark
ORDER BY confidence, source_mark;

-- 低置信度高影响主张（关联实体多但置信度低，需要优先验证）
SELECT
    c.uuid,
    c.content,
    c.confidence,
    c.source_mark,
    COUNT(DISTINCT ce.entity_uuid) AS entity_count
FROM claim c
JOIN claim_entity ce ON ce.claim_uuid = c.uuid AND ce.deleted_at IS NULL
WHERE c.deleted_at IS NULL
  AND c.confidence <= 2
GROUP BY c.uuid
HAVING entity_count >= 3
ORDER BY entity_count DESC, c.confidence ASC
LIMIT 20;

-- 最近提升到高置信度的主张（显示治理引擎的工作效果）
SELECT
    ar.target_uuid AS claim_uuid,
    ar.operation_data,
    ar.timestamp,
    c.content
FROM audit_receipt ar
JOIN claim c ON c.uuid = ar.target_uuid
WHERE ar.target_type = 'claim'
  AND ar.operation = 'update'
  AND json_extract(ar.operation_data, '$.field') = 'confidence'
  AND json_extract(ar.operation_data, '$.new') >= 3
ORDER BY ar.timestamp DESC
LIMIT 20;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q3. 新鲜度衰减与过期检测                                                  ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 按新鲜度级别统计（治理引擎 lint 报告的核心数据）
SELECT
    freshness,
    CASE freshness
        WHEN 0 THEN 'just created'
        WHEN 1 THEN '< 1 day'
        WHEN 2 THEN '< 3 days'
        WHEN 3 THEN '< 1 week'
        WHEN 4 THEN '< 2 weeks'
        WHEN 5 THEN '< 1 month'
        WHEN 6 THEN '< 3 months'
        WHEN 7 THEN '< 6 months'
        WHEN 8 THEN '> 6 months'
    END AS freshness_label,
    COUNT(*) AS cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM claim
WHERE deleted_at IS NULL
GROUP BY freshness
ORDER BY freshness;

-- 需要复查的主张（新鲜度 >= 5 且为战略性知识）
SELECT
    uuid,
    content,
    freshness,
    lifecycle,
    confidence,
    freshness_base,
    ROUND((julianday('now') - julianday(freshness_base))) AS days_since_base
FROM claim
WHERE deleted_at IS NULL
  AND freshness >= 5
  AND lifecycle = 'strategic'
ORDER BY freshness DESC, freshness_base ASC
LIMIT 20;

-- 可自动过期的战术性知识（新鲜度 >= 7 且为战术性知识）
SELECT
    uuid,
    content,
    freshness,
    lifecycle,
    freshness_base,
    ROUND((julianday('now') - julianday(freshness_base))) AS days_old
FROM claim
WHERE deleted_at IS NULL
  AND freshness >= 7
  AND lifecycle = 'tactical'
ORDER BY freshness DESC
LIMIT 50;

-- 新鲜度衰减批处理: 基于 freshness_base 时间重新计算新鲜度
-- （应用层定期执行，此处展示计算逻辑）
SELECT
    uuid,
    freshness AS current_freshness,
    CASE
        WHEN julianday('now') - julianday(freshness_base) < 0.5 THEN 0
        WHEN julianday('now') - julianday(freshness_base) < 1 THEN 1
        WHEN julianday('now') - julianday(freshness_base) < 3 THEN 2
        WHEN julianday('now') - julianday(freshness_base) < 7 THEN 3
        WHEN julianday('now') - julianday(freshness_base) < 14 THEN 4
        WHEN julianday('now') - julianday(freshness_base) < 30 THEN 5
        WHEN julianday('now') - julianday(freshness_base) < 90 THEN 6
        WHEN julianday('now') - julianday(freshness_base) < 180 THEN 7
        ELSE 8
    END AS computed_freshness,
    freshness_base
FROM claim
WHERE deleted_at IS NULL
HAVING current_freshness != computed_freshness
ORDER BY computed_freshness DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q4. 矛盾检测与冲突分析                                                    ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 所有未解决的矛盾
SELECT
    ct.uuid AS contradiction_id,
    ct.contradiction_type,
    ct.resolution_strategy,
    ct.similarity_score,
    a.content AS claim_a,
    a.confidence AS confidence_a,
    a.source_mark AS mark_a,
    b.content AS claim_b,
    b.confidence AS confidence_b,
    b.source_mark AS mark_b
FROM contradiction ct
JOIN claim a ON a.uuid = ct.claim_a_uuid
JOIN claim b ON b.uuid = ct.claim_b_uuid
WHERE ct.resolution_status = 'pending'
  AND ct.deleted_at IS NULL
  AND a.deleted_at IS NULL
  AND b.deleted_at IS NULL
ORDER BY ct.similarity_score DESC;

-- 同一文档内的潜在矛盾检测（基于 content_hash 去重后的语义近似）
-- 找出来自同一文档、类型为 fact 但内容可能冲突的主张对
SELECT
    a.uuid AS claim_a,
    a.content AS content_a,
    b.uuid AS claim_b,
    b.content AS content_b,
    a.source_uuid AS common_source
FROM claim a
JOIN claim b ON a.source_uuid = b.source_uuid AND a.uuid < b.uuid
WHERE a.deleted_at IS NULL
  AND b.deleted_at IS NULL
  AND a.claim_type = 'fact'
  AND b.claim_type = 'fact'
  AND NOT EXISTS (
      SELECT 1 FROM contradiction ct
      WHERE ct.deleted_at IS NULL
        AND ((ct.claim_a_uuid = a.uuid AND ct.claim_b_uuid = b.uuid)
          OR (ct.claim_a_uuid = b.uuid AND ct.claim_b_uuid = a.uuid))
  )
LIMIT 50;

-- 矛盾处理统计
SELECT
    contradiction_type,
    resolution_strategy,
    resolution_status,
    COUNT(*) AS cnt
FROM contradiction
WHERE deleted_at IS NULL
GROUP BY contradiction_type, resolution_strategy, resolution_status
ORDER BY contradiction_type, resolution_strategy;

-- 已解决矛盾的时间趋势
SELECT
    strftime('%Y-%m', resolved_at) AS month,
    resolution_strategy,
    COUNT(*) AS resolved_count
FROM contradiction
WHERE deleted_at IS NULL
  AND resolution_status = 'resolved'
  AND resolved_at IS NOT NULL
GROUP BY month, resolution_strategy
ORDER BY month, resolution_strategy;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q5. 知识图谱邻居查询 (BFS 遍历)                                          ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 1-hop 邻居: 查找 "Transformer" 实体的所有直接关联
SELECT
    e_from.name AS from_entity,
    e_from.entity_type AS from_type,
    er.relation_type,
    er.strength,
    e_to.name AS to_entity,
    e_to.entity_type AS to_type,
    er.description
FROM entity_relation er
JOIN entity e_from ON e_from.uuid = er.from_entity_uuid
JOIN entity e_to ON e_to.uuid = er.to_entity_uuid
WHERE er.deleted_at IS NULL
  AND (e_from.name = 'Transformer' OR e_to.name = 'Transformer')
ORDER BY er.strength DESC;

-- 2-hop 邻居: 通过中间实体查找间接关联
-- 先找 Transformer 的所有 1-hop 实体，再找这些实体的关联
WITH transformer_1hop AS (
    SELECT to_entity_uuid AS hop1_uuid
    FROM entity_relation
    WHERE from_entity_uuid = (SELECT uuid FROM entity WHERE name = 'Transformer')
      AND deleted_at IS NULL
    UNION
    SELECT from_entity_uuid AS hop1_uuid
    FROM entity_relation
    WHERE to_entity_uuid = (SELECT uuid FROM entity WHERE name = 'Transformer')
      AND deleted_at IS NULL
)
SELECT DISTINCT
    e2hop.name AS entity_name,
    e2hop.entity_type,
    er2.relation_type,
    er2.strength,
    e_hop1.name AS via_entity
FROM entity_relation er2
JOIN entity e2hop ON (e2hop.uuid = er2.from_entity_uuid OR e2hop.uuid = er2.to_entity_uuid)
JOIN entity e_hop1 ON e_hop1.uuid IN (
    CASE
        WHEN er2.from_entity_uuid IN (SELECT hop1_uuid FROM transformer_1hop)
            THEN er2.from_entity_uuid
        WHEN er2.to_entity_uuid IN (SELECT hop1_uuid FROM transformer_1hop)
            THEN er2.to_entity_uuid
    END
)
WHERE er2.deleted_at IS NULL
  AND e2hop.name != 'Transformer'
ORDER BY er2.strength DESC
LIMIT 30;

-- 实体的主张关联查询: 某实体的所有主张及其关系
SELECT
    e.name AS entity_name,
    ce.role AS claim_role,
    c.uuid AS claim_uuid,
    c.content,
    c.confidence,
    c.claim_type,
    c.freshness
FROM entity e
JOIN claim_entity ce ON ce.entity_uuid = e.uuid AND ce.deleted_at IS NULL
JOIN claim c ON c.uuid = ce.claim_uuid AND c.deleted_at IS NULL
WHERE e.name = 'Transformer'
ORDER BY c.confidence DESC, c.freshness ASC;

-- Adamic-Adar 指数计算 (共同邻居加权)
-- 用于查询引擎的"4 信号关联度模型"中的信号 3
WITH entity_claims AS (
    SELECT entity_uuid, claim_uuid
    FROM claim_entity
    WHERE deleted_at IS NULL
),
claim_neighbors AS (
    SELECT
        ec1.entity_uuid AS entity_a,
        ec2.entity_uuid AS entity_b,
        COUNT(*) AS shared_claims
    FROM entity_claims ec1
    JOIN entity_claims ec2 ON ec1.claim_uuid = ec2.claim_uuid
    WHERE ec1.entity_uuid < ec2.entity_uuid
    GROUP BY ec1.entity_uuid, ec2.entity_uuid
    HAVING shared_claims >= 2
)
SELECT
    ea.name AS entity_a,
    eb.name AS entity_b,
    cn.shared_claims AS common_claim_count
FROM claim_neighbors cn
JOIN entity ea ON ea.uuid = cn.entity_a AND ea.deleted_at IS NULL
JOIN entity eb ON eb.uuid = cn.entity_b AND eb.deleted_at IS NULL
ORDER BY cn.shared_claims DESC
LIMIT 20;

-- 高连接度实体 (Hub 节点)
SELECT
    e.name,
    e.entity_type,
    e.claim_count,
    (SELECT COUNT(*) FROM entity_relation er
     WHERE (er.from_entity_uuid = e.uuid OR er.to_entity_uuid = e.uuid)
       AND er.deleted_at IS NULL) AS relation_count
FROM entity e
WHERE e.deleted_at IS NULL
ORDER BY e.claim_count DESC, relation_count DESC
LIMIT 20;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q6. 审计链验证                                                           ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 某条主张的完整操作历史
SELECT
    ar.agent_id,
    ar.operation,
    ar.operation_data,
    ar.session_id,
    ar.timestamp
FROM audit_receipt ar
WHERE ar.target_type = 'claim'
  AND ar.target_uuid = 'c1'
ORDER BY ar.timestamp;

-- 某次摄入会话的所有操作
SELECT
    ar.target_type,
    ar.operation,
    ar.target_uuid,
    ar.agent_id,
    ar.timestamp
FROM audit_receipt ar
WHERE ar.session_id = 'session-001'
ORDER BY ar.timestamp;

-- Agent 操作统计
SELECT
    agent_id,
    operation,
    COUNT(*) AS op_count,
    MIN(timestamp) AS first_op,
    MAX(timestamp) AS last_op
FROM audit_receipt
GROUP BY agent_id, operation
ORDER BY agent_id, operation;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q7. 治理引擎 lint 健康检查                                                ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 综合健康指标
SELECT
    'total_claims' AS metric,
    COUNT(*) AS value
FROM claim WHERE deleted_at IS NULL
UNION ALL
SELECT
    'avg_confidence',
    ROUND(AVG(confidence), 2)
FROM claim WHERE deleted_at IS NULL
UNION ALL
SELECT
    'high_freshness_claims',
    COUNT(*)
FROM claim WHERE deleted_at IS NULL AND freshness >= 7
UNION ALL
SELECT
    'pending_contradictions',
    COUNT(*)
FROM contradiction WHERE resolution_status = 'pending' AND deleted_at IS NULL
UNION ALL
SELECT
    'total_entities',
    COUNT(*)
FROM entity WHERE deleted_at IS NULL
UNION ALL
SELECT
    'orphan_entities',
    COUNT(*)
FROM entity e
WHERE e.deleted_at IS NULL
  AND e.claim_count = 0
UNION ALL
SELECT
    'unverified_claims',
    COUNT(*)
FROM claim WHERE confidence = 1 AND deleted_at IS NULL
UNION ALL
SELECT
    'hot_claims',
    COUNT(*)
FROM claim WHERE temperature = 'hot' AND deleted_at IS NULL;

-- 主张类型分布
SELECT
    claim_type,
    COUNT(*) AS cnt,
    ROUND(AVG(confidence), 2) AS avg_confidence
FROM claim
WHERE deleted_at IS NULL
GROUP BY claim_type
ORDER BY cnt DESC;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q8. 温度分层与缓存构建                                                    ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 构建热缓存: 选取访问最频繁的高置信度主张
SELECT
    uuid,
    content,
    confidence,
    access_count,
    last_accessed
FROM claim
WHERE deleted_at IS NULL
  AND temperature = 'hot'
ORDER BY access_count DESC, confidence DESC
LIMIT 50;

-- 温度自动降级: 30 天未访问的 warm → glacier 候选
SELECT
    uuid,
    content,
    temperature,
    last_accessed,
    ROUND(julianday('now') - julianday(COALESCE(last_accessed, created_at))) AS days_idle
FROM claim
WHERE deleted_at IS NULL
  AND temperature = 'warm'
  AND julianday('now') - julianday(COALESCE(last_accessed, created_at)) > 30
LIMIT 100;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║ Q9. 溯源链查询                                                           ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 完整溯源链: Claim → ClaimSource → Vault
SELECT
    c.uuid AS claim_uuid,
    c.content,
    c.confidence,
    c.source_mark,
    cs.uuid AS source_id,
    cs.vault_uuid,
    cs.page_number,
    cs.paragraph,
    cs.text_offset,
    cs.text_length,
    cs.surrounding_text,
    cs.media_timestamp
FROM claim c
LEFT JOIN claim_source cs ON cs.claim_uuid = c.uuid AND cs.deleted_at IS NULL
WHERE c.uuid = 'c1'
  AND c.deleted_at IS NULL;

-- 某文档贡献的所有主张及其来源位置
SELECT
    c.uuid,
    c.content,
    c.confidence,
    c.claim_type,
    cs.page_number,
    cs.paragraph,
    cs.surrounding_text
FROM claim c
JOIN claim_source cs ON cs.claim_uuid = c.uuid AND cs.deleted_at IS NULL
WHERE cs.vault_uuid = 'v1'
  AND c.deleted_at IS NULL
ORDER BY cs.page_number, cs.paragraph;
