"""Merchant settings service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.merchant_settings import MerchantSettings


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, merchant_id: int) -> MerchantSettings:
        result = await self.db.execute(
            select(MerchantSettings).where(MerchantSettings.merchant_id == merchant_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = MerchantSettings(merchant_id=merchant_id)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings

    async def update(self, merchant_id: int, **kwargs) -> MerchantSettings:
        settings = await self.get_or_create(merchant_id)
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def is_open(self, merchant_id: int) -> bool:
        """Check if the merchant is currently open."""
        from datetime import datetime

        settings = await self.get_or_create(merchant_id)

        # Check day
        now = datetime.utcnow()
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        current_day = day_names[now.weekday()]
        closed_days = [d.strip() for d in settings.closed_days.split(",") if d.strip()]

        if current_day in closed_days:
            return False

        # Check time
        current_time = now.strftime("%H:%M")
        return settings.opening_time <= current_time <= settings.closing_time

    def to_dict(self, settings: MerchantSettings) -> dict:
        return {
            "notify_new_orders": settings.notify_new_orders,
            "notify_low_stock": settings.notify_low_stock,
            "notify_daily_report": settings.notify_daily_report,
            "notify_new_reviews": settings.notify_new_reviews,
            "opening_time": settings.opening_time,
            "closing_time": settings.closing_time,
            "closed_days": settings.closed_days,
            "auto_confirm_orders": settings.auto_confirm_orders,
            "accept_scheduled_orders": settings.accept_scheduled_orders,
            "accept_reservations": settings.accept_reservations,
            "min_order_amount": float(settings.min_order_amount),
            "preferred_language": settings.preferred_language,
            "welcome_message": settings.welcome_message,
            "away_message": settings.away_message,
        }
