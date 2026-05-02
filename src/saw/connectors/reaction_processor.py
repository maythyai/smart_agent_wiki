"""Message reaction to confidence signal mapping.

Plan 11-03: IM message handling and sync API endpoints.
Per IM-05: Handle message reactions as confidence signals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReactionConfig:
    """Configuration for reaction processing.

    Attributes:
        positive_emojis: Dict mapping emoji to positive weight.
        negative_emojis: Dict mapping emoji to negative weight.
        neutral_emojis: Set of neutral emoji (no confidence impact).
        min_reaction_count: Minimum reactions to affect confidence.
        max_confidence_delta: Maximum confidence adjustment.
    """

    positive_emojis: dict[str, float] = field(default_factory=lambda: {
        "👍": 1.0,
        "👍🏻": 1.0,
        "thumbsup": 1.0,
        "+1": 1.0,
        "✅": 0.8,
        "❤️": 0.5,
        "💯": 0.7,
        "🎯": 0.6,
    })

    negative_emojis: dict[str, float] = field(default_factory=lambda: {
        "👎": -1.0,
        "👎🏻": -1.0,
        "thumbsdown": -1.0,
        "-1": -1.0,
        "❌": -0.8,
        "🚫": -0.7,
    })

    neutral_emojis: set[str] = field(default_factory=lambda: {
        "👀",
        "🤔",
        "💭",
        "👀",
        "😀",
    })

    min_reaction_count: int = 1
    max_confidence_delta: float = 0.3


@dataclass
class ReactionResult:
    """Result of reaction processing.

    Attributes:
        confidence_delta: Confidence adjustment (-1.0 to 1.0).
        positive_count: Total positive reactions.
        negative_count: Total negative reactions.
        neutral_count: Total neutral reactions.
        weighted_score: Weighted sum of reactions.
        contributors: Dict of emoji to count.
    """

    confidence_delta: float = 0.0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    weighted_score: float = 0.0
    contributors: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "confidence_delta": self.confidence_delta,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "weighted_score": self.weighted_score,
            "contributors": self.contributors,
        }


class ReactionProcessor:
    """Processes message reactions as confidence signals.

    Per IM-05: Handle message reactions as confidence signals.
    """

    def __init__(self, config: Optional[ReactionConfig] = None) -> None:
        """Initialize reaction processor.

        Args:
            config: Reaction configuration.
        """
        self._config = config or ReactionConfig()

    def process_reactions(self, reactions: dict[str, int]) -> ReactionResult:
        """Process reactions into confidence adjustment.

        Args:
            reactions: Dict mapping emoji to reaction count.

        Returns:
            ReactionResult with confidence delta and breakdown.
        """
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        weighted_score = 0.0
        contributors: dict[str, int] = {}

        for emoji, count in reactions.items():
            category = self.categorize_emoji(emoji)
            contributors[emoji] = count

            if category == "positive":
                weight = self._config.positive_emojis.get(emoji, 0.0)
                positive_count += count
                weighted_score += weight * count

            elif category == "negative":
                weight = self._config.negative_emojis.get(emoji, 0.0)
                negative_count += count
                weighted_score += weight * count  # weight is negative

            elif category == "neutral":
                neutral_count += count

        # Apply min_reaction_count filter
        total_significant = positive_count + negative_count
        if total_significant < self._config.min_reaction_count:
            return ReactionResult(
                positive_count=positive_count,
                negative_count=negative_count,
                neutral_count=neutral_count,
                weighted_score=weighted_score,
                contributors=contributors,
            )

        # Calculate confidence delta (normalized)
        # weighted_score can range from -total_count to +total_count
        # We want delta in range [-1, 1]
        max_possible = total_significant
        if max_possible > 0:
            raw_delta = weighted_score / max_possible
        else:
            raw_delta = 0.0

        # Cap at max_confidence_delta
        delta = max(-self._config.max_confidence_delta,
                    min(self._config.max_confidence_delta, raw_delta))

        return ReactionResult(
            confidence_delta=delta,
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            weighted_score=weighted_score,
            contributors=contributors,
        )

    def get_confidence_adjustment(
        self,
        reactions: dict[str, int],
        base_confidence: float,
    ) -> float:
        """Adjust base confidence by reaction delta.

        Args:
            reactions: Dict mapping emoji to reaction count.
            base_confidence: Current confidence (0.0 to 1.0).

        Returns:
            Adjusted confidence (clamped to 0.0-1.0).
        """
        result = self.process_reactions(reactions)

        # Apply delta to base confidence
        adjusted = base_confidence + result.confidence_delta

        # Clamp to valid range
        return max(0.0, min(1.0, adjusted))

    def is_significant(self, reactions: dict[str, int]) -> bool:
        """Check if reactions are significant enough to affect confidence.

        Args:
            reactions: Dict mapping emoji to reaction count.

        Returns:
            True if reactions exceed min_reaction_count.
        """
        result = self.process_reactions(reactions)
        total_significant = result.positive_count + result.negative_count
        return total_significant >= self._config.min_reaction_count

    def categorize_emoji(self, emoji: str) -> str:
        """Categorize emoji as positive, negative, or neutral.

        Args:
            emoji: Emoji string to categorize.

        Returns:
            Category string: "positive", "negative", "neutral", or "unknown".
        """
        if emoji in self._config.positive_emojis:
            return "positive"
        elif emoji in self._config.negative_emojis:
            return "negative"
        elif emoji in self._config.neutral_emojis:
            return "neutral"
        else:
            return "unknown"

    def get_positive_emojis(self) -> dict[str, float]:
        """Get configured positive emoji weights."""
        return self._config.positive_emojis.copy()

    def get_negative_emojis(self) -> dict[str, float]:
        """Get configured negative emoji weights."""
        return self._config.negative_emojis.copy()

    def add_custom_emoji(
        self,
        emoji: str,
        weight: float,
        category: str,
    ) -> None:
        """Add a custom emoji configuration.

        Args:
            emoji: Emoji to add.
            weight: Weight (positive or negative).
            category: "positive" or "negative".
        """
        if category == "positive":
            self._config.positive_emojis[emoji] = abs(weight)
        elif category == "negative":
            self._config.negative_emojis[emoji] = -abs(weight)
        elif category == "neutral":
            self._config.neutral_emojis.add(emoji)
