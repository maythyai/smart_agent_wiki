# Logseq Connector Guide

Logseq 是一款本地优先的知识管理和笔记应用。SAW 的 Logseq 连接器通过监听文件变更实现双向同步，支持块解析和 wikilink 保留。

## 前提条件

- Logseq 已安装
- 本地 Logseq 图谱目录
- SAW 服务运行中

## 步骤 1: 确定图谱路径

Logseq 图谱通常位于：

- macOS: `~/logseq/my-graph`
- Linux: `~/logseq/my-graph`
- Windows: `%USERPROFILE%\logseq\my-graph`

在 Logseq 中，点击左上角图谱名称可查看图谱路径。

## 步骤 2: 配置图谱路径

设置环境变量：

```bash
export LOGSEQ_GRAPH_PATH="/path/to/your/logseq/graph"
```

或在 SAW 配置文件中：

```yaml
connectors:
  logseq:
    graph_path: "/home/user/logseq/my-graph"
```

## 步骤 3: 启动文件监听

启动 Logseq 文件监听：

```bash
saw logseq watch
```

这会启动后台进程，监听 `.md` 文件的变更。

### 通过 Web UI

1. 访问 `http://localhost:8000/integrations`
2. 找到 "Logseq" 卡片
3. 点击 "Connect"
4. 输入图谱路径
5. 点击 "Start Watching"

## 步骤 4: 测试同步

在 Logseq 中编辑一个页面，SAW 会自动检测变更：

```bash
# 查看监听状态
saw logseq status

# 手动触发全量同步
saw logseq sync
```

## 块解析

Logseq 页面由块（blocks）组成，SAW 会解析块结构：

### 属性解析

Logseq 属性语法：

```
- title:: My Page
- confidence:: 3
- freshness:: 2026-05-02
```

SAW 会自动提取这些属性并映射到对应字段。

### Wikilink 解析

Wikilink 语法 `[[Page Name]]` 会被保留并建立关联：

```
This links to [[Another Page]] and [[Concepts/Topic]].
```

### 命名空间解析

命名空间页面（如 `Projects/2026/May`）会被解析为层级结构。

## 双向同步注意事项

### 从 Logseq 到 SAW

- 新 `.md` 文件自动同步
- 文件修改立即检测
- 删除文件会在 SAW 中标记为已删除

### 从 SAW 到 Logseq

- SAW 中的新建条目会创建对应 `.md` 文件
- 编辑会更新文件内容
- 保留 Logseq 特有的块语法

### Wikilink 保留

编辑时，SAW 会保留 wikilink 格式：

```
原始: See [[Related Topic]] for more.
编辑后: See [[Related Topic]] and [[New Link]] for more.
```

## 故障排除

### 文件权限

错误信息: `Permission denied`

解决方案: 确保 SAW 进程有读写 Logseq 图谱目录的权限：

```bash
chmod -R u+rw /path/to/logseq/graph
```

### 并发编辑

当 Logseq 和 SAW 同时编辑同一页面时：

1. SAW 检测到冲突
2. 根据配置的冲突策略处理
3. 备份原始版本

```bash
# 查看冲突记录
saw logseq conflicts

# 手动解决冲突
saw logseq resolve --id <conflict_id> --strategy saw_wins
```

### Wikilink 断裂

如果 wikilink 指向不存在的页面：

```bash
# 检查断裂的 wikilink
saw logseq check-broken-links

# 自动修复（创建缺失页面）
saw logseq fix-broken-links --create-missing
```

## 配置参考

```bash
saw logseq config --help
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--graph-path` | - | Logseq 图谱路径 |
| `--watch` | true | 是否监听文件变更 |
| `--poll-interval` | 5 | 文件轮询间隔 (秒) |
| `--include-journals` | true | 是否包含日记页面 |
| `--namespace-depth` | 3 | 命名空间解析深度 |

---

*最后更新: 2026-05-02*