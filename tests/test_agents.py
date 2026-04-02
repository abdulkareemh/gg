"""Tests for agent router and intent routing."""

import pytest

from src.agents.router import AgentRouter, INTENT_AGENT_MAP
from src.nlp.syrian_arabic import detect_intent


class TestAgentRouter:
    def setup_method(self):
        self.router = AgentRouter()

    def test_all_intents_mapped(self):
        """Every known intent should map to an agent."""
        from src.nlp.syrian_arabic import INTENT_KEYWORDS
        for intent in INTENT_KEYWORDS:
            assert intent in INTENT_AGENT_MAP, f"Intent '{intent}' not mapped to an agent"

    def test_agents_initialized(self):
        """All agent types should be available."""
        assert "order" in self.router.agents
        assert "crm" in self.router.agents
        assert "inventory" in self.router.agents

    @pytest.mark.asyncio
    async def test_route_greeting(self):
        """Greeting should route to CRM agent."""
        response = await self.router.route(1, "مرحبا", {})
        assert response is not None
        assert response.text_ar  # Should have Arabic response

    @pytest.mark.asyncio
    async def test_route_unknown_low_confidence(self):
        """Unknown message should ask for clarification."""
        response = await self.router.route(1, "xyz123random", {})
        assert response.action == "clarify"

    @pytest.mark.asyncio
    async def test_route_order_check(self):
        """Order check should route to order agent."""
        context = {"last_order": {"id": 42, "status": "preparing"}}
        response = await self.router.route(1, "وين طلبيتي", context)
        assert response.action == "check_order"
