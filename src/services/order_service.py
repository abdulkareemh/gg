"""Order database operations."""

from datetime import datetime, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.order import Order, OrderItem
from src.models.product import Product


ORDER_STATUSES = ["pending", "confirmed", "preparing", "ready", "delivered", "completed", "cancelled"]


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(
        self,
        merchant_id: int,
        customer_id: int,
        items: list[dict],  # [{"product_id": 1, "quantity": 2}, ...]
        notes: str | None = None,
        payment_method: str | None = None,
    ) -> Order:
        """Create a new order with items."""
        order = Order(
            merchant_id=merchant_id,
            customer_id=customer_id,
            notes=notes,
            payment_method=payment_method,
        )
        self.db.add(order)
        await self.db.flush()  # Get order.id

        total = 0.0
        for item_data in items:
            product = await self.db.get(Product, item_data["product_id"])
            if not product or not product.is_available:
                continue

            quantity = item_data.get("quantity", 1)
            unit_price = float(product.price)
            line_total = unit_price * quantity

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=line_total,
            )
            self.db.add(order_item)

            # Decrease stock
            product.stock_quantity = max(0, product.stock_quantity - quantity)
            total += line_total

        order.total_amount = total
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_order(self, order_id: int) -> Order | None:
        result = await self.db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, order_id: int, new_status: str) -> Order | None:
        if new_status not in ORDER_STATUSES:
            return None

        order = await self.get_order(order_id)
        if order:
            order.status = new_status
            order.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(order)
        return order

    async def get_merchant_orders(
        self, merchant_id: int, status: str | None = None, limit: int = 20
    ) -> list[Order]:
        query = select(Order).where(Order.merchant_id == merchant_id)
        if status:
            query = query.where(Order.status == status)
        query = query.order_by(Order.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_customer_orders(self, customer_id: int, limit: int = 10) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_daily_summary(self, merchant_id: int) -> dict:
        """Get today's order summary for a merchant."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        result = await self.db.execute(
            select(
                func.count(Order.id).label("count"),
                func.sum(Order.total_amount).label("total"),
            ).where(
                and_(
                    Order.merchant_id == merchant_id,
                    Order.created_at >= today_start,
                )
            )
        )
        row = result.one()
        return {
            "order_count": row.count or 0,
            "total_revenue": float(row.total or 0),
            "currency": "SYP",
        }
