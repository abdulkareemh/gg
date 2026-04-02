"""Promotional messaging service.

Allows merchants to send bulk promotional messages
to their customer base via WhatsApp/Telegram.
"""

from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Customer
from src.services.notification_service import NotificationService


@dataclass
class Promotion:
    merchant_id: int
    title: str
    message: str
    target: str  # "all", "vip", "diaspora", "inactive"
    min_orders: int = 0


PROMO_TEMPLATES = {
    "discount": "🎉 عرض خاص من {business}!\n\n{message}\n\nلفترة محدودة — اطلب الآن!",
    "new_product": "✨ جديد في {business}!\n\n{message}\n\nجربو هلق!",
    "holiday": "🌙 {business} يتمنالكم أحلى المناسبات!\n\n{message}",
    "loyalty": "💎 شكراً لوفائكم!\n\n{message}\n\nزبائننا المميزين بيستاهلو الأفضل.",
}


class PromotionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notifier = NotificationService()

    async def get_target_customers(self, promotion: Promotion) -> list[Customer]:
        """Get the target customer list based on promotion criteria."""
        stmt = select(Customer).where(Customer.merchant_id == promotion.merchant_id)

        if promotion.target == "vip":
            stmt = stmt.where(Customer.total_orders >= 10)
        elif promotion.target == "diaspora":
            stmt = stmt.where(Customer.is_diaspora == True)
        elif promotion.target == "inactive":
            # Customers who haven't ordered in 30 days
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(days=30)
            stmt = stmt.where(
                (Customer.last_order_at < cutoff) | (Customer.last_order_at == None)
            )
        elif promotion.target == "frequent":
            stmt = stmt.where(Customer.total_orders >= promotion.min_orders)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def send_promotion(
        self,
        promotion: Promotion,
        template: str = "discount",
        business_name: str = "",
        platform: str = "whatsapp",
    ) -> dict:
        """Send a promotional message to targeted customers."""
        customers = await self.get_target_customers(promotion)

        if not customers:
            return {"sent": 0, "target": promotion.target, "error": "No matching customers"}

        # Format the message
        tmpl = PROMO_TEMPLATES.get(template, PROMO_TEMPLATES["discount"])
        formatted = tmpl.format(business=business_name, message=promotion.message)

        sent = 0
        failed = 0

        for customer in customers:
            try:
                await self.notifier._send(customer.phone, formatted, platform)
                sent += 1
            except Exception:
                failed += 1

        return {
            "sent": sent,
            "failed": failed,
            "total_targeted": len(customers),
            "target": promotion.target,
            "template": template,
        }

    async def get_promotion_stats(self, merchant_id: int) -> dict:
        """Get customer segment counts for targeting."""
        all_count = await self._count_customers(merchant_id)
        vip_count = await self._count_customers(merchant_id, min_orders=10)
        diaspora_count = await self._count_diaspora(merchant_id)

        return {
            "segments": {
                "all": {"label": "الكل", "count": all_count},
                "vip": {"label": "زبائن VIP (10+ طلبات)", "count": vip_count},
                "diaspora": {"label": "المغتربين", "count": diaspora_count},
            },
            "templates": list(PROMO_TEMPLATES.keys()),
        }

    async def _count_customers(self, merchant_id: int, min_orders: int = 0) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Customer.id)).where(
                and_(Customer.merchant_id == merchant_id, Customer.total_orders >= min_orders)
            )
        )
        return result.scalar() or 0

    async def _count_diaspora(self, merchant_id: int) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Customer.id)).where(
                and_(Customer.merchant_id == merchant_id, Customer.is_diaspora == True)
            )
        )
        return result.scalar() or 0
