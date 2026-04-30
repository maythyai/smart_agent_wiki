# Media Ingestion Engine — 设计规范

> Phase 4: Media Ingestion 实现规范

**Created:** 2026-04-30
**Milestone:** v2.0
**Status:** Design Complete

---

## 一、概述

### 1.1 目标

扩展 Smart Agent Wiki 的摄入能力，支持视频和音频文件的转录功能，使用 Whisper 将语音内容转换为可搜索的文本 Claims。

### 1.2 范围

- 支持视频格式：MP4, WebM, MOV
- 支持音频格式：MP3, WAV, M4A, OGG
- Whisper 本地/API 双模式
- 批量处理支持
- 转录预览机制

### 1.3 核心设计原则

1. **本地优先** — 优先使用本地 Whisper（faster-whisper），零 API 成本
2. **渐进增强** — 本地不可用时自动降级到 API
3. **源数据不可变** — 原始媒体文件存储在 Vault，Claims 仅存储转录文本
4. **时间戳溯源** — 每个 Claim 保留时间戳信息，可定位到原始时间点

---

## 二、架构设计

### 2.1 组件架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Media Ingestion Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │ 文件上传  │───►│ 格式检测     │───►│ 音频轨道提取     │  │
│  │(CLI/API) │    │(MediaExtractor)│   │(pydub/ffmpeg)    │  │
│  └──────────┘    └──────────────┘    └───────────────────┘  │
│                                              │               │
│                                              ▼               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Whisper Transcriber                   │   │
│  │  ┌─────────────┐              ┌─────────────────┐    │   │
│  │  │ faster-whisper│  ◄─────►  │ OpenAI API      │    │   │
│  │  │ (本地优先)    │   降级      │ (API fallback) │    │   │
│  │  └─────────────┘              └─────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                              │               │
│                                              ▼               │
│  ┌───────────────┐    ┌───────────────┐    ┌──────────────┐ │
│  │ 转录分段      │───►│ Preview Manager │───►│ 用户确认     │ │
│  │(按时间戳)     │    │(临时 SQLite)   │    │(confirm/discard)│
│  └───────────────┘    └───────────────┘    └──────────────┘ │
│                                                    │         │
│                                                    ▼         │
│  ┌──────────────────────────────────────────────────────────┐│
│  │                    Write Queue                           ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐ ││
│  │  │VaultSink│  │ClaimsSink│  │IndexSink│  │AuditSink   │ ││
│  │  │(原始文件)│  │(转录Claims)│  │(全文索引)│  │(操作审计) │ ││
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────────┘ ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心类设计

#### MediaExtractor

```python
class MediaExtractor(BaseExtractor):
    """媒体文件提取器 — 支持 Whisper 转录"""
    
    SUPPORTED_VIDEO = ['.mp4', '.webm', '.mov']
    SUPPORTED_AUDIO = ['.mp3', '.wav', '.m4a', '.ogg']
    
    def __init__(self, config: MediaIngestConfig):
        self.config = config
        self._whisper = None  # Lazy load
    
    async def extract(
        self, 
        content: bytes, 
        metadata: dict
    ) -> ExtractionResult:
        """
        提取媒体文件内容：
        1. 检测文件格式
        2. 提取音频轨道（视频文件）
        3. 提取元数据（duration, format, bitrate）
        4. 调用 Whisper 转录
        5. 返回结构化结果
        """
        pass
    
    def _get_whisper_instance(self) -> WhisperModel:
        """懒加载 Whisper 模型"""
        if self._whisper is None:
            from faster_whisper import WhisperModel
            self._whisper = WhisperModel(
                self.config.whisper_model,
                device=self.config.whisper_device,
                compute_type=self.config.whisper_compute_type
            )
        return self._whisper
    
    def _extract_audio_track(self, video_path: str) -> str:
        """从视频文件提取音频轨道"""
        pass
    
    def _transcribe(self, audio_path: str) -> TranscriptionResult:
        """Whisper 转录"""
        pass
```

#### MediaIngestConfig

```python
@dataclass
class MediaIngestConfig:
    """媒体摄入配置"""
    
    # Whisper 配置
    whisper_model: str = "base"  # tiny/base/small/medium/large
    whisper_device: str = "auto"  # auto/cuda/cpu
    whisper_language: str = "auto"  # auto 检测
    whisper_compute_type: str = "float16"  # GPU 优化
    
    # 文件限制
    max_file_size_mb: int = 500
    supported_video_formats: List[str] = field(
        default_factory=lambda: ['.mp4', '.webm', '.mov']
    )
    supported_audio_formats: List[str] = field(
        default_factory=lambda: ['.mp3', '.wav', '.m4a', '.ogg']
    )
    
    # 批量处理
    batch_concurrency: int = 3
    batch_timeout_seconds: int = 3600
    
    # 存储配置
    keep_original_file: bool = True  # 是否保留原始媒体文件
    temp_dir: Optional[str] = None  # 临时文件目录
```

#### BatchMediaProcessor

