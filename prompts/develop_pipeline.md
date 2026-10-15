用 lifecycle-orchestrator 从当前 .csp/lifecycle-state.json 续跑，连续推进所有待交付版本（待交付 = ROADMAP 中 status planned/in-progress；deferred 版本不并入活跃队列，待解除条件满足才并入），版本间不停：每个版本 06 done（push origin、已打 tag、已出 Release、已归档）后，自动读 docs/strategy/ROADMAP.md 取下一个未交付版本，回 01 开启下一轮，直到队列清空。ROADMAP 须已过集成必要性审视；若未过或过期，先 spawn roadmap-planner 净化版本队列再续跑；若净化产生新增/重排的版本批次，先过 prompts/product-design-convergence.md 收敛审查（定位对齐/导航准入/系统卫生），收敛后功能清单才是 01 的合法输入。仅当我说"只做某个版本"时才单版本停。

每轮 01 前置四读（缺一不可）：
① 读 .csp/agent-conventions/ 全部规范（ai-coding-guardrails.md 的 G-01~G-08、VERIFICATION-DISCIPLINE.md、e2e-deep-audit-prompt.md），05 开发逐条遵守；
② 读 .csp/{audit,ui-review,critic,gap-analysis}/ 最新批次 findings，把与本版本主题对应的 findings 并入入口清单作为验收项；
③ 对账 .csp/lifecycle-state.json 与 docs/strategy/ROADMAP.md（前者为运行时真相、后者为规划真相），漂移则按授权修复并记 DEV-LOG；
④ 检查既有 BLOCKED 项解除条件，满足者并入本版本入口清单。

先有完整 PRD 和详细技术 Spec，Spec 齐全后才进开发（05），不写无 Spec 的代码。Spec 验收门：PRD 含背景/目标/功能清单/Given-When-Then 验收标准；Spec 含技术方案/接口契约/测试计划/风险，关键改动带 file:line 证据。quick-fix 类版本（如 v5.711.0 B0）走轻量 Spec 一页纸（改动点+证据+验证方式），主题版本走完整 Spec。

自决策授权（默认自己拍板，不问我）：范围/优先级、Spec 歧义、Wave 排序、fix 路由（05 实现缺陷 / 03 Spec 缺口）、可逆整改（归档 re-point、版本漂移 bump）、CMS re-align、deferred 取舍——这些你自己定，定了记入 DEV-LOG 即可，不打断我。

循环收敛：06 未过按根因回 05/03 修 delta 重验，循环到全绿；超 5 轮再报我。跨版本熔断：连续 3 个版本因同一根因失败，暂停并报我，附根因证据链。

06 done 硬定义（任一不满足即 06 未过，按根因回 05/03 修 delta 重验）：S6 门控全 ran（附命令+exit code 证据，禁止 not-run 降级；工具链不可用 = BLOCKED 报我，不得用 grep/review 替代动态门控）→ S7 无 CRITICAL → 7.6 对账 reconciled=true（含 findings 闭合闸门 exit 0）→ 版本对齐（prompts/scripts/version_integrity_check.py 通过，T1 多 tag 同 commit / T2 空 tag / T3 六处同步 / T4 CHANGELOG 全零违规）→ 归档完成。发布动作只是 06 的一部分，详见 prompts/06-verify-ship.md。

留尾纪律：剩余项只能 done / BLOCKED（附阻塞+谁解除）/ deferred（附解除条件并计入 Release notes），禁止"下轮再补/gate 全绿就交差"。deferred 项不阻塞当前版本发布，但要自动并入下一版本 01 的入口清单。收尾必做：commit（Conventional Commits、原子提交）→ CHANGELOG.md 追加 → tag（执行 docs/references/repo_rules/02-版本号与发布管理规范.md，六处版本同步）→ push origin → Release → 归档。

findings 回写契约（执行 .csp/agent-conventions/findings-lifecycle.md，禁止预关闭）：仅对"本版本真实修复且已验证"的 findings 回写；回写必带 fixed_in（真实存在的 tag/commit）+ verification 证据（code-evidence file:line / dynamic ran+exit / runtime 实机截图），resolution 必须与本 finding 主题一致；fixed_in 不存在 → 回滚 open；closed 落盘时间必须晚于 fixed_in commit 提交时间。01-05 阶段只读 findings 禁止写 status。收尾后强制跑双闸门：python3 prompts/scripts/findings_closure_check.py --baseline .csp/findings-baseline.json（新增预关闭即 exit 1，回滚并报我；基线只降不增，存量清零后删基线）+ python3 prompts/scripts/version_integrity_check.py --baseline .csp/version-baseline.json（新增多 tag/空 tag/失同步即 exit 1）。脚本在 prompts/scripts/ 下，可整体同步到其他项目复用。

版本与门禁条款：纯文档 commit 禁打版本 tag（文档变更走 chore commit 不带 tag）；一个 tag 只对应一个 commit 的代码交付，禁多 tag 同 commit；六处版本同步必须脚本校验通过。guardrail 脚本部署 = 脚本落盘 + CI 接线，未接 CI 不得声称 enforcement。

每版本 checkpoint 落盘：版本结束时更新 .csp/lifecycle-state.json（stage/version/shipped 数组）+ DEV-LOG 追加本轮决策摘要，保证会话中断可无损续跑。

gate 即授权，全自动推进，只在战略根本模糊 / PRD Rejected / 真破坏操作 / 多 tag 不明 / 无法 auto-resolve 的报错这五类才打断我（07 复盘也默认自动触发，不问；复盘产物落 .csp/ 固定位置，lessons 并入下一版本 01 入口清单）。完成每个版本按进度条格式播报（锚点：[vX.Y.Z] [0X/06 阶段名] 进度条 完成项/总项），全部版本清空后输出总发布摘要再停。

---

继续完成所有任务，循环执行，不用等我给你指令让你继续，你要自己把控进度，没有完成就继续完成任务，直到所有任务完成。需要决策的你要能自我驱动给出最合理的决策，实在不敢自己定夺的时候要询问我。