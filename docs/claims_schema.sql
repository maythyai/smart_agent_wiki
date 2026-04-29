-- =============================================================================
-- Smart Agent Wiki — Claims Database Schema (L1 Layer)
-- =============================================================================
-- 存储从原始文档中提取的结构化知识主张。
-- 每条主张可追溯到原始文档的精确位置。
--
-- 设计原则:
--   - SQLite 单文件部署，零配置
--   - UUID 使用 TEXT 类型存储
--   - 时间使用 ISO 8601 TEXT
--   - 布尔使用 INTEGER 0/1
--   - JSON 字段使用 TEXT + json() / json_extract()
--   - 所有表都有 created_at / updated_at 审计字段
--   - 软删除: deleted_at IS NULL 表示活跃记录
--   - 幂等写入: 通过 UUID 主键 + UPSERT 模式保证
-- =============================================================================

-- ─── Schema Versioning ─────────────────────────────────────────────────────
-- 采用 user_version PRAGMA 管理版本，应用层据此决定是否执行迁移。
-- 每次不可逆 schema 变更递增版本号。
--
-- 迁移策略:
--   PRAGMA user_version;                     -- 读取当前版本
--   PRAGMA user_version = N;                 -- 标记已迁移到版本 N
--   迁移脚本放在 migrations/001_to_002.sql 等文件中
--   应用启动时检查 user_version，按序执行未应用的迁移
-- ────────────────────────────────────────────────────────────────────────────
PRAGMA user_version = 1;

-- ─── SQLite 性能优化 PRAGMA ────────────────────────────────────────────────
-- 这些设置应在每次连接时执行（通过连接初始化钩子）
-- ────────────────────────────────────────────────────────────────────────────
PRAGMA journal_mode = WAL;                -- Write-Ahead Logging，读写不互斥
PRAGMA synchronous = NORMAL;              -- WAL 模式下 NORMAL 已足够安全
PRAGMA cache_size = -64000;               -- 64MB 页缓存
PRAGMA temp_store = MEMORY;               -- 临时表在内存中
PRAGMA mmap_size = 67108864;              -- 64MB 内存映射 I/O
PRAGMA foreign_keys = ON;                 -- 启用外键约束
PRAGMA busy_timeout = 5000;               -- 锁等待 5 秒

-- =============================================================================
-- 1. Claim（主张）
-- =============================================================================
-- 核心实体: 一条从原始文档中提取的结构化知识主张
-- 置信度层级: Unverified(1) / SingleSource(2) / CrossValidated(3) / HumanVerified(4)
-- 来源标记: extracted / inferred / ambiguous
-- 新鲜度: 0-8 级 (0=刚创建, 8=超过半年)
-- 温度: hot / warm / glacier
-- 知识生命周期: strategic / tactical
-- 审核状态: pending / approved / rejected / needs_review
-- 类型: fact / opinion / procedure / definition / relationship
-- =============================================================================

