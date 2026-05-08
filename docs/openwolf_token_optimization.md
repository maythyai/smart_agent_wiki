# OpenWolf Token 优化技术分析

> 来源: https://github.com/cytostack/openwolf
> 分析日期: 2026-05-05

## 一、核心问题

Claude Code 在处理大型项目时存在以下 Token 浪费问题：

| 问题 | 描述 |
|------|------|
| **重复读取** | 同一会话中多次读取同一文件，无感知 |
| **盲目扫描** | 不知道文件内容就打开，即使只需摘要信息 |
| **无记忆** | 每次会话从零开始，无法复用之前的学习成果 |
| **不可见** | 用户无法看到 Token 消耗情况 |

## 二、OpenWolf 解决方案

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenWolf 架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   用户输入                                                       │
│       ↓                                                         │
│   Claude Code CLI                                               │
│       ↓                                                         │
│   ┌──────────────────────────────────────────────────────┐     │
│   │            6 个 Hook 脚本 (生命周期拦截)                 │     │
│   │  PreToolUse → 检查 anatomy.md，判断是否需要读取        │     │
│   │  PostToolUse → 更新 memory.md，记录 token 消耗         │     │
│   └──────────────────────────────────────────────────────┘     │
│       ↓                                                         │
│   .wolf/ 目录 (持久化知识库)                                     │
│   ├── anatomy.md      # 项目文件地图 + token 估算               │
│   ├── cerebrum.md     # 学习记忆 + Do-Not-Repeat                │
│   ├── memory.md       # 操作时间线                              │
│   ├── buglog.json     # Bug 修复记录                            │
│   └── token-ledger.json # Token 消耗账本                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心文件结构

#### 2.2.1 anatomy.md - 项目文件地图

**原理**: 在读取文件前，先查阅 `anatomy.md` 获取文件摘要和 token 估算。

```markdown
## src/

- `index.ts` - Main entry point. Exports createProgram() for CLI. (~180 tok)
- `server.ts` - Express HTTP server with middleware chain. (~520 tok)

## src/api/

- `auth.ts` - JWT validation middleware. Reads from env.JWT_SECRET. (~340 tok)
- `users.ts` - CRUD endpoints for /api/users. Pagination via query params. (~890 tok)
```

**节省方式**:
- 如果摘要已足够，直接跳过文件读取
- 提前告知 token 成本，避免"盲开"大文件

#### 2.2.2 cerebrum.md - 学习记忆

**原理**: 跨会话积累知识，避免重复犯错。

```markdown
## Do-Not-Repeat

- 2026-03-10: Never use `var` - always `const` or `let`
- 2026-03-11: Don't mock the database in integration tests - use the real connection
- 2026-03-14: The auth middleware reads from `cfg.talk`, not `cfg.tts` - got burned twice

## User Preferences

- Prefers functional components over class components
- Always use named exports, never default exports
- Tests go in `__tests__/` next to the source file

## Key Learnings

- This project uses pnpm workspaces with strict hoisting
- The API rate limiter uses a sliding window, not fixed buckets
- Auth middleware reads from env.JWT_SECRET, not config file
```

#### 2.2.3 buglog.json - Bug 记忆

**原理**: 修复前先查询，避免重复调试。

```json
{
  "id": "bug-012",
  "error_message": "TypeError: Cannot read properties of undefined (reading 'map')",
  "file": "src/components/UserList.tsx",
  "root_cause": "API response was null when users array was expected",
  "fix": "Added optional chaining: data?.users?.map() and fallback empty array",
  "tags": ["null-check", "api-response", "react"]
}
```

#### 2.2.4 token-ledger.json - Token 账本

```json
{
  "lifetime": {
    "total_tokens_estimated": 503978,
    "total_reads": 287,
    "total_writes": 269,
    "anatomy_hits": 198,
    "anatomy_misses": 89,
    "repeated_reads_blocked": 106,
    "estimated_savings_vs_bare_cli": 2066959
  }
}
```

### 2.3 Hook 生命周期

```
┌────────────────────────────────────────────────────────────────────┐
│                    Hook 执行流程                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. PreToolUse Hook                                                 │
│     ├── 如果工具是 Read                                             │
│     │   ├── 检查 anatomy.md 是否有该文件                             │
│     │   ├── 如果摘要足够 → 注入上下文，建议跳过读取                   │
│     │   └── 如果文件已在本会话读取过 → 警告重复读取                   │
│     └── 如果工具是 Write                                            │
│         └── 检查 cerebrum.md 的 Do-Not-Repeat                       │
│                                                                    │
│  2. 工具执行                                                        │
│                                                                    │
│  3. PostToolUse Hook                                                │
│     ├── 记录操作到 memory.md                                        │
│     ├── 估算 token 消耗                                             │
│     ├── 如果是文件创建/删除 → 更新 anatomy.md                        │
│     └── 更新 token-ledger.json                                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## 三、Token 节省技术详解

### 3.1 技术 1: 文件地图索引 (Anatomy Index)

**问题**: Claude 不知道文件内容就必须打开文件，即使只需要知道"这个文件有没有 X 函数"。

**解决**:
```javascript
// PreToolUse Hook 逻辑伪代码
function preReadHook(filePath) {
  const anatomy = readAnatomy();
  const entry = anatomy.find(e => e.path === filePath);
  
  if (entry) {
    // 注入摘要到上下文
    injectContext(`[OpenWolf] ${filePath}: ${entry.description} (~${entry.tokens} tok)`);
    
    // 如果摘要足够，建议跳过
    if (entry.sufficientForCurrentTask) {
      return { skip: true, reason: 'anatomy_hit' };
    }
  }
  
  return { proceed: true };
}
```

**节省量**: 约 50-70% 的文件读取可被摘要替代。

### 3.2 技术 2: 重复读取检测 (Read Tracking)

**问题**: Claude 同一会话内可能多次读取同一文件，无感知。

**解决**:
```javascript
// 会话级读取追踪
const sessionReads = new Map();

