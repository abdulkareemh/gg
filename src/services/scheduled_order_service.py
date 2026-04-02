"""Scheduled order / pre-order service.

Allows customers to place orders for a specific future time,
e.g., "I want shawarma delivered at 7pm tomorrow."
"""

import json
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.scheduled_order import ScheduledOrder


class ScheduledOrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_scheduled_order(
        self,
        merchant_id: int,
        customer_id: int,
        scheduled_for: datetime,
        items: list[dict],
        total_amount: float,
        notes: str | None = None,
    ) -> ScheduledOrder:
        """Create a new scheduled order."""
        scheduled = ScheduledOrder(
            merchant_id=merchant_id,
            customer_id=customer_id,
            scheduled_for=scheduled_for,
            items_json=json.dumps(items, ensure_ascii=False),
            total_amount=total_amount,
            notes=notes,
        )
        self.db.add(scheduled)
        await self.db.commit()
        await self.db.refresh(scheduled)
        return scheduled

    async def get_upcoming(self, merchant_id: int, hours_ahead: int = 24) -> list[ScheduledOrder]:
        """Get scheduled orders for the next N hours."""
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours_ahead)

        result = await self.db.execute(
            select(ScheduledOrder).where(
                and_(
                    ScheduledOrder.merchant_id == merchant_id,
                    ScheduledOrder.status == "scheduled",
                    ScheduledOrder.scheduled_for >= now,
                    ScheduledOrder.scheduled_for <= cutoff,
                )
            ).order_by(ScheduledOrder.scheduled_for)
        )
        return list(result.scalars().all())

    async def get_due_reminders(self, minutes_before: int = 30) -> list[ScheduledOrder]:
        """Get orders that need a reminder sent (30 min before scheduled time)."""
        now = datetime.utcnow()
        reminder_window = now + timedelta(minutes=minutes_before)

        result = await self.db.execute(
            select(ScheduledOrder).where(
                and_(
                    ScheduledOrder.status == "scheduled",
                    ScheduledOrder.scheduled_for <= reminder_window,
                    ScheduledOrder.scheduled_for > now,
                )
            )
        )
        return list(result.scalars().all())

    async def mark_reminded(self, order_id: int) -> None:
        order = await self.db.get(ScheduledOrder, order_id)
        if order:
            order.status = "reminded"
            await self.db.commit()

    async def convert_to_order(self, scheduled_id: int, real_order_id: int) -> None:
        """Mark a scheduled order as converted to a real order."""
        order = await self.db.get(ScheduledOrder, scheduled_id)
        if order:
            order.status = "converted"
            order.is_converted = True
            order.order_id = real_order_id
            await self.db.commit()

    async def cancel(self, scheduled_id: int) -> bool:
        order = await self.db.get(ScheduledOrder, scheduled_id)
        if order and order.status in ("scheduled", "reminded"):
            order.status = "cancelled"
            await self.db.commit()
            return True
        return False


def format_scheduled_orders(orders: list[ScheduledOrder]) -> str:
    """Format upcoming scheduled orders as chat message."""
    if not orders:
        return "ما في طلبيات مجدولة."

    lines = ["📅 الطلبيات المجدولة:"]
    for o in orders:
        time_str = o.scheduled_for.strftime("%H:%M")
        date_str = o.scheduled_for.strftime("%Y-%m-%d")
        items = json.loads(o.items_json) if o.items_json else []
        item_names = ", ".join(i.get("name_ar", "?") for i in items[:3])

        lines.append(
            f"  🕐 {date_str} {time_str} — {item_names} ({o.total_amount:,.0f} ل.س)"
        )

    return "\n".join(lines)