CREATE TABLE IF NOT EXISTS claim (
    -- 主键
    uuid            TEXT        NOT NULL PRIMARY KEY,

    -- 内容
    content         TEXT        NOT NULL,              -- 主张的完整文本
    content_hash    TEXT        NOT NULL,              -- SHA-256 hash，用于去重检测

    -- 来源文档 (FK → Vault 层，这里只记录关联，不强依赖)
    source_uuid     TEXT        NOT NULL,              -- 关联到 Vault 中的原始文档 UUID

    -- 来源位置信息 (JSON)
    -- 示例: {"page": 12, "paragraph": 3, "line": 15, "timestamp": "00:12:34"}
    source_location TEXT        NOT NULL DEFAULT '{}', -- JSON TEXT

    -- ── 置信度体系 ──
    -- 4 层置信度: 1=Unverified, 2=SingleSource, 3=CrossValidated, 4=HumanVerified
    confidence      INTEGER     NOT NULL DEFAULT 1
        CHECK (confidence BETWEEN 1 AND 4),

    -- 来源标记 (主张级别): extracted / inferred / ambiguous
    -- 与 confidence 正交:
    --   confidence 是聚合后的整体可信度
    --   source_mark 是这条主张本身的来源质量
    source_mark     TEXT        NOT NULL DEFAULT 'extracted'
        CHECK (source_mark IN ('extracted', 'inferred', 'ambiguous')),

    -- ── 新鲜度系统 (0-8 级) ──
    -- 0=刚创建, 1=1天内, 2=3天内, 3=1周内, 4=2周内
    -- 5=1月内, 6=3月内, 7=半年内, 8=超过半年
    freshness       INTEGER     NOT NULL DEFAULT 0
        CHECK (freshness BETWEEN 0 AND 8),

    -- 新鲜度基准时间: 用于计算新鲜度衰减
    freshness_base  TEXT        NOT NULL,              -- ISO 8601

    -- ── 温度分层 (hot/warm/glacier) ──
    temperature     TEXT        NOT NULL DEFAULT 'warm'
        CHECK (temperature IN ('hot', 'warm', 'glacier')),

    -- ── 知识生命周期 ──
    -- strategic: 永久保留 (核心概念、验证过的主张)
    -- tactical: 自动过期 (临时工作流、短期任务状态)
    lifecycle       TEXT        NOT NULL DEFAULT 'strategic'
        CHECK (lifecycle IN ('strategic', 'tactical')),

    -- ── 审核状态 ──
    review_status   TEXT        NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'approved', 'rejected', 'needs_review')),

    -- ── 类型标记 ──
    claim_type      TEXT        NOT NULL DEFAULT 'fact'
        CHECK (claim_type IN ('fact', 'opinion', 'procedure', 'definition', 'relationship')),

    -- ── 标签与元数据 ──
    tags            TEXT        NOT NULL DEFAULT '[]',  -- JSON ARRAY of strings
    metadata        TEXT        NOT NULL DEFAULT '{}',  -- JSON TEXT, 可扩展元数据

    -- ── 访问统计 ──
    access_count    INTEGER     NOT NULL DEFAULT 0,     -- 被查询引用的次数
    last_accessed   TEXT,                                -- 最近一次被查询引用的时间

    -- ── 审计字段 ──
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted_at      TEXT        DEFAULT NULL             -- 软删除，非 NULL 表示已删除
);

-- Claim 索引
-- 按来源文档查找所有主张
CREATE INDEX IF NOT EXISTS idx_claim_source_uuid
    ON claim (source_uuid) WHERE deleted_at IS NULL;

-- 按置信度筛选
CREATE INDEX IF NOT EXISTS idx_claim_confidence
    ON claim (confidence) WHERE deleted_at IS NULL;

-- 按新鲜度筛选（治理引擎用于查找需要复查的主张）
CREATE INDEX IF NOT EXISTS idx_claim_freshness
    ON claim (freshness) WHERE deleted_at IS NULL;

-- 按温度分层查询
CREATE INDEX IF NOT EXISTS idx_claim_temperature
    ON claim (temperature) WHERE deleted_at IS NULL;

-- 按审核状态查询
CREATE INDEX IF NOT EXISTS idx_claim_review_status
    ON claim (review_status) WHERE deleted_at IS NULL;

-- 按类型查询
CREATE INDEX IF NOT EXISTS idx_claim_type
    ON claim (claim_type) WHERE deleted_at IS NULL;

-- 按知识生命周期查询（过期修剪用）
CREATE INDEX IF NOT EXISTS idx_claim_lifecycle
    ON claim (lifecycle, freshness) WHERE deleted_at IS NULL;

-- 按创建时间排序（时间线视图）
CREATE INDEX IF NOT EXISTS idx_claim_created_at
    ON claim (created_at DESC) WHERE deleted_at IS NULL;

-- 内容去重: 通过 content_hash 快速检测重复主张
CREATE INDEX IF NOT EXISTS idx_claim_content_hash
    ON claim (content_hash) WHERE deleted_at IS NULL;

