"""Lint tiered governance domain models.

Defines the two-tier lint system:
- Auto-fix: issues that can be resolved without human confirmation
- Report-only: issues requiring human judgment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from saw.domain.utils import utcnow


class LintSeverity(str, Enum):
    """Lint finding severity level."""

    AUTO_FIX = "auto_fix"  # Automatically fixable
    WARNING = "warning"  # Needs attention
    ERROR = "error"  # Needs human intervention


class LintCategory(str, Enum):
    """Lint check categories."""

    # Auto-fix categories
    INDEX_CONSISTENCY = "index_consistency"
    BROKEN_LINK = "broken_link"
    SOURCE_VALIDITY = "source_validity"
    SEE_ALSO = "see_also"
    DIR_METADATA = "dir_metadata"
    LOG_FORMAT = "log_format"

    # Report-only categories
    CONTRADICTION = "contradiction"
    STALE_CONTENT = "stale_content"
    ORPHAN_PAGE = "orphan_page"
    MISSING_CONCEPT = "missing_concept"
    CROSS_TOPIC = "cross_topic"
    LOW_CONFIDENCE = "low_confidence"
    ARCHIVE_STALE = "archive_stale"


# Categories that can be auto-fixed
AUTO_FIX_CATEGORIES: frozenset[LintCategory] = frozenset({
    LintCategory.INDEX_CONSISTENCY,
    LintCategory.BROKEN_LINK,
    LintCategory.SOURCE_VALIDITY,
    LintCategory.SEE_ALSO,
    LintCategory.DIR_METADATA,
    LintCategory.LOG_FORMAT,
})

# Categories that are report-only
REPORT_ONLY_CATEGORIES: frozenset[LintCategory] = frozenset({
    LintCategory.CONTRADICTION,
    LintCategory.STALE_CONTENT,
    LintCategory.ORPHAN_PAGE,
    LintCategory.MISSING_CONCEPT,
    LintCategory.CROSS_TOPIC,
    LintCategory.LOW_CONFIDENCE,
    LintCategory.ARCHIVE_STALE,
})


@dataclass
class LintFinding:
    """A single lint finding."""

    category: LintCategory
    severity: LintSeverity
    page: str  # Affected page path
    description: str
    suggestion: str = ""
    auto_fixed: bool = False
    fix_detail: str = ""

    @property
    def is_auto_fixable(self) -> bool:
        return self.category in AUTO_FIX_CATEGORIES


@dataclass
class LintReport:
    """Complete lint report with tiered findings."""

    timestamp: datetime = field(default_factory=utcnow)
    auto_fixed: list[LintFinding] = field(default_factory=list)
    warnings: list[LintFinding] = field(default_factory=list)
    errors: list[LintFinding] = field(default_factory=list)
    exploration_suggestions: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def total_findings(self) -> int:
        return len(self.auto_fixed) + len(self.warnings) + len(self.errors)

    @property
    def health_score(self) -> int:
        """Compute health score 0-100 (higher is better)."""
        if self.total_findings == 0:
            return 100
        penalty = len(self.errors) * 10 + len(self.warnings) * 3
        return max(0, 100 - penalty)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "health_score": self.health_score,
            "total_findings": self.total_findings,
            "auto_fixed": [
                {"category": f.category.value, "page": f.page, "description": f.description, "fix": f.fix_detail}
                for f in self.auto_fixed
            ],
            "warnings": [
                {"category": f.category.value, "page": f.page, "description": f.description, "suggestion": f.suggestion}
                for f in self.warnings
            ],
            "errors": [
                {"category": f.category.value, "page": f.page, "description": f.description, "suggestion": f.suggestion}
                for f in self.errors
            ],
            "exploration_suggestions": self.exploration_suggestions,
            "duration_seconds": self.duration_seconds,
        }
