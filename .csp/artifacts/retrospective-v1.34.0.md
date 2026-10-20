# 复盘 — v1.34.0 wiki 根性能 + coverage 推进（2026-10-20）

> 07 闭环。feat MINOR。前置 06-ship done。

## 闭环校验：✅ 通过
| 链路 | 状态 |
|---|---|
| PRD→Spec | ✅ PRD-wiki-root-perf-v1.34.0 + SPEC-F-WIKI-ROOT-PERF |
| Spec→Task | ✅ app.py wiki_path Path(wiki) + 12 pipeline tests + fail_under 67→68 |
| S6 动态门控 | ✅ pytest 2437/0 fail, cov 68.74% (gate 68), ruff 0, tsc clean |
| 双闸门 | ✅ version_integrity exit 0 + findings_closure exit 0 |
| push+Release | ✅ v1.34.0 @23adaf38, pushed, Release wheel+sdist |

## 度量
- 2 feat done (wiki root perf + coverage 12 tests)
- saw web 启动 80s→15s (e2e 86s→16s)
- parse.py 13→77%, validate.py 15→87%
- coverage 68.43→68.74%, fail_under 67→68
- pytest 2437 (+12)

## Lessons（并入 v1.34.1 入口）
- wiki 根 = cwd 是预置反模式（v1.33.0 retro 发现）——wiki 内容应在 wiki/ 下，不该扫整个 repo。同类审查应看 WikiRepository 的 wiki_root 参数是否其他调用点也用 cwd。
- coverage 70% 目标差 1.3%——extract.py（async+LLM 难测，14%）+ feed_cmd.py（CLI+ORM，12%）是剩余洼地。v1.34.1 应优先这俩。

## 下游 → v1.34.1
- v1.34.1 (feat MINOR): AUDIT-F-04 70% target（补 extract/feed_cmd/learn 测试）+ AUDIT-F-01 god-files 拆分起步 + stale-freshness contamination。
