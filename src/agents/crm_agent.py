"""CRM agent — manages customer relationships and interactions."""

from .base_agent import BaseAgent, AgentResponse


class CRMAgent(BaseAgent):
    """Handles customer relationship management."""

    async def handle(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        customer = context.get("customer", {})

        if not customer:
            return AgentResponse(
                text="New customer detected. Creating profile.",
                text_ar="أهلا وسهلا فيك! منتشرف بمعرفتك. شو اسمك الكريم؟",
                action="new_customer",
                data={"merchant_id": merchant_id},
            )

        # Returning customer — personalized greeting
        name = customer.get("name", "")
        total_orders = customer.get("total_orders", 0)

        if total_orders > 10:
            text_ar = f"هلا {name}! من أحسن زبايننا. كيف بقدر ساعدك اليوم؟"
        elif total_orders > 0:
            text_ar = f"أهلا {name}! نورتنا من جديد. شو بدك تطلب؟"
        else:
            text_ar = f"أهلا {name}! كيف بقدر ساعدك؟"

        return AgentResponse(
            text=f"Returning customer: {name} ({total_orders} orders)",
            text_ar=text_ar,
            action="greet_customer",
            data=customer,
        )