```python
class BatchMediaProcessor:
    """批量媒体处理器"""
    
    def __init__(
        self, 
        config: MediaIngestConfig,
        engine: IngestionEngine
    ):
        self.config = config
        self.engine = engine
        self._cancelled = False
        self._progress_callback = None
    
    async def process_batch(
        self,
        files: List[str],
        options: BatchOptions
    ) -> BatchResult:
        """
        批量处理媒体文件：
        1. 使用 asyncio.gather() 控制并发
        2. 每个文件独立处理
        3. 收集成功/失败结果
        4. 支持取消和进度回调
        """
        pass
    
    def cancel(self):
        """取消批量处理"""
        self._cancelled = True
    
    def set_progress_callback(
        self, 
        callback: Callable[[BatchProgress], None]
    ):
        """设置进度回调"""
        self._progress_callback = callback
```

#### PreviewManager

```python
class PreviewManager:
    """转录预览管理器"""
    
    def __init__(self, vault: Vault, db_path: str = ":memory:"):
        self.vault = vault
        self.db_path = db_path
        self._init_db()
    
    def save_preview(
        self,
        transcription: TranscriptionResult,
        metadata: dict
    ) -> str:
        """
        保存转录预览：
        - 存储到内存 SQLite `previews` 表
        - 返回 preview_id
        """
        pass
    
    def get_preview(self, preview_id: str) -> PreviewRecord:
        """获取预览记录"""
        pass
    
    def confirm(self, preview_id: str) -> str:
        """
        确认预览：
        - 迁移数据到 Claims 层
        - 删除预览记录
        - 返回 vault_id
        """
        pass
    
    def discard(self, preview_id: str) -> None:
        """丢弃预览"""
        pass
    
    def list_previews(self) -> List[PreviewSummary]:
        """列出所有待确认预览"""
        pass
```

---

## 三、数据模型

### 3.1 MediaInfo

```python
@dataclass
class MediaInfo:
    """媒体文件元数据"""
    
    duration_seconds: float
    format: str  # mp4, mp3, etc.
    bitrate_kbps: Optional[int]
    
    # Whisper 相关
    whisper_model: str
    language: str  # 检测到的语言
    transcription_timestamp: datetime
    
    # 可选
    sample_rate: Optional[int]
    channels: Optional[int]
    video_codec: Optional[str]  # 视频文件
    audio_codec: Optional[str]
```

### 3.2 TranscriptionResult

```python
@dataclass
class TranscriptionResult:
    """Whisper 转录结果"""
    
    text: str  # 完整文本
    language: str  # 检测到的语言
    segments: List[Segment]  # 带时间戳的分段
    
@dataclass
class Segment:
    """转录分段"""
    
    start: float  # 开始时间（秒）
    end: float  # 结束时间（秒）
    text: str
    confidence: float  # Whisper 置信度
```

### 3.3 ClaimInput (扩展)

```python
@dataclass
class ClaimInput:
    """主张输入 — 扩展支持媒体时间戳"""
    
    # 现有字段
    content: str
    source_id: str
    confidence: ConfidenceLevel
    ...
    
    # 新增媒体字段
    media_timestamp: Optional[Tuple[float, float]]  # (start, end)
    media_id: Optional[str]  # Vault entry ID
```

---

## 四、存储设计

### 4.1 Vault 扩展

Vault 表添加 `media_info` JSON 字段：

```sql
ALTER TABLE vault_entries ADD COLUMN media_info TEXT;  -- JSON

-- 示例数据
{
  "duration_seconds": 3600,
  "format": "mp4",
  "bitrate_kbps": 1500,
  "whisper_model": "base",
  "language": "zh",
  "transcription_timestamp": "2026-04-30T00:00:00Z"
}
```

### 4.2 Preview 临时表

```sql
CREATE TABLE previews (
    id TEXT PRIMARY KEY,
    vault_id TEXT,
    transcription TEXT,  -- JSON
    metadata TEXT,  -- JSON
    created_at TEXT,
    status TEXT  -- pending, confirmed, discarded
);
```

### 4.3 Claims 时间戳字段

```sql
ALTER TABLE claims ADD COLUMN media_timestamp_start REAL;
ALTER TABLE claims ADD COLUMN media_timestamp_end REAL;
ALTER TABLE claims ADD COLUMN media_vault_id TEXT;
```

---

## 五、CLI 接口设计

### 5.1 命令结构

```bash
# 单文件摄入
saw ingest-media <file> [--model base] [--preview]

# 批量摄入
saw ingest-media ./videos/ --batch --batch-size 3

# 预览管理
saw preview list
saw preview show <preview_id>
saw preview confirm <preview_id>
saw preview discard <preview_id>

# 带参数
saw ingest-media podcast.mp3 \
  --model medium \
  --language zh \
  --no-preview \
  --keep-original
```

### 5.2 进度显示

使用 rich.progress 显示批量处理进度：

```
Processing media files ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3/10 30%
  ✓ podcast_ep1.mp3 (12:34)
  ⏳ lecture.mp4 (processing... 45%)
  ⏸️  interview.m4a (queued)
  ✗ corrupt.mp3 (failed: invalid format)
```

