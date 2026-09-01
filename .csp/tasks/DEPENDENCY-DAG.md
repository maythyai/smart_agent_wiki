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