-- 最近访问（热缓存构建用）
CREATE INDEX IF NOT EXISTS idx_claim_last_accessed
    ON claim (last_accessed DESC) WHERE deleted_at IS NULL AND last_accessed IS NOT NULL;

-- 更新时间触发器: 自动维护 updated_at
CREATE TRIGGER IF NOT EXISTS trg_claim_updated_at
    AFTER UPDATE ON claim
    FOR EACH ROW
BEGIN
    UPDATE claim SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE uuid = NEW.uuid AND NEW.updated_at = OLD.updated_at;
END;


-- =============================================================================
-- 2. ClaimRelation（主张间关系）
-- =============================================================================
-- 支持: supports / refutes / supplements / corrects / supersedes
-- =============================================================================

CREATE TABLE IF NOT EXISTS claim_relation (
    uuid            TEXT        NOT NULL PRIMARY KEY,

    -- 关系的两个端点
    from_claim_uuid TEXT        NOT NULL,
    to_claim_uuid   TEXT        NOT NULL,

    -- 关系类型
    relation_type   TEXT        NOT NULL
        CHECK (relation_type IN (
            'supports',     -- 支持: from 支持 to
            'refutes',      -- 反驳: from 反驳 to
            'supplements',  -- 补充: from 补充 to
            'corrects',     -- 修正: from 修正 to 的错误
            'supersedes'    -- 取代: from 是 to 的更新版本
        )),

    -- 关系强度 (0.0 - 1.0)
    strength        REAL        NOT NULL DEFAULT 0.5
        CHECK (strength BETWEEN 0.0 AND 1.0),

    -- 关系来源
    source          TEXT        NOT NULL DEFAULT 'auto_detected'
        CHECK (source IN ('auto_detected', 'human_verified')),

    -- 关系说明
    explanation     TEXT,

    -- 审计字段
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted_at      TEXT        DEFAULT NULL,

    -- 约束: 同一对主张的同一类型关系只能有一条（活跃）
    UNIQUE (from_claim_uuid, to_claim_uuid, relation_type)
        ON CONFLICT REPLACE
);

-- 查找某条主张的所有关联主张
CREATE INDEX IF NOT EXISTS idx_claim_relation_from
    ON claim_relation (from_claim_uuid) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_claim_relation_to
    ON claim_relation (to_claim_uuid) WHERE deleted_at IS NULL;

-- 按关系类型筛选（如: 找出所有反驳关系）
CREATE INDEX IF NOT EXISTS idx_claim_relation_type
    ON claim_relation (relation_type) WHERE deleted_at IS NULL;

-- 外键约束（通过触发器实现，因为 SQLite FK 只能引用表列不能做软删除过滤）
CREATE TRIGGER IF NOT EXISTS trg_claim_relation_from_fk
    BEFORE INSERT ON claim_relation
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'from_claim_uuid references non-existent claim')
    WHERE NOT EXISTS (SELECT 1 FROM claim WHERE uuid = NEW.from_claim_uuid AND deleted_at IS NULL);
END;

CREATE TRIGGER IF NOT EXISTS trg_claim_relation_to_fk
    BEFORE INSERT ON claim_relation
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'to_claim_uuid references non-existent claim')
    WHERE NOT EXISTS (SELECT 1 FROM claim WHERE uuid = NEW.to_claim_uuid AND deleted_at IS NULL);
END;


-- =============================================================================
-- 3. ClaimSource（主张来源）
-- =============================================================================
-- 关联到 Vault 中的原始文档，包含精确位置信息
-- 一条 Claim 可以有多个来源（交叉验证场景）
-- =============================================================================

