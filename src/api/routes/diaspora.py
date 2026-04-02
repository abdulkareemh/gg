"""Diaspora ordering endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db
from src.services.diaspora_service import (
    DiasporaService,
    DiasporaOrder,
    convert_to_syp,
    convert_from_syp,
    EXCHANGE_RATES,
    DIASPORA_COUNTRIES,
)

router = APIRouter()


class DiasporaOrderCreate(BaseModel):
    sender_phone: str
    sender_name: str
    sender_country: str
    recipient_phone: str
    recipient_name: str
    recipient_city: str
    merchant_id: int
    items: list[dict]
    message: str = ""
    payment_currency: str = "USD"
    is_gift: bool = True


@router.get("/exchange-rates")
async def get_exchange_rates():
    """Get current exchange rates to SYP."""
    return {
        "base": "SYP",
        "rates": EXCHANGE_RATES,
        "supported_countries": DIASPORA_COUNTRIES,
    }


@router.post("/convert")
async def convert_currency(amount: float, from_currency: str, to_currency: str = "SYP"):
    """Convert between currencies."""
    if to_currency == "SYP":
        result = convert_to_syp(amount, from_currency)
        return {"amount": amount, "from": from_currency, "to": "SYP", "result": result}
    elif from_currency == "SYP":
        result = convert_from_syp(amount, to_currency)
        return {"amount": amount, "from": "SYP", "to": to_currency, "result": result}
    else:
        # Convert via SYP
        syp = convert_to_syp(amount, from_currency)
        if syp is None:
            return {"error": f"Unsupported currency: {from_currency}"}
        result = convert_from_syp(syp, to_currency)
        return {"amount": amount, "from": from_currency, "to": to_currency, "result": result}


@router.post("/orders")
async def create_diaspora_order(data: DiasporaOrderCreate, db: AsyncSession = Depends(get_db)):
    """Create a cross-border diaspora order."""
    svc = DiasporaService(db)

    order_data = DiasporaOrder(
        sender_phone=data.sender_phone,
        sender_name=data.sender_name,
        sender_country=data.sender_country,
        recipient_phone=data.recipient_phone,
        recipient_name=data.recipient_name,
        recipient_city=data.recipient_city,
        merchant_id=data.merchant_id,
        items=data.items,
        message=data.message,
        payment_currency=data.payment_currency,
        is_gift=data.is_gift,
    )

    result = await svc.create_diaspora_order(order_data)
    return result


@router.get("/merchants/{merchant_id}/stats")
async def diaspora_stats(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Get diaspora order statistics for a merchant."""
    svc = DiasporaService(db)
    return await svc.get_diaspora_stats(merchant_id)
