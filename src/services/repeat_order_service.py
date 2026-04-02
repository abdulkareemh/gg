"""Repeat last order service.

Allows customers to quickly reorder their last order
by saying "كرر طلبيتي" or "نفس الطلبية".
"""

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.order import Order, OrderItem
from src.models.product import Product


class RepeatOrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_last_order_items(self, merchant_id: int, customer_id: int) -> list[dict] | None:
        """Get items from the customer's last completed order."""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                and_(
                    Order.merchant_id == merchant_id,
                    Order.customer_id == customer_id,
                    Order.status.in_(["completed", "delivered"]),
                )
            )
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        order = result.scalar_one_or_none()

        if not order or not order.items:
            return None

        items = []
        for item in order.items:
            # Check product still exists and is available
            product = await self.db.get(Product, item.product_id)
            if product and product.is_available and product.stock_quantity > 0:
                items.append({
                    "product_id": product.id,
                    "name": product.name,
                    "name_ar": product.name_ar,
                    "quantity": item.quantity,
                    "price": float(product.price),  # Use current price
                    "total": float(product.price) * item.quantity,
                })

        return items if items else None

    async def get_frequent_orders(self, merchant_id: int, customer_id: int, limit: int = 3) -> list[dict]:
        """Get the customer's most frequently ordered item combinations."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(
                OrderItem.product_id,
                Product.name_ar,
                func.sum(OrderItem.quantity).label("total_qty"),
                func.count(OrderItem.id).label("times_ordered"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(
                and_(
                    Order.merchant_id == merchant_id,
                    Order.customer_id == customer_id,
                    Product.is_available == True,
                )
            )
            .group_by(OrderItem.product_id, Product.name_ar)
            .order_by(func.count(OrderItem.id).desc())
            .limit(limit)
        )

        return [
            {
                "product_id": row.product_id,
                "name_ar": row.name_ar,
                "total_ordered": int(row.total_qty),
                "times_ordered": row.times_ordered,
            }
            for row in result.all()
        ]


def format_repeat_order(items: list[dict]) -> str:
    """Format repeat order confirmation."""
    if not items:
        return "ما لقيت طلبية سابقة لتكرارها."

    lines = ["🔄 تكرار آخر طلبية:"]
    total = 0
    for item in items:
        lines.append(f"  • {item['name_ar']} × {item['quantity']} = {item['total']:,.0f} ل.س")
        total += item["total"]

    lines.append(f"\n💰 المجموع: {total:,.0f} ل.س")
    lines.append("\nبدك تأكد هالطلبية؟")

    return "\n".join(lines)