CREATE TABLE IF NOT EXISTS claim_source (
    uuid            TEXT        NOT NULL PRIMARY KEY,

    -- 关联的主张
    claim_uuid      TEXT        NOT NULL,

    -- 来源文档 (Vault UUID)
    vault_uuid      TEXT        NOT NULL,

    -- 精确位置信息
    page_number     INTEGER,            -- 页码 (PDF/文档)
    paragraph       INTEGER,            -- 段落号
    text_offset     INTEGER,            -- 在文档中的字符偏移量
    text_length     INTEGER,            -- 引用文本的长度

    -- 提取时的上下文片段（原文的前后文）
    surrounding_text TEXT,               -- 包含前后文的原始片段

    -- 媒体时间戳 (视频/音频场景)
    media_timestamp TEXT,                -- ISO 8601 duration 或 HH:MM:SS

    -- 来源标记 (在此来源中的标记，与 claim 级别的 source_mark 可能不同)
    source_mark     TEXT        NOT NULL DEFAULT 'extracted'
        CHECK (source_mark IN ('extracted', 'inferred', 'ambiguous')),

    -- 审计字段
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted_at      TEXT        DEFAULT NULL
);

-- 查找某条主张的所有来源
CREATE INDEX IF NOT EXISTS idx_claim_source_claim
    ON claim_source (claim_uuid) WHERE deleted_at IS NULL;

-- 查找某个文档贡献了哪些主张
CREATE INDEX IF NOT EXISTS idx_claim_source_vault
    ON claim_source (vault_uuid) WHERE deleted_at IS NULL;

-- 按页码查找（同页关联分析）
CREATE INDEX IF NOT EXISTS idx_claim_source_page
    ON claim_source (vault_uuid, page_number) WHERE deleted_at IS NULL;

-- FK 触发器
CREATE TRIGGER IF NOT EXISTS trg_claim_source_claim_fk
    BEFORE INSERT ON claim_source
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'claim_uuid references non-existent claim')
    WHERE NOT EXISTS (SELECT 1 FROM claim WHERE uuid = NEW.claim_uuid AND deleted_at IS NULL);
END;


-- =============================================================================
-- 4. Contradiction（矛盾记录）
-- =============================================================================
-- 记录两个 Claim 之间的冲突及其处理策略
-- =============================================================================

CREATE TABLE IF NOT EXISTS contradiction (
    uuid            TEXT        NOT NULL PRIMARY KEY,

    -- 冲突的两个主张
    claim_a_uuid    TEXT        NOT NULL,
    claim_b_uuid    TEXT        NOT NULL,

    -- 矛盾类型
    -- temporal:  时序性矛盾 (新数据取代旧数据)
    -- factual:   事实性矛盾 (硬性冲突，触发人工审核)
    -- opinion:   观点性矛盾 (不同视角)
    contradiction_type TEXT     NOT NULL
        CHECK (contradiction_type IN ('temporal', 'factual', 'opinion')),

    -- 处理策略
    -- Superseded: 新主张取代旧主张
    -- Disputed:   标记为争议，保留双方
    -- Historical: 历史记录，保留旧版本作为历史参考
    resolution_strategy TEXT    NOT NULL
        CHECK (resolution_strategy IN ('Superseded', 'Disputed', 'Historical')),

    -- 处理结果
    -- pending:   等待处理
    -- resolved:  已处理
    -- escalated: 已升级为人工审核
    resolution_status TEXT     NOT NULL DEFAULT 'pending'
        CHECK (resolution_status IN ('pending', 'resolved', 'escalated')),

    -- 获胜方（仅 Superseded 策略有意义）
    winning_claim_uuid TEXT,

    -- 处理说明
    resolution_note TEXT,

    -- 自动检测还是人工发现
    detected_by     TEXT        NOT NULL DEFAULT 'auto'
        CHECK (detected_by IN ('auto', 'human')),

    -- 相似度分数 (0-1, 越高越相似, 用来判断是否真的是同一主题)
    similarity_score REAL,

    -- 审计字段
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    resolved_at     TEXT,                               -- 处理时间
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted_at      TEXT        DEFAULT NULL
);

-- 查找某条主张涉及的所有矛盾
CREATE INDEX IF NOT EXISTS idx_contradiction_claim_a
    ON contradiction (claim_a_uuid) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_contradiction_claim_b
    ON contradiction (claim_b_uuid) WHERE deleted_at IS NULL;

