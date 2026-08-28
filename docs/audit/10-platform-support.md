# 平台支撑 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/plugins/*`、`src/saw/onboarding/*`、`src/saw/tutorial/*`、`src/saw/config/*`、`src/saw/token_optimizer/*`、`src/saw/context/loader.py`
> 覆盖缺口: `token_optimizer/`（7 文件）与 `context/loader.py` 未读（工具降级），已标 F-TOK-01/F-CTX-01，待补审。

## 1. 执行摘要
- 插件系统事件总线骨架存在但 PluginContext 事件字段未真正接 EventBus、生命周期裸 except 吞错；onboarding 仅有静态数据无流程控制器；tutorial 仅静态示例；ConfigError 暴露技术路径。
- 已审部分完成度偏低，token_optimizer/context 待补。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| 插件注册/启用 | 部分 | F-PLUG-01/05 |
| 事件总线 | 部分 | F-PLUG-02 |
| Onboarding 流程 | 缺失 | F-ONB-01 |
| 交互式教程 | 缺失 | F-TUT-01 |
| 配置 TUI | 部分 | F-CONF-02 |
| Token 优化 | 未审 | F-TOK-01 |

## 4. Findings 列表

### F-PLUG-01 — 插件生命周期裸 except 吞错
- **P0** | 严重度 4 | **原则** #1
- **位置**: `plugins/registry.py:57,84,107,121`
- **问题**: 四个生命周期操作全用裸 `except Exception`，用户无法得知插件加载/启用失败原因。

### F-PLUG-02 — event_bus 静默丢事件
- **P0** | 严重度 3 | **原则** #1
- **位置**: `plugins/event_bus.py:55,63`
- **问题**: 队列满静默丢事件、handler 异常静默吞。

### F-PLUG-05 — PluginContext 事件未接 EventBus
- **P0** | 严重度 4 | **原则** #1
- **问题**: `subscribe_event`/`publish_event` 字段类型为 `Any`，从未连接 InMemoryEventBus，插件实际无法收发事件。
- **注**: `app.py` 的 `_subscribe_event`/`_publish_event` 闭包已桥接，需核对 PluginContext 是否接收该闭包——待核。

### F-ONB-01 — Onboarding 仅有静态数据
- **P0** | 严重度 3 | **原则** #1/#6
- **位置**: `onboarding/starter_kits.py`
- **问题**: 无流程控制器、无 skip、无进度跟踪。

### F-TUT-01 — Tutorial 无交互式流程
- **P1** | 严重度 2 | **原则** #1/#10
- **位置**: `tutorial/demo_content.py`
- **问题**: 仅 3 个静态示例文档，无交互式流程，用 print() 而非结构化日志。

### F-CONF-01 — ConfigError 暴露技术路径
- **P1** | 严重度 2 | **原则** #2/#9
- **位置**: `config/settings.py:130,138`

### F-CONF-02 — 无配置 TUI/向导
- **P1** | 严重度 2 | **原则** #6
- **问题**: DEFAULT_CONFIG 定义但未被引用，config_tui 未接入。

### F-TOK-01 — token_optimizer 未审（待补）
- **P2** | 待审 | **原则** #1/#2
- **范围**: `token_optimizer/{anatomy,cerebrum,buglog,session_tracker,token_ledger,models,__init__}.py`
- **审查重点**: Token 优化指标的用户可懂性、优化失败反馈。

### F-CTX-01 — context/loader 未审（待补）
- **P2** | 待审 | **原则** #1
- **范围**: `context/loader.py`
- **审查重点**: 上下文加载的错误处理与进度可见性。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 2 |
| 3 | 3 |
| 2 | 4 |
| 1 | 1 |
| 优先级 | P0×3 P1×4 P2×2+ |

## 6. 修复优先级
- **Foundation**: F-PLUG-01/02/05、F-ONB-01
- **Core UI**: F-CONF-01/02、F-TUT-01
- **Interactions & States**: F-TOK-01/F-CTX-01 补审

## 7. 下一步建议
- 补审 token_optimizer/context；修插件事件总线接线；onboarding 加流程控制器与 skip。
