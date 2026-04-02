"""Loyalty and rewards points service."""

from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.loyalty import LoyaltyProgram, LoyaltyBalance, LoyaltyTransaction


class LoyaltyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def setup_program(
        self,
        merchant_id: int,
        name: str = "برنامج الولاء",
        points_per_syp: float = 0.001,
        min_redeem: int = 100,
        point_value: float = 100,
    ) -> LoyaltyProgram:
        """Create or update a merchant's loyalty program."""
        result = await self.db.execute(
            select(LoyaltyProgram).where(LoyaltyProgram.merchant_id == merchant_id)
        )
        program = result.scalar_one_or_none()

        if program:
            program.name = name
            program.points_per_syp = points_per_syp
            program.min_redeem_points = min_redeem
            program.point_value_syp = point_value
        else:
            program = LoyaltyProgram(
                merchant_id=merchant_id,
                name=name,
                points_per_syp=points_per_syp,
                min_redeem_points=min_redeem,
                point_value_syp=point_value,
            )
            self.db.add(program)

        await self.db.commit()
        await self.db.refresh(program)
        return program

    async def get_program(self, merchant_id: int) -> LoyaltyProgram | None:
        result = await self.db.execute(
            select(LoyaltyProgram).where(
                and_(LoyaltyProgram.merchant_id == merchant_id, LoyaltyProgram.is_active == True)
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_balance(self, customer_id: int, merchant_id: int) -> LoyaltyBalance:
        result = await self.db.execute(
            select(LoyaltyBalance).where(
                and_(LoyaltyBalance.customer_id == customer_id, LoyaltyBalance.merchant_id == merchant_id)
            )
        )
        balance = result.scalar_one_or_none()

        if not balance:
            balance = LoyaltyBalance(customer_id=customer_id, merchant_id=merchant_id)
            self.db.add(balance)
            await self.db.commit()
            await self.db.refresh(balance)

        return balance

    async def earn_points(
        self, customer_id: int, merchant_id: int, order_amount: float, order_id: int | None = None
    ) -> dict:
        """Award loyalty points for an order."""
        program = await self.get_program(merchant_id)
        if not program:
            return {"earned": 0, "message": "ما في برنامج ولاء مفعّل"}

        points = int(order_amount * float(program.points_per_syp))
        if points <= 0:
            return {"earned": 0, "total": 0}

        balance = await self.get_or_create_balance(customer_id, merchant_id)
        balance.points += points
        balance.total_earned += points

        transaction = LoyaltyTransaction(
            balance_id=balance.id,
            type="earn",
            points=points,
            order_id=order_id,
            description=f"نقاط من طلبية بقيمة {order_amount:,.0f} ل.س",
        )
        self.db.add(transaction)
        await self.db.commit()

        return {
            "earned": points,
            "total": balance.points,
            "message": f"🎯 كسبت {points} نقطة! رصيدك: {balance.points} نقطة",
        }

    async def redeem_points(
        self, customer_id: int, merchant_id: int, points_to_redeem: int
    ) -> dict:
        """Redeem loyalty points for a discount."""
        program = await self.get_program(merchant_id)
        if not program:
            return {"success": False, "message": "ما في برنامج ولاء مفعّل"}

        balance = await self.get_or_create_balance(customer_id, merchant_id)

        if balance.points < points_to_redeem:
            return {
                "success": False,
                "message": f"رصيدك {balance.points} نقطة بس. ما بيكفي.",
            }

        if points_to_redeem < program.min_redeem_points:
            return {
                "success": False,
                "message": f"الحد الأدنى للاستبدال: {program.min_redeem_points} نقطة",
            }

        discount_syp = points_to_redeem * float(program.point_value_syp)

        balance.points -= points_to_redeem
        balance.total_redeemed += points_to_redeem

        transaction = LoyaltyTransaction(
            balance_id=balance.id,
            type="redeem",
            points=points_to_redeem,
            description=f"استبدال {points_to_redeem} نقطة = خصم {discount_syp:,.0f} ل.س",
        )
        self.db.add(transaction)
        await self.db.commit()

        return {
            "success": True,
            "redeemed": points_to_redeem,
            "discount_syp": discount_syp,
            "remaining_points": balance.points,
            "message": f"✅ تم استبدال {points_to_redeem} نقطة = خصم {discount_syp:,.0f} ل.س!",
        }

    async def get_balance_info(self, customer_id: int, merchant_id: int) -> dict:
        """Get customer's loyalty balance and program info."""
        program = await self.get_program(merchant_id)
        if not program:
            return {"active": False}

        balance = await self.get_or_create_balance(customer_id, merchant_id)
        potential_discount = balance.points * float(program.point_value_syp)

        return {
            "active": True,
            "program_name": program.name,
            "points": balance.points,
            "total_earned": balance.total_earned,
            "total_redeemed": balance.total_redeemed,
            "potential_discount": potential_discount,
            "min_redeem": program.min_redeem_points,
            "can_redeem": balance.points >= program.min_redeem_points,
        }


def format_loyalty_status(info: dict) -> str:
    """Format loyalty status as Arabic chat message."""
    if not info.get("active"):
        return ""

    lines = [
        f"🏆 {info['program_name']}",
        f"⭐ رصيدك: {info['points']} نقطة",
        f"💰 قيمة الخصم المتاح: {info['potential_discount']:,.0f} ل.س",
    ]

    if info["can_redeem"]:
        lines.append(f"\nابعت 'استبدال نقاط' لاستخدام رصيدك!")
    else:
        lines.append(f"\nباقيلك {info['min_redeem'] - info['points']} نقطة للاستبدال")

    return "\n".join(lines)