-- 按处理状态查询（找到所有待处理的矛盾）
CREATE INDEX IF NOT EXISTS idx_contradiction_status
    ON contradiction (resolution_status) WHERE deleted_at IS NULL;

-- 按矛盾类型查询
CREATE INDEX IF NOT EXISTS idx_contradiction_type
    ON contradiction (contradiction_type) WHERE deleted_at IS NULL;

-- FK 触发器
CREATE TRIGGER IF NOT EXISTS trg_contradiction_claim_a_fk
    BEFORE INSERT ON contradiction
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'claim_a_uuid references non-existent claim')
    WHERE NOT EXISTS (SELECT 1 FROM claim WHERE uuid = NEW.claim_a_uuid AND deleted_at IS NULL);
END;

CREATE TRIGGER IF NOT EXISTS trg_contradiction_claim_b_fk
    BEFORE INSERT ON contradiction
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'claim_b_uuid references non-existent claim')
    WHERE NOT EXISTS (SELECT 1 FROM claim WHERE uuid = NEW.claim_b_uuid AND deleted_at IS NULL);
END;


-- =============================================================================
-- 5. Entity（实体）
-- =============================================================================
-- 从主张中提取的命名实体: 人物/组织/概念/技术/地点
-- =============================================================================

CREATE TABLE IF NOT EXISTS entity (
    uuid            TEXT        NOT NULL PRIMARY KEY,

    -- 实体名称
    name            TEXT        NOT NULL,

    -- 实体类型
    entity_type     TEXT        NOT NULL
        CHECK (entity_type IN (
            'person', 'organization', 'concept', 'technology', 'location'
        )),

    -- 别名列表 (JSON ARRAY)
    -- 例: ["Transformer", "Transformer架构", "Transformer model"]
    aliases         TEXT        NOT NULL DEFAULT '[]',

    -- 实体描述 (自动生成或人工编辑)
    description     TEXT,

    -- 关联的主张数量（缓存字段，由触发器或批量更新维护）
    claim_count     INTEGER     NOT NULL DEFAULT 0,

    -- Wikipedia/外部知识库链接
    external_ref    TEXT,                -- URL

    -- 审计字段
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted_at      TEXT        DEFAULT NULL,

    -- 同类型下名称唯一
    UNIQUE (name, entity_type) ON CONFLICT IGNORE
);

-- 按名称查找实体
CREATE INDEX IF NOT EXISTS idx_entity_name
    ON entity (name) WHERE deleted_at IS NULL;

-- 按类型筛选
CREATE INDEX IF NOT EXISTS idx_entity_type
    ON entity (entity_type) WHERE deleted_at IS NULL;

-- 别名搜索 (JSON 数组包含查询)
-- SQLite json_each() 可展开 aliases 数组，但需要运行时操作
-- 此处用辅助索引: 为常用别名建立查询入口


-- =============================================================================
-- 5b. ClaimEntity（主张-实体关联）
-- =============================================================================
-- 多对多: 一条 Claim 可提及多个 Entity，一个 Entity 可出现在多条 Claim 中
-- =============================================================================

CREATE TABLE IF NOT EXISTS claim_entity (
    uuid            TEXT        NOT NULL PRIMARY KEY,

    claim_uuid      TEXT        NOT NULL,
    entity_uuid     TEXT        NOT NULL,

    -- 实体在主张中的角色
    -- subject:   实体是主张的主体
    -- object:    实体是主张的客体
    -- context:   实体是上下文背景
    role            TEXT        NOT NULL DEFAULT 'subject'
        CHECK (role IN ('subject', 'object', 'context')),

    -- 提及次数（同一主张中同一实体可能出现多次）
    mention_count   INTEGER     NOT NULL DEFAULT 1,

    -- 审计字段
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT:%M:%fZ', 'now')),
    deleted_at      TEXT        DEFAULT NULL,

    -- 一对 (claim, entity) 只能有一条活跃关联
    UNIQUE (claim_uuid, entity_uuid) ON CONFLICT REPLACE
);

