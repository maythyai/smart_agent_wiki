# Dependency DAG — Task 依赖图（无环）

> Task 依赖镜像 decomposition Feature 依赖（不反向）。DAG 无环（实机校验）。

## Mermaid

```mermaid
graph LR
  A1[T-F-A-1-1 骨架] --> A2[T-F-A-2-1 ingest+compile]
  A1 --> A3[T-F-A-3-1 query]
  A1 --> A4[T-F-A-4-1 govern+learn]
  A2 --> A5[T-F-A-5-1 离线fallback]
  A3 --> A5
  A4 --> A5
  A5 --> A6[T-F-A-6-1 CI smoke]
  A6 --> E3[T-F-E-3-1 CI集成]
  B1[T-F-B-1-1 diff] --> B2[T-F-B-2-1 能力清单]
  B1 --> B3[T-F-B-3-1 文档修正]
  D1[T-F-D-1-1 logger] --> D2[T-F-D-2-1 trace]
  E1[T-F-E-1-1 基线] --> E2[T-F-E-2-1 门禁]
  E2 --> E3
  C1[T-F-C-1-1 权限] & C2[T-F-C-2-1 receipt] & C3[T-F-C-3-1 限流] & C4[T-F-C-4-1 守卫] & C5[T-F-C-5-1 token]
  D3[T-F-D-3-1 health]
```

## DAG 校验
- 拓扑序无环（实机校验 cycle=none）✓
- 与 decomposition DEPENDENCY-GRAPH 一致：A1→{A2,A3,A4}→A5→A6→E3；B1→{B2,B3}；D1→D2；E1→E2→E3；C/D3 独立 ✓
- 无回边。若 05 重构致环 → 报错停步。

## 关键路径
T-F-A-1-1 → T-F-A-2-1 → T-F-A-5-1 → T-F-A-6-1 → T-F-E-3-1（5 步）
- 次长：T-F-E-1-1 → T-F-E-2-1 → T-F-E-3-1（3 步）
- A2/A3/A4 并行可压缩 A1→A5 段。

## 并行机会
- Wave 1 全并行（10 Task 无依赖）。
- Wave 2 中 A2/A3/A4 三引擎冒烟并行。
- C 域 5 Task 全独立并行；B 域（P1）可与 P0 异步。

---

## v1.10.0 delta（embedding track）

```mermaid
graph LR
  N1[T-F-N-1 embedding 索引] --> N2[T-F-N-2 语义检索]
  N1 --> N3[T-F-N-3 smart-linking embedding]
  N1 --> N4[T-F-N-4 importorskip 测试]
```

### v1.10.0 DAG 校验
- 拓扑序无环：N1 → {N2, N3, N4}，无回边 ✓
- 与 decomposition DEPENDENCY-GRAPH v1.10.0 delta 一致（N-1 → {N-2, N-3, N-4}）✓
- 无自环、无环。若 05 重构致环 → 报错停步。

### v1.10.0 关键路径
T-F-N-1 → T-F-N-2（2 步，最长链）
- N-2/N-3/N-4 并行可压缩 N-1→{N-2/N-3/N-4} 段。

### v1.10.0 并行机会
- Wave 1：T-F-N-1 独占（db migration 共享资源串行先行）。
- Wave 2：T-F-N-2 / T-F-N-3 / T-F-N-4 全并行（3 路独立，无共享文件冲突）。

---

## v1.11.0 delta（债务收口 IV / bug fix track）

```mermaid
graph LR
  O1[T-F-O-1 semantic cache]
  O2[T-F-O-2 compile 深覆盖]
  O3[T-F-O-3 workflow REST 统一]
  O4[T-F-O-4 Spec 回更+hash 复核]
```

### v1.11.0 DAG 校验
- 拓扑序无环：O1 / O2 / O3 / O4 互相独立，无依赖边 → 无回边 ✓
- 与 decomposition DEPENDENCY-GRAPH v1.11.0 delta 一致（4 Feature 全并行，无依赖边）✓
- 无自环、无环。若 05 重构致环 → 报错停步。

