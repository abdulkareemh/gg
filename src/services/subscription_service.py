"""Subscription and billing management.

Handles plan limits, usage tracking, and plan enforcement.
No third-party billing — usage is tracked internally.
"""

from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import Subscription, UsageLog


# Plan definitions
PLANS = {
    "free": {
        "name": "مجاني",
        "price_usd": 0,
        "max_orders": 50,
        "max_messages": 500,
        "max_ai_calls": 100,
        "max_products": 10,
        "features": ["واتساب فقط", "تقرير أسبوعي"],
    },
    "basic": {
        "name": "أساسي",
        "price_usd": 10,
        "max_orders": 500,
        "max_messages": 5000,
        "max_ai_calls": 1000,
        "max_products": 50,
        "features": ["واتساب + تلغرام", "تقارير يومية", "تنبيهات المخزون"],
    },
    "pro": {
        "name": "احترافي",
        "price_usd": 30,
        "max_orders": -1,  # unlimited
        "max_messages": -1,
        "max_ai_calls": 5000,
        "max_products": -1,
        "features": ["كل ميزات الأساسي", "دفع إلكتروني", "جسر المغتربين", "تقارير متقدمة", "دعم أولوية"],
    },
    "enterprise": {
        "name": "مؤسسات",
        "price_usd": 100,
        "max_orders": -1,
        "max_messages": -1,
        "max_ai_calls": -1,
        "max_products": -1,
        "features": ["كل ميزات الاحترافي", "فروع متعددة", "API مخصص", "مدير حساب"],
    },
}


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, merchant_id: int) -> Subscription:
        result = await self.db.execute(
            select(Subscription).where(Subscription.merchant_id == merchant_id)
        )
        sub = result.scalar_one_or_none()

        if not sub:
            sub = Subscription(
                merchant_id=merchant_id,
                plan="free",
                monthly_price_usd=0,
            )
            self.db.add(sub)
            await self.db.commit()
            await self.db.refresh(sub)

        return sub

    async def upgrade_plan(self, merchant_id: int, plan: str) -> dict:
        if plan not in PLANS:
            return {"success": False, "message": "خطة غير صالحة"}

        sub = await self.get_or_create(merchant_id)
        plan_info = PLANS[plan]

        sub.plan = plan
        sub.monthly_price_usd = plan_info["price_usd"]
        sub.orders_this_month = 0
        sub.messages_this_month = 0
        sub.ai_calls_this_month = 0
        sub.billing_cycle_start = datetime.utcnow()

        await self.db.commit()

        return {
            "success": True,
            "plan": plan,
            "message": f"تم الترقية إلى خطة {plan_info['name']}! ✅",
        }

    async def start_trial(self, merchant_id: int, plan: str = "pro", days: int = 14) -> dict:
        sub = await self.get_or_create(merchant_id)
        plan_info = PLANS.get(plan, PLANS["pro"])

        sub.plan = plan
        sub.monthly_price_usd = 0
        sub.is_trial = True
        sub.trial_ends_at = datetime.utcnow() + timedelta(days=days)

        await self.db.commit()

        return {
            "success": True,
            "message": f"تم تفعيل تجربة مجانية لخطة {plan_info['name']} لمدة {days} يوم! 🎉",
            "trial_ends": sub.trial_ends_at.isoformat(),
        }

    async def check_limit(self, merchant_id: int, resource: str) -> dict:
        """Check if merchant has reached their plan limit.

        resource: 'orders', 'messages', or 'ai_calls'
        Returns: {"allowed": bool, "used": int, "limit": int}
        """
        sub = await self.get_or_create(merchant_id)
        plan_info = PLANS.get(sub.plan, PLANS["free"])

        limit_key = f"max_{resource}"
        max_val = plan_info.get(limit_key, 0)
        used_key = f"{resource}_this_month"
        used = getattr(sub, used_key, 0)

        # -1 means unlimited
        if max_val == -1:
            return {"allowed": True, "used": used, "limit": "unlimited"}

        return {
            "allowed": used < max_val,
            "used": used,
            "limit": max_val,
            "remaining": max(0, max_val - used),
        }

    async def increment_usage(self, merchant_id: int, resource: str, amount: int = 1) -> None:
        """Increment usage counter for a resource."""
        sub = await self.get_or_create(merchant_id)
        attr = f"{resource}_this_month"
        current = getattr(sub, attr, 0)
        setattr(sub, attr, current + amount)
        await self.db.commit()

    async def get_usage_summary(self, merchant_id: int) -> dict:
        sub = await self.get_or_create(merchant_id)
        plan_info = PLANS.get(sub.plan, PLANS["free"])

        def _usage_str(used: int, max_val: int) -> str:
            if max_val == -1:
                return f"{used} (غير محدود)"
            return f"{used}/{max_val}"

        return {
            "plan": sub.plan,
            "plan_name": plan_info["name"],
            "price_usd": plan_info["price_usd"],
            "is_trial": sub.is_trial,
            "trial_ends": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
            "usage": {
                "orders": _usage_str(sub.orders_this_month, plan_info["max_orders"]),
                "messages": _usage_str(sub.messages_this_month, plan_info["max_messages"]),
                "ai_calls": _usage_str(sub.ai_calls_this_month, plan_info["max_ai_calls"]),
            },
            "features": plan_info["features"],
            "billing_cycle_start": sub.billing_cycle_start.isoformat(),
        }

    async def reset_monthly_usage(self, merchant_id: int) -> None:
        """Reset monthly usage counters (called at billing cycle)."""
        sub = await self.get_or_create(merchant_id)
        sub.orders_this_month = 0
        sub.messages_this_month = 0
        sub.ai_calls_this_month = 0
        sub.billing_cycle_start = datetime.utcnow()
        await self.db.commit()


def get_plan_comparison() -> list[dict]:
    """Get all plans for display."""
    return [
        {
            "plan": key,
            "name": info["name"],
            "price_usd": info["price_usd"],
            "max_orders": info["max_orders"],
            "max_products": info["max_products"],
            "features": info["features"],
        }
        for key, info in PLANS.items()
    ]


def format_usage_warning(resource: str, used: int, limit: int) -> str:
    """Format a usage limit warning message."""
    pct = (used / limit * 100) if limit > 0 else 0
    if pct >= 100:
        return f"⚠️ وصلت للحد الأقصى من {resource}! رقّي خطتك لتكمل."
    elif pct >= 80:
        remaining = limit - used
        return f"⚠️ باقيلك {remaining} {resource} فقط هالشهر. فكّر بالترقية!"
    return ""
