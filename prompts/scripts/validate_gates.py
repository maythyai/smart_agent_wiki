#!/usr/bin/env python3
"""validate_gates.py — 通用治理门禁验证器（配置驱动，可移植版）

契约来源: prompts/automation-validation.md（提示词↔脚本契约）
可移植性: 全部路径/关键词/阈值/委托脚本来自配置文件，同步到任何项目即用。

设计原则（对齐 findings_closure_check.py 的可移植范式）:
  - 提示词做裁决（product sense），脚本做确定性检测（计数/存在性/阈值）
  - 脚本不裁决，只产出机器证据（GATE-REPORT.json）供提示词消费
  - 项目特定部分全部外置到 config，脚本本体项目无关

9 个门禁（映射五类根因 Pattern A-E）:
  G-POS         定位漂移（drift 关键词 vs 信任模型）         Pattern A
  G-NAV         导航预算（顶级 section 数 vs budget）          Pattern B
  G-DOC         文档新鲜度（last_audit vs today）              Pattern E
  G-FLAG        Feature Flag 卫生（default-off + 定位冲突）     Pattern D/A
  G-PLACEHOLDER 占位增长（代码计数 vs baseline，只降不增）      Pattern C/D
  G-DUAL-NAV    多导航源（单一事实源违反）                     Pattern B
  G-CONTRACT    契约孤儿（委托既有脚本）                       Pattern C
  G-BUTTON      按钮 a11y（委托既有脚本）                       Pattern C
  G-LAYER       分层违规（委托既有脚本）                       Pattern D

配置文件 schema 见 prompts/scripts/gates.config.example.json

用法:
  python3 prompts/scripts/validate_gates.py --config .csp/gates.config.json
  python3 prompts/scripts/validate_gates.py --config ... --json
  python3 prompts/scripts/validate_gates.py --config ... --gate G-NAV
  python3 prompts/scripts/validate_gates.py --config ... --strict
  python3 prompts/scripts/validate_gates.py --config ... --write-template  # 生成示例配置

退出码:
  0  全部 PASS 或仅 WARNING
  1  至少一个阻断门禁 ERROR（--strict 下任一 ERROR 即 1）
  2  验证器自身失败（配置缺失/解析错误）

报告落点: {report_dir}/GATE-REPORT-{date}.json（report_dir 来自 config，默认 .csp/convergence）
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Config schema + defaults
# ---------------------------------------------------------------------------
DEFAULT_CONFIG: dict = {
    "project_name": "my-project",
    # 信任模型: single-operator | team | enterprise | multi-tenant
    # G-POS/G-FLAG 据此判定哪些关键词/flag 是漂移
    "trust_model": "single-operator",
    "paths": {
        "agents_md": "AGENTS.md",
        "nav_config": "",            # 主导航配置文件（如 sidebar-config.ts）
        "feature_flags": "",         # feature flag 定义文件
        "doc_status": "",            # DOC-STATUS.md（含 last_audit frontmatter）
        "placeholder_registry": "",  # 占位登记表（含 baseline 计数）
        "roadmap": "",               # roadmap 文件
        "web_src": "",               # 前端源码根（占位扫描用）
    },
    "thresholds": {
        "nav_budget": 7,
        "doc_stale_warn_days": 30,
        "doc_stale_error_days": 60,
        "placeholder_baseline": None,  # None = 从 registry 解析
    },
    # 定位漂移关键词: 与 trust_model 冲突的特性关键词
    # single-operator 产品填 to-B 关键词; to-B 产品填 to-C 关键词（反转）
    "drift_keywords": [
        "team", "团队", "enterprise", "企业", "tenant", "多租户",
        "SSO", "RBAC", "权限管理", "组织", "organization",
    ],
    # 严重漂移关键词: 命中 nav 即 ERROR（用户可见漂移）
    "severe_drift_keywords": [
        "team", "团队", "enterprise", "企业", "tenant", "多租户",
    ],
    # flag 名中与 trust_model 冲突的模式（正则）
    "flag_conflict_pattern": "team|enterprise|tenant|org",
    # 委托门禁: gate -> {script, args}（相对仓库根）
    "delegated_gates": {
        "G-CONTRACT": {"script": "", "args": ["--strict"]},
        "G-BUTTON": {"script": "", "args": []},
        "G-LAYER": {"script": "", "args": ["--strict"]},
    },
    # 启用的门禁（默认全部；可按项目裁剪）
    "enabled_gates": [
        "G-POS", "G-NAV", "G-DOC", "G-FLAG", "G-PLACEHOLDER",
        "G-DUAL-NAV", "G-CONTRACT", "G-BUTTON", "G-LAYER",
    ],
    # 阻断门禁（ERROR 即 exit 1）
    "blocking_gates": [
        "G-POS", "G-NAV", "G-DOC", "G-FLAG", "G-PLACEHOLDER",
        "G-CONTRACT", "G-LAYER",
    ],
    "report_dir": ".csp/convergence",
}


@dataclass
class Finding:
    gate: str
    severity: str          # PASS | WARNING | ERROR
    pattern: str           # A | B | C | D | E | -
    message: str
    evidence: str = ""
    rule: str = ""


@dataclass
class GateResult:
    gate: str
    status: str            # PASS | WARNING | ERROR | SKIPPED
    pattern: str
    findings: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    error: str = ""


class Ctx:
    """运行上下文：config + 仓库根，供各门禁读取。"""

    def __init__(self, root: Path, config: dict):
        self.root = root
        self.cfg = config
        self.paths = config.get("paths", {})
        self.th = config.get("thresholds", {})

    def path(self, key: str) -> Path | None:
        rel = self.paths.get(key)
        if not rel:
            return None
        p = self.root / rel
        return p if p.exists() else None

    def read(self, key: str) -> str:
        p = self.path(key)
        if not p:
            return ""
        try:
            return p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""


def _today() -> date:
    return date.today()


# ---------------------------------------------------------------------------
# G-POS: 定位漂移
# ---------------------------------------------------------------------------
def gate_pos(ctx: Ctx) -> GateResult:
    res = GateResult(gate="G-POS", status="PASS", pattern="A")
    agents = ctx.read("agents_md")
    trust = ctx.cfg.get("trust_model", "single-operator")

    # 验证信任模型声明（在 AGENTS.md 中找对应关键词）
    trust_patterns = {
        "single-operator": r"single.?operator|单操作者|no multi.?tenant|无多租户",
        "multi-tenant": r"multi.?tenant|多租户",
        "team": r"team|团队",
        "enterprise": r"enterprise|企业",
    }
    pat = trust_patterns.get(trust, "")
    declared = bool(re.search(pat, agents, re.IGNORECASE)) if pat and agents else False
    res.metrics["trust_model"] = trust
    res.metrics["trust_declared_in_agents"] = declared

    if not agents:
        res.status = "SKIPPED"
        res.error = "AGENTS.md not found/configured"
        return res

    # 扫描 nav/roadmap/flags 中的漂移关键词
    drift_kw = ctx.cfg.get("drift_keywords", [])
    severe_kw = set(k.lower() for k in ctx.cfg.get("severe_drift_keywords", []))
    hits: dict[str, list[str]] = {}
    for label, key in [("nav", "nav_config"), ("roadmap", "roadmap"), ("flags", "feature_flags")]:
        text = ctx.read(key)
        found = sorted({kw for kw in drift_kw if kw.lower() in text.lower()})
        if found:
            hits[label] = found
    res.metrics["drift_hits"] = hits
    total = sum(len(v) for v in hits.values())
    res.metrics["total_drift_keywords"] = total

    if total == 0:
        res.findings.append(asdict(Finding(
            "G-POS", "PASS", "A",
            f"No drift keywords; aligned with trust_model={trust}",
            rule="AGENTS.md trust model")))
        return res

    nav_hits = hits.get("nav", [])
    severe = [k for k in nav_hits if k.lower() in severe_kw]
    if severe:
        res.status = "ERROR"
        res.findings.append(asdict(Finding(
            "G-POS", "ERROR", "A",
            f"Positioning drift: nav exposes {severe} but trust_model={trust}. "
            f"Product-says != product-does.",
            evidence=f"nav keywords: {nav_hits}",
            rule="trust model is hard constraint")))
    else:
        res.status = "WARNING"
        res.findings.append(asdict(Finding(
            "G-POS", "WARNING", "A",
            f"Potential drift: {total} keywords across sources",
            evidence=json.dumps(hits, ensure_ascii=False),
            rule="verify each against AGENTS.md scope")))
    return res


# ---------------------------------------------------------------------------
# G-NAV: 导航预算
# ---------------------------------------------------------------------------
def gate_nav(ctx: Ctx) -> GateResult:
    res = GateResult(gate="G-NAV", status="PASS", pattern="B")
    text = ctx.read("nav_config")
    if not text:
        return GateResult(gate="G-NAV", status="SKIPPED", pattern="B",
                          error="nav_config not found/configured")

    budget = ctx.th.get("nav_budget", 7)
    # 通用启发式: 数顶级 section（含 items:[ 的对象）
    sections = re.findall(r'\{\s*id:\s*"([^"]+)"[^}]*?items:\s*\[', text, re.DOTALL)
    if sections:
        section_count, section_ids = len(sections), [s for s in sections]
    else:
        section_count, section_ids = text.count("items: ["), []
    item_count = len(re.findall(r'route:\s*"', text)) or len(re.findall(r'href:\s*"', text))

    res.metrics = {"top_level_sections": section_count, "section_ids": section_ids,
                   "total_items": item_count, "budget": budget}

    if section_count > budget:
        res.status = "ERROR"
        res.findings.append(asdict(Finding(
            "G-NAV", "ERROR", "B",
            f"Nav over budget: {section_count} > {budget}. FREEZE new top-level nav.",
            evidence=f"sections: {section_ids}", rule=f"nav_budget={budget}")))
    elif section_count == budget:
        res.status = "WARNING"
        res.findings.append(asdict(Finding(
            "G-NAV", "WARNING", "B",
            f"Nav at budget {section_count}/{budget}; no room for new sections.",
            rule=f"nav_budget={budget}")))
    else:
        res.findings.append(asdict(Finding(
            "G-NAV", "PASS", "B", f"Nav within budget {section_count}/{budget}",
            rule=f"nav_budget={budget}")))
    return res


# ---------------------------------------------------------------------------
# G-DOC: 文档新鲜度
# ---------------------------------------------------------------------------
def gate_doc(ctx: Ctx) -> GateResult:
    res = GateResult(gate="G-DOC", status="PASS", pattern="E")
    text = ctx.read("doc_status")
    if not text:
        return GateResult(gate="G-DOC", status="SKIPPED", pattern="E",
                          error="doc_status not found/configured")

    m = re.search(r"last_audit:\s*(\d{4}-\d{2}-\d{2})", text)
    warn_d = ctx.th.get("doc_stale_warn_days", 30)
    err_d = ctx.th.get("doc_stale_error_days", 60)
    if not m:
        res.status = "WARNING"
        res.findings.append(asdict(Finding(
            "G-DOC", "WARNING", "E", "No parseable last_audit frontmatter",
            rule="last_audit required")))
        return res

    last = datetime.strptime(m.group(1), "%Y-%m-%d").date()
    age = (_today() - last).days
    res.metrics = {"last_audit": str(last), "age_days": age}

    if age > err_d:
        res.status = "ERROR"
        res.findings.append(asdict(Finding(
            "G-DOC", "ERROR", "E",
            f"DOC-STATUS stale {age}d (> {err_d}d). BLOCK new features until refreshed.",
            evidence=f"last_audit={last}", rule=f"stale_error={err_d}d")))
    elif age > warn_d:
        res.status = "WARNING"
        res.findings.append(asdict(Finding(
            "G-DOC", "WARNING", "E", f"DOC-STATUS aging {age}d (> {warn_d}d).",
            evidence=f"last_audit={last}", rule=f"stale_warn={warn_d}d")))
    else:
        res.findings.append(asdict(Finding(
            "G-DOC", "PASS", "E", f"DOC-STATUS fresh ({age}d)", rule=f"stale_warn={warn_d}d")))
    return res


# ---------------------------------------------------------------------------
# G-FLAG: Feature Flag 卫生
# ---------------------------------------------------------------------------
def gate_flag(ctx: Ctx) -> GateResult:
    res = GateResult(gate="G-FLAG", status="PASS", pattern="D")
    text = ctx.read("feature_flags")
    if not text:
        return GateResult(gate="G-FLAG", status="SKIPPED", pattern="D",
                          error="feature_flags not found/configured")

    block = re.search(
        r"(?:DEFAULT_FLAGS|FLAGS|flags)\s*(?::\s*[\w<>\[\].]+)?\s*=\s*\{([^}]+)\}",
        text, re.DOTALL)
    flags: dict[str, bool] = {}
    if block:
        for fm in re.finditer(r'["\']?(\w+)["\']?\s*:\s*(true|false)', block.group(1)):
            flags[fm.group(1)] = fm.group(2) == "true"
    res.metrics["flags"] = flags
    res.metrics["total"] = len(flags)
    default_off = [k for k, v in flags.items() if not v]
    res.metrics["default_off"] = default_off

    conflict_pat = ctx.cfg.get("flag_conflict_pattern", "")
    trust = ctx.cfg.get("trust_model", "single-operator")
    conflict = [k for k in flags if conflict_pat and re.search(conflict_pat, k, re.I)] \
        if trust == "single-operator" else []
    res.metrics["positioning_conflict_flags"] = conflict

    if conflict:
        res.status = "ERROR"
        res.findings.append(asdict(Finding(
            "G-FLAG", "ERROR", "A",
            f"Flag(s) {conflict} contradict trust_model={trust}. Remove or amend AGENTS.md.",
            evidence=f"flags={flags}", rule="trust model")))
    elif default_off:
        res.status = "WARNING"
        res.findings.append(asdict(Finding(
            "G-FLAG", "WARNING", "D",
            f"{len(default_off)} default-off flag(s) {default_off}: dead-code candidates (TTL).",
            evidence=f"default_off={default_off}", rule="default-off >60d = dead code")))
    else:
        res.findings.append(asdict(Finding(
            "G-FLAG", "PASS", "D", f"All {len(flags)} flags healthy")))
    return res


# ---------------------------------------------------------------------------
# G-PLACEHOLDER: 占位增长（只降不增）
# ---------------------------------------------------------------------------
def gate_placeholder(ctx: Ctx) -> GateResult:
    res = GateResult(gate="G-PLACEHOLDER", status="PASS", pattern="C")
    web_src = ctx.path("web_src")
    if not web_src:
        return GateResult(gate="G-PLACEHOLDER", status="SKIPPED", pattern="C",
                          error="web_src not found/configured")

    baseline = ctx.th.get("placeholder_baseline")
    reg = ctx.read("placeholder_registry")
    if baseline is None and reg:
        bm = re.search(r"(\d+)\s*处占位", reg) or re.search(r"baseline[:\s]+(\d+)", reg, re.I)
        if bm:
            baseline = int(bm.group(1))
    if baseline is None:
        baseline = 0  # 无 baseline 则只报当前计数
    res.metrics["baseline"] = baseline

    patterns = ["即将上线", "coming soon", "敬请期待", "upcoming", "开发中",
                "under construction", "TBD"]
    count, hits = 0, []
    for f in web_src.rglob("*.tsx"):
        try:
            t = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for p in patterns:
            n = t.lower().count(p.lower())
            if n:
                count += n
                hits.append(f"{f.name}: {p} x{n}")
    res.metrics["current_count"] = count
    res.metrics["sample_hits"] = hits[:10]

    if baseline and count > baseline:
        res.status = "ERROR"
        res.findings.append(asdict(Finding(
            "G-PLACEHOLDER", "ERROR", "C",
            f"Placeholder growth: {count} > baseline {baseline}. Only-decrease violated.",
            evidence="; ".join(hits[:5]), rule="count must not increase")))
    elif baseline and count == baseline:
        res.status = "WARNING"
        res.findings.append(asdict(Finding(
            "G-PLACEHOLDER", "WARNING", "C",
            f"Placeholder at baseline {baseline}; no reduction progress",
            rule="should decrease")))
    else:
        res.findings.append(asdict(Finding(
            "G-PLACEHOLDER", "PASS", "C",
            f"Placeholder count {count}" + (f" <= baseline {baseline}" if baseline else " (no baseline)"))))
    return res


# ---------------------------------------------------------------------------
# G-DUAL-NAV: 多导航源
# ---------------------------------------------------------------------------
def gate_dual_nav(ctx: Ctx) -> GateResult:
    res = GateResult(gate="G-DUAL-NAV", status="PASS", pattern="B")
    nav_path = ctx.path("nav_config")
    if not nav_path:
        return GateResult(gate="G-DUAL-NAV", status="SKIPPED", pattern="B",
                          error="nav_config not found/configured")

    # 在 nav_config 同目录下找其他 nav/sidebar/menu 文件
    layout = nav_path.parent
    nav_files = [p.name for p in layout.glob("*.ts*")
                 if re.search(r"nav|sidebar|menu", p.name, re.I)]
    res.metrics["nav_sources"] = nav_files
    res.metrics["count"] = len(nav_files)

    if len(nav_files) > 2:
        res.status = "WARNING"
        res.findings.append(asdict(Finding(
            "G-DUAL-NAV", "WARNING", "B",
            f"{len(nav_files)} nav sources. Verify single-source-of-truth (others derive).",
            evidence=", ".join(nav_files), rule="N3: one navGroups export per domain")))
    else:
        res.findings.append(asdict(Finding(
            "G-DUAL-NAV", "PASS", "B", f"Nav sources within tolerance: {nav_files}")))
    return res


# ---------------------------------------------------------------------------
# 委托门禁（调用项目既有脚本）
# ---------------------------------------------------------------------------
def _run_delegated(ctx: Ctx, gate: str) -> GateResult:
    spec = ctx.cfg.get("delegated_gates", {}).get(gate, {})
    script = spec.get("script", "")
    pattern = {"G-CONTRACT": "C", "G-BUTTON": "C", "G-LAYER": "D"}.get(gate, "-")
    res = GateResult(gate=gate, status="PASS", pattern=pattern)
    if not script:
        res.status = "SKIPPED"
        res.error = f"{gate}: no delegated script configured"
        return res
    spath = ctx.root / script
    if not spath.exists():
        res.status = "SKIPPED"
        res.error = f"script not found: {script}"
        return res
    cmd = [sys.executable, str(spath)] + spec.get("args", [])
    try:
        proc = subprocess.run(cmd, cwd=str(ctx.root), capture_output=True,
                              text=True, timeout=180)
        code, out = proc.returncode, (proc.stdout + proc.stderr)[-2000:]
    except subprocess.TimeoutExpired:
        res.status = "ERROR"
        res.error = f"timeout running {script}"
        return res
    except Exception as e:  # noqa: BLE001
        res.status = "ERROR"
        res.error = f"error running {script}: {e}"
        return res

    res.metrics["exit_code"] = code
    res.metrics["output_tail"] = out[-500:]
    if code != 0:
        res.status = "ERROR"
        res.findings.append(asdict(Finding(
            gate, "ERROR", pattern, f"{script} found violations (exit {code})",
            evidence=out[-300:], rule=f"{script} {' '.join(spec.get('args', []))}")))
    else:
        # G-BUTTON 特例: 解析 JSON 计数
        if gate == "G-BUTTON":
            m = re.search(r"\{.*\}", out)
            if m:
                try:
                    data = json.loads(m.group(0))
                    res.metrics.update(data)
                    if data.get("missing_aria_label") or data.get("missing_onclick"):
                        res.status = "WARNING"
                        res.findings.append(asdict(Finding(
                            gate, "WARNING", pattern,
                            f"Buttons missing aria={data.get('missing_aria_label',0)}, "
                            f"onClick={data.get('missing_onclick',0)}",
                            rule=script)))
                except json.JSONDecodeError:
                    pass
        if res.status == "PASS":
            res.findings.append(asdict(Finding(gate, "PASS", pattern, f"{script} clean")))
    return res


def gate_contract(ctx: Ctx) -> GateResult:
    return _run_delegated(ctx, "G-CONTRACT")


def gate_button(ctx: Ctx) -> GateResult:
    return _run_delegated(ctx, "G-BUTTON")


def gate_layer(ctx: Ctx) -> GateResult:
    return _run_delegated(ctx, "G-LAYER")


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
GATES: dict[str, Callable] = {
    "G-POS": gate_pos,
    "G-NAV": gate_nav,
    "G-DOC": gate_doc,
    "G-FLAG": gate_flag,
    "G-PLACEHOLDER": gate_placeholder,
    "G-DUAL-NAV": gate_dual_nav,
    "G-CONTRACT": gate_contract,
    "G-BUTTON": gate_button,
    "G-LAYER": gate_layer,
}


def write_template(path: str) -> int:
    Path(path).write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    print(f"示例配置已写入 {path} — 按项目实际路径/关键词/阈值修改后使用")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="通用治理门禁验证器（配置驱动）")
    ap.add_argument("--config", help="配置文件路径（JSON，schema 见 gates.config.example.json）")
    ap.add_argument("--root", default=".", help="仓库根目录（默认当前目录）")
    ap.add_argument("--json", action="store_true", help="仅输出 JSON")
    ap.add_argument("--gate", help="只跑单个门禁（如 G-NAV）")
    ap.add_argument("--strict", action="store_true", help="任一 ERROR 即 exit 1")
    ap.add_argument("--out", help="报告输出路径（默认 {report_dir}/GATE-REPORT-{date}.json）")
    ap.add_argument("--write-template", metavar="PATH", help="生成示例配置文件后退出")
    args = ap.parse_args()

    if args.write_template:
        return write_template(args.write_template)

    if not args.config:
        print("ERROR: 必须提供 --config（或 --write-template 生成示例）", file=sys.stderr)
        return 2

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"ERROR: 配置文件不存在: {cfg_path}", file=sys.stderr)
        return 2
    try:
        user_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: 配置解析失败: {e}", file=sys.stderr)
        return 2

    # 深度合并 user_cfg 到 DEFAULT_CONFIG
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    for k, v in user_cfg.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v

    root = Path(args.root).resolve()
    ctx = Ctx(root, cfg)

    enabled = cfg.get("enabled_gates", list(GATES.keys()))
    gates_to_run = [args.gate] if args.gate else [g for g in enabled if g in GATES]
    blocking = set(cfg.get("blocking_gates", []))

    results: list[GateResult] = []
    for g in gates_to_run:
        fn = GATES.get(g)
        if not fn:
            results.append(GateResult(gate=g, status="SKIPPED", pattern="-",
                                      error=f"unknown gate {g}"))
            continue
        try:
            results.append(fn(ctx))
        except Exception as e:  # noqa: BLE001
            results.append(GateResult(gate=g, status="ERROR", pattern="-",
                                      error=f"validator exception: {e}"))

    counts = {"PASS": 0, "WARNING": 0, "ERROR": 0, "SKIPPED": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    blocking_errors = [r.gate for r in results if r.status == "ERROR" and r.gate in blocking]
    any_error = any(r.status == "ERROR" for r in results)

    report = {
        "validator": "validate_gates.py (generic)",
        "project": cfg.get("project_name", "?"),
        "trust_model": cfg.get("trust_model", "?"),
        "date": str(_today()),
        "summary": counts,
        "blocking_errors": blocking_errors,
        "verdict": "BLOCKED" if blocking_errors else ("WARN" if counts["WARNING"] else "PASS"),
        "gates": [asdict(r) for r in results],
    }

    out_path = args.out
    if not out_path:
        rdir = root / cfg.get("report_dir", ".csp/convergence")
        rdir.mkdir(parents=True, exist_ok=True)
        out_path = str(rdir / f"GATE-REPORT-{_today().isoformat()}.json")
    try:
        Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        report["report_path"] = out_path
    except OSError as e:
        report["report_write_error"] = str(e)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"=== Gate Validation — {cfg.get('project_name')} ({_today()}) ===")
        print(f"trust_model={cfg.get('trust_model')}  verdict={report['verdict']}  "
              f"(PASS={counts['PASS']} WARN={counts['WARNING']} "
              f"ERROR={counts['ERROR']} SKIP={counts['SKIPPED']})")
        if blocking_errors:
            print(f"BLOCKING ERRORS: {blocking_errors}")
        print()
        for r in results:
            icon = {"PASS": "✅", "WARNING": "🟡", "ERROR": "🔴", "SKIPPED": "⚪"}.get(r.status, "?")
            print(f"{icon} {r.gate} [{r.pattern}]: {r.status}")
            for f in r.findings:
                print(f"    - {f['message']}")
            if r.error:
                print(f"    ! {r.error}")
            if r.metrics:
                short = {k: v for k, v in r.metrics.items() if k not in ("output_tail", "sample_hits")}
                if short:
                    print(f"    metrics: {json.dumps(short, ensure_ascii=False)}")
        print(f"\nReport: {out_path}")

    if args.strict and any_error:
        return 1
    if blocking_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())