### v1.11.0 关键路径
- 无关键路径（4 Task 无依赖，全并行 1 步完成）。

### v1.11.0 并行机会
- Wave 1：T-F-O-1 / T-F-O-2 / T-F-O-3 / T-F-O-4 全并行（4 路独立，无共享文件冲突）。

---

## v1.12.0 delta（embedding API 重构 track）

```mermaid
graph LR
  Q1[T-F-Q-1 provider 重构] --> Q2[T-F-Q-2 维度可配+重建检测]
  Q1 --> Q3[T-F-Q-3 本地 ST fallback]
  Q1 --> Q4[T-F-Q-4 测试 mock+benchmark]
```

### v1.12.0 DAG 校验
- 拓扑序无环：Q-1 → {Q-2, Q-3, Q-4}，无回边 ✓
- 与 decomposition DEPENDENCY-GRAPH v1.12.0 delta 一致（F-Q-1 → {F-Q-2, F-Q-3, F-Q-4}）✓
- 无自环、无环。若 05 重构致环 → 报错停步。

### v1.12.0 关键路径
T-F-Q-1 → T-F-Q-2（2 步，最长链，与 Q-1→Q-3/Q-1→Q-4 等长）
- Q-2/Q-3/Q-4 并行可压缩 Q-1→{Q-2,Q-3,Q-4} 段。

### v1.12.0 并行机会
- Wave 1：T-F-Q-1 独占（provider 重构前置）。
- Wave 2：T-F-Q-2 / T-F-Q-3 / T-F-Q-4 全并行（3 路独立，无共享文件冲突；`embeddings.py`/`settings.py` 由 Q-3 续写 Wave 1 Q-1 成果，串行 Wave 1→2 不构成 Wave 2 内冲突）。

---

## v1.14.0 delta（semantic 性能优化 track）

```mermaid
graph LR
  S1[T-F-S-1 cache 阈值可配]
  S2[T-F-S-2 ANN 索引]
  S3[T-F-S-3 benchmark 更新]

  S2 --> S3
```

### v1.14.0 DAG 校验
- 拓扑序无环：S-1 独立（无入边无出边）；S-2→S-3 单向边；无回边 ✓
- 与 decomposition DEPENDENCY-GRAPH v1.14.0 delta 一致（F-S-2→F-S-3，F-S-1 独立）✓
- 无自环、无环。若 05 重构致环 → 报错停步。

### v1.14.0 关键路径
T-F-S-2 → T-F-S-3（2 步，最长链）
- S-1 独立，与 S-2 可 Wave 1 并行。

### v1.14.0 并行机会
- Wave 1：T-F-S-1 / T-F-S-2 全并行（engine.py 不同 section：cache 条件分支 vs cosine→ANN 切换，worktree 隔离 + 合并协调）。
- Wave 2：T-F-S-3 独占（依赖 S-2 ANN 路径完成）。

---

## v1.15.0 delta（agent/link 能力 track）

```mermaid
graph LR
  T1[T-F-T-1 自定义角色注册]
  T2[T-F-T-2 links auto-apply]
  T3[T-F-T-3 agent 活动聚合]
```

### v1.15.0 DAG 校验
- 拓扑序无环：T-1 / T-2 / T-3 互相独立，无依赖边 → 无回边 ✓
- 与 decomposition DEPENDENCY-GRAPH v1.15.0 delta 一致（F-T-1 / F-T-2 / F-T-3 全独立，无边）✓
- 无自环、无环。若 05 重构致环 → 报错停步。

### v1.15.0 关键路径
- 无关键路径（3 Task 无依赖，全并行 1 步完成）。

