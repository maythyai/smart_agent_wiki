#!/usr/bin/env python3
"""findings_closure_check.py — findings 闭合真实性机器闸门（可移植版）

契约来源: agent-conventions/findings-lifecycle.md §5（closed 前置 C1-C5）
可移植性: --root / --dirs / --baseline 全参数化，同步到任何项目即用。

校验规则:
  C1 VIOLATION  fixed_in 非空且指向真实 git tag/commit
  C2 VIOLATION  verification 证据字段存在且非空（code-evidence/dynamic/runtime）
  C3 WARNING    resolution 与 title 关键词零交叉（张冠李戴弱信号，2-gram 启发式）
  C4 WARNING    fixed_in commit 时间早于批次审计日期（伪闭环信号）
  C5 WARNING    fixed_in 对应 commit 仅文档变更（空 tag 闭环信号）

baseline 模式（存量治理 + 只降不增）:
  --write-baseline PATH   把当前违规清单固化为基线
  --baseline PATH         只对"基线之外的新增违规"exit 1（存量清零前 CI 不红，
                          新增虚假关闭立即红）；无 --baseline 则全部违规 exit 1

用法:
  python3 prompts/scripts/findings_closure_check.py                       # 全量，违规即 exit 1
  python3 prompts/scripts/findings_closure_check.py --write-baseline .csp/findings-baseline.json
  python3 prompts/scripts/findings_closure_check.py --baseline .csp/findings-baseline.json
  # 其他项目: --root /path/to/repo --dirs .csp/audit:.csp/review
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TAG_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?(-[a-z0-9.]+)?$")  # accepts 2-part (v1.2) or 3-part (v1.2.0) SemVer
HASH_RE = re.compile(r"^[0-9a-f]{7,40}$")


def git(root: Path, args: list[str]) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_object_exists(root: Path, ref: str) -> bool:
    if TAG_RE.match(ref):
        return bool(git(root, ["tag", "-l", ref]))
    if HASH_RE.match(ref):
        return git(root, ["cat-file", "-e", f"{ref}^{{commit}}"]) is not None
    return False


def commit_date(root: Path, ref: str) -> str | None:
    return git(root, ["show", "-s", "--format=%ci", ref])


def commit_has_code(root: Path, ref: str) -> bool | None:
    """tag/commit 是否含非文档代码变更。None = 无法判定。"""
    stat = git(root, ["show", "--stat", "--oneline", ref])
    if stat is None:
        return None
    lines = [l for l in stat.splitlines() if "|" in l and not l.strip().startswith("|")]
    non_doc = [l for l in lines if not l.strip().split("|")[0].strip().endswith(".md")]
    return len(non_doc) > 0


def iter_bigrams(text: str) -> set[str]:
    """中文 2-gram + 英文/数字词，用于 C3 主题交叉弱启发式。"""
    grams: set[str] = set()
    for w in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|\d{2,}", text):
        grams.add(w.lower())
    clean = re.sub(r"[^\u4e00-\u9fff]", "", text)
    for i in range(len(clean) - 1):
        grams.add(clean[i : i + 2])
    return grams


def topic_overlap(title: str, resolution: str) -> bool:
    """resolution 与 title 是否有主题交叉（C3 弱信号）。"""
    t = iter_bigrams(title)
    r = iter_bigrams(resolution)
    return len(t & r) > 0


def batch_date(data: object) -> str | None:
    if not isinstance(data, dict):
        return None
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    for src in (meta, data):
        for key in ("audit_date", "date", "updated_at", "generated_at"):
            if src.get(key):
                return str(src[key])
    return None


def scan(root: Path, dirs: list[str]) -> list[dict]:
    """返回全部违规/警告记录（含 legacy 定位信息）。"""
    records: list[dict] = []
    for d in dirs:
        p = root / d
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*FINDINGS*.json")):
            rel = str(f.relative_to(root))
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                records.append(
                    {"file": rel, "id": "-", "level": "VIOLATION", "rule": "C0", "msg": f"JSON 解析失败: {e}"}
                )
                continue
            findings = (
                data.get("findings", [])
                if isinstance(data, dict)
                else (data if isinstance(data, list) else [])
            ) or []
            a_date = batch_date(data)
            for item in findings:
                if not isinstance(item, dict) or item.get("status") != "closed":
                    continue
                fid = str(item.get("id", "?"))
                ref = str(item.get("fixed_in") or "")
                resolution = str(item.get("resolution") or "")
                title = str(item.get("title") or "")
                exists = git_object_exists(root, ref) if ref else False

                if not ref:
                    records.append({"file": rel, "id": fid, "level": "VIOLATION", "rule": "C1", "msg": "fixed_in 为空"})
                elif not exists:
                    records.append({"file": rel, "id": fid, "level": "VIOLATION", "rule": "C1", "msg": f"fixed_in={ref} 不是真实 git tag/commit"})

                verif = item.get("verification")
                if not verif or (isinstance(verif, (dict, list)) and len(verif) == 0):
                    records.append({"file": rel, "id": fid, "level": "VIOLATION", "rule": "C2", "msg": "缺 verification 证据字段"})

                if title and resolution and not topic_overlap(title, resolution):
                    records.append({"file": rel, "id": fid, "level": "WARNING", "rule": "C3", "msg": "resolution 与 title 关键词零交叉 — 疑似张冠李戴"})

                if exists:
                    c_date = commit_date(root, ref)
                    if c_date and a_date and a_date not in c_date and c_date < a_date:
                        records.append({"file": rel, "id": fid, "level": "WARNING", "rule": "C4", "msg": f"fixed_in commit({c_date[:10]}) 早于审计日期({a_date})"})
                    if commit_has_code(root, ref) is False:
                        records.append({"file": rel, "id": fid, "level": "WARNING", "rule": "C5", "msg": f"fixed_in={ref} 的 commit 仅文档变更 — 疑似空 tag 闭环"})
    return records


def key_of(r: dict) -> str:
    return f"{r['file']}::{r['id']}::{r['rule']}"


def main() -> int:
    ap = argparse.ArgumentParser(description="findings 闭合真实性闸门")
    ap.add_argument("--root", default=".", help="仓库根目录（默认当前目录）")
    ap.add_argument("--dirs", default=".csp/audit,.csp/ui-review,.csp/critic,.csp/gap-analysis,.csp/review", help="逗号分隔的 findings 扫描目录")
    ap.add_argument("--baseline", help="基线文件：只对新增违规 exit 1")
    ap.add_argument("--write-baseline", help="把当前违规清单写入基线文件")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not (root / ".git").exists():
        print(f"ERROR: {root} 不是 git 仓库")
        return 2
    dirs = [d.strip() for d in args.dirs.split(",") if d.strip()]
    records = scan(root, dirs)

    if args.write_baseline:
        Path(args.write_baseline).write_text(
            json.dumps({"records": records}, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"baseline 已写入 {args.write_baseline}（{len(records)} 条）")

    baseline_keys: set[str] = set()
    if args.baseline:
        bp = Path(args.baseline)
        if bp.exists():
            try:
                baseline_keys = {key_of(r) for r in json.loads(bp.read_text(encoding="utf-8")).get("records", [])}
            except (json.JSONDecodeError, OSError):
                print(f"WARN: 基线 {args.baseline} 解析失败，按无基线处理")

    violations = [r for r in records if r["level"] == "VIOLATION"]
    warnings = [r for r in records if r["level"] == "WARNING"]
    new_violations = [r for r in violations if key_of(r) not in baseline_keys]

    print(f"== findings 闭合闸门 == 目录 {len(dirs)} 个, 记录 {len(records)} 条（违规 {len(violations)} / 警告 {len(warnings)}）")
    if baseline_keys:
        print(f"基线存量 {len(baseline_keys)} 条, 新增违规 {len(new_violations)} 条")
    print()
    for r in records:
        flag = "NEW " if key_of(r) not in baseline_keys else "BASE"
        print(f"{r['level']:<9} {flag} [{r['file']}] {r['id']} {r['rule']}: {r['msg']}")

    if new_violations:
        print(f"\nFAIL: 新增违规 {len(new_violations)} 条（预关闭/无证据关闭）")
        return 1
    print("\nPASS: 无新增违规" + (f"（存量 {len(violations)} 条待清，见基线）" if violations else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
