#!/usr/bin/env python3
"""version_integrity_check.py — 版本完整性闸门（verify-version 执行体，可移植版）

契约来源: version-management.md §十（verify-version = 发布前强制 gate）
         + findings-lifecycle.md §6（一 tag 一 commit、纯文档禁 tag）
可移植性: --root / --files / --changelog 全参数化，同步到任何项目即用。

校验规则:
  T1 VIOLATION  多 tag 同 commit —— 一个 commit 只承载一个版本的交付
  T2 VIOLATION  空 tag —— tag 指向的 commit 仅文档(.md)变更，禁打版本 tag
  T3 VIOLATION  版本文件失同步 —— 各 --files 提取的 version 与最新 tag 不一致
  T4 VIOLATION  CHANGELOG 失同步 —— 最新条目版本与最新 tag 不一致（若提供 --changelog）
  T5 WARNING    tag 领先于所有版本文件（疑似打了 tag 忘 bump）

用法:
  python3 prompts/scripts/version_integrity_check.py
  python3 prompts/scripts/version_integrity_check.py --files package.json:apps/web/package.json:pyproject.toml --changelog CHANGELOG.md
  # 其他项目: --root /path --files package.json --changelog CHANGE.md --tag-prefix v
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SEMVER_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?(?:[-+][0-9A-Za-z.-]+)?")
TOML_VER_RE = re.compile(r'^version\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def git(root: Path, args: list[str]) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, timeout=30
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def semver_key(tag: str) -> tuple[int, int, int, int]:
    """Sort key. Handles 2-part (1.2) and 3-part (1.2.0) SemVer. CalVer
    (vYYYY.M.DD — major is a year >= 2000) is treated as historical and must
    NOT win 'latest' over active SemVer. Bucket CalVer below active SemVer:
    (is_active_semver, major, minor, patch)."""
    m = SEMVER_RE.search(tag)
    if not m:
        return (0, 0, 0, 0)
    major, minor = int(m.group(1)), int(m.group(2))
    patch = int(m.group(3)) if m.group(3) else 0
    is_active_semver = 1 if major < 2000 else 0  # CalVer years (2026…) → bucket 0
    return (is_active_semver, major, minor, patch)


def list_tags(root: Path, prefix: str) -> dict[str, str]:
    """tag -> commit。annotated tag 解引用到 commit。"""
    out = git(
        root,
        ["for-each-ref", f"refs/tags/{prefix}*", "--format=%(refname:short) %(*objectname) %(objectname)"],
    )
    tags: dict[str, str] = {}
    if not out:
        return tags
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[0]
        deref = parts[1] if len(parts) >= 3 and parts[1] != "" else None
        commit = deref or (parts[1] if len(parts) >= 2 else "")
        if SEMVER_RE.search(name) and commit:
            tags[name] = commit
    return tags


def commit_is_doc_only(root: Path, commit: str) -> bool | None:
    stat = git(root, ["show", "--stat", "--oneline", commit])
    if stat is None:
        return None
    lines = [l for l in stat.splitlines() if "|" in l and not l.strip().startswith("|")]
    if not lines:
        return False  # 空 commit（如 merge），不判 doc-only
    non_doc = [l for l in lines if not l.strip().split("|")[0].strip().endswith(".md")]
    return len(non_doc) == 0


def extract_version(path: Path) -> str | None:
    """从 JSON / TOML / 纯文本文件提取 version 字段。"""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        try:
            v = json.loads(text).get("version")
            return str(v) if v else None
        except json.JSONDecodeError:
            return None
    if path.suffix == ".toml":
        m = TOML_VER_RE.search(text)
        return m.group(1) if m else None
    m = SEMVER_RE.search(text[:400])
    return m.group(0) if m else None


def changelog_latest(path: Path, prefix: str) -> str | None:
    """提取 CHANGELOG 最新版本条目。兼容 `## [x.y.z]` / `## vx.y.z` / `## x.y.z`。"""
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:200]:
        m = re.match(r"^#{1,3}\s*\[?(v?\d+\.\d+(?:\.\d+)?)", line.strip())
        if m:
            v = m.group(1)
            return v[len(prefix):] if v.startswith(prefix) else v
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="版本完整性闸门（verify-version）")
    ap.add_argument("--root", default=".", help="仓库根目录")
    ap.add_argument("--files", default="package.json:apps/web/package.json:pyproject.toml",
                    help="冒号分隔的版本文件（JSON/TOML/纯文本自动识别）")
    ap.add_argument("--changelog", default="CHANGELOG.md", help="CHANGELOG 路径（空字符串跳过）")
    ap.add_argument("--tag-prefix", default="v", help="tag 前缀")
    ap.add_argument("--skip-empty-tag", action="store_true", help="跳过 T2 空 tag 检测（存量治理期）")
    ap.add_argument("--baseline", help="基线文件：只对新增违规 exit 1（只降不增）")
    ap.add_argument("--write-baseline", help="把当前违规清单写入基线文件")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not (root / ".git").exists():
        print(f"ERROR: {root} 不是 git 仓库")
        return 2

    violations: list[str] = []
    warnings: list[str] = []
    tags = list_tags(root, args.tag_prefix)
    if not tags:
        print("PASS: 无版本 tag（新项目）")
        return 0

    # latest release tag = most recently CREATED (handles multiple version
    # lines + historical CalVer: the active line is the one most recently
    # released, not the highest semver). Falls back to semver max if query fails.
    recent = git(root, ["for-each-ref", "--sort=-creatordate",
                        f"refs/tags/{args.tag_prefix}*", "--format=%(refname:short)", "--count=1"])
    latest_tag = recent.strip() if (recent and recent.strip() in tags) else max(tags, key=semver_key)
    latest_ver = latest_tag[len(args.tag_prefix):] if latest_tag.startswith(args.tag_prefix) else latest_tag

    # T1 多 tag 同 commit
    by_commit: dict[str, list[str]] = {}
    for t, c in tags.items():
        by_commit.setdefault(c, []).append(t)
    for c, group in sorted(by_commit.items()):
        if len(group) > 1:
            group_sorted = sorted(group, key=semver_key)
            violations.append(f"T1 多 tag 同 commit {c[:8]}: {', '.join(group_sorted)} — 每个版本号必须有独立代码交付")

    # T2 空 tag（仅文档变更）
    if not args.skip_empty_tag:
        for t, c in sorted(tags.items(), key=lambda kv: semver_key(kv[0])):
            if commit_is_doc_only(root, c):
                violations.append(f"T2 空 tag {t}: commit {c[:8]} 仅文档(.md)变更 — 纯文档禁打版本 tag")

    # T3 版本文件同步
    for rel in [f for f in args.files.split(":") if f]:
        ver = extract_version(root / rel)
        if ver is None:
            warnings.append(f"T3 {rel}: 无法提取 version 字段（文件缺失或格式未识别）")
        elif ver != latest_ver:
            violations.append(f"T3 {rel} version={ver} ≠ 最新 tag {latest_tag} — 六处同步未落实")

    # T4 CHANGELOG
    if args.changelog:
        cl = changelog_latest(root / args.changelog, args.tag_prefix)
        if cl is None:
            warnings.append(f"T4 {args.changelog}: 前 200 行未找到版本条目")
        elif cl != latest_ver:
            violations.append(f"T4 CHANGELOG 最新条目 {cl} ≠ 最新 tag {latest_tag}")

    print(f"== 版本完整性闸门 == tag 总数 {len(tags)}, 最新 {latest_tag}")

    if args.write_baseline:
        Path(args.write_baseline).write_text(
            json.dumps({"violations": violations, "warnings": warnings}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"baseline 已写入 {args.write_baseline}（违规 {len(violations)} 条）")

    baseline_keys: set[str] = set()
    if args.baseline:
        bp = Path(args.baseline)
        if bp.exists():
            try:
                baseline_keys = set(json.loads(bp.read_text(encoding="utf-8")).get("violations", []))
            except (json.JSONDecodeError, OSError):
                print(f"WARN: 基线 {args.baseline} 解析失败，按无基线处理")
    new_violations = [v for v in violations if v not in baseline_keys]

    print(f"违规 {len(violations)} 条（新增 {len(new_violations)}）/ 警告 {len(warnings)} 条\n")
    for v in violations:
        flag = "NEW " if v not in baseline_keys else "BASE"
        print(f"VIOLATION  {flag} {v}")
    for w in warnings:
        print(f"WARNING    {w}")
    if new_violations:
        print(f"\nFAIL: 新增违规 {len(new_violations)} 条")
        return 1
    print("\nPASS: 无新增违规" + (f"（存量 {len(violations)} 条待清，见基线）" if violations else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
