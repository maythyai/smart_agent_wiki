# 复盘 — v1.17.0 desktop 完成 v4.4（2026-09-07）

> 07 闭环校验。findings 回流下一轮 01（v2.0.0/v1.18.0 决策）。前置：06-ship done（v1.17.0 tagged @e391611，已 push 远端 + GitHub Release 含 .dmg asset）。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-desktop-v1.17.0 Approved；4 SPEC-F-V-1..4 1:1 对应 F-V-1..4 |
| Spec → Task | ✅ | WBS/TASKS-DELTA-v1.17.0 4 Task（T-F-V-1..4）1:1 |
| Task → commit | ✅ | git log：`f922a99`(feat F-V-1) / `19578ef`(feat F-V-2) / `6bb6949`(build F-V-3) / `1ca63a1`(fix F-V-4) + `eb4fd2e`(docs) + `e391611`(reconcile) + `1cca7dc`(release) |
| AC → 测试 | ✅ | COVERAGE-REPORT 9 AC 全映射（AC-V-1/2→V-1 / AC-W-1/2→V-2 / AC-B-1/2→V-3 / AC-C-1/2/3→V-4） |
| commit → tag | ✅ | `git tag -l v1.17.0` @e391611 + `git ls-remote --tags origin v1.17.0` = 6f46f37（已 push 远端）|
| 测试/lint | ✅ | pytest 2267 passed / 7 skipped / 0 failed；ruff 0；smoke 16/16；vitest 64 passed；vite build 1029 modules OK |
| 构建 | ✅ | tauri build 产 `Smart Agent Wiki.app` + `Smart Agent Wiki_1.0.0_aarch64.dmg` (2.8MB, unsigned)；wheel smart_agent_wiki-1.17.0；pyproject 1.17.0；desktop 0.1.0→1.0.0；web 0.1.0→1.0.0 |
| Release | ✅ | GitHub Release https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.17.0（--latest，assets: wheel + sdist + .dmg）|

## v1.17.0 度量
- 4 Feature done（desktop 1.0 bump + 配置收敛 / web 仪表盘集成验证 / tauri build .app+.dmg / 端口收敛+CORS）
- desktop 0.1.0→1.0.0（package.json + tauri.conf.json + Cargo.toml + web/package.json 4 文件同步）
- tauri build 首次产原生包（mac aarch64 .app + .dmg 2.8MB，unsigned per ADR-017 defer）
- 端口收敛：vite proxy 8080→8000（与 saw web 默认一致）+ CORS localhost:5173
- 后端 +50 测试（2217→2267）；前端 vitest 64 持
- 复用 v1.16.0 web 仪表盘（frontendDist=../../web/dist），desktop 集成无需新建前端

## Findings（回流下一轮）

### V1 — .dmg 未签名/公证 [Medium / P3]
tauri build 产 .dmg 但 unsigned（ADR-017 决策 defer）。生产分发须 Apple Developer ID 签名 + 公证，否则 macOS Gatekeeper 拦截。
- **证据**：`desktop/src-tauri/target/release/bundle/dmg/Smart Agent Wiki_1.0.0_aarch64.dmg`（unsigned）；ADR-017（sidecar + 签名 defer）。
- **影响**：用户下载 .dmg 双击会被 Gatekeeper 警告/拦截，须 `xattr -d com.apple.quarantine` 或右键打开。
- **严重度**：Medium（分发可用性，本地开发不阻塞）。
- **建议**：后续加 Apple Developer ID 签名 + notarization（CI secrets 注入）；或文档标注 manual override。
- **回流**：下一轮（desktop 签名专项 OR 用户侧配置）。

### V2 — 仅 mac aarch64 包，无跨平台 [Low / P3]
tauri build 仅产 mac aarch64（本机 arm64）。无 x86_64 / Windows / Linux 包。
- **证据**：`bundle/dmg/` 只有 aarch64；无 .exe/.AppImage。
- **影响**：跨平台用户无原生包（仍可用 pip install + web）。
- **建议**：后续加跨平台 CI（GitHub Actions matrix: mac x86_64/win/linux）。
- **回流**：后续（跨平台 CI 专项）。

