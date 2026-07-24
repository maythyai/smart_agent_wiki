"""Knowledge feedback domain models.

Defines structured knowledge challenge and correction protocols:
- Issues: lightweight feedback (challenge, request, suggestion)
- Change Requests: heavyweight modifications requiring approval
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from saw.domain.utils import utcnow


class IssueType(str, Enum):
    """Type of knowledge issue."""

    CHALLENGE = "challenge"  # Content contradicts known facts
    REQUEST = "request"  # Knowledge gap (needed but missing)
    SUGGESTION = "suggestion"  # Improvement idea


class IssueStatus(str, Enum):
    """Issue lifecycle status."""

    OPEN = "open"
    DISCUSSING = "discussing"
    RESOLVED = "resolved"
    WONTFIX = "wontfix"


class CRStatus(str, Enum):
    """Change Request lifecycle status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass
class IssueComment:
    """A comment on a knowledge issue."""

    author: str
    content: str
    created: datetime = field(default_factory=utcnow)


@dataclass
class KnowledgeIssue:
    """A structured knowledge feedback item."""

    id: str
    type: IssueType
    title: str
    description: str
    affected_pages: list[str] = field(default_factory=list)
    reporter: str = ""
    status: IssueStatus = IssueStatus.OPEN
    comments: list[IssueComment] = field(default_factory=list)
    linked_cr: Optional[str] = None
    created: datetime = field(default_factory=utcnow)
    resolved_at: Optional[datetime] = None

    def add_comment(self, author: str, content: str) -> IssueComment:
        comment = IssueComment(author=author, content=content)
        self.comments.append(comment)
        if self.status == IssueStatus.OPEN:
            self.status = IssueStatus.DISCUSSING
        return comment

    def resolve(self) -> None:
        self.status = IssueStatus.RESOLVED
        self.resolved_at = utcnow()


@dataclass
class ChangeRequest:
    """A structured knowledge change request requiring approval.

    Key rule: creator != reviewer (no self-approval).
    """

    id: str
    title: str
    target_page: str
    proposed_content: str
    creator: str
    description: str = ""
    reviewer: Optional[str] = None
    status: CRStatus = CRStatus.PENDING
    review_comment: str = ""
    linked_issue: Optional[str] = None
    created: datetime = field(default_factory=utcnow)
    reviewed_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None

    def approve(self, reviewer: str, comment: str = "") -> None:
        """Approve the CR. Reviewer must differ from creator."""
        if reviewer == self.creator:
            raise ValueError("Self-approval is forbidden: reviewer must differ from creator")
        self.reviewer = reviewer
        self.status = CRStatus.APPROVED
        self.review_comment = comment
        self.reviewed_at = utcnow()

    def reject(self, reviewer: str, comment: str = "") -> None:
        """Reject the CR."""
        if reviewer == self.creator:
            raise ValueError("Self-review is forbidden: reviewer must differ from creator")
        self.reviewer = reviewer
        self.status = CRStatus.REJECTED
        self.review_comment = comment
        self.reviewed_at = utcnow()

    def mark_applied(self) -> None:
        """Mark CR as applied after page update."""
        if self.status != CRStatus.APPROVED:
            raise ValueError(f"Cannot apply CR in status {self.status.value}")
        self.status = CRStatus.APPLIED
        self.applied_at = utcnow()


@dataclass
class FeedbackDecision:
    """Decision on how to handle a knowledge update based on certainty."""

    certainty: float  # 0.0 - 1.0
    action: str  # direct_update | create_cr | create_issue | annotate_only
    reason: str

    @classmethod
    def decide(cls, certainty: float, is_stable: bool) -> FeedbackDecision:
        """Apply the decision matrix."""
        if certainty > 0.9:
            if is_stable:
                return cls(certainty, "create_cr", "High certainty but stable knowledge requires approval")
            return cls(certainty, "direct_update", "High certainty + fresh knowledge: direct update")
        elif certainty >= 0.6:
            return cls(certainty, "create_issue", "Medium certainty: open issue for discussion")
        else:
            return cls(certainty, "annotate_only", "Low certainty: annotate only, do not modify")
