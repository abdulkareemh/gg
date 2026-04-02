"""Admin dashboard API — platform-level stats and management."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db
from src.models.merchant import Merchant
from src.models.customer import Customer
from src.models.order import Order
from src.models.product import Product
from src.models.payment import Payment

router = APIRouter()


@router.get("/stats")
async def platform_stats(db: AsyncSession = Depends(get_db)):
    """Get platform-wide statistics."""
    merchants = await db.execute(select(func.count(Merchant.id)))
    active_merchants = await db.execute(
        select(func.count(Merchant.id)).where(Merchant.is_active == True)
    )
    customers = await db.execute(select(func.count(Customer.id)))
    orders = await db.execute(select(func.count(Order.id)))
    revenue = await db.execute(select(func.sum(Order.total_amount)))
    products = await db.execute(select(func.count(Product.id)))

    return {
        "merchants": {
            "total": merchants.scalar() or 0,
            "active": active_merchants.scalar() or 0,
        },
        "customers": customers.scalar() or 0,
        "orders": orders.scalar() or 0,
        "total_revenue_syp": float(revenue.scalar() or 0),
        "products": products.scalar() or 0,
    }


@router.get("/merchants")
async def list_all_merchants(
    city: str | None = None,
    plan: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all merchants with filters."""
    stmt = select(Merchant).order_by(Merchant.created_at.desc()).limit(limit)

    if city:
        stmt = stmt.where(Merchant.city == city)
    if plan:
        stmt = stmt.where(Merchant.plan == plan)

    result = await db.execute(stmt)
    merchants = result.scalars().all()

    return {
        "count": len(merchants),
        "merchants": [
            {
                "id": m.id,
                "name": m.name,
                "business_name": m.business_name,
                "business_type": m.business_type,
                "city": m.city,
                "plan": m.plan,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat(),
            }
            for m in merchants
        ],
    }


@router.get("/merchants/by-city")
async def merchants_by_city(db: AsyncSession = Depends(get_db)):
    """Get merchant distribution by city."""
    result = await db.execute(
        select(Merchant.city, func.count(Merchant.id).label("count"))
        .where(Merchant.is_active == True)
        .group_by(Merchant.city)
        .order_by(func.count(Merchant.id).desc())
    )
    return {"cities": [{"city": r.city, "count": r.count} for r in result.all()]}


@router.get("/merchants/by-plan")
async def merchants_by_plan(db: AsyncSession = Depends(get_db)):
    """Get merchant distribution by subscription plan."""
    result = await db.execute(
        select(Merchant.plan, func.count(Merchant.id).label("count"))
        .group_by(Merchant.plan)
        .order_by(func.count(Merchant.id).desc())
    )

    plan_labels = {"free": "مجاني", "basic": "أساسي", "pro": "احترافي", "enterprise": "مؤسسات"}

    return {
        "plans": [
            {"plan": r.plan, "label": plan_labels.get(r.plan, r.plan), "count": r.count}
            for r in result.all()
        ]
    }


@router.get("/orders/overview")
async def orders_overview(db: AsyncSession = Depends(get_db)):
    """Get platform-wide order overview."""
    result = await db.execute(
        select(Order.status, func.count(Order.id).label("count"))
        .group_by(Order.status)
    )

    status_labels = {
        "pending": "بانتظار التأكيد",
        "confirmed": "مؤكد",
        "preparing": "قيد التحضير",
        "ready": "جاهز",
        "delivered": "تم التوصيل",
        "completed": "مكتمل",
        "cancelled": "ملغي",
    }

    return {
        "statuses": [
            {"status": r.status, "label": status_labels.get(r.status, r.status), "count": r.count}
            for r in result.all()
        ]
    }


@router.get("/payments/overview")
async def payments_overview(db: AsyncSession = Depends(get_db)):
    """Get payment statistics."""
    result = await db.execute(
        select(
            Payment.provider,
            Payment.status,
            func.count(Payment.id).label("count"),
            func.sum(Payment.amount).label("total"),
        )
        .group_by(Payment.provider, Payment.status)
    )

    return {
        "payments": [
            {
                "provider": r.provider,
                "status": r.status,
                "count": r.count,
                "total": float(r.total or 0),
            }
            for r in result.all()
        ]
    }