### V3 — sidecar defer，prod 仍需外部 saw server [Low / P3]
ADR-017 选 hybrid（dev proxy + prod external），sidecar（desktop 内嵌 saw server）defer v2.0——因 sidecar 须捆绑 Python 运行时，超出 1.0 bump 范围。
- **证据**：ADR-017（决策③ hybrid，sidecar defer）。
- **影响**：prod 模式 desktop 仍需用户先起 `saw web` server，非真正"一键启动"。
- **建议**：v2.0+ 评估 sidecar（PyInstaller 打包 saw server + Tauri sidecar）。
- **回流**：v2.0+ 候选。

### V4 — desktop build 产物不入 git（.gitignore 已排除）[Info]
`desktop/src-tauri/target/` 构建产物不入 git（.gitignore 排除），.dmg 作为 GitHub Release asset 附件分发。正确。
- **回流**：无（信息项，确认正确）。

### 续留 findings（跨迭代 backlog）
- **N3/K2** per-request workspace 注入（架构债，v2.0/v1.18.0 候选）
- **O4** tag 指向 reconcile commit 非 release commit（记录一致性，P3）
- **S1-S4**（v1.14.0 续留：ANN 小规模慢 / scale_curve 维度 / COVERAGE-REPORT 状态 / engine.py god-file）
- **T1-T4**（v1.15.0 续留：activity 不持久化 / links apply 无 undo / 角色无分享 / agents_cmd 结构）
- **U1-U6**（v1.16.0 续留：视觉 E2E 未跑 / polling 延迟 / 等）

## v2.0.0 MAJOR 判断建议（关键，留 v2.0 01 决策）

> roadmap §1.1：MAJOR 仅在真实 breaking API 变更/范式跃迁时 bump。战略主题号 ≠ SemVer 号。

**per-request workspace 注入（N3/K2）的版本号判断**：

| 实现方式 | 是否 breaking | 版本号 |
|---|---|---|
| contextvar 注入 workspace_id（QueryEngine 内部读，构造签名不变，公开 API 不变） | **否**（additive） | **v1.18.0 MINOR** |
| QueryEngine 构造签名改（workspace_id 从可选变必填，或移除 default） | **是**（不兼容） | v2.0.0 MAJOR |
| 移除 deprecated v3.x 兼容层 / 重构公开 API surface | **是** | v2.0.0 MAJOR |

**建议**：走 **v1.18.0 MINOR**——用 contextvar 注入 workspace_id（additive，不改公开 API 契约），诚实按 SemVer 不强行 MAJOR。v2.0.0 MAJOR 推迟到真实 breaking（如 sidecar 重构 API / 移除 deprecated / 范式跃迁）时再 bump。这符合 roadmap 反模式"战略主题号当 SemVer 打 tag"的规避。

若 01 PRD 决策引入真实 breaking（如 QueryEngine 构造签名改、移除 deprecated），则 bump v2.0.0 MAJOR——但须有真实 breaking 变更支撑，不为"平台化"叙事强行 MAJOR。

## 下游衔接 → 下一迭代候选

| 候选 | findings 关联 | 说明 |
|---|---|---|
| **per-request workspace 注入**（v1.18.0 MINOR 或 v2.0.0 MAJOR，视 breaking） | N3/K2 | web 路径请求级 workspace 隔离（contextvar 注入 additive→MINOR；构造签名改→MAJOR）|
| desktop 签名 + 公证 | V1 | Apple Developer ID + notarization（CI secrets）|
| 跨平台 CI（win/linux/mac x86_64） | V2 | GitHub Actions matrix |
| desktop sidecar（内嵌 saw server） | V3 | PyInstaller + Tauri sidecar（v2.0+）|
| 清剩余 S/T/U findings | S1-S4/T1-T4/U1-U6 | 持续债务收口 |

- 累计 v1.5.0–v1.17.0 九轮：3 轮债务收口 + 4 轮新能力（embedding/agent-link/dashboard/desktop）+ 2 轮 E2E/perf。
- v2.0.0（MAJOR）推迟到真实 breaking API 变更/范式跃迁时再 bump；当前 v1.x 序列继续 additive 逼近。

---

*本复盘所有证据均经 git/manifest 真实状态核验。.dmg 未签名诚实标注（ADR-017 defer）。findings 带证据 file:line/DEV-LOG。*