---

## 六、API 接口设计

### 6.1 端点定义

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/ingest/media` | 单文件上传转录 |
| POST | `/api/v1/ingest/media/batch` | 批量上传 |
| GET | `/api/v1/preview/{id}` | 获取预览 |
| POST | `/api/v1/preview/{id}/confirm` | 确认预览 |
| DELETE | `/api/v1/preview/{id}` | 丢弃预览 |
| GET | `/api/v1/ingest/media/{task_id}` | 查询处理状态 |
| WS | `/ws/ingest/{task_id}` | WebSocket 进度 |

### 6.2 请求示例

```bash
# 上传媒体文件
curl -X POST http://localhost:8000/api/v1/ingest/media \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@lecture.mp4" \
  -F "model=base" \
  -F "preview=true"

# 响应
{
  "preview_id": "pv_abc123",
  "status": "processing",
  "estimated_seconds": 180
}

# 查询状态
curl http://localhost:8000/api/v1/ingest/media/task_xyz

# 确认预览
curl -X POST http://localhost:8000/api/v1/preview/pv_abc123/confirm
```

---

## 七、性能考虑

### 7.1 Whisper 模型选择

| 模型 | VRAM | 速度 (RTF) | 准确度 | 推荐场景 |
|------|------|-----------|--------|---------|
| tiny | ~1GB | 0.3x | 一般 | 快速预览 |
| base | ~1GB | 0.5x | 良好 | 日常使用 |
| small | ~2GB | 0.8x | 很好 | 高质量需求 |
| medium | ~5GB | 1.2x | 优秀 | 专业场景 |
| large | ~10GB | 2x | 最佳 | 最高质量 |

### 7.2 并发控制

- 默认并发数：3（可配置）
- GPU 模式：受 VRAM 限制，建议并发 1-2
- CPU 模式：可根据核心数增加并发

### 7.3 内存管理

- 视频文件流式处理，不一次性加载到内存
- 临时音频文件处理完成后立即清理
- Whisper 模型懒加载，按需初始化

---

## 八、错误处理

### 8.1 错误类型

```python
class MediaExtractionError(Exception):
    """媒体提取错误基类"""
    pass

class FFmpegNotAvailableError(MediaExtractionError):
    """ffmpeg 不可用"""
    pass

class WhisperModelLoadError(MediaExtractionError):
    """Whisper 模型加载失败"""
    pass

class TranscriptionTimeoutError(MediaExtractionError):
    """转录超时"""
    pass

class UnsupportedFormatError(MediaExtractionError):
    """不支持的格式"""
    pass
```

### 8.2 降级策略

```
1. 尝试 faster-whisper (本地 GPU)
   ↓ 失败（CUDA 不可用）
2. 尝试 faster-whisper (本地 CPU)
   ↓ 失败（内存不足）
3. 尝试 OpenAI Whisper API
   ↓ 失败（API 错误）
4. 返回错误，提示用户手动处理
```

---

## 九、测试策略

### 9.1 单元测试

- `test_media_extractor_can_handle_video_formats`
- `test_media_extractor_can_handle_audio_formats`
- `test_extract_audio_from_mp4`
- `test_transcribe_audio_success`
- `test_whisper_model_fallback_to_cpu`
- `test_batch_process_multiple_files`
- `test_batch_concurrency_limit`
- `test_preview_save_and_confirm`

### 9.2 集成测试

- 端到端流程：上传 → 转录 → 预览 → 确认 → 搜索
- 溯源链验证：Claims → Vault → 原始文件
- 性能测试：10 分钟视频处理时间 < 2x 实时

### 9.3 测试资源

```
tests/fixtures/media/
├── sample_video.mp4      # 30 秒测试视频
├── sample_audio.mp3      # 1 分钟测试音频
├── sample_podcast.m4a    # 5 分钟播客片段
└── corrupt_file.mp4      # 损坏文件（错误处理测试）
```

---

## 十、依赖项

### 10.1 新增 Python 包

```
# requirements.txt
faster-whisper>=1.0.0    # CTranslate2 优化的 Whisper
pydub>=0.25.1            # 音频处理
```

### 10.2 系统依赖

```
# ffmpeg 必须安装
# Ubuntu/Debian
apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载
```

---

## 十一、安全性考虑

### 11.1 文件大小限制

- 默认最大 500MB
- 防止 DoS 攻击
- 可通过配置调整

### 11.2 临时文件清理

- 使用 `try/finally` 确保清理
- 进程异常退出时由系统清理 `/tmp`

### 11.3 API 认证

- 需要 API Key
- 速率限制（100 次/小时/IP）

---

## 十二、未来扩展

### 12.1 v2.1 可能添加

- 说话人分离（Speaker Diarization）
- 实时流媒体转录
- 多语言混合转录优化

### 12.2 v2.2+ 可能添加

- 视频内容分析（图像识别）
- 字幕时间轴编辑 UI
- 多音轨支持

---

*Design document created: 2026-04-30*
*Milestone: v2.0 — Phase 4: Media Ingestion*