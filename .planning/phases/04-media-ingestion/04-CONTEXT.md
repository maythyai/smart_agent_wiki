# Phase 4: Media Ingestion - Context

**Gathered:** 2026-04-30
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous mode with Claude discretion)

<domain>
## Phase Boundary

**Goal:** 实现视频/音频转录并集成现有摄入管线

**Requirements:**
- MING-01: Video file upload (MP4, WebM, MOV)
- MING-02: Audio file upload (MP3, WAV, M4A, OGG)
- MING-03: Whisper transcription (local/API)
- MING-04: Metadata extraction (duration, format, bitrate)
- MING-05: Whisper model configuration
- MING-06: Claims/Wiki pipeline integration
- MING-07: Batch transcription support
- MING-08: Transcription preview before ingest

**In Scope:**
- 视频文件上传和转录
- 音频文件上传和转录
- Whisper 本地/API 双模式
- 元数据提取
- 批量处理支持
- 与现有 Claims/Wiki 管线集成

**Out of Scope:**
- 实时流媒体转录（延迟到 v2.2+）
- 视频内容分析（图像识别）
- 音频说话人分离（Speaker Diarization）

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion — 技术架构决策

**1. Whisper 实现模式**
- **决策:** 优先支持本地 Whisper (faster-whisper)，可选 OpenAI API
- **理由:** 本地模式零 API 成本，隐私安全；API 模式作为降级选项
- **实现:** 使用 `faster-whisper` 库（CTranslate2 优化），比官方 whisper 快 4x

**2. 大文件处理策略**
- **决策:** 使用临时文件 + 流式处理，限制单个文件 500MB
- **理由:** 视频文件通常较大，需要避免内存溢出
- **实现:** 上传到临时目录，分块处理，完成后清理

**3. 批量处理架构**
- **决策:** 使用 asyncio 并发 + 任务队列
- **理由:** 转录是 CPU/GPU 密集型，需要异步处理
- **实现:** 基于 asyncio.gather() 并发控制，最大并发数可配置

**4. 元数据存储**
- **决策:** 扩展 Vault metadata 字段，添加 media_info JSON
- **理由:** 与现有 Vault 架构一致，无需新增表
- **实现:** `media_info: {duration, format, bitrate, whisper_model, language}`

**5. 转录预览流程**
- **决策:** 添加 "preview" 状态，用户确认后才写入 Claims
- **理由:** Whisper 转录可能有误差，用户需要审核机会
- **实现:** 转录结果先存临时表，确认后迁移到 Claims

</decisions>

<code_context>
## Existing Code Insights

### 摄入引擎架构 (v1.1)

**核心文件:**
- `src/saw/ingest/` — 摄入引擎主目录
- `src/saw/ingest/extractors/` — 多格式提取器
- `src/saw/ingest/processors/` — 处理管线
- `src/saw/storage/vault.py` — Vault 存储
- `src/saw/storage/claims.py` — Claims 存储

**现有提取器模式:**
```python
# BaseExtractor 接口
class BaseExtractor:
    async def extract(self, content: bytes, metadata: dict) -> ExtractionResult:
        ...

# 已有: PDFExtractor, MarkdownExtractor, URLExtractor, CodeExtractor
```

**集成点:**
- 新增 `MediaExtractor` 实现 `BaseExtractor`
- 扩展 `IngestionEngine.register_extractor()` 注册媒体类型
- 复用 `ClaimsPipeline` 处理转录文本

### Write Queue 架构

**文件:** `src/saw/storage/write_queue.py`

```python
# 单入口写入模式
class WriteQueue:
    async def enqueue(self, operation: WriteOperation) -> str:
        # 写入 outbox，返回 operation_id
        ...

# Sinks: VaultSink, ClaimsSink, WikiSink, IndexSink, AuditSink
```

**集成点:**
- 转录完成后通过 WriteQueue 写入 Claims
- 复用现有的 idempotent sinks

### CLI 入口

**文件:** `src/saw/cli.py`

```python
# 现有命令: init, ingest, query, lint, verify, status, web
# 需要扩展: ingest --media <file> --model <whisper-model>
```

</code_context>

<specifics>
## Specific Ideas

### 1. MediaExtractor 实现

```python
# src/saw/ingest/extractors/media.py
class MediaExtractor(BaseExtractor):
    SUPPORTED_VIDEO = ['.mp4', '.webm', '.mov']
    SUPPORTED_AUDIO = ['.mp3', '.wav', '.m4a', '.ogg']
    
    def __init__(self, whisper_model: str = "base"):
        self.model = whisper_model
        self._whisper = None  # Lazy load
    
    async def extract(self, content: bytes, metadata: dict) -> ExtractionResult:
        # 1. 提取音频轨道（如果是视频）
        # 2. 调用 Whisper 转录
        # 3. 返回文本 + 时间戳 + 元数据
        ...
```

### 2. Whisper 模型配置

```yaml
# config.yaml
whisper:
  model: "base"  # tiny/base/small/medium/large
  device: "auto"  # auto/cuda/cpu
  language: "auto"  # auto detect
  compute_type: "float16"  # for GPU
```

### 3. 批量处理接口

```python
# CLI
saw ingest --media ./videos/ --batch-size 5 --model medium

# API
POST /api/v1/ingest/media/batch
{
  "files": ["video1.mp4", "audio1.mp3"],
  "options": {"model": "base", "preview": true}
}
```

### 4. 转录预览流程

1. 上传文件 → 创建临时条目（status: preview）
2. 转录完成 → 返回预览结果
3. 用户确认 → 迁移到 Claims（status: confirmed）
4. 用户取消 → 删除临时条目

</specifics>

<deferred>
## Deferred Ideas

### 实时流媒体转录
- 需要持续的音频流处理
- 延迟到 v2.2+ 或专门的项目

### 说话人分离 (Speaker Diarization)
- 需要额外的 pyannote.audio 模型
- 增加复杂度，延迟到 v2.1

### 视频内容分析
- 图像识别、OCR 等
- 超出当前范围

### 多语言转录优化
- 当前使用 Whisper 自动检测
- 未来可添加语言特定优化

</deferred>
