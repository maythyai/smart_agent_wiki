"""Tests for reaction processor.

Plan 11-03, Task 2: ReactionProcessor.
"""
import pytest

from saw.connectors.reaction_processor import (
    ReactionConfig,
    ReactionResult,
    ReactionProcessor,
)


class TestReactionConfig:
    """Tests for ReactionConfig."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = ReactionConfig()
        assert "👍" in config.positive_emojis
        assert "👎" in config.negative_emojis
        assert "👀" in config.neutral_emojis
        assert config.min_reaction_count == 1
        assert config.max_confidence_delta == 0.3

    def test_config_custom_emojis(self):
        """Test custom emoji configuration."""
        config = ReactionConfig(
            positive_emojis={"✅": 1.0, "🎉": 0.8},
            negative_emojis={"❌": -1.0},
            min_reaction_count=2,
            max_confidence_delta=0.5,
        )
        assert "✅" in config.positive_emojis
        assert "🎉" in config.positive_emojis
        assert config.min_reaction_count == 2


class TestReactionResult:
    """Tests for ReactionResult."""

    def test_result_creation(self):
        """Test creating ReactionResult."""
        result = ReactionResult(
            confidence_delta=0.2,
            positive_count=5,
            negative_count=1,
            weighted_score=4.0,
            contributors={"👍": 5, "👎": 1},
        )
        assert result.confidence_delta == 0.2
        assert result.positive_count == 5
        assert result.negative_count == 1

    def test_result_to_dict(self):
        """Test ReactionResult serialization."""
        result = ReactionResult(
            confidence_delta=-0.1,
            positive_count=2,
            negative_count=3,
            contributors={"👍": 2, "👎": 3},
        )
        d = result.to_dict()
        assert d["confidence_delta"] == -0.1
        assert d["contributors"]["👍"] == 2


class TestReactionProcessor:
    """Tests for ReactionProcessor."""

    @pytest.fixture
    def processor(self):
        """Create ReactionProcessor instance."""
        return ReactionProcessor()

    def test_thumbs_up_positive_boost(self, processor):
        """Test 1: Thumbs up gives positive confidence boost."""
        reactions = {"👍": 5}
        result = processor.process_reactions(reactions)

        assert result.confidence_delta > 0
        assert result.positive_count == 5
        assert result.negative_count == 0

    def test_thumbs_down_negative_confidence(self, processor):
        """Test 2: Thumbs down gives negative confidence."""
        reactions = {"👎": 3}
        result = processor.process_reactions(reactions)

        assert result.confidence_delta < 0
        assert result.positive_count == 0
        assert result.negative_count == 3

    def test_weighted_confidence_multiple_reactions(self, processor):
        """Test 3: Weighted confidence from multiple reactions."""
        reactions = {"👍": 10, "❤️": 5, "👎": 2}
        result = processor.process_reactions(reactions)

        # Positive reactions should outweigh negative
        assert result.confidence_delta > 0
        assert result.positive_count == 15
        assert result.negative_count == 2
        assert result.weighted_score > 0

    def test_custom_emoji_reactions(self, processor):
        """Test 4: Custom emoji reactions are categorized."""
        # Unknown emoji defaults to "unknown"
        category = processor.categorize_emoji("🦄")
        assert category == "unknown"

        # Can add custom emoji
        processor.add_custom_emoji("🦄", 0.5, "positive")
        category = processor.categorize_emoji("🦄")
        assert category == "positive"

        reactions = {"🦄": 3}
        result = processor.process_reactions(reactions)
        assert result.positive_count == 3

    def test_ignores_bot_reactions_below_threshold(self, processor):
        """Test 5: Reactions below min count don't affect confidence (simulating bot filter)."""
        config = ReactionConfig(min_reaction_count=3)
        processor_with_threshold = ReactionProcessor(config)

        # Below threshold - should not affect confidence
        reactions = {"👍": 2}
        result = processor_with_threshold.process_reactions(reactions)

        assert result.confidence_delta == 0.0
        assert result.positive_count == 2  # Still counted

        # Above threshold - should affect confidence
        reactions = {"👍": 5}
        result = processor_with_threshold.process_reactions(reactions)

        assert result.confidence_delta > 0

    def test_capped_confidence_delta(self):
        """Test confidence delta is capped at max."""
        config = ReactionConfig(max_confidence_delta=0.3)
        processor = ReactionProcessor(config)

        # Even with many positive reactions, delta is capped
        reactions = {"👍": 100}
        result = processor.process_reactions(reactions)

        assert result.confidence_delta <= 0.3
        assert result.confidence_delta > 0

    def test_get_confidence_adjustment(self, processor):
        """Test confidence adjustment calculation."""
        reactions = {"👍": 5, "👎": 1}
        base_confidence = 0.5

        adjusted = processor.get_confidence_adjustment(reactions, base_confidence)

        # Should be higher than base (net positive reactions)
        assert adjusted > base_confidence
        # Should be clamped to valid range
        assert 0.0 <= adjusted <= 1.0

    def test_is_significant(self, processor):
        """Test significance check."""
        # Empty reactions
        assert processor.is_significant({}) is False

        # Single reaction (default min is 1)
        assert processor.is_significant({"👍": 1}) is True

    def test_neutral_reactions_no_impact(self, processor):
        """Test neutral reactions don't affect confidence."""
        reactions = {"👀": 10, "🤔": 5}
        result = processor.process_reactions(reactions)

        assert result.neutral_count == 15
        assert result.confidence_delta == 0.0

    def test_mixed_reactions_calculation(self, processor):
        """Test mixed positive and negative reactions."""
        # Equal positive and negative
        reactions = {"👍": 5, "👎": 5}
        result = processor.process_reactions(reactions)

        # Net should be close to zero
        assert abs(result.confidence_delta) < 0.5

    def test_unknown_emoji_ignored(self, processor):
        """Test unknown emoji are ignored."""
        reactions = {"🦄": 10}  # Unknown emoji
        result = processor.process_reactions(reactions)

        # Unknown emoji shouldn't affect counts
        assert result.positive_count == 0
        assert result.negative_count == 0
        assert result.neutral_count == 0