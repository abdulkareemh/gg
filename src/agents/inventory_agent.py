"""Inventory management agent — tracks stock and alerts."""

from .base_agent import BaseAgent, AgentResponse


class InventoryAgent(BaseAgent):
    """Handles inventory checks, updates, and low-stock alerts."""

    async def handle(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        action = context.get("intent", "check_stock")

        if action == "inventory_check":
            return await self._check_stock(merchant_id, context)
        elif action == "report":
            return await self._inventory_report(merchant_id, context)
        else:
            return await self._general_inventory(merchant_id, message, context)

    async def _check_stock(self, merchant_id: int, context: dict) -> AgentResponse:
        products = context.get("products", [])
        low_stock = [p for p in products if p.get("stock", 0) <= p.get("threshold", 5)]

        if low_stock:
            items = "\n".join(
                f"- {p['name_ar']}: باقي {p['stock']} حبة"
                for p in low_stock
            )
            text_ar = f"تنبيه! المنتجات التالية قربت تخلص:\n{items}"
        else:
            text_ar = "المخزون تمام! كل المنتجات متوفرة بكميات كافية."

        return AgentResponse(
            text=f"Stock check: {len(low_stock)} items low",
            text_ar=text_ar,
            action="stock_check",
            data={"low_stock_count": len(low_stock), "low_stock_items": low_stock},
        )

    async def _inventory_report(self, merchant_id: int, context: dict) -> AgentResponse:
        products = context.get("products", [])
        total = len(products)
        available = sum(1 for p in products if p.get("is_available", True))

        text_ar = (
            f"تقرير المخزون:\n"
            f"- إجمالي المنتجات: {total}\n"
            f"- متوفر: {available}\n"
            f"- غير متوفر: {total - available}"
        )

        return AgentResponse(
            text=f"Inventory: {available}/{total} available",
            text_ar=text_ar,
            action="inventory_report",
        )

    async def _general_inventory(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        response_text = await self.ask_claude(
            "You are Noor, an inventory management assistant for Syrian businesses. "
            "Respond in Syrian Arabic dialect. Be concise and helpful.",
            f"Merchant asks about inventory: {message}",
        )
        return AgentResponse(text=response_text, text_ar=response_text, action="inventory_help")