### v1.15.0 并行机会
- Wave 1：T-F-T-1 / T-F-T-2 / T-F-T-3 全并行（3 路独立，不同关注点：角色注册 / 链接写回 / 活动聚合；`collaborate.py`/`agents_cmd.py`/`test_agents_rest.py` 同文件不同 section，worktree 隔离 + 合并协调）。

---

## v1.16.0 delta（realtime 仪表盘 track）

```mermaid
graph LR
  U1[T-F-U-1 agent roster+activity 仪表盘]
  U2[T-F-U-2 workflow 运行态视图]
  U3[T-F-U-3 实时更新]

  U1 --> U3
  U2 --> U3
```

### v1.16.0 DAG 校验
- 拓扑序无环：U-1 / U-2 独立（无入边无出边至彼此），U-1→U-3 + U-2→U-3，无回边 ✓
- 与 decomposition DEPENDENCY-GRAPH v1.16.0 delta 一致（F-U-1→F-U-3 + F-U-2→F-U-3，F-U-1/F-U-2 独立）✓
- 无自环、无环。若 05 重构致环 → 报错停步。

### v1.16.0 关键路径
T-F-U-1 → T-F-U-3（2 步，最长链，与 U-2→U-3 等长）
- U-1/U-2 并行可压缩 Wave 1 段，U-3 Wave 2 依赖两者完成。

### v1.16.0 并行机会
- Wave 1：T-F-U-1 / T-F-U-2 全并行（2 路独立，不同数据源 + 不同组件；`Dashboard.tsx`/`types/api.ts` 同文件不同 section/类型，worktree 隔离 + 合并协调）。
- Wave 2：T-F-U-3 独占（依赖 U-1 useAgents + U-2 useWorkflows 已建好 react-query 查询）。

---

## v1.17.0 delta（desktop 完成 v4.4 track）

```mermaid
graph LR
  V1[T-F-V-1 版本 bump + 配置收敛]
  V2[T-F-V-2 web 仪表盘集成验证]
  V3[T-F-V-3 tauri build 验证]
  V4[T-F-V-4 后端协同 + 端口收敛]

  V1 --> V2
  V1 --> V3
  V1 --> V4
```

### v1.17.0 DAG 校验
- 拓扑序无环：V-1 独立（无入边），V-1→{V-2, V-3, V-4}，无回边 ✓
- 与 decomposition DEPENDENCY-GRAPH v1.17.0 delta 一致（F-V-1→{F-V-2, F-V-3, F-V-4}）✓
- 无自环、无环。若 05 重构致环 → 报错停步。

### v1.17.0 关键路径
T-F-V-1 → T-F-V-2（2 步，最长链，与 V-1→V-3 / V-1→V-4 等长）
- V-2/V-3/V-4 并行可压缩 Wave 2 段，V-1 Wave 1 先行。

### v1.17.0 并行机会
- Wave 1：T-F-V-1 独占（版本 bump + 配置收敛先行）。
- Wave 2：T-F-V-2 / T-F-V-3 / T-F-V-4 全并行（3 路独立，不同文件集无重叠：只读验证 / 构建 / 端口配置）。

---

## v1.18.0 delta（per-request workspace 注入 + O4 tag 流程 track）

```mermaid
graph LR
  W1[T-F-W-1 per-request workspace contextvar 注入]
  W2[T-F-W-2 O4 tag 流程修复]
```

### v1.18.0 DAG 校验
- 拓扑序无环：W-1 / W-2 互相独立，无依赖边 → 无回边 ✓
- 与 decomposition DEPENDENCY-GRAPH v1.18.0 delta 一致（F-W-1 / F-W-2 全独立，无边）✓
- 无自环、无环。若 05 重构致环 → 报错停步。

### v1.18.0 关键路径
- 无关键路径（2 Task 无依赖，全并行 1 步完成）。

### v1.18.0 并行机会
- Wave 1：T-F-W-1 / T-F-W-2 全并行（2 路独立，完全不同文件集与关注点：多租户 web 隔离 vs release 流程文档）。

