# Coverage Baseline — T-F-E-1-1（首次实测）

> 2026-09-03 实测。pytest-cov 7.1.0 / coverage 7.16.0 / 1780 passed + 3 skipped。
> 命令: `.venv/bin/pytest tests/ --cov=src/saw --cov-report=term-missing`（排除 heavy-SDK learn-extras 测试: test_distiller/test_fsrs/test_trends，需 sentence-transformers）。

## 聚合基线

| 范围 | 语句 | 缺失 | 覆盖率 |
|---|---|---|---|
| **TOTAL（src/saw 全量）** | 28386 | 10649 | **62%** |
| 核心引擎+write_queue+code_graph | 8519 | 3068 | 64% |
| 非核心（adapters/drivers/auth 抽样） | 6712 | 3302 | 51% |

## 核心引擎明细（阈值对象）

| 模块 | 关键文件覆盖率 |
|---|---|
| **ingest** | pipeline 72 / scheduler 83 / validator 82 / feed_manager 87 / preview 95 / fuser 91 / classifier 100 / batch 41 / extractors: markdown 93 / code_ast 74 / llm 71 / media 41 / pdf 45 / structured 28 / url 45 |
| **query** | engine 58 / search 86 / compiler 95 / graph_traverse 82 / memory 81 / cache 79 / wiki_indexer 86 / wiki_links 73 / **compare 30 / related_pages 23 / tree_mode 24 / wiki_graph 43** |
| **govern** | governor 98 / audit 92 / linter 88 / blast_radius 87 / freshness 78 / contradiction 76 / confidence 80 |
| **collaborate** | orchestrator 86 / workflow_executor 90 / workflow_parser 96 / dispatcher 70 / a2a 61 / base 91 / **agents: critic 23 / librarian 23 / scholar 25 / writer 28 / linker 30 / guardian 66** |
| **compile** | **compiler 17 / code_wiki 14 / linter 14 / parsers 15 / archiver 20 / concept_graph 21 / feedback 31** |
| **write_queue** | dispatcher 89 / queue 88 / sinks: contradictions 96 / fts5 92 / graph 93 / vault 90 / claims 83 / connector 73 / wiki 69 |
| **code_graph** | parser 81 / snapshot 84 / store 76 / postprocess 77 / models 100 / resolvers 92-100 |

## 阈值决策（[TBD] 落定）

SPEC-F-E-1 原设阈值：核心引擎 ≥80% / 非核心 ≥60%。

**实测基线：核心 64% / 非核心 51%，均低于原设阈值**——若直接挂 80%/60% 门禁，CI 立即红。Spec 标注 [TBD]"基线数值首次实测后定阈值"，现基线已测。

### Lead 决策（Spec 偏离，记 DEV-LOG）
1. **E-2 门禁阈值设为实测基线 floor（no-regression ratchet）**：
   - 核心引擎 ≥ **64%**（按聚合，rounded；个别模块 floor 见下）
   - 非核心 ≥ **51%**
   - 全量 ≥ **62%**
2. **80%/60% 为 ratchet 目标**（非立即门禁），后续 Wave 逐步抬升；gap 集中在 compile（14-31%）+ collaborate agents（23-30%，印证 CMS drift D1 空实现）+ query 子模块（compare/tree_mode/related_pages 23-30%）。
3. **E-2 门禁（T-F-E-2-1，Wave 2）** 实现为 `--cov-fail-under` + 模块级 fail-under，低于 floor 则 CI red（防回退）。

### 偏离理由
- 棕地硬化项目，覆盖率应从现状 ratchet，不应要求不可能的跳跃致 CI 恒红。
- compile/collaborate-agents 低覆盖源于空实现/drift（CMS D1 已标），属 03 设计/05 后续 Wave 范畴，非本 hardening 波次能补齐。
- 保留 80%/60% 为 north-star，gap 透明记录，不掩盖。

## 低洼地清单（供后续 Wave 补测）
| 文件 | 覆盖 | 根因 |
|---|---|---|
| engines/compile/{compiler,code_wiki,linter,parsers} | 14-17% | compile 引擎大半未测 |
| engines/collaborate/agents/{critic,librarian,scholar,writer,linker} | 23-30% | drift D1 疑空实现 |
| engines/query/{compare,related_pages,tree_mode} | 23-30% | query 分支未测 |
| engines/learn/* | 22-36% | heavy-SDK 排除（sentence-transformers） |
| reconcile/{detector,strategies,engine} | 25-36% | 未测 |

## manifest 回写
- `tms:saw:coverage-baseline` → output_path=`.csp/artifacts/coverage-baseline.md`，build_status=built
