"""Agent router — directs incoming messages to the appropriate agent."""

from src.nlp.syrian_arabic import detect_intent, normalize_arabic
from .base_agent import AgentResponse
from .order_agent import OrderAgent
from .crm_agent import CRMAgent
from .inventory_agent import InventoryAgent
from .feedback_agent import FeedbackAgent
from .analytics_agent import AnalyticsAgent


# Map intents to agents
INTENT_AGENT_MAP = {
    "new_order": "order",
    "check_order": "order",
    "cancel_order": "order",
    "view_products": "order",
    "greeting": "crm",
    "inventory_check": "inventory",
    "report": "analytics",
    "payment": "order",
    "help": "crm",
}

# Keywords that trigger specific agents
REPEAT_KEYWORDS = ["كرر", "نفس الطلبية", "كرر طلبيتي", "repeat"]
FEEDBACK_KEYWORDS = ["تقييم", "رأيي", "فيدباك", "rate", "review"]


class AgentRouter:
    """Routes incoming messages to the correct specialized agent."""

    def __init__(self):
        self.agents = {
            "order": OrderAgent(),
            "crm": CRMAgent(),
            "inventory": InventoryAgent(),
            "feedback": FeedbackAgent(),
            "analytics": AnalyticsAgent(),
        }

    async def route(self, merchant_id: int, message: str, context: dict | None = None) -> AgentResponse:
        """Route a message to the appropriate agent."""
        context = context or {}
        normalized = normalize_arabic(message.lower())

        # Check for feedback flow
        if context.get("feedback_step") is not None:
            return await self.agents["feedback"].handle(merchant_id, message, context)

        # Check for repeat order keyword
        if any(kw in normalized for kw in REPEAT_KEYWORDS):
            return AgentResponse(
                text="Repeat order requested",
                text_ar="تكرار آخر طلبية... 🔄",
                action="repeat_order",
            )

        # Check for feedback keyword
        if any(kw in normalized for kw in FEEDBACK_KEYWORDS):
            return await self.agents["feedback"].handle(merchant_id, message, context)

        # Detect intent from the message
        intent, confidence = detect_intent(message)
        context["intent"] = intent
        context["confidence"] = confidence

        # Select the right agent
        agent_key = INTENT_AGENT_MAP.get(intent, "crm")
        agent = self.agents[agent_key]

        # If confidence is too low, use Claude for understanding
        if confidence < 0.2 and intent == "unknown":
            return AgentResponse(
                text="I didn't understand. Can you rephrase?",
                text_ar="ما فهمت عليك. ممكن توضحلي أكتر شو بدك؟",
                action="clarify",
            )

        return await agent.handle(merchant_id, message, context)
