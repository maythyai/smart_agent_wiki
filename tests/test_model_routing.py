"""Tests for AgentDispatcher and model routing.

Per PLAN.md Task 3: Model routing and fallback logic.
"""
from __future__ import annotations

import pytest


class TestAgentDispatcher:
    """Tests for AgentDispatcher model routing."""

    def test_dispatcher_maps_haiku_to_correct_model(self):
        """Test 1: AgentDispatcher maps model_tier='haiku' to 'claude-3-5-haiku-latest'."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher, ModelTier

        dispatcher = AgentDispatcher(llm_router=None, agents={})
        model = dispatcher.get_model_for_tier(ModelTier.HAIKU)
        assert model == "claude-3-5-haiku-latest"

    def test_dispatcher_maps_sonnet_to_correct_model(self):
        """Test 2: AgentDispatcher maps model_tier='sonnet' to 'claude-sonnet-4-20250514'."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher, ModelTier

        dispatcher = AgentDispatcher(llm_router=None, agents={})
        model = dispatcher.get_model_for_tier(ModelTier.SONNET)
        assert model == "claude-sonnet-4-20250514"

    def test_dispatcher_maps_opus_to_correct_model(self):
        """Test 3: AgentDispatcher maps model_tier='opus' to 'claude-opus-4-20250514'."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher, ModelTier

        dispatcher = AgentDispatcher(llm_router=None, agents={})
        model = dispatcher.get_model_for_tier(ModelTier.OPUS)
        assert model == "claude-opus-4-20250514"

    def test_dispatcher_fallback_order_opus_to_sonnet(self):
        """Test 4: When Opus unavailable, dispatcher falls back to Sonnet."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher, ModelTier, FALLBACK_ORDER

        # Opus should fallback to Sonnet first
        fallbacks = FALLBACK_ORDER.get(ModelTier.OPUS, [])
        assert ModelTier.SONNET in fallbacks
        assert ModelTier.HAIKU in fallbacks
        # Sonnet should be first fallback
        assert fallbacks[0] == ModelTier.SONNET

    def test_dispatcher_fallback_order_sonnet_to_haiku(self):
        """Test 5: When Sonnet unavailable, dispatcher falls back to Haiku."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher, ModelTier, FALLBACK_ORDER

        # Sonnet should fallback to Haiku
        fallbacks = FALLBACK_ORDER.get(ModelTier.SONNET, [])
        assert ModelTier.HAIKU in fallbacks
        # Haiku should be first fallback
        assert fallbacks[0] == ModelTier.HAIKU

    def test_dispatcher_config_allowed_fails(self):
        """Test 7: Dispatcher uses allowed_fails=3 (PITFALLS.md recommendation)."""
        from saw.engines.collaborate.dispatcher import DispatcherConfig

        config = DispatcherConfig()
        assert config.allowed_fails == 3

    def test_dispatcher_config_cooldown_time(self):
        """Test dispatcher config has cooldown_time."""
        from saw.engines.collaborate.dispatcher import DispatcherConfig

        config = DispatcherConfig()
        assert config.cooldown_time == 120  # seconds

    def test_dispatcher_config_timeout(self):
        """Test dispatcher config has timeout."""
        from saw.engines.collaborate.dispatcher import DispatcherConfig

        config = DispatcherConfig()
        assert config.timeout == 60  # seconds


class TestModelTier:
    """Tests for ModelTier enum."""

    def test_model_tier_has_haiku(self):
        """Test ModelTier has HAIKU value."""
        from saw.engines.collaborate.dispatcher import ModelTier

        assert ModelTier.HAIKU.value == "haiku"

    def test_model_tier_has_sonnet(self):
        """Test ModelTier has SONNET value."""
        from saw.engines.collaborate.dispatcher import ModelTier

        assert ModelTier.SONNET.value == "sonnet"

    def test_model_tier_has_opus(self):
        """Test ModelTier has OPUS value."""
        from saw.engines.collaborate.dispatcher import ModelTier

        assert ModelTier.OPUS.value == "opus"

    def test_model_tier_has_rule(self):
        """Test ModelTier has RULE value for zero-LLM agents."""
        from saw.engines.collaborate.dispatcher import ModelTier

        assert ModelTier.RULE.value == "rule"


class TestDispatcherIntegration:
    """Integration tests for AgentDispatcher with mock agents."""

    def test_dispatch_raises_for_unknown_agent(self):
        """Test dispatch raises AgentNotFoundError for unknown agent."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher, AgentNotFoundError

        dispatcher = AgentDispatcher(llm_router=None, agents={})

        import asyncio
        from saw.domain.agent import AgentTask, AgentContext

        task = AgentTask(type="test", payload={})
        context = AgentContext(wiki_state={}, claims_context=[])

        with pytest.raises(AgentNotFoundError):
            asyncio.run(dispatcher.dispatch("NonExistent", task, context))

    def test_dispatch_calls_rule_agent_without_llm(self):
        """Test dispatch calls rule-based agent without LLM."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher
        from saw.engines.collaborate.agents.guardian import GuardianAgent
        from saw.domain.agent import AgentTask, AgentContext

        import asyncio

        guardian = GuardianAgent()
        dispatcher = AgentDispatcher(llm_router=None, agents={"Guardian": guardian})

        task = AgentTask(type="check", payload={"action": "read"})
        context = AgentContext(wiki_state={}, claims_context=[])

        result = asyncio.run(dispatcher.dispatch("Guardian", task, context))
        assert result.success is True

    def test_dispatch_returns_metadata_with_tier_used(self):
        """Test dispatch returns metadata with model_tier_used."""
        from saw.engines.collaborate.dispatcher import AgentDispatcher
        from saw.engines.collaborate.agents.guardian import GuardianAgent
        from saw.domain.agent import AgentTask, AgentContext

        import asyncio

        guardian = GuardianAgent()
        dispatcher = AgentDispatcher(llm_router=None, agents={"Guardian": guardian})

        task = AgentTask(type="check", payload={"action": "read"})
        context = AgentContext(wiki_state={}, claims_context=[])

        result = asyncio.run(dispatcher.dispatch("Guardian", task, context))
        # Rule agent should have 'rule' as tier used
        assert result.metadata.get("model_tier_used") == "rule"