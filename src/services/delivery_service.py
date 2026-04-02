"""Delivery zone management service."""

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.delivery import DeliveryZone


# Common Damascus neighborhoods
DAMASCUS_ZONES = [
    {"name": "المزة", "city": "دمشق", "delivery_fee": 10000, "estimated_minutes": 25},
    {"name": "باب توما", "city": "دمشق", "delivery_fee": 8000, "estimated_minutes": 20},
    {"name": "الشعلان", "city": "دمشق", "delivery_fee": 8000, "estimated_minutes": 20},
    {"name": "المالكي", "city": "دمشق", "delivery_fee": 10000, "estimated_minutes": 25},
    {"name": "أبو رمانة", "city": "دمشق", "delivery_fee": 10000, "estimated_minutes": 25},
    {"name": "الميدان", "city": "دمشق", "delivery_fee": 12000, "estimated_minutes": 30},
    {"name": "ركن الدين", "city": "دمشق", "delivery_fee": 12000, "estimated_minutes": 30},
    {"name": "المهاجرين", "city": "دمشق", "delivery_fee": 12000, "estimated_minutes": 30},
    {"name": "جرمانا", "city": "دمشق", "delivery_fee": 15000, "estimated_minutes": 35},
    {"name": "صحنايا", "city": "دمشق", "delivery_fee": 18000, "estimated_minutes": 40},
    {"name": "داريا", "city": "دمشق", "delivery_fee": 20000, "estimated_minutes": 45},
    {"name": "دمر", "city": "دمشق", "delivery_fee": 15000, "estimated_minutes": 35},
]


class DeliveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_zone(
        self,
        merchant_id: int,
        name: str,
        city: str,
        delivery_fee: float = 0,
        min_order_amount: float = 0,
        estimated_minutes: int = 30,
    ) -> DeliveryZone:
        zone = DeliveryZone(
            merchant_id=merchant_id,
            name=name,
            city=city,
            delivery_fee=delivery_fee,
            min_order_amount=min_order_amount,
            estimated_minutes=estimated_minutes,
        )
        self.db.add(zone)
        await self.db.commit()
        await self.db.refresh(zone)
        return zone

    async def get_zones(self, merchant_id: int) -> list[DeliveryZone]:
        result = await self.db.execute(
            select(DeliveryZone).where(
                and_(DeliveryZone.merchant_id == merchant_id, DeliveryZone.is_active == True)
            ).order_by(DeliveryZone.delivery_fee)
        )
        return list(result.scalars().all())

    async def find_zone(self, merchant_id: int, area_name: str) -> DeliveryZone | None:
        """Find a delivery zone by area name (fuzzy)."""
        result = await self.db.execute(
            select(DeliveryZone).where(
                and_(
                    DeliveryZone.merchant_id == merchant_id,
                    DeliveryZone.is_active == True,
                    DeliveryZone.name.ilike(f"%{area_name}%"),
                )
            )
        )
        return result.scalar_one_or_none()

    async def seed_default_zones(self, merchant_id: int, city: str = "دمشق") -> int:
        """Seed default delivery zones for a merchant."""
        zones = DAMASCUS_ZONES if city == "دمشق" else []
        count = 0
        for zone_data in zones:
            zone = DeliveryZone(merchant_id=merchant_id, **zone_data)
            self.db.add(zone)
            count += 1
        await self.db.commit()
        return count

    async def calculate_delivery(self, merchant_id: int, area_name: str, order_total: float) -> dict:
        """Calculate delivery fee and estimated time for an area."""
        zone = await self.find_zone(merchant_id, area_name)

        if not zone:
            return {
                "available": False,
                "message": f"عذراً، ما منوصل لمنطقة {area_name}. تواصل معنا للتفاصيل.",
            }

        if order_total < float(zone.min_order_amount):
            return {
                "available": False,
                "message": f"الحد الأدنى للطلب لمنطقة {zone.name}: {float(zone.min_order_amount):,.0f} ل.س",
            }

        return {
            "available": True,
            "zone": zone.name,
            "delivery_fee": float(zone.delivery_fee),
            "estimated_minutes": zone.estimated_minutes,
            "total_with_delivery": order_total + float(zone.delivery_fee),
            "message": f"🚚 التوصيل لـ {zone.name}: {float(zone.delivery_fee):,.0f} ل.س (~{zone.estimated_minutes} دقيقة)",
        }


def format_delivery_zones(zones: list[DeliveryZone]) -> str:
    """Format delivery zones as a chat message."""
    if not zones:
        return "ما في مناطق توصيل محددة حالياً."

    lines = ["🚚 مناطق التوصيل:"]
    for z in zones:
        lines.append(
            f"  • {z.name} — {float(z.delivery_fee):,.0f} ل.س (~{z.estimated_minutes} دقيقة)"
        )

    return "\n".join(lines)
