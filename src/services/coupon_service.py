"""Coupon and discount code service."""

import secrets
import string
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.coupon import Coupon


def generate_code(length: int = 8) -> str:
    """Generate a random coupon code."""
    chars = string.ascii_uppercase + string.digits
    return "NOOR-" + "".join(secrets.choice(chars) for _ in range(length))


class CouponService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_coupon(
        self,
        merchant_id: int,
        discount_type: str,
        discount_value: float,
        code: str | None = None,
        description: str | None = None,
        min_order: float = 0,
        max_discount: float | None = None,
        max_uses: int = 100,
        valid_until: datetime | None = None,
    ) -> Coupon:
        """Create a new coupon code."""
        if code is None:
            code = generate_code()

        coupon = Coupon(
            merchant_id=merchant_id,
            code=code.upper(),
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            min_order_amount=min_order,
            max_discount=max_discount,
            max_uses=max_uses,
            valid_until=valid_until,
        )
        self.db.add(coupon)
        await self.db.commit()
        await self.db.refresh(coupon)
        return coupon

    async def validate_coupon(self, code: str, merchant_id: int, order_total: float) -> dict:
        """Validate a coupon and calculate the discount."""
        result = await self.db.execute(
            select(Coupon).where(
                and_(Coupon.code == code.upper(), Coupon.merchant_id == merchant_id)
            )
        )
        coupon = result.scalar_one_or_none()

        if not coupon:
            return {"valid": False, "message": "كود الخصم غير صالح"}

        if not coupon.is_active:
            return {"valid": False, "message": "كود الخصم منتهي"}

        if coupon.valid_until and datetime.utcnow() > coupon.valid_until:
            return {"valid": False, "message": "كود الخصم منتهي الصلاحية"}

        if coupon.used_count >= coupon.max_uses:
            return {"valid": False, "message": "كود الخصم استُنفد"}

        if order_total < float(coupon.min_order_amount):
            return {
                "valid": False,
                "message": f"الحد الأدنى للطلب: {float(coupon.min_order_amount):,.0f} ل.س",
            }

        # Calculate discount
        if coupon.discount_type == "percentage":
            discount = order_total * (float(coupon.discount_value) / 100)
            if coupon.max_discount:
                discount = min(discount, float(coupon.max_discount))
        else:  # fixed
            discount = float(coupon.discount_value)

        discount = min(discount, order_total)  # Can't exceed order total

        return {
            "valid": True,
            "code": coupon.code,
            "discount": discount,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "new_total": order_total - discount,
            "message": f"🎉 خصم {discount:,.0f} ل.س! المجموع الجديد: {order_total - discount:,.0f} ل.س",
        }

    async def use_coupon(self, code: str) -> bool:
        """Increment usage count when a coupon is applied to an order."""
        result = await self.db.execute(
            select(Coupon).where(Coupon.code == code.upper())
        )
        coupon = result.scalar_one_or_none()
        if coupon:
            coupon.used_count += 1
            await self.db.commit()
            return True
        return False

    async def get_active_coupons(self, merchant_id: int) -> list[Coupon]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Coupon).where(
                and_(
                    Coupon.merchant_id == merchant_id,
                    Coupon.is_active == True,
                    (Coupon.valid_until == None) | (Coupon.valid_until > now),
                    Coupon.used_count < Coupon.max_uses,
                )
            ).order_by(Coupon.created_at.desc())
        )
        return list(result.scalars().all())

    async def deactivate_coupon(self, coupon_id: int) -> bool:
        coupon = await self.db.get(Coupon, coupon_id)
        if coupon:
            coupon.is_active = False
            await self.db.commit()
            return True
        return False


def format_coupon_list(coupons: list[Coupon]) -> str:
    """Format coupons as Arabic chat message."""
    if not coupons:
        return "ما في قسائم خصم حالياً."

    lines = ["🎟️ قسائم الخصم المتوفرة:"]
    for c in coupons:
        if c.discount_type == "percentage":
            discount_str = f"{float(c.discount_value):.0f}%"
        else:
            discount_str = f"{float(c.discount_value):,.0f} ل.س"

        remaining = c.max_uses - c.used_count
        lines.append(f"  🏷️ {c.code} — خصم {discount_str} (باقي {remaining} استخدام)")

    return "\n".join(lines)
