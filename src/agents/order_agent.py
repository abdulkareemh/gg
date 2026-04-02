"""Order management agent — handles creating, tracking, and updating orders."""

from .base_agent import BaseAgent, AgentResponse

SYSTEM_PROMPT = """You are Noor (نور), a friendly AI assistant for a Syrian business.
You help manage orders in Syrian Arabic dialect. Be warm, concise, and helpful.
Always respond in Syrian Arabic unless the customer speaks English.

When handling orders:
- Confirm items and quantities clearly
- Provide order total in Syrian Pounds (SYP)
- Give estimated preparation/delivery time
- Be polite and use Syrian expressions like "تكرم", "إن شاء الله", "على راسي"

Current merchant context: {context}
"""


class OrderAgent(BaseAgent):
    """Handles order creation, tracking, and management."""

    async def handle(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        action = context.get("intent", "new_order")

        if action == "new_order":
            return await self._create_order(merchant_id, message, context)
        elif action == "check_order":
            return await self._check_order(merchant_id, message, context)
        elif action == "cancel_order":
            return await self._cancel_order(merchant_id, message, context)
        else:
            return await self._general_order_help(merchant_id, message, context)

    async def _create_order(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        response_text = await self.ask_claude(
            SYSTEM_PROMPT.format(context=context),
            f"Customer wants to place an order. Their message: {message}\n"
            f"Available products: {context.get('products', [])}\n"
            f"Help them complete their order.",
        )
        return AgentResponse(
            text=response_text,
            text_ar=response_text,
            action="create_order",
            data={"merchant_id": merchant_id, "raw_message": message},
        )

    async def _check_order(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        order_info = context.get("last_order", {})
        if order_info:
            status_map = {
                "pending": "تم استلام طلبيتك وبانتظار التأكيد",
                "confirmed": "تم تأكيد طلبيتك وجاري التحضير",
                "preparing": "طلبيتك قيد التحضير",
                "ready": "طلبيتك جاهزة!",
                "delivered": "تم توصيل طلبيتك",
            }
            status = order_info.get("status", "pending")
            text_ar = status_map.get(status, "جاري التحقق من حالة طلبيتك")
            return AgentResponse(
                text=f"Order #{order_info.get('id')} status: {status}",
                text_ar=f"طلبية #{order_info.get('id')}: {text_ar}",
                action="check_order",
                data=order_info,
            )
        return AgentResponse(
            text="No recent orders found.",
            text_ar="ما لقيت طلبيات سابقة. بدك تطلب شي جديد؟",
            action="check_order",
        )

    async def _cancel_order(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        return AgentResponse(
            text="Order cancellation requested.",
            text_ar="تم طلب إلغاء الطلبية. رح نتواصل معك للتأكيد.",
            action="cancel_order",
        )

    async def _general_order_help(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        response_text = await self.ask_claude(
            SYSTEM_PROMPT.format(context=context),
            f"Customer needs help with orders. Their message: {message}",
        )
        return AgentResponse(text=response_text, text_ar=response_text, action="order_help")
