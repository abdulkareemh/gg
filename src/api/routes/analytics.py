"""Analytics endpoints for merchant dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.models.database import get_db
from src.models.order import Order
from src.models.customer import Customer
from src.models.product import Product

router = APIRouter()


@router.get("/{merchant_id}/analytics/overview")
async def analytics_overview(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Get business overview analytics."""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # This week's stats
    week_result = await db.execute(
        select(
            func.count(Order.id),
            func.sum(Order.total_amount),
        ).where(
            and_(Order.merchant_id == merchant_id, Order.created_at >= week_ago)
        )
    )
    week_orders, week_revenue = week_result.one()

    # This month's stats
    month_result = await db.execute(
        select(
            func.count(Order.id),
            func.sum(Order.total_amount),
        ).where(
            and_(Order.merchant_id == merchant_id, Order.created_at >= month_ago)
        )
    )
    month_orders, month_revenue = month_result.one()

    # Total customers
    customer_count = await db.execute(
        select(func.count(Customer.id)).where(Customer.merchant_id == merchant_id)
    )
    total_customers = customer_count.scalar() or 0

    # Total products
    product_count = await db.execute(
        select(func.count(Product.id)).where(Product.merchant_id == merchant_id)
    )
    total_products = product_count.scalar() or 0

    return {
        "weekly": {
            "orders": week_orders or 0,
            "revenue": float(week_revenue or 0),
        },
        "monthly": {
            "orders": month_orders or 0,
            "revenue": float(month_revenue or 0),
        },
        "total_customers": total_customers,
        "total_products": total_products,
        "currency": "SYP",
    }


@router.get("/{merchant_id}/analytics/top-products")
async def top_products(merchant_id: int, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Get top selling products."""
    from src.models.order import OrderItem

    result = await db.execute(
        select(
            Product.name_ar,
            func.sum(OrderItem.quantity).label("total_sold"),
            func.sum(OrderItem.total_price).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.merchant_id == merchant_id)
        .group_by(Product.id, Product.name_ar)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )

    return {
        "products": [
            {"name_ar": row.name_ar, "total_sold": int(row.total_sold), "revenue": float(row.total_revenue)}
            for row in result.all()
        ]
    }


@router.get("/{merchant_id}/analytics/top-customers")
async def top_customers(merchant_id: int, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Get top customers by order count."""
    result = await db.execute(
        select(Customer)
        .where(Customer.merchant_id == merchant_id)
        .order_by(Customer.total_orders.desc())
        .limit(limit)
    )
    customers = result.scalars().all()

    return {
        "customers": [
            {"name": c.name or "Unknown", "phone": c.phone, "total_orders": c.total_orders}
            for c in customers
        ]
    }