-- 查找某条主张关联的所有实体
CREATE INDEX IF NOT EXISTS idx_claim_entity_claim
    ON claim_entity (claim_uuid) WHERE deleted_at IS NULL;

-- 查找某个实体出现的所有主张
CREATE INDEX IF NOT EXISTS idx_claim_entity_entity
    ON claim_entity (entity_uuid) WHERE deleted_at IS NULL;

-- FK 触发器
CREATE TRIGGER IF NOT EXISTS trg_claim_entity_claim_fk
    BEFORE INSERT ON claim_entity
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'claim_uuid references non-existent claim')
    WHERE NOT EXISTS (SELECT 1 FROM claim WHERE uuid = NEW.claim_uuid AND deleted_at IS NULL);
END;

CREATE TRIGGER IF NOT EXISTS trg_claim_entity_entity_fk
    BEFORE INSERT ON claim_entity
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'entity_uuid references non-existent entity')
    WHERE NOT EXISTS (SELECT 1 FROM entity WHERE uuid = NEW.entity_uuid AND deleted_at IS NULL);
END;

-- 维护 entity.claim_count 缓存
CREATE TRIGGER IF NOT EXISTS trg_claim_entity_insert_count
    AFTER INSERT ON claim_entity
    FOR EACH ROW
BEGIN
    UPDATE entity
    SET claim_count = claim_count + 1,
        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE uuid = NEW.entity_uuid;
END;

CREATE TRIGGER IF NOT EXISTS trg_claim_entity_delete_count
    AFTER UPDATE OF deleted_at ON claim_entity
    FOR EACH ROW
    WHEN NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL
BEGIN
    UPDATE entity
    SET claim_count = MAX(0, claim_count - 1),
        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE uuid = NEW.entity_uuid;
END;


-- =============================================================================
-- 6. EntityRelation（实体间关系）
-- =============================================================================
-- =============================================================================

CREATE TABLE IF NOT EXISTS entity_relation (
    uuid            TEXT        NOT NULL PRIMARY KEY,

    -- 关系的两个端点
    from_entity_uuid TEXT       NOT NULL,
    to_entity_uuid   TEXT       NOT NULL,

    -- 关系类型
    relation_type   TEXT        NOT NULL
        CHECK (relation_type IN (
            'related_to',    -- 一般关联
            'part_of',       -- 组成关系 (子集)
            'depends_on',    -- 依赖关系
            'contradicts',   -- 对立关系
            'similar_to',    -- 相似关系
            'evolves_from',  -- 演化关系 (如: RNN → LSTM → Transformer)
            'uses'           -- 使用关系 (如: BERT uses Transformer)
        )),

    -- 来源主张（这条关系是从哪条主张中提取的）
    source_claim_uuid TEXT,

    -- 关系强度
    strength        REAL        NOT NULL DEFAULT 0.5
        CHECK (strength BETWEEN 0.0 AND 1.0),

    -- 关系描述
    description     TEXT,

    -- 审计字段
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted_at      TEXT        DEFAULT NULL,

    -- 同一对实体的同一类型关系只保留一条
    UNIQUE (from_entity_uuid, to_entity_uuid, relation_type)
        ON CONFLICT REPLACE
);

-- 查找某实体的所有出边
CREATE INDEX IF NOT EXISTS idx_entity_relation_from
    ON entity_relation (from_entity_uuid) WHERE deleted_at IS NULL;

-- 查找某实体的所有入边
CREATE INDEX IF NOT EXISTS idx_entity_relation_to
    ON entity_relation (to_entity_uuid) WHERE deleted_at IS NULL;

-- 按关系类型筛选
CREATE INDEX IF NOT EXISTS idx_entity_relation_type
    ON entity_relation (relation_type) WHERE deleted_at IS NULL;

