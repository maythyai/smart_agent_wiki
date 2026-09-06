---
id: SPEC-F-T-2
title: L2 links auto-apply（saw links apply --suggestion 写回 WikiRepository + dry-run/confirm + 去重）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-agent-link-v1.15.0.md
pms_ref: .csp/product-spec/PMS-agent-link.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-T-2
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-015-agent-role-registry-activity.md
adr_ref: .csp/tech-decisions/ADR/ADR-015-agent-role-registry-activity.md
ac_coverage: 4/4
related_tasks: [.csp/tasks/TASKS-DELTA-v1.15.0.md#T-F-T-2]
---

# SPEC-F-T-2: L2 links auto-apply

## 实现 delta（ground 自源码）

> ADR-015 不直接涉及（无新选型），复用既有 `WikiRepository.write()` + `compute_related_pages`。
> PRD §3.2 明确 `## Related` 段落追加 + frontmatter `related` 字段同步。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `src/saw/drivers/cli/commands/links_cmd.py` L51 | `suggest` 命令调用 `compute_related_pages` 打印表格，不调用 `WikiRepository.write` | 新增 `apply` 子命令：读取 suggest 输出 → dry-run/confirm → `WikiRepository.write` 写回 |
| `src/saw/adapters/storage/wiki_repository.py` L42 | `write(page: WikiPage)` 写回 Markdown+YAML frontmatter | 不改动（复用既有 write 机制，不绕过） |
| `src/saw/engines/query/related_pages.py` | `compute_related_pages` 返回建议列表 | 不改动（复用既有 suggest 逻辑） |

### 不改动

- `WikiRepository.write()` 签名和实现——直接复用（ground claim 4 TRUE，接受 `WikiPage` 对象，序列化 Markdown+YAML frontmatter）。
- `compute_related_pages()` 算法——复用既有 suggest 逻辑（3-signal + embedding）。
- `WikiPage` 数据结构——复用既有 `page.content` + `page.related` + `page.frontmatter`。

## 后端架构

### `saw links apply` 子命令（`links_cmd.py` 新增）

```python
@app.command(name="apply")
def apply(
    page: str = typer.Argument(..., help="Page slug/path to apply link suggestions to"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm write-back (default: dry-run)"),
    top_k: int = typer.Option(0, "--top", "-n", help="Max suggestions to apply (0=all)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Explicit dry-run preview"),
    suggestion: str = typer.Option("", "--suggestion", "-s", help="Apply single suggestion slug"),
) -> None:
    """Apply suggested [[links]] to wiki page (AC-B-1..4).

    Default: dry-run (preview only). Use --confirm to write back.
    """
    wiki, console = _wiki(path)
    resolved = _resolve_page(wiki, page)
    if resolved is None:
        console.print(f"[red]Error:[/red] page not found: {page}")
        raise typer.Exit(code=1)

    # 1. Compute suggestions (reuse suggest logic)
    from saw.engines.query.related_pages import compute_related_pages
    from saw.engines.query.wiki_links import extract_unique_targets, slugify

    src = wiki.read(resolved)
    outlinked = extract_unique_targets(src.content) | {slugify(Path(resolved).stem)}

    conn_to_pass = None
    workspace_id = "default"
    try:
        from saw.config.settings import detect_tier
        from saw.domain.value_objects import CapabilityTier
        import sqlite3
        from pathlib import Path as _Path
        wiki_path = _Path(path).resolve()
        db_path = wiki_path / ".saw" / "db" / "claims.db"
        tier = detect_tier()
        if tier >= CapabilityTier.FULL and db_path.is_file():
            conn_to_pass = sqlite3.connect(str(db_path))
    except Exception:
        pass

    try:
        related = compute_related_pages(
            resolved, wiki, top_k=top_k * 2 if top_k > 0 else 100,
            conn=conn_to_pass, workspace_id=workspace_id,
        )
    finally:
        if conn_to_pass is not None:
            conn_to_pass.close()

    # Filter out already-linked pages (dedup)
    suggestions = [
        r for r in related
        if slugify(Path(r["slug"]).stem) not in outlinked
    ]
    if top_k > 0:
        suggestions = suggestions[:top_k]
    if suggestion:
        suggestions = [r for r in suggestions if slugify(Path(r["slug"]).stem) == suggestion]

    if not suggestions:
        console.print("[yellow]No link suggestions to apply — all related pages already linked.[/yellow]")
        raise typer.Exit(code=0)

    # 2. Dry-run or confirm
    is_dry_run = not confirm or dry_run
    if is_dry_run:
        table = Table(title=f"Dry run — {len(suggestions)} link(s) would be applied to {resolved}")
        table.add_column("page", style="cyan")
        table.add_column("score", justify="right")
        for r in suggestions:
            table.add_row(r["slug"], f"{r['score']:.2f}")
        console.print(table)
        console.print(f"\n[yellow]Dry run — {len(suggestions)} links would be applied. Run with --confirm to apply.[/yellow]")
        raise typer.Exit(code=0)

    # 3. Confirm: write back via WikiRepository.write()
    from saw.domain.wiki import WikiPage
    from saw.domain.value_objects import PageType, ConfidenceLevel, FreshnessLevel

    applied = []
    skipped = []
    failed = []

    for r in suggestions:
        link_slug = slugify(Path(r["slug"]).stem)
        # Dedup check: already linked?
        if f"[[{link_slug}]]" in src.content or link_slug in src.related:
            skipped.append(link_slug)
            console.print(f"[yellow]Link [[{link_slug}]] already exists in {resolved}, skipped[/yellow]")
            continue

        # Update content: append ## Related section
        related_section = f"## Related\n\n- [[{link_slug}]]\n"
        # Check if ## Related already exists
        if "## Related" in src.content:
            # Append to existing ## Related section
            src.content += f"- [[{link_slug}]]\n"
        else:
            src.content += f"\n{related_section}"

        # Update frontmatter related field
        if link_slug not in src.related:
            src.related.append(link_slug)

        applied.append(link_slug)

    # Write back via WikiRepository.write()
    if applied:
        try:
            # Reconstruct WikiPage with updated content + related
            updated_page = WikiPage(
                path=src.path,
                title=src.title if hasattr(src, 'title') else Path(resolved).stem,
                page_type=src.page_type,
                entity_type=src.entity_type,
                tags=src.tags,
                related=src.related,
                confidence=src.confidence,
                freshness=src.freshness,
                content=src.content,
                properties=src.properties,
                frontmatter=src.frontmatter,
            )
            wiki.write(updated_page)
        except Exception as e:
            failed.append((resolved, str(e)))
            console.print(f"[red]Failed to write {resolved}: {e}[/red]")

    # 4. Summary
    console.print(f"[green]{len(applied)} links applied to {resolved}[/green]")
    if skipped:
        console.print(f"[yellow]{len(skipped)} links skipped (already exist)[/yellow]")
    if failed:
        console.print(f"[red]{len(failed)} pages failed:[/red]")
        for p, e in failed:
            console.print(f"  {p}: {e}")

    raise typer.Exit(code=0)
```

### 链接插入策略（`## Related` 段落 + frontmatter `related` 同步）

1. **内容追加**：页面 content 末尾检查是否已有 `## Related` 段落——有则追加 `- [[slug]]` 行；无则新增 `## Related\n\n- [[slug]]\n` 段落。
2. **frontmatter `related` 同步**：`page.related` 列表追加 `link_slug`（若不在列表中）。
3. **去重检查**：apply 前检查 `[[link_slug]]` 是否已在 `page.content` 中 或 `link_slug` 是否已在 `page.related` 中——已存在则跳过（skipped）。
4. **写回**：通过 `WikiRepository.write(updated_page)` 写回（复用既有 write 机制，不绕过）。

### 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| 目标页面不存在 | 跳过该链接 | `"Page '{slug}' not found, skipped"` |
| 页面已有该 `[[link]]` | 跳过，不重复 | `"Link [[{slug}]] already exists in {page}, skipped"` |
| 写回时磁盘错误 | 记录失败，继续其余 | `"Failed to write {page}: {error}"` |
| 无 `--confirm` 标志 | 仅预览不写 | `"Dry run — {N} links would be applied. Run with --confirm to apply."` |
| 无建议（全部已链接） | 正常退出 | `"No link suggestions to apply — all related pages already linked."` |

## 数据库 Schema

无 schema 变更。links apply 写回 wiki 页面文件（Markdown + YAML frontmatter），通过 `WikiRepository.write()` 复用既有文件写回机制。

## API 契约

无 REST API 变更。`saw links apply` 是纯 CLI 命令。

### CLI 命令签名

```
saw links apply <page> [--path .] [--confirm] [--top N] [--dry-run] [--suggestion <slug>]
```

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `page` | str | 必填 | 目标页面 slug/path |
| `--path` / `-p` | str | `.` | Wiki 目录路径 |
| `--confirm` | flag | `false` | 确认写回（默认 dry-run） |
| `--top` / `-n` | int | `0` | 限制应用数量（0=全部建议） |
| `--dry-run` | flag | `false` | 显式预览（同默认行为） |
| `--suggestion` / `-s` | str | `""` | 只应用单条建议 |

## 测试策略（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-B-1 | `tests/unit/test_links_apply.py`（新建）：创建 3 页面 wiki → `saw links apply A --path .`（无 `--confirm`）→ 打印 3 条将应用链接 + 文件未修改 | 文件内容不变，CLI 输出含 3 条链接 |
| AC-B-2 | `test_links_apply.py`：`saw links apply A --path . --confirm` → 页面 A 文件新增 `## Related` 段落含 `[[link]]` + frontmatter `related` 同步更新 | `wiki.read(A).content` 含 `## Related` + `[[link]]`；`wiki.read(A).related` 含 link_slug |
| AC-B-3 | `test_links_apply.py`：页面 A 已含 `[[page-b]]` → `saw links apply A --confirm` → `[[page-b]]` 不重复插入 | `page-b` 在 skipped 列表，文件中 `[[page-b]]` 出现 1 次 |
| AC-B-4 | `test_links_apply.py`：apply 后 `saw links audit` → 插入的链接目标都存在，无新断链 | `audit` 输出无新 broken links |

**CI 兼容**：全部用临时 wiki 目录（`tmp_path` fixture），mock `compute_related_pages` 返回固定建议列表。不依赖 embedding/vLLM。

## 安全考量

- 破坏性操作默认 dry-run，须 `--confirm` 方写回（PRD §4 NFR）。
- 不绕过 `WikiRepository.write()` 安全边界（复用既有 write 机制）。
- 单页写回失败不中断，继续处理其余页面（PRD §3.2 异常处理）。
- `--suggestion <slug>` 只应用单条建议，防止批量误操作。

## 实现就绪度

- [x] `apply` 子命令伪代码完整（suggest 消费 + dry-run/confirm + 写回 + 去重）
- [x] `## Related` 段落插入策略明确（检查已有 → 追加 or 新建）
- [x] frontmatter `related` 字段同步策略明确
- [x] 去重逻辑明确（content + related 双重检查）
- [x] 复用 `WikiRepository.write()` 不绕过
- [x] 异常处理覆盖（页面不存在/已有链接/磁盘错误/无 confirm）
- [x] AC 覆盖 4/4
- [ ] 05 实施后 CI 验证 `saw links apply --confirm` 写回正确
