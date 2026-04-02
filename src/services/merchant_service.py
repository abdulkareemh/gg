"""Merchant database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.merchant import Merchant


class MerchantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_phone(self, phone: str) -> Merchant | None:
        result = await self.db.execute(
            select(Merchant).where(Merchant.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, merchant_id: int) -> Merchant | None:
        result = await self.db.execute(
            select(Merchant).where(Merchant.id == merchant_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        phone: str,
        name: str,
        business_name: str,
        business_type: str,
        city: str,
        platform: str = "whatsapp",
        language: str = "ar-SY",
    ) -> Merchant:
        merchant = Merchant(
            phone=phone,
            name=name,
            business_name=business_name,
            business_type=business_type,
            city=city,
            platform=platform,
            language=language,
        )
        self.db.add(merchant)
        await self.db.commit()
        await self.db.refresh(merchant)
        return merchant

    async def update_plan(self, merchant_id: int, plan: str) -> Merchant | None:
        merchant = await self.get_by_id(merchant_id)
        if merchant:
            merchant.plan = plan
            await self.db.commit()
            await self.db.refresh(merchant)
        return merchant

    async def deactivate(self, merchant_id: int) -> bool:
        merchant = await self.get_by_id(merchant_id)
        if merchant:
            merchant.is_active = False
            await self.db.commit()
            return True
        return False
