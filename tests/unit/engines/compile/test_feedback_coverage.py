"""T-F-R-4: feedback.py coverage tests (coverage ratchet 65→67).

Tests the FeedbackEngine issue/CR lifecycle and persistence.
"""
from __future__ import annotations

from pathlib import Path

from saw.domain.concept import KnowledgeStability
from saw.domain.feedback import CRStatus, IssueStatus, IssueType
from saw.engines.compile.feedback import FeedbackEngine


def _make_engine(tmp_path: Path) -> FeedbackEngine:
    return FeedbackEngine(tmp_path / "feedback.json")


def test_create_issue(tmp_path):
    engine = _make_engine(tmp_path)
    issue = engine.create_issue(
        IssueType.CHALLENGE, "Wrong fact", "description", ["page.md"], "user"
    )
    assert issue.title == "Wrong fact"
    assert issue.status == IssueStatus.OPEN
    assert len(engine.list_issues()) == 1


def test_comment_issue(tmp_path):
    engine = _make_engine(tmp_path)
    issue = engine.create_issue(IssueType.CHALLENGE, "Wrong", "d", [], "user")
    comment = engine.comment_issue(issue.id, "alice", "looks wrong")
    assert comment is not None
    assert comment.content == "looks wrong"
    assert engine.comment_issue("nonexistent", "x", "y") is None


def test_resolve_issue(tmp_path):
    engine = _make_engine(tmp_path)
    issue = engine.create_issue(IssueType.CHALLENGE, "Wrong", "d", [], "user")
    assert engine.resolve_issue(issue.id) is True
    assert engine.get_issue(issue.id).status == IssueStatus.RESOLVED
    assert engine.resolve_issue("nonexistent") is False


def test_list_issues_filtered(tmp_path):
    engine = _make_engine(tmp_path)
    engine.create_issue(IssueType.CHALLENGE, "a", "d", [], "u")
    engine.create_issue(IssueType.SUGGESTION, "b", "d", [], "u")
    assert len(engine.list_issues(issue_type=IssueType.CHALLENGE)) == 1
    assert len(engine.list_issues(issue_type=IssueType.SUGGESTION)) == 1
    assert len(engine.list_issues(status=IssueStatus.OPEN)) == 2


def test_create_cr(tmp_path):
    engine = _make_engine(tmp_path)
    cr = engine.create_cr("Update page", "page.md", "new content", "alice")
    assert cr.title == "Update page"
    assert cr.status == CRStatus.PENDING
    assert len(engine.list_crs()) == 1


def test_review_cr_approve(tmp_path):
    engine = _make_engine(tmp_path)
    cr = engine.create_cr("Title", "page.md", "content", "alice")
    reviewed = engine.review_cr(cr.id, "bob", approved=True, comment="looks good")
    assert reviewed is not None
    assert reviewed.status == CRStatus.APPROVED


def test_review_cr_reject(tmp_path):
    engine = _make_engine(tmp_path)
    cr = engine.create_cr("Title", "page.md", "content", "alice")
    reviewed = engine.review_cr(cr.id, "bob", approved=False, comment="nope")
    assert reviewed is not None
    assert reviewed.status == CRStatus.REJECTED


def test_review_cr_nonexistent(tmp_path):
    engine = _make_engine(tmp_path)
    assert engine.review_cr("nonexistent", "bob", True) is None


def test_apply_cr(tmp_path):
    engine = _make_engine(tmp_path)
    cr = engine.create_cr("Title", "page.md", "content", "alice")
    engine.review_cr(cr.id, "bob", True)
    applied = engine.apply_cr(cr.id)
    assert applied is not None
    assert applied.status == CRStatus.APPLIED


def test_apply_cr_nonexistent(tmp_path):
    engine = _make_engine(tmp_path)
    assert engine.apply_cr("nonexistent") is None


def test_list_crs_filtered(tmp_path):
    engine = _make_engine(tmp_path)
    cr1 = engine.create_cr("a", "p", "c", "u")
    cr2 = engine.create_cr("b", "p", "c", "u")
    engine.review_cr(cr1.id, "rev", True)
    assert len(engine.list_crs(status=CRStatus.APPROVED)) == 1
    assert len(engine.list_crs(status=CRStatus.PENDING)) == 1


def test_get_cr(tmp_path):
    engine = _make_engine(tmp_path)
    cr = engine.create_cr("t", "p", "c", "u")
    assert engine.get_cr(cr.id) is not None
    assert engine.get_cr("nonexistent") is None


def test_persistence_save_load(tmp_path):
    path = tmp_path / "feedback.json"
    engine1 = FeedbackEngine(path)
    issue = engine1.create_issue(IssueType.CHALLENGE, "test", "d", [], "u")
    engine1.create_cr("cr1", "p.md", "content", "alice")
    assert path.exists()
    engine2 = FeedbackEngine(path)
    issues = engine2.list_issues()
    assert len(issues) == 1
    assert issues[0].title == "test"
    crs = engine2.list_crs()
    assert len(crs) == 1


def test_load_corrupt_json(tmp_path):
    path = tmp_path / "feedback.json"
    path.write_text("not valid {{{", encoding="utf-8")
    engine = FeedbackEngine(path)
    assert len(engine.list_issues()) == 0
    assert len(engine.list_crs()) == 0


def test_decide_action(tmp_path):
    engine = _make_engine(tmp_path)
    decision = engine.decide_action(0.9, KnowledgeStability.STABLE)
    assert decision is not None
    decision2 = engine.decide_action(0.3, KnowledgeStability.FRESH)
    assert decision2 is not None


def test_create_cr_with_linked_issue(tmp_path):
    engine = _make_engine(tmp_path)
    issue = engine.create_issue(IssueType.CHALLENGE, "t", "d", [], "u")
    cr = engine.create_cr("fix", "p.md", "content", "alice", linked_issue=issue.id)
    assert cr.linked_issue == issue.id
