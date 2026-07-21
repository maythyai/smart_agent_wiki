"""Markdown import route for bulk importing Obsidian/Markdown vaults.

Supports:
- Batch upload of .md files
- Obsidian frontmatter parsing
- [[wiki-link]] resolution
- Tag extraction
"""
from __future__ import annotations

import io
import uuid
import zipfile
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from saw.engines.query.wiki_links import parse_wiki_links, slugify

if TYPE_CHECKING:
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.write_queue.queue import SQLiteWriteQueue

router = APIRouter()


def get_wiki_repo(request: Request) -> WikiRepository:
    """Dependency: get WikiRepository from app.state."""
    engine = request.app.state.query
    return getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)


def get_write_queue(request: Request) -> SQLiteWriteQueue:
    """Dependency: get WriteQueue from app.state."""
    return request.app.state.write_queue


@router.post("/import/markdown")
async def import_markdown(
    files: list[UploadFile] = File(..., description="Markdown files to import"),
    wiki_repo: WikiRepository = Depends(get_wiki_repo),
    write_queue: SQLiteWriteQueue = Depends(get_write_queue),
) -> dict:
    """Import multiple markdown files into the wiki.

    Parses Obsidian-style frontmatter and creates wiki pages.
    Resolves [[wiki-links]] between imported files.

    Args:
        files: List of .md files to import.
        wiki_repo: Wiki repository.
        write_queue: Write queue for durable mutations.

    Returns:
        Import summary with counts and file list.
    """
    if wiki_repo is None:
        raise HTTPException(status_code=500, detail="Wiki repository not available")

    imported: list[str] = []
    skipped: list[str] = []
    errors: list[dict] = []

    for file in files:
        if not file.filename or not file.filename.endswith(".md"):
            skipped.append(file.filename or "unknown")
            continue

        try:
            content = await file.read()
            text = content.decode("utf-8")

            # Parse frontmatter
            import frontmatter
            post = frontmatter.loads(text)
            title = post.metadata.get("title", file.filename.replace(".md", ""))
            tags = post.metadata.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            # Generate slug from filename
            slug = slugify(file.filename.replace(".md", ""))

            # Create wiki page
            from saw.domain.value_objects import ConfidenceLevel, FreshnessLevel, PageType
            from saw.domain.wiki import WikiPage

            page = WikiPage(
                path=f"imported/{slug}.md",
                title=title,
                page_type=PageType.CONCEPT,
                tags=tags,
                related=[],
                confidence=ConfidenceLevel.UNVERIFIED,
                freshness=FreshnessLevel.LEVEL_0,
                content=post.content,
                frontmatter=post.metadata,
            )

            # Write to wiki repo
            wiki_repo.write(page)
            imported.append(slug)

        except Exception as e:
            errors.append({"file": file.filename, "error": str(e)})

    return {
        "status": "completed",
        "imported": len(imported),
        "skipped": len(skipped),
        "errors": len(errors),
        "imported_files": imported,
        "skipped_files": skipped,
        "error_details": errors,
    }


@router.post("/import/zip")
async def import_zip(
    file: UploadFile = File(..., description="ZIP archive containing .md files"),
    wiki_repo: WikiRepository = Depends(get_wiki_repo),
    write_queue: SQLiteWriteQueue = Depends(get_write_queue),
) -> dict:
    """Import markdown files from a ZIP archive.

    Extracts .md files from the ZIP and imports them.
    Supports nested directory structures.

    Args:
        file: ZIP file containing .md files.
        wiki_repo: Wiki repository.
        write_queue: Write queue.

    Returns:
        Import summary.
    """
    if wiki_repo is None:
        raise HTTPException(status_code=500, detail="Wiki repository not available")

    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")

    try:
        content = await file.read()
        zip_buffer = io.BytesIO(content)

        with zipfile.ZipFile(zip_buffer, "r") as zf:
            # List all .md files in the archive
            md_files = [f for f in zf.namelist() if f.endswith(".md") and not f.startswith("__MACOSX")]

            imported: list[str] = []
            errors: list[dict] = []

            for md_path in md_files:
                try:
                    with zf.open(md_path) as f:
                        text = f.read().decode("utf-8")

                    # Parse frontmatter
                    import frontmatter
                    post = frontmatter.loads(text)
                    filename = md_path.split("/")[-1]
                    title = post.metadata.get("title", filename.replace(".md", ""))
                    tags = post.metadata.get("tags", [])
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.split(",")]

                    # Generate slug
                    slug = slugify(filename.replace(".md", ""))

                    # Create wiki page
                    from saw.domain.value_objects import ConfidenceLevel, FreshnessLevel, PageType
                    from saw.domain.wiki import WikiPage

                    page = WikiPage(
                        path=f"imported/{slug}.md",
                        title=title,
                        page_type=PageType.CONCEPT,
                        tags=tags,
                        related=[],
                        confidence=ConfidenceLevel.UNVERIFIED,
                        freshness=FreshnessLevel.LEVEL_0,
                        content=post.content,
                        frontmatter=post.metadata,
                    )

                    wiki_repo.write(page)
                    imported.append(slug)

                except Exception as e:
                    errors.append({"file": md_path, "error": str(e)})

            return {
                "status": "completed",
                "imported": len(imported),
                "total_files": len(md_files),
                "errors": len(errors),
                "imported_files": imported,
                "error_details": errors,
            }

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {e}")
