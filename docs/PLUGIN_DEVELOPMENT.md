# Plugin Development Guide

**Smart Agent Wiki — Plugin SDK**

本文档介绍如何为 Smart Agent Wiki 开发自定义插件。

## 目录

1. [快速开始](#快速开始)
2. [插件结构](#插件结构)
3. [Plugin Metadata](#plugin-metadata)
4. [PluginBase 类](#pluginbase-类)
5. [事件系统](#事件系统)
6. [PluginContext](#plugincontext)
7. [完整示例](#完整示例)
8. [测试与调试](#测试与调试)
9. [发布与分发](#发布与分发)

---

## 快速开始

### 1. 创建插件目录

```bash
mkdir my-plugin && cd my-plugin
```

### 2. 创建 `plugin.yaml`

```yaml
name: my-plugin
version: 1.0.0
description: 我的第一个 SAW 插件
author: Your Name
entry: plugin.py
class: MyPlugin
events:
  - PageCreated
  - PageUpdated
```

### 3. 创建 `plugin.py`

```python
from saw.plugins.base import PluginBase, PluginContext, PluginMetadata

class MyPlugin(PluginBase):
    metadata = PluginMetadata(
        name="my-plugin",
        version="1.0.0",
        description="My first SAW plugin",
    )

    async def on_enable(self, ctx: PluginContext) -> None:
        ctx.logger.info("Plugin enabled!")

    async def on_disable(self, ctx: PluginContext) -> None:
        ctx.logger.info("Plugin disabled.")

    async def on_page_created(self, event, ctx: PluginContext) -> None:
        ctx.logger.info(f"New page: {event.title}")
```

### 4. 安装插件

```bash
saw plugin install ./my-plugin
saw plugin enable my-plugin
```

---

## 插件结构

一个标准插件包含：

```
my-plugin/
├── plugin.yaml      # 插件元数据（必需）
├── plugin.py        # 插件入口（必需）
├── README.md        # 说明文档
├── requirements.txt # 额外依赖（可选）
└── data/            # 插件资源（可选）
```

### plugin.yaml 字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | ✅ | 插件唯一标识符 |
| version | string | ✅ | 语义化版本号 |
| description | string | ✅ | 插件简介 |
| author | string | ✅ | 作者 |
| entry | string | ✅ | Python 入口文件 |
| class | string | ✅ | PluginBase 子类名 |
| events | list | ❌ | 订阅的事件列表 |
| config | object | ❌ | 默认配置 |

---

## Plugin Metadata

```python
from saw.plugins.base import PluginMetadata

metadata = PluginMetadata(
    name="my-plugin",          # 唯一标识
    version="1.0.0",           # 语义化版本
    description="Description", # 插件描述
    author="Your Name",        # 作者
    homepage="https://...",    # 主页（可选）
    license="MIT",             # 许可证（可选）
)
```

---

## PluginBase 类

所有插件必须继承 `PluginBase`：

```python
from saw.plugins.base import PluginBase, PluginContext

class MyPlugin(PluginBase):
    metadata = PluginMetadata(name="my-plugin")

    # 生命周期钩子
    async def on_enable(self, ctx: PluginContext) -> None:
        """插件启用时调用"""
        pass

    async def on_disable(self, ctx: PluginContext) -> None:
        """插件禁用时调用"""
        pass

    # 事件处理器
    async def on_page_created(self, event, ctx: PluginContext) -> None:
        """页面创建时触发"""
        pass

    async def on_page_updated(self, event, ctx: PluginContext) -> None:
        """页面更新时触发"""
        pass

    async def on_page_deleted(self, event, ctx: PluginContext) -> None:
        """页面删除时触发"""
        pass

    async def on_claim_created(self, event, ctx: PluginContext) -> None:
        """声明创建时触发"""
        pass

    async def on_ingest_completed(self, event, ctx: PluginContext) -> None:
        """摄入完成时触发"""
        pass

    async def on_query_executed(self, event, ctx: PluginContext) -> None:
        """查询执行后触发"""
        pass
```

---

## 事件系统

### 可用事件

| 事件 | 触发时机 | 属性 |
|------|----------|------|
| `PageCreated` | 新页面创建 | page_id, title, author |
| `PageUpdated` | 页面更新 | page_id, title, author |
| `PageDeleted` | 页面删除 | page_id, author |
| `ClaimCreated` | 声明创建 | claim_id, page_id, content |
| `IngestCompleted` | 摄入完成 | source, items_processed |
| `QueryExecuted` | 查询执行 | query, results_count, duration_ms |

### 订阅事件

在 `plugin.yaml` 中声明：

```yaml
events:
  - PageCreated
  - PageUpdated
  - IngestCompleted
```

或在代码中动态订阅：

```python
async def on_enable(self, ctx):
    ctx.subscribe("PageCreated", self.on_page_created)
```

---

## PluginContext

`PluginContext` 提供插件运行时环境：

```python
class PluginContext:
    data_dir: Path           # 插件专属数据目录
    config: dict             # 插件配置
    logger: logging.Logger   # 日志记录器

    # 方法
    def get_config(self, key: str, default=None) -> Any
    def set_config(self, key: str, value: Any) -> None
    def get_data_path(self, filename: str) -> Path
```

### 数据隔离

每个插件有独立的 `data_dir`，确保数据隔离：

```python
async def on_enable(self, ctx):
    # 存储插件数据
    cache_file = ctx.get_data_path("cache.json")
    with open(cache_file, "w") as f:
        json.dump({"count": 0}, f)
```

---

## 完整示例

### Word Counter 插件

统计页面字数并生成报告。

**plugin.yaml:**
```yaml
name: word-counter
version: 1.0.0
description: 统计 Wiki 页面字数
author: SAW Team
entry: plugin.py
class: WordCounterPlugin
events:
  - PageCreated
  - PageUpdated
```

**plugin.py:**
```python
import json
from pathlib import Path
from saw.plugins.base import PluginBase, PluginContext, PluginMetadata

class WordCounterPlugin(PluginBase):
    metadata = PluginMetadata(
        name="word-counter",
        version="1.0.0",
        description="Count words in wiki pages",
    )

    async def on_enable(self, ctx: PluginContext) -> None:
        self.stats_file = ctx.get_data_path("stats.json")
        if not self.stats_file.exists():
            self.stats_file.write_text("{}")
        ctx.logger.info("Word Counter enabled")

    async def on_disable(self, ctx: PluginContext) -> None:
        ctx.logger.info("Word Counter disabled")

    async def on_page_created(self, event, ctx: PluginContext) -> None:
        await self._count_words(event, ctx)

    async def on_page_updated(self, event, ctx: PluginContext) -> None:
        await self._count_words(event, ctx)

    async def _count_words(self, event, ctx: PluginContext) -> None:
        content = getattr(event, "content", "")
        word_count = len(content.split())

        stats = json.loads(self.stats_file.read_text())
        stats[event.page_id] = {
            "title": event.title,
            "words": word_count,
        }
        self.stats_file.write_text(json.dumps(stats, indent=2))

        ctx.logger.info(
            f"Page '{event.title}': {word_count} words"
        )
```

---

## 测试与调试

### 运行测试

```bash
# 运行所有插件测试
pytest tests/unit/test_plugins.py -v

# 运行特定测试
pytest tests/unit/test_plugins.py::TestEvents -v
```

### 调试模式

```bash
# 启用详细日志
SAW_LOG_LEVEL=DEBUG saw plugin enable my-plugin
```

### 检查插件状态

```bash
saw plugin list
saw plugin info my-plugin
```

---

## 发布与分发

### 打包

将插件目录打包为 zip：

```bash
zip -r my-plugin-1.0.0.zip my-plugin/
```

### 发布到 GitHub

1. 创建 GitHub Release
2. 上传 zip 文件
3. 用户在 `plugin.yaml` 中添加 URL

### 安装远程插件

```bash
saw plugin install https://github.com/user/my-plugin/releases/download/v1.0.0/my-plugin.zip
```

---

## CLI 命令

| 命令 | 说明 |
|------|------|
| `saw plugin list` | 列出已安装插件 |
| `saw plugin install <path\|url>` | 安装插件 |
| `saw plugin enable <name>` | 启用插件 |
| `saw plugin disable <name>` | 禁用插件 |
| `saw plugin uninstall <name>` | 卸载插件 |
| `saw plugin info <name>` | 显示插件详情 |

---

*最后更新: 2026-06-22*