-- FK 触发器
CREATE TRIGGER IF NOT EXISTS trg_entity_relation_from_fk
    BEFORE INSERT ON entity_relation
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'from_entity_uuid references non-existent entity')
    WHERE NOT EXISTS (SELECT 1 FROM entity WHERE uuid = NEW.from_entity_uuid AND deleted_at IS NULL);
END;

CREATE TRIGGER IF NOT EXISTS trg_entity_relation_to_fk
    BEFORE INSERT ON entity_relation
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'to_entity_uuid references non-existent entity')
    WHERE NOT EXISTS (SELECT 1 FROM entity WHERE uuid = NEW.to_entity_uuid AND deleted_at IS NULL);
END;


-- =============================================================================
-- 7. AuditReceipt（审计收据）
-- =============================================================================
-- Ed25519 签名收据，为多 Agent 环境提供密码学级别的操作审计
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_receipt (
    uuid            TEXT        NOT NULL PRIMARY KEY,

    -- 操作信息
    agent_id        TEXT        NOT NULL,               -- 执行操作的 Agent 标识
    operation       TEXT        NOT NULL,               -- 操作类型: create/update/delete/verify/merge/...
    target_type     TEXT        NOT NULL,               -- 目标实体类型: claim/entity/relation/contradiction
    target_uuid     TEXT        NOT NULL,               -- 目标实体 UUID

    -- 操作详情
    -- JSON: {"field": "confidence", "old": 1, "new": 3, "reason": "cross-validated"}
    operation_data  TEXT        NOT NULL DEFAULT '{}',

    -- Ed25519 签名
    -- 对 (agent_id || operation || target_type || target_uuid || timestamp) 的签名
    signature       TEXT        NOT NULL,               -- Base64 encoded Ed25519 signature
    public_key      TEXT        NOT NULL,               -- Base64 encoded Ed25519 public key

    -- 会话信息
    session_id      TEXT,                                -- 摄入/查询会话 ID

    -- 时间戳
    timestamp       TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    -- 不可篡改: 审计收据不提供 UPDATE/DELETE，只 INSERT
    -- 不设置 updated_at / deleted_at
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- 查找某目标的完整审计历史
CREATE INDEX IF NOT EXISTS idx_audit_target
    ON audit_receipt (target_type, target_uuid);

-- 查找某 Agent 的所有操作
CREATE INDEX IF NOT EXISTS idx_audit_agent
    ON audit_receipt (agent_id);

-- 按时间范围查询审计日志
CREATE INDEX IF NOT EXISTS idx_audit_timestamp
    ON audit_receipt (timestamp);

-- 按会话查询
CREATE INDEX IF NOT EXISTS idx_audit_session
    ON audit_receipt (session_id);

-- 禁止修改和删除审计收据
CREATE TRIGGER IF NOT EXISTS trg_audit_no_update
    BEFORE UPDATE ON audit_receipt
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'audit receipts are immutable');
END;

CREATE TRIGGER IF NOT EXISTS trg_audit_no_delete
    BEFORE DELETE ON audit_receipt
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'audit receipts are immutable');
END;


-- =============================================================================
-- 8. FTS5 全文搜索虚拟表
-- =============================================================================
-- 对 claim.content 建全文索引，支持 BM25 排序
-- 使用独立内容表策略（数据写入时通过触发器同步更新 FTS）
-- =============================================================================

CREATE VIRTUAL TABLE IF NOT EXISTS claim_fts USING fts5(
    content,                -- 主张全文
    tags,                   -- 标签文本（空格分隔）
    claim_type,             -- 类型
    source_mark,            -- 来源标记
    tokenize='porter unicode61'  -- Porter 词干 + Unicode61
);

-- FTS 同步触发器: 插入 claim 时自动更新 FTS
CREATE TRIGGER IF NOT EXISTS trg_claim_fts_insert
    AFTER INSERT ON claim
    FOR EACH ROW
    WHEN NEW.deleted_at IS NULL
