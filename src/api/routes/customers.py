"""Customer-facing endpoints — order history, profile."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db
from src.services.customer_service import CustomerService
from src.services.order_service import OrderService

router = APIRouter()


@router.get("/{merchant_id}/customers/{customer_phone}/orders")
async def customer_order_history(
    merchant_id: int, customer_phone: str, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """Get a customer's order history with a specific merchant."""
    c_svc = CustomerService(db)
    customer, is_new = await c_svc.get_or_create(merchant_id, customer_phone)

    if is_new:
        return {"customer": customer_phone, "orders": [], "message": "No order history found."}

    o_svc = OrderService(db)
    orders = await o_svc.get_customer_orders(customer.id, limit=limit)

    return {
        "customer": {
            "name": customer.name,
            "phone": customer.phone,
            "total_orders": customer.total_orders,
            "is_diaspora": customer.is_diaspora,
        },
        "orders": [
            {
                "id": o.id,
                "status": o.status,
                "total": float(o.total_amount),
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
    }


@router.get("/{merchant_id}/customers/top")
async def top_customers(merchant_id: int, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get top customers for a merchant."""
    c_svc = CustomerService(db)
    customers = await c_svc.get_top_customers(merchant_id, limit=limit)

    return {
        "customers": [
            {
                "name": c.name or "—",
                "phone": c.phone,
                "total_orders": c.total_orders,
                "last_order": c.last_order_at.isoformat() if c.last_order_at else None,
                "is_diaspora": c.is_diaspora,
            }
            for c in customers
        ],
    }
