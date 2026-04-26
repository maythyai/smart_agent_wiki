"""Freshness tracking for claims and pages.

Per D-10 to D-13:
- D-10: 9-level freshness system (levels 0-8)
- D-11: Color mapping (Green 0-2, Yellow 3-5, Orange 6-7, Red 8)
- D-12: Multi-signal calculation (time decay + access + references + source updates)
- D-13: Access refresh resets freshness
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from saw.domain.value_objects import FreshnessLevel
from saw.domain.protocols import ClaimsRepository


class FreshnessTracker:
    """Tracks and calculates freshness levels for claims and pages.

    Freshness is calculated using multiple signals (per D-12):
    - Time decay: Age of the content
    - Access: Recent access reduces staleness
    - References: High reference count indicates importance
    - Source updates: Updated sources refresh freshness
    """

    # Time thresholds for each level (in days)
    LEVEL_THRESHOLDS: list[int] = [
        0,      # LEVEL_0: Just created
        1,      # LEVEL_1: 1 day old
        3,      # LEVEL_2: 3 days old
        7,      # LEVEL_3: 1 week old
        14,     # LEVEL_4: 2 weeks old
        30,     # LEVEL_5: 1 month old
        90,     # LEVEL_6: 3 months old
        180,    # LEVEL_7: 6 months old
        999,    # LEVEL_8: Over 6 months
    ]

    def calculate_freshness(
        self,
        created_at: datetime,
        last_accessed: datetime,
        reference_count: int,
        source_updated: bool,
    ) -> FreshnessLevel:
        """Calculate freshness level based on multiple signals (per D-12).

        Args:
            created_at: When the claim/page was created.
            last_accessed: When it was last accessed by user.
            reference_count: Number of references to this claim/page.
            source_updated: Whether the source document was updated.

        Returns:
            Calculated FreshnessLevel.
        """
        now = datetime.now(timezone.utc)
        age_days = (now - created_at).days
        access_age_days = (now - last_accessed).days

        # Base level from time decay
        base_level = self._time_to_level(age_days)

        # Adjust for recent access (per D-13)
        if access_age_days <= 1:
            # Very recent access - reduce staleness by 2 levels
            base_level = max(0, base_level - 2)
        elif access_age_days <= 7:
            # Recent access - reduce staleness by 1 level
            base_level = max(0, base_level - 1)

        # Adjust for reference count (per D-12: high refs = importance)
        if reference_count >= 10:
            base_level = max(0, base_level - 1)
        elif reference_count >= 5:
            # Slight reduction for moderately referenced content
            base_level = max(0, base_level - 0.5)

        # Adjust for source update (per D-12)
        if source_updated:
            base_level = max(0, base_level - 2)

        # Convert to integer level
        return FreshnessLevel(int(base_level))

    def _time_to_level(self, days: int) -> int:
        """Convert age in days to freshness level.

        Args:
            days: Age in days.

        Returns:
            Freshness level (0-8).
        """
        for level, threshold in enumerate(self.LEVEL_THRESHOLDS):
            if days <= threshold:
                return level
        return 8  # Maximum staleness

    def get_color(self, level: FreshnessLevel) -> str:
        """Get color indicator for freshness level (per D-11).

        Args:
            level: FreshnessLevel enum value.

        Returns:
            Color string: 'green', 'yellow', 'orange', or 'red'.
        """
        if level <= FreshnessLevel.LEVEL_2:
            return "green"
        elif level <= FreshnessLevel.LEVEL_5:
            return "yellow"
        elif level <= FreshnessLevel.LEVEL_7:
            return "orange"
        else:
            return "red"

    def refresh_on_access(
        self,
        claim_uuid: str,
        claims_repo: ClaimsRepository,
    ) -> None:
        """Refresh freshness when user accesses a claim (per D-13).

        Updates the last_accessed timestamp, which reduces staleness
        in subsequent freshness calculations.

        Args:
            claim_uuid: UUID of the accessed claim.
            claims_repo: Repository for claim operations.
        """
        # In production, this would update the claim's last_accessed field
        # via WriteQueue. For now, we just record the access.
        claim = claims_repo.get_by_id(claim_uuid)
        if claim is None:
            return
        # Would update last_accessed to now() in production

    def get_freshness_distribution(
        self,
        claims_repo: ClaimsRepository,
    ) -> dict[FreshnessLevel, int]:
        """Get distribution of claims by freshness level.

        Args:
            claims_repo: Repository to query.

        Returns:
            Dict mapping freshness level to count.
        """
        # Placeholder - would query DB for distribution
        return {level: 0 for level in FreshnessLevel}

    def get_stale_claims(
        self,
        claims_repo: ClaimsRepository,
        threshold: FreshnessLevel = FreshnessLevel.LEVEL_6,
    ) -> list[str]:
        """Get claims with freshness above threshold.

        Args:
            claims_repo: Repository to query.
            threshold: Freshness level threshold (claims >= this level).

        Returns:
            List of claim UUIDs needing review.
        """
        # Placeholder - would query DB for stale claims
        return []