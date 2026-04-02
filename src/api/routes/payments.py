"""Payment webhook endpoints for provider callbacks."""

from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db
from src.services.payment_service import PaymentService

router = APIRouter()


@router.post("/payment/syriatel")
async def syriatel_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle SyriaTel Cash payment callback."""
    body = await request.json()
    transaction_id = body.get("transaction_id")
    status = body.get("status", "pending")

    if not transaction_id:
        return {"status": "ignored", "reason": "no transaction_id"}

    svc = PaymentService(db)
    payment = await svc.handle_callback("syriatel_cash", transaction_id, status)

    if payment and status == "completed":
        # TODO: Notify merchant that payment was received
        print(f"[PAYMENT] SyriaTel Cash payment {transaction_id} completed for order {payment.order_id}")

    return {"status": "ok"}


@router.post("/payment/mtn")
async def mtn_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle MTN Cash payment callback."""
    body = await request.json()
    transaction_id = body.get("reference_id") or body.get("transaction_id")
    status_raw = body.get("status", "PENDING")

    status_map = {
        "SUCCESSFUL": "completed",
        "FAILED": "failed",
        "PENDING": "pending",
    }
    status = status_map.get(status_raw, "pending")

    if not transaction_id:
        return {"status": "ignored"}

    svc = PaymentService(db)
    payment = await svc.handle_callback("mtn_cash", transaction_id, status)

    if payment and status == "completed":
        print(f"[PAYMENT] MTN Cash payment {transaction_id} completed for order {payment.order_id}")

    return {"status": "ok"}
