"""Customer database operations."""

from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.customer import Customer


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, merchant_id: int, phone: str) -> tuple[Customer, bool]:
        """Get existing customer or create new one. Returns (customer, is_new)."""
        result = await self.db.execute(
            select(Customer).where(
                and_(Customer.merchant_id == merchant_id, Customer.phone == phone)
            )
        )
        customer = result.scalar_one_or_none()

        if customer:
            return customer, False

        customer = Customer(merchant_id=merchant_id, phone=phone)
        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)
        return customer, True

    async def update_name(self, customer_id: int, name: str) -> Customer | None:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if customer:
            customer.name = name
            await self.db.commit()
            await self.db.refresh(customer)
        return customer

    async def increment_orders(self, customer_id: int) -> None:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if customer:
            customer.total_orders += 1
            customer.last_order_at = datetime.utcnow()
            await self.db.commit()

    async def get_top_customers(self, merchant_id: int, limit: int = 10) -> list[Customer]:
        result = await self.db.execute(
            select(Customer)
            .where(Customer.merchant_id == merchant_id)
            .order_by(Customer.total_orders.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_diaspora_customers(self, merchant_id: int) -> list[Customer]:
        result = await self.db.execute(
            select(Customer).where(
                and_(Customer.merchant_id == merchant_id, Customer.is_diaspora == True)
            )
        )
        return list(result.scalars().all())