BEGIN
    INSERT INTO claim_fts (rowid, content, tags, claim_type, source_mark)
    VALUES (
        NEW.rowid,
        NEW.content,
        -- 将 JSON 数组标签转为空格分隔的文本
        -- SQLite 3.38+ 支持 json_each
        COALESCE(
            (SELECT group_concat(je.value, ' ') FROM json_each(NEW.tags) AS je),
            ''
        ),
        NEW.claim_type,
        NEW.source_mark
    );
END;

-- FTS 同步触发器: 更新 claim 时先删后插
CREATE TRIGGER IF NOT EXISTS trg_claim_fts_update
    AFTER UPDATE ON claim
    FOR EACH ROW
    WHEN NEW.deleted_at IS NULL
BEGIN
    DELETE FROM claim_fts WHERE rowid = OLD.rowid;
    INSERT INTO claim_fts (rowid, content, tags, claim_type, source_mark)
    VALUES (
        NEW.rowid,
        NEW.content,
        COALESCE(
            (SELECT group_concat(je.value, ' ') FROM json_each(NEW.tags) AS je),
            ''
        ),
        NEW.claim_type,
        NEW.source_mark
    );
END;

-- FTS 同步触发器: 软删除时从 FTS 移除
CREATE TRIGGER IF NOT EXISTS trg_claim_fts_delete
    AFTER UPDATE OF deleted_at ON claim
    FOR EACH ROW
    WHEN NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL
BEGIN
    DELETE FROM claim_fts WHERE rowid = OLD.rowid;
END;


-- =============================================================================
-- 9. Schema Migrations 元数据表
-- =============================================================================
-- 记录每次迁移的详细信息，用于排查和回滚决策
-- =============================================================================

CREATE TABLE IF NOT EXISTS schema_migration (
    version         INTEGER     NOT NULL PRIMARY KEY,
    description     TEXT        NOT NULL,
    applied_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    checksum        TEXT        NOT NULL                -- 迁移脚本的 SHA-256，用于检测篡改
);


-- =============================================================================
-- 10. Write Queue Outbox（写入队列持久化）
-- =============================================================================
-- 保证多 Sink 写入的持久性和最终一致性
-- =============================================================================

CREATE TABLE IF NOT EXISTS write_outbox (
    uuid            TEXT        NOT NULL PRIMARY KEY,

    -- 操作信息
    op_id           TEXT        NOT NULL,               -- 幂等 ID（去重用）
    sink_name       TEXT        NOT NULL,               -- 目标 Sink: vault / claims / wiki / fts5 / vector / graph
    operation       TEXT        NOT NULL,               -- create / update / delete
    target_type     TEXT        NOT NULL,               -- claim / entity / relation / ...
    target_uuid     TEXT        NOT NULL,               -- 目标 UUID

    -- 操作数据
    payload         TEXT        NOT NULL DEFAULT '{}',  -- JSON

    -- 会话信息
    session_id      TEXT        NOT NULL,

    -- 状态
    status          TEXT        NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'dead_letter')),

    -- 重试
    retry_count     INTEGER     NOT NULL DEFAULT 0,
    max_retries     INTEGER     NOT NULL DEFAULT 5,
    next_retry_at   TEXT,                               -- 下次重试时间

    -- 审计字段
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    processed_at    TEXT,
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    -- 幂等保证
    UNIQUE (op_id, sink_name) ON CONFLICT IGNORE
);

-- 查找待处理的写入
CREATE INDEX IF NOT EXISTS idx_outbox_pending
    ON write_outbox (status, created_at)
    WHERE status IN ('pending', 'failed');

-- 按 session 分组查询
CREATE INDEX IF NOT EXISTS idx_outbox_session
    ON write_outbox (session_id);

-- 按 Sink 查询
CREATE INDEX IF NOT EXISTS idx_outbox_sink
    ON write_outbox (sink_name, status);

-- 死信队列查询
CREATE INDEX IF NOT EXISTS idx_outbox_dead_letter
    ON write_outbox (created_at)
    WHERE status = 'dead_letter';