function trackRead(filePath, tokens) {
  if (sessionReads.has(filePath)) {
    // 检测到重复读取
    injectWarning(`[OpenWolf] File already read ${sessionReads.get(filePath).count} times this session`);
    incrementLedger('repeated_reads_blocked');
  }
  sessionReads.set(filePath, { 
    count: (sessionReads.get(filePath)?.count || 0) + 1,
    tokens 
  });
}
```

**节省量**: 拦截 71% 的重复读取。

### 3.3 技术 3: 跨会话学习 (Cerebrum Memory)

**问题**: 每次 Claude 会话都从零开始，无法复用之前的发现和修正。

**解决**:
```markdown
## Do-Not-Repeat 示例

| 日期 | 错误 | 正确做法 |
|------|------|----------|
| 2026-03-10 | 使用 `var` | 使用 `const`/`let` |
| 2026-03-11 | Mock 数据库做集成测试 | 用真实连接 |
| 2026-03-14 | 从 config 读取 JWT_SECRET | 从 env 读取 |
```

**节省量**: 避免重复调试相同问题，节省 20-40% 调试 token。

### 3.4 技术 4: Bug 记忆库 (Bug Log)

**问题**: 相同 Bug 反复调试，无历史记录。

**解决**:
```javascript
function preFixHook(errorMessage) {
  const buglog = readBuglog();
  const knownBug = buglog.find(b => 
    b.error_message.includes(errorMessage) || 
    b.tags.some(t => errorMessage.includes(t))
  );
  
  if (knownBug) {
    injectContext(`[OpenWolf] Known bug: ${knownBug.id}\nFix: ${knownBug.fix}`);
    return { skip: true, useKnownFix: knownBug };
  }
}
```

### 3.5 技术 5: Token 估算公式

```javascript
function estimateTokens(content) {
  // 基于字符数的估算（精度 ~15%）
  // 英文: ~4 chars/token
  // 代码: ~3.5 chars/token (因为符号密度高)
  const ratio = content.includes('function') ? 3.5 : 4;
  return Math.ceil(content.length / ratio);
}

function estimateFileTokens(filePath) {
  const stats = fs.statSync(filePath);
  // 小文件直接用字符数
  if (stats.size < 10000) {
    return estimateTokens(fs.readFileSync(filePath, 'utf8'));
  }
  // 大文件用采样估算
  const sample = readSample(filePath, 1000);
  const sampleTokens = estimateTokens(sample);
  return Math.ceil((stats.size / sample.length) * sampleTokens);
}
```

## 四、实际效果数据

根据 OpenWolf 的实测数据：

| 指标 | 数值 |
|------|------|
| 平均 Token 减少 | 65.8% |
| 重复读取拦截率 | 71% |
| Anatomy 命中率 | 69% (198/287) |
| 单项目节省 | ~2M tokens |

对比测试（同一项目）：
```
OpenClaw + Claude          ~3.4M tokens  ██████████████████████████████████████
Claude CLI (no OpenWolf)   ~2.5M tokens  ████████████████████████████████
OpenWolf + Claude CLI      ~425K tokens  ████████
```

## 五、技术实现要点

### 5.1 Hook 集成

OpenWolf 使用 Claude Code 的原生 Hook API：

```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      { "command": "node .wolf/hooks/pre-tool-use.js" }
    ],
    "PostToolUse": [
      { "command": "node .wolf/hooks/post-tool-use.js" }
    ]
  }
}
```

### 5.2 无侵入设计

- **零工作流变更**: 用户继续使用 `claude` 命令
- **纯 Node.js**: 无外部依赖
- **被动注入**: 通过 Hook 自动注入上下文

### 5.3 关键设计决策

| 决策 | 原因 |
|------|------|
| 用 Markdown 而非数据库 | 可读、可编辑、版本控制友好 |
| Token 估算而非精确计数 | API 不暴露实际 token 数，估算精度足够 |
| Hook 而非 Wrapper | 遵循 Claude Code 原生扩展机制 |

## 六、对 Smart Agent Wiki 的启发

### 6.1 可借鉴的技术

1. **文件索引 + Token 估算**: 在 Ingest Engine 中实现文件预分析
2. **读取追踪**: 在会话级别跟踪已读取文件
3. **学习记忆**: 扩展 Wiki 层实现跨会话知识积累
4. **Bug 记忆**: 新增 `buglog.md` 或 `buglog.json` 结构

### 6.2 差异化方向

OpenWolf 的局限 → Smart Agent Wiki 的机会：

| OpenWolf 局限 | SAW 解决方案 |
|---------------|--------------|
| 纯文件索引，无语义理解 | 结合 Code DAG 构建语义图谱 |
| 无 MCP 集成 | 原生 MCP Server 暴露优化能力 |
| 单机使用 | 团队协作 + 知识共享 |
| 无置信度系统 | 四级置信度体系集成 |

## 七、总结

OpenWolf 的核心 Token 优化策略可归纳为：

```
┌─────────────────────────────────────────────────────────────┐
│                   Token 优化公式                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   节省 Token = 摘要替代 + 重复拦截 + 学习复用 + Bug 预查     │
│                                                             │
│   摘要替代: anatomy.md 提前告知文件内容                       │
│   重复拦截: 会话级追踪防止重复读取                           │
│   学习复用: cerebrum.md 跨会话积累                           │
│   Bug 预查: buglog.json 避免重复调试                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

这为 Smart Agent Wiki 提供了经过验证的 Token 优化技术栈，可作为设计参考。
