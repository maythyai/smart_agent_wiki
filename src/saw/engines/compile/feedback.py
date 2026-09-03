"""Knowledge feedback engine.

Manages structured knowledge challenge and correction protocols:
- Issues: lightweight feedback (challenge, request, suggestion)
- Change Requests: heavyweight modifications requiring approval (creator != reviewer)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from saw.domain.feedback import (
    ChangeRequest,
    CRStatus,
    FeedbackDecision,
    IssueComment,
    IssueStatus,
    IssueType,
    KnowledgeIssue,
)
from saw.domain.concept import KnowledgeStability


class FeedbackEngine:
    """Knowledge feedback and correction engine.

    Provides structured protocols for:
    - Challenging incorrect knowledge (Issue)
    - Requesting missing knowledge (Issue)
    - Suggesting improvements (Issue)
    - Proposing modifications with approval (CR)

    Key governance rules:
    - AI agents cannot self-approve (creator != reviewer)
    - Stable knowledge requires CR approval for modifications
    - Fresh knowledge can be directly updated by AI
    """

    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._issues: list[KnowledgeIssue] = []
        self._crs: list[ChangeRequest] = []
        self._load()

    def _load(self) -> None:
        """Load feedback data from storage."""
        if not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text(encoding="utf-8"))
            for i in data.get("issues", []):
                issue = KnowledgeIssue(
                    id=i["id"],
                    type=IssueType(i["type"]),
                    title=i["title"],
                    description=i["description"],
                    affected_pages=i.get("affected_pages", []),
                    reporter=i.get("reporter", ""),
                    status=IssueStatus(i.get("status", "open")),
                    linked_cr=i.get("linked_cr"),
                )
                for c in i.get("comments", []):
                    issue.comments.append(IssueComment(
                        author=c["author"],
                        content=c["content"],
                    ))
                self._issues.append(issue)

            for cr in data.get("change_requests", []):
                self._crs.append(ChangeRequest(
                    id=cr["id"],
                    title=cr["title"],
                    target_page=cr["target_page"],
                    proposed_content=cr["proposed_content"],
                    creator=cr["creator"],
                    description=cr.get("description", ""),
                    reviewer=cr.get("reviewer"),
                    status=CRStatus(cr.get("status", "pending")),
                    review_comment=cr.get("review_comment", ""),
                    linked_issue=cr.get("linked_issue"),
                ))
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    def _save(self) -> None:
        """Persist feedback data."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "issues": [
                {
                    "id": i.id,
                    "type": i.type.value,
                    "title": i.title,
                    "description": i.description,
                    "affected_pages": i.affected_pages,
                    "reporter": i.reporter,
                    "status": i.status.value,
                    "linked_cr": i.linked_cr,
                    "comments": [
                        {"author": c.author, "content": c.content}
                        for c in i.comments
                    ],
                }
                for i in self._issues
            ],
            "change_requests": [
                {
                    "id": cr.id,
                    "title": cr.title,
                    "target_page": cr.target_page,
                    "proposed_content": cr.proposed_content,
                    "creator": cr.creator,
                    "description": cr.description,
                    "reviewer": cr.reviewer,
                    "status": cr.status.value,
                    "review_comment": cr.review_comment,
                    "linked_issue": cr.linked_issue,
                }
                for cr in self._crs
            ],
        }
        self._storage_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # ─── Issue operations ──────────────────────────────────────────────

    def create_issue(
        self,
        issue_type: IssueType,
        title: str,
        description: str,
        affected_pages: list[str],
        reporter: str,
    ) -> KnowledgeIssue:
        """Create a new knowledge issue."""
        issue = KnowledgeIssue(
            id=str(uuid.uuid4())[:8],
            type=issue_type,
            title=title,
            description=description,
            affected_pages=affected_pages,
            reporter=reporter,
        )
        self._issues.append(issue)
        self._save()
        return issue

    def comment_issue(self, issue_id: str, author: str, content: str) -> Optional[IssueComment]:
        """Add a comment to an issue."""
        issue = self._get_issue(issue_id)
        if not issue:
            return None
        comment = issue.add_comment(author, content)
        self._save()
        return comment

    def resolve_issue(self, issue_id: str) -> bool:
        """Resolve an issue."""
        issue = self._get_issue(issue_id)
        if not issue:
            return False
        issue.resolve()
        self._save()
        return True

    def list_issues(
        self,
        status: Optional[IssueStatus] = None,
        issue_type: Optional[IssueType] = None,
    ) -> list[KnowledgeIssue]:
        """List issues with optional filters."""
        results = self._issues
        if status:
            results = [i for i in results if i.status == status]
        if issue_type:
            results = [i for i in results if i.type == issue_type]
        return results

    def get_issue(self, issue_id: str) -> Optional[KnowledgeIssue]:
        """Get a single issue by ID."""
        return self._get_issue(issue_id)

    # ─── CR operations ─────────────────────────────────────────────────

    def create_cr(
        self,
        title: str,
        target_page: str,
        proposed_content: str,
        creator: str,
        description: str = "",
        linked_issue: Optional[str] = None,
    ) -> ChangeRequest:
        """Create a new change request."""
        cr = ChangeRequest(
            id=str(uuid.uuid4())[:8],
            title=title,
            target_page=target_page,
            proposed_content=proposed_content,
            creator=creator,
            description=description,
            linked_issue=linked_issue,
        )
        self._crs.append(cr)
        self._save()
        return cr

    def review_cr(
        self, cr_id: str, reviewer: str, approved: bool, comment: str = ""
    ) -> Optional[ChangeRequest]:
        """Review a CR. Enforces creator != reviewer."""
        cr = self._get_cr(cr_id)
        if not cr:
            return None
        if approved:
            cr.approve(reviewer, comment)
        else:
            cr.reject(reviewer, comment)
        self._save()
        return cr

    def apply_cr(self, cr_id: str) -> Optional[ChangeRequest]:
        """Mark a CR as applied (after page update is done externally)."""
        cr = self._get_cr(cr_id)
        if not cr:
            return None
        cr.mark_applied()
        self._save()
        return cr

    def list_crs(
        self, status: Optional[CRStatus] = None
    ) -> list[ChangeRequest]:
        """List CRs with optional status filter."""
        if status:
            return [cr for cr in self._crs if cr.status == status]
        return self._crs

    def get_cr(self, cr_id: str) -> Optional[ChangeRequest]:
        """Get a single CR by ID."""
        return self._get_cr(cr_id)

    # ─── Decision support ──────────────────────────────────────────────

    def decide_action(
        self, certainty: float, stability: KnowledgeStability
    ) -> FeedbackDecision:
        """Decide feedback action based on certainty and knowledge stability."""
        return FeedbackDecision.decide(certainty, stability == KnowledgeStability.STABLE)

    # ─── Helpers ───────────────────────────────────────────────────────

    def _get_issue(self, issue_id: str) -> Optional[KnowledgeIssue]:
        for issue in self._issues:
            if issue.id == issue_id:
                return issue
        return None

    def _get_cr(self, cr_id: str) -> Optional[ChangeRequest]:
        for cr in self._crs:
            if cr.id == cr_id:
                return cr
        return None
