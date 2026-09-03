# TMS Delta — v1.5.0（2026-09-03）

> 03 测试规约 delta。intelligence-adaptation 新域 + debt 续。增量用例（不重写存量）。ground 自各 SPEC-F-I-*/SPEC-F-Z-* 的"测试映射"。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-WF-1（run + crash 可恢复） | F-I-1 | `tests/unit/test_workflow_cmd.py`（新建）：run_executes + resume_after_interrupt（注入 interrupted 行→resume→completed） | [TBD-impl] |
| AC-WF-2（schema 校验失败报错） | F-I-1 | 同上：validate_invalid_yaml（缺 name/steps/未知 agent→exit 1） | [TBD-impl] |
| AC-LR-1（distill 在线产 SOP 非空） | F-I-2 | `tests/unit/engines/learn/test_distiller_cli.py`（新建）：mock LLMRouter→assert SOP.steps 非空 + `.saw/sops/` 落盘 | [TBD-impl] |
| AC-LR-2（gaps 输出列表） | F-I-2 | `tests/unit/engines/learn/test_trends_cli.py`（新建）：fresh repo→gaps 列表 | [TBD-impl] |
| AC-TK-1（token 节省 % 对比基线） | F-I-3 | `tests/unit/test_token_bench.py`（新建）：固定语料→saved_pct>0 + 确定性 | [TBD-impl] |
| AC-AG-1（声明 agent ∈ 注册集） | F-I-4 | `tests/unit/test_workflow_lint.py`（新建）：valid→exit 0；未知 agent→exit 1 | [TBD-impl] |
| AC-LINT-2 续（F841 0 errors） | F-Z-6 | `tests/unit/test_lint_baseline.py`（扩 v1.4.0）：`--select F401,F841` 断言 0 | [TBD-impl] |
| AC-WS-3（全路径 workspace 隔离） | F-Z-7 | `tests/unit/test_workspace_routing.py`（新建）：A ws 写 claim→B ws search 空；default 兼容 | [TBD-impl] |
| AC-SEC-5 续（reload CLI 触发） | F-Z-8 | `tests/unit/test_policy_reload_cmd.py`（新建）：mock reload→CLI 退出 0 + backend 报告 | [TBD-impl] |
| AC-COV-1（query 覆盖 + 棘轮 65） | F-Z-9 | `tests/unit/engines/query/test_compare.py`/`test_related_pages.py`/`test_tree_mode.py`（新建/扩）+ `fail_under=65` | [TBD-impl] |

## 约定
- intelligence-adaptation 新域无既有 TMS，本轮建增量用例（10 用例落 10 文件）。
- mock 纪律：F-I-2 distill mock LLMRouter.extract_claims（CI 无 LLM）；F-I-3 bench 确定性语料；F-Z-8 mock CedarPolicyEngine.reload。
- F-Z-6 扩 v1.4.0 test_lint_baseline（F401→F401,F841）。
- F-Z-9 coverage 棘轮 60→65（不一步 80，硬约定 #10）。
